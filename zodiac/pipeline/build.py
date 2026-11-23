#!/usr/bin/env python3
"""卡卡夫人占星館 daily horoscope video builder.

usage:
  python3 zodiac/pipeline/build.py EP plan     # writes EP/tts/plan.json (what to synthesize)
  python3 zodiac/pipeline/build.py EP video    # renders EP/video.mp4 (<= ~16 MB) + EP/check/sheet.jpg

EP = zodiac/episodes/YYYY-MM-DD with episode.json (see zodiac/ROUTINE.md). Inputs the run puts in EP:
  tts/<id>.wav    one Gemini TTS clip per plan.json entry (open, s12..s1, bonus1, bonus2)
  open.mp4        Calywood lip-sync clip of 卡卡夫人 speaking tts/open.wav (optional: without it the
                  opening falls back to a slow zoom on assets/kaka_c.jpg with the same subtitles)
  bonus1.png, bonus2.png   Image MCP illustrations for the 開運推薦 cards
"""
import io, json, math, os, random, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import fftconvolve, stft
from scipy.ndimage import uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
ZROOT = os.path.dirname(HERE)
ASSET = lambda *p: os.path.join(ZROOT, "assets", *p)
W, H, FPS = 1080, 1920, 30
SPEED = 1.33                       # Gemini's delivery is slow; every clip is sped up by this (pitch kept)
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
FINAL_KBPS = 1300                  # final two-pass video bitrate -> ~16 MB for ~88 s (Postiz/FB fail on big files)

# Facebook full-screen viewer (measured on an iPhone 17 Pro, 2026-11-23), in 1080x1920 video coordinates:
# the phone is taller than 9:16, so FB scales the video up and crops ~55 px off each side; its UI sits on top.
# Keep text and plates inside SAFE_X; anything between y 1180 and 1670 must also stay left of RIGHT_COL_X.
FB_CROP = (55, 1025)               # visible x range on the phone
SAFE_X = (100, 980)                # where plates / text may go (room for phones that crop a bit more)
RIGHT_COL_X = 895                  # like / comment / share / save buttons: x >= 910, y 1190-1860
FB_ZONES = [(0, 0, W, 110), (80, 170, 140, 260), (820, 170, 1010, 260),      # status bar, back / search / more
            (905, 1190, W, 1870), (60, 1670, 905, 1880)]                     # action column, page name + caption
CARD_W = 2 * (RIGHT_COL_X - W // 2)  # 710: widest panel that stays clear of the action column

SIGN_INFO = {
    "aries": ("牡羊座", "3/21 - 4/19"), "taurus": ("金牛座", "4/20 - 5/20"), "gemini": ("雙子座", "5/21 - 6/21"),
    "cancer": ("巨蟹座", "6/22 - 7/22"), "leo": ("獅子座", "7/23 - 8/22"), "virgo": ("處女座", "8/23 - 9/22"),
    "libra": ("天秤座", "9/23 - 10/23"), "scorpio": ("天蠍座", "10/24 - 11/22"),
    "sagittarius": ("射手座", "11/23 - 12/21"), "capricorn": ("摩羯座", "12/22 - 1/19"),
    "aquarius": ("水瓶座", "1/20 - 2/18"), "pisces": ("雙魚座", "2/19 - 3/20"),
}
CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十", 11: "十一", 12: "十二"}
WEEK = "一二三四五六日"
STYLE_NORMAL = "Warm, cheerful, slightly mysterious astrologer greeting her audience in the morning. Taiwanese Mandarin accent. Brisk, lively pace."
STYLE_CHAT = "Warm, chatty, caring astrologer greeting her audience in the morning like old friends, smiling while she talks. Taiwanese Mandarin accent. Brisk, lively pace."
STYLE_TOP = STYLE_NORMAL + " Extra excited for the number one announcement."

def tts_text(s):
    """Gemini reads 雙 badly; 霜 has the same sound (shuāng). Screen text keeps 雙."""
    return s.replace("雙", "霜")

# ======================================================================= drawing helpers
FD = "/usr/share/fonts/opentype/noto/"
_fc = {}
def F(kind, size):
    k = (kind, size)
    if k not in _fc:
        path = {"serif": "NotoSerifCJK-Black.ttc", "sans": "NotoSansCJK-Black.ttc", "med": "NotoSansCJK-Medium.ttc"}[kind]
        _fc[k] = ImageFont.truetype(FD + path, size, index=3)  # TC
    return _fc[k]

GOLD_TOP, GOLD_BOT = (255, 236, 160), (222, 150, 40)
CREAM = (255, 230, 168)
NAVY = (12, 20, 64)

def eo(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

def eb(x, k=1.70158):
    x = min(max(x, 0.0), 1.0); return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2

def prog(t, start, dur): return min(max((t - start) / dur, 0.0), 1.0)

def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def paste(dst, src, x, y):
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, W - x), min(src.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0: return
    if (sx0, sy0, sx1, sy1) != (0, 0, src.width, src.height): src = src.crop((sx0, sy0, sx1, sy1))
    dst.alpha_composite(src, (x + sx0, y + sy0))

def paste_c(dst, src, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.003 or scale <= 0.01: return
    if abs(scale - 1) > 0.002:
        src = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.BICUBIC)
    paste(dst, with_alpha(src, alpha), cx - src.width / 2, cy - src.height / 2)

def text_layer(text, font, fill=(255, 255, 255), gradient=None, stroke=0, stroke_fill=(40, 10, 20), shadow=8, glow=None):
    pad = 40 + stroke + (glow[1] if glow else 0)
    runs = text if isinstance(text, list) else [(text, font, 0)]
    asc = max(f.getmetrics()[0] for _, f, _ in runs); desc = max(f.getmetrics()[1] for _, f, _ in runs)
    tw = sum(f.getlength(s) + g for s, f, g in runs)
    w, h = int(tw) + pad * 2, asc + desc + pad * 2
    mask = Image.new("L", (w, h), 0); smask = Image.new("L", (w, h), 0)
    dm, ds = ImageDraw.Draw(mask), ImageDraw.Draw(smask)
    x = pad
    for s, f, g in runs:
        dm.text((x, pad + asc), s, font=f, fill=255, anchor="ls")
        if stroke: ds.text((x, pad + asc), s, font=f, fill=255, anchor="ls", stroke_width=stroke, stroke_fill=255)
        x += f.getlength(s) + g
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    base = smask if stroke else mask
    if glow:
        gl = Image.new("RGBA", (w, h), glow[0] + (0,)); gl.putalpha(base.filter(ImageFilter.GaussianBlur(glow[1])).point(lambda v: min(255, int(v * 1.6))))
        out.alpha_composite(gl)
    if shadow:
        sl = Image.new("RGBA", (w, h), (0, 0, 10, 0)); sl.putalpha(base.filter(ImageFilter.GaussianBlur(shadow / 2)).point(lambda v: int(v * 0.75)))
        out.alpha_composite(sl, (0, shadow // 2))
    if stroke:
        st = Image.new("RGBA", (w, h), stroke_fill + (0,)); st.putalpha(smask); out.alpha_composite(st)
    if gradient:
        gy = np.linspace(0, 1, h)[:, None]; arr = np.zeros((h, w, 4), np.uint8)
        for c in range(3): arr[..., c] = (gradient[0][c] * (1 - gy) + gradient[1][c] * gy).astype(np.uint8)
        fl = Image.fromarray(arr, "RGBA")
    else:
        fl = Image.new("RGBA", (w, h), fill + (0,))
    fl.putalpha(mask); out.alpha_composite(fl)
    return out.crop(out.getbbox())

def fit_width(im, maxw):
    if im.width <= maxw: return im
    return im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)

def panel(w, h, fill=NAVY + (215,), border=(232, 180, 70, 255), r=30, bw=3):
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).rounded_rectangle((20, 26, 20 + w, 26 + h), r, fill=140)
    shl = Image.new("RGBA", im.size, (0, 0, 0, 0)); shl.putalpha(sh.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(shl)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), r, fill=fill, outline=border, width=bw)
    d.rounded_rectangle((28, 28, 12 + w, 12 + h), max(4, r - 8), outline=border[:3] + (90,), width=1)
    return im

def star_icon(size, filled):
    ss = 4; n = size * ss; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = n / 2
    pts = [(c + (c * 0.98 if i % 2 == 0 else c * 0.42) * math.cos(-math.pi / 2 + i * math.pi / 5),
            c * 1.06 + (c * 0.98 if i % 2 == 0 else c * 0.42) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    if filled: d.polygon(pts, fill=(255, 205, 70, 255), outline=(255, 245, 200, 255))
    else: d.polygon(pts, fill=(255, 255, 255, 40), outline=(255, 230, 170, 150))
    return im.resize((size, size), Image.LANCZOS)

def sparkle_sprite(size, color=(255, 248, 225)):
    ss = 3; n = size * ss; m = Image.new("L", (n, n), 0); d = ImageDraw.Draw(m); c = n / 2
    d.polygon([(c, 0), (c + n * 0.06, c), (c, n), (c - n * 0.06, c)], fill=255)
    d.polygon([(0, c), (c, c - n * 0.06), (n, c), (c, c + n * 0.06)], fill=255)
    d.ellipse((c - n * 0.12, c - n * 0.12, c + n * 0.12, c + n * 0.12), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(ss * 0.8)).resize((size, size), Image.LANCZOS)
    im = Image.new("RGBA", (size, size), color + (0,)); im.putalpha(m); return im

def fit_crop(path, maxdim):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    s = maxdim / max(im.size)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)

def glow_disc(radius, color=(255, 210, 110)):
    n = int(radius * 2.6); m = Image.new("L", (n, n), 0)
    ImageDraw.Draw(m).ellipse((n / 2 - radius, n / 2 - radius, n / 2 + radius, n / 2 + radius), fill=255)
    im = Image.new("RGBA", (n, n), color + (0,)); im.putalpha(m.filter(ImageFilter.GaussianBlur(radius * 0.18)).point(lambda v: int(v * 0.85)))
    return im

# ======================================================================= episode
class Ep:
    def __init__(self, ep):
        self.dir = os.path.abspath(ep)
        self.E = json.load(open(os.path.join(self.dir, "episode.json"), encoding="utf-8"))
        y, m, d = map(int, self.E["date"].split("-"))
        import datetime
        wd = WEEK[datetime.date(y, m, d).weekday()]
        self.y, self.m, self.d, self.wd = y, m, d, wd
        self.date_label = f"{m}月{d}日 週{wd}"
        self.work = os.path.join(self.dir, "work")
    def p(self, *a): return os.path.join(self.dir, *a)
    def w(self, *a): return os.path.join(self.work, *a)
    def signs(self):  # rank 12 -> 1
        return sorted(self.E["signs"], key=lambda s: -s["rank"])

def sign_line(s):
    name = SIGN_INFO[s["key"]][0]
    return f"第{CN_NUM[s['rank']]}名，{name}{'！' if s['rank'] == 1 else '。'}{s['say']}"

def cmd_plan(ep):
    e = Ep(ep)
    os.makedirs(e.p("tts"), exist_ok=True)
    plan = [dict(id="open", text=tts_text(e.E["opening"]), style=STYLE_CHAT)]
    for s in e.signs():
        plan.append(dict(id=f"s{s['rank']}", text=tts_text(sign_line(s)), style=STYLE_TOP if s["rank"] == 1 else STYLE_NORMAL))
    for i, b in enumerate(e.E["bonus"], 1):
        plan.append(dict(id=f"bonus{i}", text=tts_text(b["say"]), style=STYLE_CHAT))
    for x in plan: x.update(voice="Sulafat", language="cmn-tw", model="gemini-2.5-flash-tts", format="wav")
    json.dump(plan, open(e.p("tts", "plan.json"), "w"), ensure_ascii=False, indent=1)
    for x in plan: print(f"{x['id']:7s} {len(x['text']):3d} 字  {x['text']}")
    print("plan ->", e.p("tts", "plan.json"))

# ======================================================================= audio
SR = 48000
def run(cmd): subprocess.run(cmd, check=True)
def wav_len(p):
    w = wave.open(p); return w.getnframes() / w.getframerate()
def load_mono(p, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ar", str(sr), "-ac", "1", "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def speech_span(x, sr=SR, thr=0.02):
    idx = np.where(np.abs(x) > thr)[0]
    return (idx[0] / sr, idx[-1] / sr) if len(idx) else (0, len(x) / sr)

def proc_clip(src, dst, a, b):
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"atrim={a}:{b},asetpts=PTS-STARTPTS,atempo={SPEED},aresample={SR}",
         "-ac", "1", dst])

def pauses(path, thr="-30dB", d="0.07"):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=n={thr}:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    return list(zip(st, en))

def sub_chunks(text, maxlen=10):
    """Split the opening into subtitle chunks at punctuation, merging short phrases up to maxlen chars."""
    parts = re.findall(r"[^，。！？、]+[，。！？、]?", text)
    chunks, cur = [], ""
    for p in parts:
        core = re.sub(r"[，。！？、]", "", cur + p)
        if cur and len(core) > maxlen:
            chunks.append(cur); cur = p
        else:
            cur += p
        if p and p[-1] in "。！？" and len(re.sub(r"[，。！？、]", "", cur)) >= 4:
            chunks.append(cur); cur = ""
    if cur: chunks.append(cur)
    return [c.rstrip("，、。") for c in chunks if c.strip()]

def chunk_times(chunks, raw_wav):
    """Raw-narration start time of each chunk: char-proportional estimate snapped to the nearest pause."""
    x = load_mono(raw_wav); s0, s1 = speech_span(x)
    n = [len(re.sub(r"[，。！？、]", "", c)) for c in chunks]; tot = sum(n)
    ps = [(a + b) / 2 for a, b in pauses(raw_wav) if s0 < (a + b) / 2 < s1]
    times, acc = [s0], 0
    for k in range(1, len(chunks)):
        acc += n[k - 1]
        est = s0 + (s1 - s0) * acc / tot
        near = min(ps, key=lambda p: abs(p - est)) if ps else est
        t = near if abs(near - est) < 0.9 else est
        times.append(max(t, times[-1] + 0.4))
    return times, s1

def dtw_map(clip, ref, out):
    """narration time -> clip time (clip lips follow a re-performance of the narration)."""
    sr = 16000
    def feat(x):
        _, _, Z = stft(x, fs=sr, nperseg=400, noverlap=240)
        S = np.log(np.abs(Z) ** 2 + 1e-8); e = np.linspace(2, 180, 25).astype(int)
        B = np.stack([S[e[i]:e[i + 1]].mean(0) for i in range(24)]); B = B - B.mean(0, keepdims=True)
        return B / (np.linalg.norm(B, axis=0, keepdims=True) + 1e-6)
    A, R = feat(load_mono(clip, sr)), feat(load_mono(ref, sr))
    n, m = R.shape[1], A.shape[1]; band = 120
    D = np.full((n + 1, m + 1), 1e18); D[0, 0] = 0; cost = 1 - R.T @ A
    for i in range(1, n + 1):
        j0, j1 = max(1, int(i * m / n) - band), min(m, int(i * m / n) + band)
        for j in range(j0, j1 + 1):
            D[i, j] = cost[i - 1, j - 1] + min(D[i - 1, j - 1], D[i - 1, j] + 0.3, D[i, j - 1] + 0.3)
    lo = max(1, m - band); i, j = n, int(np.argmin(D[n, lo:]) + lo); path = []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        k = np.argmin([D[i - 1, j - 1], D[i - 1, j] + 0.3, D[i, j - 1] + 0.3])
        i, j = (i - 1, j - 1) if k == 0 else (i - 1, j) if k == 1 else (i, j - 1)
    path.reverse(); mp = np.zeros(n); cnt = np.zeros(n)
    for a, b in path: mp[a] += b; cnt[a] += 1
    mp = np.maximum.accumulate(uniform_filter1d(mp / np.maximum(cnt, 1), 25))
    np.save(out, mp / 100.0)
    c = float(np.mean([cost[a, b] for a, b in path]))
    return c

# ======================================================================= layers
BG = HEADER = None
rng0 = random.Random(7)
SPARKLES = [dict(x=rng0.uniform(150, 930), y=rng0.uniform(260, 1780), s=rng0.choice([14, 18, 22, 28]),
                 f=rng0.uniform(0.35, 0.9), p=rng0.uniform(0, 6.28)) for _ in range(34)]
SPR = None
STAR_ON = STAR_OFF = None

def init_static(e):
    global BG, HEADER, SPR, STAR_ON, STAR_OFF
    bg = Image.open(ASSET("bg.jpg")).convert("RGBA")
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse((90, 330, 990, 1650), fill=120)
    dk = Image.new("RGBA", (W, H), (4, 6, 26, 0)); dk.putalpha(m.filter(ImageFilter.GaussianBlur(120))); bg.alpha_composite(dk)
    BG = bg
    SPR = {s: sparkle_sprite(s) for s in (14, 18, 22, 28)}
    STAR_ON, STAR_OFF = star_icon(36, True), star_icon(36, False)
    p = panel(780, 96, r=48)
    t1 = text_layer("卡卡夫人占星館", F("serif", 44), gradient=(GOLD_TOP, GOLD_BOT), shadow=4)
    t2 = text_layer(f"{e.date_label}・今日運勢", F("med", 36), shadow=4)
    x0 = (p.width - (t1.width + 26 + t2.width)) // 2; cy = p.height // 2
    p.alpha_composite(t1, (x0, cy - t1.height // 2)); p.alpha_composite(t2, (x0 + t1.width + 26, cy - t2.height // 2 + 2))
    HEADER = p

def draw_sparkles(fr, T):
    for sp in SPARKLES:
        a = (0.5 + 0.5 * math.sin(6.283 * sp["f"] * T + sp["p"])) ** 2
        if a >= 0.05: paste_c(fr, SPR[sp["s"]], sp["x"], sp["y"], alpha=a)

def split_tip(tip):
    i = tip.find("，")
    return [tip[:i + 1], tip[i + 1:]] if 0 < i < len(tip) - 1 else [tip]

def sign_layers(s):
    L = {}; rk = s["rank"]; name, rng = SIGN_INFO[s["key"]]
    L["rank"] = text_layer([("第", F("serif", 84), 14), (str(rk), F("serif", 150 if rk <= 3 else 132), 14), ("名", F("serif", 84), 0)],
                           None, gradient=(GOLD_TOP, GOLD_BOT), stroke=6, stroke_fill=(90, 14, 30),
                           glow=((255, 200, 90), 22) if rk <= 3 else None)
    L["icon"] = fit_crop(ASSET("signs", s["key"] + ".png"), 460)
    L["glow"] = glow_disc(250, (255, 205, 110) if rk > 3 else (255, 225, 140))
    L["name"] = fit_width(text_layer(name, F("serif", 108), stroke=6, stroke_fill=(20, 26, 80), glow=((120, 170, 255), 18)), CARD_W)
    L["range"] = text_layer(rng, F("med", 38), fill=CREAM, shadow=4)
    cw = CARD_W
    tp = panel(cw, 178)
    ls = [fit_width(text_layer(x, F("sans", 54), shadow=4), cw - 40) for x in split_tip(s["tip"])]
    y = (tp.height - (sum(x.height for x in ls) + 18 * (len(ls) - 1))) // 2 + 2
    for x in ls: tp.alpha_composite(x, ((tp.width - x.width) // 2, y)); y += x.height + 18
    L["tip"] = tp
    sp = panel(cw, 222); L["score_pos"] = []
    for k, (lab, v) in enumerate([("愛情", s["love"]), ("事業", s["work"]), ("財運", s["money"])]):
        cx = 20 + cw // 6 + k * cw // 3; lt = text_layer(lab, F("med", 36), fill=CREAM, shadow=3)
        sp.alpha_composite(lt, (cx - lt.width // 2, 34)); L["score_pos"].append((cx, int(v)))
    d = ImageDraw.Draw(sp); d.line((60, 142, cw - 20, 142), fill=(232, 180, 70, 110), width=2)
    lc = text_layer("幸運色", F("med", 34), fill=CREAM, shadow=3); cn = text_layer(s["color"], F("sans", 38), shadow=3)
    ln = text_layer("幸運數字", F("med", 34), fill=CREAM, shadow=3)
    nn = text_layer(str(s["num"]), F("serif", 48), gradient=(GOLD_TOP, GOLD_BOT), shadow=3)
    ry, sw = 206, 40
    x = 20 + int(cw * 0.27) - (lc.width + 14 + sw + 12 + cn.width) // 2
    sp.alpha_composite(lc, (x, ry - lc.height // 2)); x += lc.width + 14
    col = tuple(int(s["hex"][i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    d.ellipse((x, ry - sw // 2, x + sw, ry + sw // 2), fill=col, outline=(255, 255, 255, 230), width=3); x += sw + 12
    sp.alpha_composite(cn, (x, ry - cn.height // 2))
    x = 20 + int(cw * 0.75) - (ln.width + 16 + nn.width) // 2
    sp.alpha_composite(ln, (x, ry - ln.height // 2)); sp.alpha_composite(nn, (x + ln.width + 16, ry - nn.height // 2 - 2))
    L["score"] = sp
    return L

def frame_sign(L, s, t, T, dur):
    fr = BG.copy(); draw_sparkles(fr, T); paste_c(fr, HEADER, W / 2, 315)   # below FB's back/search/more icons
    out = 1 - prog(t, dur - 0.22, 0.22)
    p = prog(t, 0.0, 0.38); paste_c(fr, L["rank"], W / 2, 465, scale=1.5 - 0.5 * eb(p), alpha=eo(p) * out)
    p = prog(t, 0.08, 0.5); bob = math.sin(T * 2.2) * 6
    pulse = 0.55 + 0.25 * math.sin(T * 3.0) + (0.2 if s["rank"] <= 3 else 0)
    paste_c(fr, L["glow"], W / 2, 772 + bob, scale=0.9 + 0.1 * eo(p), alpha=pulse * eo(p) * out)
    paste_c(fr, L["icon"], W / 2, 772 + bob, scale=0.55 + 0.45 * eb(p), alpha=eo(p) * out)
    p = eo(prog(t, 0.3, 0.4))
    paste_c(fr, L["name"], W / 2, 1070 + 40 * (1 - p), alpha=p * out); paste_c(fr, L["range"], W / 2, 1148 + 40 * (1 - p), alpha=p * out)
    p = eo(prog(t, 0.45, 0.4)); paste_c(fr, L["tip"], W / 2, 1280 + 50 * (1 - p), alpha=p * out)
    p = eo(prog(t, 0.6, 0.4))
    if p * out > 0.003:
        layer = L["score"].copy(); k = 0
        for cx, v in L["score_pos"]:
            for j in range(5):
                st = STAR_ON if j < v else STAR_OFF; ps = prog(t, 0.85 + k * 0.05, 0.25); k += 1
                if ps <= 0: continue
                ss = 0.4 + 0.6 * eb(ps)
                s2 = st.resize((max(1, int(36 * ss)),) * 2, Image.BICUBIC) if abs(ss - 1) > 0.01 else st
                layer.alpha_composite(with_alpha(s2, min(1, ps * 2)), (int(cx - 80 + j * 40 - s2.width / 2), int(112 - s2.height / 2)))
        paste(fr, with_alpha(layer, p * out), W / 2 - layer.width / 2, 1512 - layer.height / 2 + 50 * (1 - p))
    return fr

def bonus_layers(b, img):
    L = {}
    hp = panel(780, 96, r=48); t = text_layer("卡卡夫人的今日開運推薦", F("serif", 46), gradient=(GOLD_TOP, GOLD_BOT), shadow=4)
    hp.alpha_composite(t, ((hp.width - t.width) // 2, (hp.height - t.height) // 2)); L["header"] = hp
    chip = panel(420, 84, fill=(176, 18, 46, 245), border=(245, 200, 90, 255), r=42)
    t = fit_width(text_layer(b["chip"], F("sans", 50), shadow=4), 390)
    chip.alpha_composite(t, ((chip.width - t.width) // 2, (chip.height - t.height) // 2)); L["chip"] = chip
    L["img"] = Image.open(img).convert("RGBA").resize((820, 820), Image.LANCZOS)
    m = Image.new("L", (740, 740), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 739, 739), 40, fill=255); L["mask"] = m
    fr = Image.new("RGBA", (800, 800), (0, 0, 0, 0)); sh = Image.new("L", fr.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, 770, 780), 44, fill=170)
    s2 = Image.new("RGBA", fr.size, (0, 0, 0, 0)); s2.putalpha(sh.filter(ImageFilter.GaussianBlur(14))); fr.alpha_composite(s2); L["shadow"] = fr
    br = Image.new("RGBA", (800, 800), (0, 0, 0, 0)); ImageDraw.Draw(br).rounded_rectangle((26, 26, 774, 774), 46, outline=(240, 190, 80, 255), width=7)
    L["border"] = br; L["glow"] = glow_disc(420, (255, 205, 110))
    L["title"] = fit_width(text_layer(b["title"], F("serif", 96), stroke=6, stroke_fill=(20, 26, 80), glow=((120, 170, 255), 18)), CARD_W)
    tp = panel(CARD_W, 160)
    ls = [fit_width(text_layer(x, F("sans", 48), fill=(255, 255, 255) if i == 0 else CREAM, shadow=4), CARD_W - 40) for i, x in enumerate(b["lines"][:2])]
    y = (tp.height - (sum(x.height for x in ls) + 16 * (len(ls) - 1))) // 2 + 2
    for x in ls: tp.alpha_composite(x, ((tp.width - x.width) // 2, y)); y += x.height + 16
    L["reason"] = tp
    return L

def frame_bonus(L, t, T, dur, first, last):
    fr = BG.copy(); draw_sparkles(fr, T)
    out = 1 - prog(t, dur - 0.22, 0.22)
    paste_c(fr, L["header"], W / 2, 315, alpha=(eo(prog(t, 0, 0.35)) if first else 1.0) * (out if last else 1.0))
    p = prog(t, 0.05, 0.4); paste_c(fr, L["chip"], W / 2, 432, scale=0.6 + 0.4 * eb(p), alpha=eo(p) * out)
    p = prog(t, 0.15, 0.55); a = eo(p) * out
    if a > 0.003:
        cs = int(800 / (1.0 + 0.05 * (t / dur))); c0 = (820 - cs) // 2
        crop = L["img"].crop((c0, c0, c0 + cs, c0 + cs)).resize((740, 740), Image.BICUBIC); crop.putalpha(L["mask"])
        card = L["shadow"].copy(); card.alpha_composite(crop, (30, 30)); card.alpha_composite(L["border"])
        k = 0.92                     # 680 px picture: clear of the phone crop and FB's action column
        paste_c(fr, L["glow"], W / 2, 830, scale=k, alpha=(0.35 + 0.1 * math.sin(T * 2.5)) * a)
        paste_c(fr, card, W / 2, 830, scale=(0.82 + 0.18 * eb(p)) * k, alpha=a)
    p = eo(prog(t, 0.4, 0.4)); paste_c(fr, L["title"], W / 2, 1252 + 40 * (1 - p), alpha=p * out)
    p = eo(prog(t, 0.6, 0.4)); paste_c(fr, L["reason"], W / 2, 1412 + 50 * (1 - p), alpha=p * out)
    return fr

# --- live (opening / outro) overlays
def bottom_grad():
    y = np.arange(H)
    a = np.repeat((np.clip((y - 980) / 700, 0, 1) ** 1.3 * 215)[:, None], W, 1)
    g = Image.new("RGBA", (W, H), (6, 8, 30, 0)); g.putalpha(Image.fromarray(a.astype(np.uint8)))
    t = np.repeat((np.clip((170 - y) / 170, 0, 1) * 120)[:, None], W, 1)
    g2 = Image.new("RGBA", (W, H), (6, 8, 30, 0)); g2.putalpha(Image.fromarray(t.astype(np.uint8))); g.alpha_composite(g2)
    return g

def vplate(cells, fill, border):
    gap = 6; inner = sum(18 if c == "div" else c.height for c in cells) + gap * (len(cells) - 1)
    w, h = 124, inner + 64; p = panel(w, h, fill=fill, border=border, r=w // 2); d = ImageDraw.Draw(p); y = 52
    for c in cells:
        if c == "div":
            d.ellipse((20 + w // 2 - 5, y + 4, 20 + w // 2 + 5, y + 14), fill=(240, 190, 80, 255)); y += 18 + gap; continue
        p.alpha_composite(c, (20 + (w - c.width) // 2, y)); y += c.height + gap
    return p

def nametag():
    cells = [sparkle_sprite(34, (255, 225, 140))] + [text_layer(ch, F("serif", 76), gradient=(GOLD_TOP, GOLD_BOT), shadow=3) for ch in "卡卡夫人"]
    return vplate(cells, (176, 18, 46, 240), (245, 200, 90, 255))

def dateplate(e):
    cells = [text_layer(str(e.m), F("serif", 54), gradient=(GOLD_TOP, GOLD_BOT), shadow=3), text_layer("月", F("serif", 50), shadow=3),
             text_layer(str(e.d), F("serif", 54), gradient=(GOLD_TOP, GOLD_BOT), shadow=3), text_layer("日", F("serif", 50), shadow=3), "div"] + \
            [text_layer(ch, F("sans", 52), fill=CREAM, shadow=3) for ch in "星期" + e.wd]
    return vplate(cells, NAVY + (215,), (232, 180, 70, 255))

def sub_layer(text):
    """One subtitle chunk, at most CARD_W wide so it never runs under FB's action buttons; a long phrase wraps to two lines."""
    mk = lambda s: text_layer(s, F("sans", 68), stroke=8, stroke_fill=(12, 14, 40), shadow=8, glow=((0, 0, 18), 16))
    pad = 60                                    # text_layer leaves ~30 px of faint glow on each side
    im = mk(text)
    if im.width - pad <= CARD_W or len(text) <= 10: return fit_width(im, CARD_W + pad)
    cut = (len(text) + 1) // 2
    a, b = mk(text[:cut]), mk(text[cut:]); y2 = a.height - 48
    out = Image.new("RGBA", (max(a.width, b.width), y2 + b.height), (0, 0, 0, 0))
    out.alpha_composite(a, ((out.width - a.width) // 2, 0)); out.alpha_composite(b, ((out.width - b.width) // 2, y2))
    return fit_width(out, CARD_W + pad)

def top3_panel(e):
    by = {s["rank"]: s for s in e.E["signs"]}
    p = panel(780, 196, r=32); t = text_layer("今日幸運前三名", F("serif", 38), gradient=(GOLD_TOP, GOLD_BOT), shadow=3)
    p.alpha_composite(t, ((p.width - t.width) // 2, 26))
    for rk, cx in [(2, 170), (1, 410), (3, 650)]:
        ic = fit_crop(ASSET("signs", by[rk]["key"] + ".png"), 92 if rk == 1 else 80)
        p.alpha_composite(ic, (cx - ic.width // 2, 128 - ic.height // 2))
        lab = ("冠軍 " if rk == 1 else f"第{rk}名 ") + SIGN_INFO[by[rk]["key"]][0]
        lt = text_layer(lab, F("sans", 28 if rk == 1 else 25), gradient=(GOLD_TOP, GOLD_BOT) if rk == 1 else None, shadow=3)
        p.alpha_composite(lt, (cx - lt.width // 2, 168))
    return p

def cta_panel():
    p = panel(780, 176, r=32)
    t1 = text_layer("你今天排第幾名？留言告訴我", F("sans", 44), shadow=3)
    t2 = text_layer("追蹤卡卡夫人・每天早上見", F("sans", 42), gradient=(GOLD_TOP, GOLD_BOT), shadow=3)
    p.alpha_composite(t1, ((p.width - t1.width) // 2, 40)); p.alpha_composite(t2, ((p.width - t2.width) // 2, 112))
    return p

def clip_frames(clip, mapf, a, n, src_fps=24):
    mp = np.load(mapf)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", clip, "-an", "-vf",
                            f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    jpgs = []                      # stream-decode: keep JPEGs, never the whole raw clip (8 GB box)
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        bio = io.BytesIO(); Image.frombytes("RGB", (W, H), buf).save(bio, "JPEG", quality=93); jpgs.append(bio.getvalue())
    dec.stdout.close(); dec.wait()
    fs = len(jpgs)
    cache = {}
    def get(k):
        k = min(max(k, 0), fs - 1)
        if k not in cache:
            if len(cache) > 8: cache.pop(next(iter(cache)))
            cache[k] = Image.open(io.BytesIO(jpgs[k])).convert("RGB")
        return cache[k]
    for i in range(n):
        tc = float(np.interp((a + i / FPS * SPEED) * 100, np.arange(len(mp)), mp)); f = tc * src_fps
        k0 = int(math.floor(f)); w = f - k0
        im = get(k0) if w < 0.15 else get(k0 + 1) if w > 0.85 else Image.blend(get(k0), get(k0 + 1), w)
        yield im.convert("RGBA")

def still_frames(n):
    """Fallback opening (no Calywood clip): slow push-in on the 卡卡夫人 photo."""
    src = Image.open(ASSET("kaka_c.jpg")).convert("RGB")
    s = max(W / src.width, H / src.height) * 1.04
    big = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
    for i in range(n):
        z = 1.0 + 0.04 * i / max(1, n - 1)
        ch = big.height / 1.04 / z; cw = ch * W / H
        if cw > big.width: cw = big.width / z; ch = cw * H / W
        x0 = (big.width - cw) / 2; y0 = (big.height - ch) * 0.35
        yield big.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC).convert("RGBA")

# ======================================================================= scenes
def render_scene(job):
    epdir, idx, seg = job
    e = Ep(epdir); init_static(e)
    n = int(round(seg["dur"] * FPS))
    out = e.w("scenes", f"{idx:02d}.mp4"); tmp = out.replace(".mp4", ".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
                         + ENC + [tmp], stdin=subprocess.PIPE)
    k = seg["kind"]
    if k == "sign":
        s = seg["data"]; L = sign_layers(s)
        frames = (frame_sign(L, s, i / FPS, seg["start"] + i / FPS, seg["dur"]) for i in range(n))
    elif k == "bonus":
        L = bonus_layers(seg["data"], seg["img"])
        frames = (frame_bonus(L, i / FPS, seg["start"] + i / FPS, seg["dur"], seg["first"], seg["last"]) for i in range(n))
    else:
        frames = live_frames(e, seg, n)
    for fr in frames: p.stdin.write(fr.convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError(f"scene {idx} failed")
    os.replace(tmp, out)
    return idx

def live_frames(e, seg, n):
    G = bottom_grad(); total = n / FPS
    src = clip_frames(seg["clip"], seg["map"], seg["a"], n) if seg.get("clip") else still_frames(n)
    if seg["kind"] == "open":
        NT, DP = nametag(), dateplate(e)
        subs = [(t, sub_layer(x)) for t, x in seg["subs"]]
        sub_y = 1462 if seg.get("clip") else 1150   # still photo: ball sits lower, so put subtitles between chin and ball
        t_end_plates = subs[-1][0] if len(subs) > 1 else total
        for i, fr in enumerate(src):
            t = i / FPS; fr.alpha_composite(G)
            pin, pout = eo(prog(t, 0.25, 0.45)), 1 - prog(t, t_end_plates - 0.1, 0.3)
            paste_c(fr, NT, 912 + 70 * (1 - pin), 620, alpha=pin * pout)    # inside SAFE_X: FB crops ~55 px per side
            paste_c(fr, DP, 162 - 70 * (1 - pin), 620, alpha=pin * pout)
            fo = 1 - prog(t, total - 0.22, 0.22)
            for k, (s0, lay) in enumerate(subs):
                s1 = subs[k + 1][0] if k + 1 < len(subs) else total
                if s0 - 0.02 <= t < s1:
                    a = eo(prog(t, s0, 0.12)); paste_c(fr, lay, W / 2, sub_y, scale=0.94 + 0.06 * a, alpha=a * fo)
            if fo < 1: fr.alpha_composite(Image.new("RGBA", (W, H), (4, 6, 26, int(255 * (1 - fo)))))
            yield fr
    else:
        T3, CTA = top3_panel(e), cta_panel()
        for i, fr in enumerate(src):
            t = i / FPS; fr.alpha_composite(G)
            p, o = prog(t, 0.15, 0.45), 1 - prog(t, 2.7, 0.2)
            paste_c(fr, T3, 515, 975, scale=0.85 + 0.15 * eb(p), alpha=eo(p) * o)
            p = prog(t, 2.9, 0.45); paste_c(fr, CTA, 515, 975, scale=0.85 + 0.15 * eb(p), alpha=eo(p))
            end = prog(t, total - 0.6, 0.6)
            if end > 0: fr.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * end))))
            yield fr

# ======================================================================= mix
def note(m): return 440.0 * 2 ** ((m - 69) / 12)

def make_mix(e, segs, total, out):
    N = int(total * SR) + SR; rng = np.random.default_rng(3); t = np.arange(N) / SR
    chords = [[53, 57, 60, 64], [55, 59, 62, 64], [52, 55, 59, 62], [57, 60, 64, 67]]; CL = 4.0
    pad = np.zeros(N, np.float32)
    for k in range(int(total / CL) + 2):
        s0 = int((k * CL - 1.0) * SR); s1 = int(((k + 1) * CL + 1.0) * SR); a, b = max(0, s0), min(N, s1)
        if a >= b: continue
        loc = (np.arange(a, b) - s0) / SR
        env = np.clip(loc / 1.5, 0, 1) * np.clip((s1 - s0) / SR - loc, 0, 1.5) / 1.5
        seg = np.zeros(b - a)
        for mm in chords[k % 4]:
            for det in (-0.7, 0.7):
                f = note(mm) + det; seg += np.sin(2 * np.pi * f * t[a:b]) * 0.5 + 0.12 * np.sin(4 * np.pi * f * t[a:b])
        pad[a:b] += seg * env * 0.05
    pl = np.zeros(N, np.float32); tp = 0.6
    while tp < total - 1:
        f = note(rng.choice(chords[int(tp / CL) % 4]) + 24); Lr = int(1.2 * SR); s = int(tp * SR); tl = np.arange(Lr) / SR
        tone = (np.sin(2 * np.pi * f * tl) + 0.3 * np.sin(2 * np.pi * 2.01 * f * tl)) * np.exp(-tl * 4.5)
        en = min(N, s + Lr); pl[s:en] += tone[:en - s] * rng.uniform(0.04, 0.07); tp += rng.choice([0.6, 0.9, 1.2])
    ir = rng.standard_normal(int(1.8 * SR)).astype(np.float32) * np.exp(-np.arange(int(1.8 * SR)) / SR * 3.2); ir[0] = 6.0
    music = fftconvolve(pad + pl, ir)[:N].astype(np.float32)
    end = int(total * SR)
    music = music / (np.sqrt(np.mean(music[:end] ** 2)) + 1e-9) * 0.045
    fade = np.ones(N, np.float32); fade[:int(1.5 * SR)] = np.linspace(0, 1, int(1.5 * SR))
    fade[end - 2 * SR:end] = np.linspace(1, 0, 2 * SR); fade[end:] = 0; music *= fade
    def chime(big):
        Lc = 2 * SR; tl = np.arange(Lc) / SR; o = np.zeros(Lc, np.float32)
        for i, mm in enumerate([84, 88, 91, 96] if big else [88, 95]):
            off = int(i * 0.07 * SR); f = note(mm)
            o[off:] += ((np.sin(2 * np.pi * f * tl) + 0.25 * np.sin(2 * np.pi * 2.76 * f * tl)) * np.exp(-tl * 3.0))[:Lc - off]
        return o / np.max(np.abs(o)) * (0.2 if big else 0.16)
    sfx = np.zeros(N, np.float32); voice = np.zeros(N, np.float32)
    for s in segs:
        if s["kind"] in ("sign", "bonus", "outro"):
            c = chime(s["kind"] == "outro" or (s["kind"] == "sign" and s["data"]["rank"] == 1))
            i = int(s["start"] * SR); en = min(N, i + len(c)); sfx[i:en] += c[:en - i]
        v = load_mono(s["wav"]); v = v / (np.max(np.abs(v)) + 1e-9) * 0.88
        i = int((s["start"] + s["lead"]) * SR); en = min(N, i + len(v)); voice[i:en] += v[:en - i]
    venv = np.convolve(np.abs(voice), np.ones(4800) / 4800, mode="same")
    mix = (voice + music * (1.0 - 0.35 * np.clip(venv / 0.05, 0, 1)) + sfx)[:end]
    mix /= max(1.0, np.max(np.abs(mix)) / 0.97)
    o = wave.open(out, "w"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes()); o.close()

# ======================================================================= video command
def cmd_video(ep):
    e = Ep(ep); os.makedirs(e.w("proc"), exist_ok=True); os.makedirs(e.w("scenes"), exist_ok=True); os.makedirs(e.p("check"), exist_ok=True)
    need = ["open"] + [f"s{s['rank']}" for s in e.signs()] + [f"bonus{i}" for i in range(1, len(e.E["bonus"]) + 1)]
    miss = [x for x in need if not os.path.exists(e.p("tts", x + ".wav"))]
    miss += [f"bonus{i}.png" for i in range(1, len(e.E["bonus"]) + 1) if not os.path.exists(e.p(f"bonus{i}.png"))]
    if miss: sys.exit("missing inputs: " + ", ".join(miss))
    segs, t = [], 0.0
    def add(seg):
        nonlocal t
        seg["dur"] = math.ceil(seg["dur"] * FPS) / FPS; seg["start"] = t; segs.append(seg); t += seg["dur"]
    # opening
    raw = e.w("proc", "open_raw.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", e.p("tts", "open.wav"), "-ar", str(SR), "-ac", "1", raw])
    x = load_mono(raw); s0, s1 = speech_span(x); L0 = len(x) / SR
    a, b = max(0.0, s0 - 0.15), min(L0, s1 + 0.13)
    proc_clip(raw, e.w("proc", "open.wav"), a, b)
    chunks = sub_chunks(e.E["opening"]); times, _ = chunk_times(chunks, raw)
    subs = [((tt - a) / SPEED, c) for tt, c in zip(times, chunks)]
    clip = e.p("open.mp4") if os.path.exists(e.p("open.mp4")) else None
    oseg = dict(kind="open", dur=(b - a) / SPEED, lead=0.0, wav=e.w("proc", "open.wav"), a=a, subs=subs)
    if clip:
        c = dtw_map(clip, raw, e.w("open_map.npy")); oseg.update(clip=clip, map=e.w("open_map.npy"))
        print(f"opening: Calywood clip aligned (path cost {c:.3f}; > 0.35 means the clip may not match the narration)")
    else:
        print("opening: NO open.mp4 -> still-photo fallback")
    add(oseg)
    for s in e.signs():
        src = e.p("tts", f"s{s['rank']}.wav"); xx = load_mono(src); q0, q1 = speech_span(xx)
        dst = e.w("proc", f"s{s['rank']}.wav"); proc_clip(src, dst, max(0, q0 - 0.02), q1 + 0.02)
        add(dict(kind="sign", data=s, lead=0.12, dur=0.12 + wav_len(dst) + 0.2, wav=dst))
    nb = len(e.E["bonus"])
    for i, bb in enumerate(e.E["bonus"], 1):
        src = e.p("tts", f"bonus{i}.wav"); xx = load_mono(src); q0, q1 = speech_span(xx)
        dst = e.w("proc", f"bonus{i}.wav"); proc_clip(src, dst, max(0, q0 - 0.02), q1 + 0.02)
        add(dict(kind="bonus", data=bb, img=e.p(f"bonus{i}.png"), first=i == 1, last=i == nb, lead=0.2, dur=0.2 + wav_len(dst) + 0.25, wav=dst))
    oa, ob = 0.05, 7.45
    proc_clip(ASSET("outro", "outro_raw.wav"), e.w("proc", "outro.wav"), oa, ob)
    add(dict(kind="outro", lead=0.0, dur=(ob - oa) / SPEED + 0.5, wav=e.w("proc", "outro.wav"),
             clip=ASSET("outro", "outro.mp4"), map=ASSET("outro", "outro_map.npy"), a=oa))
    total = t
    print(f"timeline: {len(segs)} scenes, {total:.1f} s")
    for s in segs: print(f"  {s['kind']:6s} {s['start']:6.2f} {s['dur']:5.2f}")
    with Pool(2) as pool:
        for idx in pool.imap_unordered(render_scene, [(e.dir, i, s) for i, s in enumerate(segs)]): print("  scene", idx, "ok", flush=True)
    with open(e.w("list.txt"), "w") as f:
        for i in range(len(segs)): f.write(f"file '{e.w('scenes', f'{i:02d}.mp4')}'\n")
    make_mix(e, segs, total, e.w("mix.wav"))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", e.w("list.txt"), "-c", "copy", e.w("video_noaudio.mp4")])
    run(["ffmpeg", "-v", "error", "-y", "-i", e.w("video_noaudio.mp4"), "-i", e.w("mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", e.w("video_hq.mp4")])
    kb = FINAL_KBPS
    for _ in range(3):
        plog = e.w("x264pass")
        run(["ffmpeg", "-v", "error", "-y", "-i", e.w("video_hq.mp4"), "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kb}k",
             "-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"])
        run(["ffmpeg", "-v", "error", "-y", "-i", e.w("video_hq.mp4"), "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kb}k",
             "-pass", "2", "-passlogfile", plog, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
             e.p("video.tmp.mp4")])
        size = os.path.getsize(e.p("video.tmp.mp4"))
        if size <= 18_500_000: break
        kb = int(kb * 0.85)
    os.replace(e.p("video.tmp.mp4"), e.p("video.mp4"))
    # contact sheet
    picks = [("開場", 1.2), ("開場字幕", segs[0]["dur"] * 0.6), ("第12名", segs[1]["start"] + segs[1]["dur"] - 0.5),
             ("第1名", segs[12]["start"] + segs[12]["dur"] - 0.5), ("推薦1", segs[13]["start"] + segs[13]["dur"] - 0.5),
             ("推薦2", segs[-2]["start"] + segs[-2]["dur"] - 0.5), ("結尾", segs[-1]["start"] + 1.5), ("結尾CTA", segs[-1]["start"] + 4.0)]
    ims = []
    for lab, tt in picks:
        fp = e.w(f"chk_{len(ims)}.jpg")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tt:.2f}", "-i", e.p("video.mp4"), "-frames:v", "1", "-vf", "scale=270:480", fp])
        im = Image.open(fp).convert("RGB"); ImageDraw.Draw(im).text((8, 8), lab, font=F("sans", 24), fill=(255, 255, 0)); ims.append(im)
    sheet = Image.new("RGB", (275 * 4, 485 * 2), (255, 255, 255))
    for i, im in enumerate(ims): sheet.paste(im, ((i % 4) * 275, (i // 4) * 485))
    sheet.save(e.p("check", "sheet.jpg"), quality=85)
    # what an iPhone shows in FB's full-screen viewer: side crop + FB's UI (red). Nothing important may sit under red.
    fb = []
    for k, (lab, tt) in enumerate([("開場字幕", segs[0]["dur"] * 0.6), ("第12名", picks[2][1]), ("推薦1", picks[4][1]), ("結尾CTA", picks[7][1])]):
        fp = e.w(f"fb_{k}.png")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tt:.2f}", "-i", e.p("video.mp4"), "-frames:v", "1", fp])
        im = Image.open(fp).convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for z in FB_ZONES: d.rectangle(z, fill=(255, 0, 0, 90), outline=(255, 40, 40, 220), width=4)
        im.alpha_composite(ov); im = im.crop((FB_CROP[0], 0, FB_CROP[1], H)).convert("RGB")
        im = im.resize((im.width * 3 // 8, H * 3 // 8)); ImageDraw.Draw(im).text((8, 44), lab, font=F("sans", 26), fill=(255, 255, 0)); fb.append(im)
    view = Image.new("RGB", ((fb[0].width + 6) * 4, fb[0].height), (255, 255, 255))
    for i, im in enumerate(fb): view.paste(im, (i * (im.width + 6), 0))
    view.save(e.p("check", "fb_view.jpg"), quality=85)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", e.p("video.mp4")],
                               capture_output=True, text=True).stdout)
    print(f"video -> {e.p('video.mp4')}  {os.path.getsize(e.p('video.mp4')) / 1e6:.1f} MB, {dur:.1f} s (video bitrate {kb}k)")
    print(f"check -> {e.p('check', 'sheet.jpg')}  +  {e.p('check', 'fb_view.jpg')} (FB full-screen safe zones)")
    print("opening subtitles:", " | ".join(f"{s:.1f}s {c}" for s, c in subs))

if __name__ == "__main__":
    ep, cmd = sys.argv[1], sys.argv[2]
    {"plan": cmd_plan, "video": cmd_video}[cmd](ep)
