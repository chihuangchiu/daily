# -*- coding: utf-8 -*-
"""每日ETF整理 直式 720x1280 逐格繪製（資料來自 WORK/data.json 與 WORK/timeline.json）。
用法：python3 render.py WORK            → WORK/video_noaudio.mp4
      python3 render.py WORK still 6 22  → WORK/still_6.png …（抽格檢查）"""
import json, math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load

WORK = sys.argv[1]
D = load(WORK)
tl = json.load(open(os.path.join(WORK, "timeline.json"), encoding="utf-8"))
W, H, FPS = 720, 1280, 30
TOTAL = tl["total"]; NF = int(math.ceil(TOTAL * FPS))
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"
_fc = {}
def f(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(FONT % w, s, index=3)
    return _fc[k]

BG = (11, 27, 52); CARD = (20, 42, 77); LINE = (44, 70, 110); TXT = (236, 241, 248)
SUB = (150, 170, 200); RED = (235, 64, 64); GRN = (30, 190, 110); GOLD = (242, 192, 72); DARK = (7, 18, 36)
HOT = (34, 58, 98)

Y, M, DD = D["date"].split("-")
DATE_TAG = f"{M}/{DD}（{D['weekday']}）收盤"
DATA_LINE = D.get("data_line", f"資料時點：{Y}/{M}/{DD} 收盤｜淨值為投信預估淨值")

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def tw(g, s, ft): return g.textlength(s, font=ft)
def rtext(g, x, y, s, ft, fill): g.text((x - tw(g, s, ft), y), s, font=ft, fill=fill)
def ctext(g, cx, y, s, ft, fill): g.text((cx - tw(g, s, ft) / 2, y), s, font=ft, fill=fill)
def col(v): return RED if v > 0 else GRN if v < 0 else TXT
def dcol(d): return RED if d > 0 else GRN if d < 0 else TXT
def pct(v): return ("▲ +" if v > 0 else "▼ −" if v < 0 else "") + f"{abs(v):.2f}%"
def spct(v): return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}%"
def fit(g, x, y, s, weight, size, maxw, fill, minsize=16):
    """放不下就縮小字級（名稱太長時用），回傳實際字級。"""
    while size > minsize and tw(g, s, f(weight, size)) > maxw: size -= 1
    g.text((x, y + (0 if size >= 0 else 0)), s, font=f(weight, size), fill=fill); return size
def card(g, box, fill=CARD): g.rounded_rectangle(box, 18, fill=fill)
def title(g, a, t1, t2):
    oy = int((1 - a) * 20)
    g.text((32, 196 + oy), t1, font=f("Black", 44), fill=TXT)
    if t2: fit(g, 34, 254 + oy, t2, "Medium", 23, W - 68, SUB)

# ---------- header & ticker ----------
def header():
    im = Image.new("RGB", (W, H), BG); g = ImageDraw.Draw(im)
    g.rounded_rectangle((24, 22, 168, 70), 12, fill=GOLD); ctext(g, 96, 25, "ETF日報", f("Black", 30), BG)
    g.text((186, 18), "每日ETF整理", font=f("Black", 40), fill=TXT)
    g.text((26, 84), "台灣股市即時報", font=f("Medium", 24), fill=SUB)
    rtext(g, W - 24, 84, DATE_TAG, f("Medium", 24), SUB)
    g.rectangle((0, 125, W, 175), fill=DARK)
    g.line((0, 125, W, 125), fill=LINE, width=2); g.line((0, 175, W, 175), fill=LINE, width=2)
    fit(g, 24, 948, DATA_LINE, "Regular", 20, W - 48, SUB)
    return im
BASE = header()

def ticker_strip():
    ft = f("Bold", 24); parts = []
    for c, n, p, v in D["close"]:
        parts += [(f"{c} {n} ", TXT), (f"{p:.2f} ", TXT), (pct(v) + "　　", col(v))]
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    w1 = int(sum(tmp.textlength(s, font=ft) for s, _ in parts))
    im = Image.new("RGB", (w1 * 2 + W, 48), DARK); g = ImageDraw.Draw(im); x = 0
    for rep in range(3):
        for s, c in parts:
            g.text((x, 6), s, font=ft, fill=c); x += g.textlength(s, font=ft)
    return im, w1
TSTRIP, TWID = ticker_strip()

# ---------- scenes ----------
def sc_hook(g, p):
    h = D["hook"]; a = ease(p / 0.6)
    bw = tw(g, h.get("badge", "今日焦點"), f("Black", 26)) + 36
    g.rounded_rectangle((32, 200, 32 + bw, 244), 10, fill=GOLD); ctext(g, 32 + bw / 2, 203, h.get("badge", "今日焦點"), f("Black", 26), BG)
    fit(g, 50 + bw, 202, h["headline"], "Bold", 30, W - 82 - bw, TXT)
    c1 = h["card1"]; oy = int((1 - a) * 30)
    card(g, (32, 268 + oy, W - 32, 560 + oy))
    fit(g, 60, 288 + oy, c1["label"], "Bold", 32, 440, SUB)
    if c1.get("tag"): rtext(g, W - 60, 300 + oy, c1["tag"], f("Medium", 24), SUB)
    fit(g, 60, 338 + oy, c1["value"], "Black", 110, W - 120, TXT, 60)
    fit(g, 60, 482 + oy, c1["sub"], "Bold", 40, W - 120, dcol(c1.get("dir", 0)))
    c2 = h.get("card2")
    b = ease((p - 0.4) / 0.6); oy2 = int((1 - b) * 30)
    if c2 and b > 0:
        card(g, (32, 584 + oy2, W - 32, 900 + oy2))
        fit(g, 60, 604 + oy2, c2["label"], "Bold", 30, W - 120, SUB)
        fit(g, 60, 650 + oy2, c2["value"], "Black", 84, W - 120, dcol(c2.get("dir", 0)), 40)
        if c2.get("line"): fit(g, 60, 780 + oy2, c2["line"], "Black", 44, W - 120, TXT)
        if c2.get("note"): fit(g, 60, 846 + oy2, c2["note"], "Regular", 21, W - 120, SUB, 14)

def sc_close(g, p):
    title(g, ease(p / 0.5), "人氣ETF收盤", f"{M}/{DD} 收盤價與漲跌幅")
    g.text((44, 300), "代號／名稱", font=f("Medium", 22), fill=SUB)
    rtext(g, 470, 300, "收盤", f("Medium", 22), SUB); rtext(g, W - 44, 300, "漲跌幅", f("Medium", 22), SUB)
    for i, (c, n, px, v) in enumerate(D["close"][:8]):
        a = ease((p - 0.08 * i) / 0.5)
        if a <= 0: continue
        y = 336 + i * 74; ox = int((1 - a) * 40)
        card(g, (32 + ox, y, W - 32 + ox, y + 64))
        g.text((48 + ox, y + 12), c, font=f("Black", 30), fill=GOLD)
        fit(g, 48 + ox + 132, y + 15, n, "Medium", 25, 470 - 100 - (48 + 132) - 8, TXT)
        rtext(g, 470 + ox, y + 12, f"{px:.2f}", f("Bold", 30), TXT)
        rtext(g, W - 48 + ox, y + 12, pct(v), f("Bold", 30), col(v))

def bars(g, rows, y0, grow, label, lc, zero, scale):
    g.text((44, y0), label, font=f("Black", 28), fill=lc)
    g.line((zero, y0 + 48, zero, y0 + 48 + 5 * 46 - 6), fill=LINE, width=2)
    for i, (c, n, v) in enumerate(rows[:5]):
        y = y0 + 48 + i * 46
        g.text((44, y + 4), c, font=f("Black", 24), fill=GOLD)
        fit(g, 44 + 104, y + 6, n, "Medium", 21, 196, TXT, 15)
        L = max(4, abs(v) * scale * grow)
        box = (zero, y + 8, zero + L, y + 36) if v > 0 else (zero - L, y + 8, zero, y + 36)
        g.rounded_rectangle(box, 6, fill=col(v))
        rtext(g, W - 40, y + 4, spct(v), f("Bold", 26), col(v))
def sc_perf(g, p):
    P = D["perf"]
    title(g, ease(p / 0.5), "近一個月績效排行", P["subtitle"])
    vals = [v for _, _, v in P["top"] + P["bottom"]]
    neg = max([-v for v in vals if v < 0] + [0]); pos = max([v for v in vals if v > 0] + [0])
    span = max(neg + pos, 1.0); x0, x1 = 352, 560          # 長條區：名稱之後、數值欄之前
    zero = x0 + (x1 - x0) * neg / span; scale = (x1 - x0) / span
    card(g, (32, 292, W - 32, 586)); card(g, (32, 598, W - 32, 892))
    bars(g, P["top"], 302, ease((p - 0.2) / 0.8), P.get("top_label", "抗跌前5名"), GOLD, zero, scale)
    bars(g, P["bottom"], 608, ease((p - 0.5) / 0.8), P.get("bottom_label", "跌幅前5名"), GRN, zero, scale)
    fit(g, 36, 902, P["scope"], "Regular", 15, W - 72, SUB, 12)

def flows(g, rows, y0, grow, label, c, sign, mx):
    g.text((52, y0 + 12), label, font=f("Black", 30), fill=c)
    for i, (code, n, amt, u) in enumerate(rows[:3]):
        y = y0 + 62 + i * 92
        g.text((52, y), code, font=f("Black", 28), fill=GOLD)
        s = f"{sign}約{amt:,}億元"; sw = tw(g, s, f("Black", 30))
        fit(g, 52 + 122, y + 3, n, "Medium", 24, W - 52 - sw - 12 - 174, TXT, 16)
        rtext(g, W - 52, y, s, f("Black", 30), c)
        L = (W - 104 - 150) * min(1, amt / mx) * grow
        g.rounded_rectangle((52, y + 48, 52 + max(6, L), y + 66), 6, fill=c)
        rtext(g, W - 52, y + 44, u, f("Medium", 21), SUB)
def sc_flow(g, p):
    F_ = D["flow"]
    title(g, ease(p / 0.5), "資金流向", F_.get("subtitle", f"{M}/{DD} 淨申購與淨買回（估算金額）"))
    mx = max([r[2] for r in F_["in"] + F_["out"]] + [1])
    card(g, (32, 296, W - 32, 600)); card(g, (32, 616, W - 32, 920))
    flows(g, F_["in"], 300, ease((p - 0.2) / 0.8), "▲ 淨申購前3名", RED, "+", mx)
    flows(g, F_["out"], 620, ease((p - 0.5) / 0.8), "▼ 淨買回前3名", GRN, "−", mx)

def sc_prem(g, p):
    P = D["prem"]
    title(g, ease(p / 0.5), P.get("title", "溢價警示"), P["subtitle"])
    g.text((44, 300), "代號／名稱", font=f("Medium", 22), fill=SUB)
    rtext(g, 450, 300, "市價／淨值", f("Medium", 22), SUB); rtext(g, W - 44, 300, "溢價", f("Medium", 22), SUB)
    for i, (c, n, px, nav, pr) in enumerate(P["rows"][:5]):
        a = ease((p - 0.1 * i) / 0.5)
        if a <= 0: continue
        y = 338 + i * 100; ox = int((1 - a) * 40)
        card(g, (32 + ox, y, W - 32 + ox, y + 86))
        g.text((50 + ox, y + 8), c, font=f("Black", 30), fill=GOLD)
        fit(g, 50 + ox, y + 48, n, "Medium", 23, 250, TXT, 15)
        rtext(g, 450 + ox, y + 10, f"{px:.2f}", f("Bold", 28), TXT)
        rtext(g, 450 + ox, y + 48, f"淨值 {nav:.2f}", f("Regular", 21), SUB)
        rtext(g, W - 50 + ox, y + 20, spct(pr), f("Black", 40), GOLD if pr > 0 else TXT)
    for j, ln in enumerate(P.get("note", ["溢價＝買進價格高於ETF淨值。追蹤海外資產的ETF，", "盤中淨值為投信預估值，與實際淨值可能有落差。"])[:2]):
        fit(g, 40, 852 + j * 30, ln, "Regular", 21, W - 80, SUB, 14)

def sc_div(g, p):
    V = D["div"]
    title(g, ease(p / 0.5), "除息倒數", V.get("subtitle", "未來兩週上市ETF除息日程"))
    rows = V["rows"][:5]
    g.line((96, 316, 96, 300 + len(rows) * 112 - 30), fill=LINE, width=4)
    for i, (d, who, amt, last) in enumerate(rows):
        a = ease((p - 0.1 * i) / 0.5)
        if a <= 0: continue
        y = 300 + i * 112; ox = int((1 - a) * 40); hot = i == V.get("hot", -1)
        g.ellipse((84, y + 26, 108, y + 50), fill=GOLD if hot else SUB)
        card(g, (124 + ox, y, W - 32 + ox, y + 100), fill=HOT if hot else CARD)
        g.text((142 + ox, y + 10), d, font=f("Black", 28), fill=GOLD)
        aw = tw(g, amt, f("Medium", 22)) + 16 if amt else 0
        fit(g, 142 + ox, y + 54, who, "Bold", 26, W - 50 - 142 - aw, TXT, 16)
        rtext(g, W - 50 + ox, y + 14, last, f("Bold", 24), RED if hot else TXT)
        if amt: rtext(g, W - 50 + ox, y + 60, amt, f("Medium", 22), SUB)
    fit(g, 40, 870, V.get("note", "配息金額以投信公告為準，除息日為證交所預告日程。"), "Regular", 21, W - 80, SUB, 14)

def sc_event(g, p):
    E = D["event"]
    title(g, ease(p / 0.5), E["title"], E.get("subtitle", ""))
    for i, ln in enumerate(E["lines"][:4]):
        a = ease((p - 0.12 * i) / 0.5)
        if a <= 0: continue
        y = 300 + i * 150; ox = int((1 - a) * 40)
        card(g, (32 + ox, y, W - 32 + ox, y + 132))
        lines = wrap(g, ln, f("Bold", 30), W - 32 - 64 - 40)
        for j, s in enumerate(lines[:2]): g.text((64 + ox, y + 22 + j * 46), s, font=f("Bold", 30), fill=TXT)

def sc_end(g, p):
    title(g, ease(p / 0.5), "今日重點", "")
    for i, s in enumerate(D["end"]["points"][:3]):
        a = ease((p - 0.15 * i) / 0.5)
        if a <= 0: continue
        y = 280 + i * 168; ox = int((1 - a) * 40)
        card(g, (32 + ox, y, W - 32 + ox, y + 148))
        g.ellipse((52 + ox, y + 44, 112 + ox, y + 104), fill=GOLD); ctext(g, 82 + ox, y + 50, str(i + 1), f("Black", 36), BG)
        lines = wrap(g, s, f("Bold", 30), W - 32 - 140 - 30)
        for j, ln in enumerate(lines[:2]): g.text((132 + ox, y + 30 + j * 46), ln, font=f("Bold", 30), fill=TXT)
    g.text((40, 812), "資訊整理，僅供參考，不構成投資建議。", font=f("Medium", 24), fill=SUB)
    g.text((40, 848), "過去績效不代表未來表現。", font=f("Medium", 24), fill=SUB)

SCENE_FN = {"hook": sc_hook, "close": sc_close, "perf": sc_perf, "flow": sc_flow, "prem": sc_prem,
            "div": sc_div, "event": sc_event, "end": sc_end}

# ---------- subtitles ----------
TOK = re.compile(r'[0-9A-Za-z.%+−\-,/&]+|.')
def wrap(g, s, ft, maxw):
    if tw(g, s, ft) <= maxw: return [s]
    best = None
    for m in re.finditer(r'[，、：；]', s):
        a, b = s[:m.end()], s[m.end():]
        if b and tw(g, a, ft) <= maxw and tw(g, b, ft) <= maxw:
            sc = abs(tw(g, a, ft) - tw(g, b, ft))
            if best is None or sc < best[0]: best = (sc, [a, b])
    if best: return best[1]
    lines, cur = [], ""
    for tk in TOK.findall(s):
        if tw(g, cur + tk, ft) <= maxw: cur += tk
        else: lines.append(cur); cur = tk
    if cur: lines.append(cur)
    for i in range(1, len(lines)):
        while lines[i] and lines[i][0] in "，。：、；%":
            lines[i - 1] += lines[i][0]; lines[i] = lines[i][1:]
    return [l for l in lines if l]

SEGS = [s for sc in tl["scenes"] for s in sc["segs"]]
def seg_at(t):
    for i, s in enumerate(SEGS):
        nxt = SEGS[i + 1]["start"] if i + 1 < len(SEGS) else 1e9
        if s["start"] <= t < min(nxt, s["end"] + 0.6): return s
    return None
_subc = {}
def sub_img(s):
    if s["text"] not in _subc:
        im = Image.new("RGBA", (W, 150), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
        g.rounded_rectangle((20, 0, W - 20, 140), 18, fill=(5, 14, 30, 235), outline=LINE, width=2)
        size = 34
        while True:
            ft = f("Bold", size); lines = wrap(g, s["text"], ft, W - 104)
            if len(lines) <= 2 or size <= 26: break
            size -= 2
        if len(lines) > 2: print("WARNING 字幕超過兩行：", s["text"])
        y0 = 70 - len(lines) * 24
        for j, ln in enumerate(lines[:2]): ctext(g, W / 2, y0 + j * 48 - 4, ln, ft, (255, 255, 255))
        _subc[s["text"]] = im
    return _subc[s["text"]]

SC = tl["scenes"]; WIN = []
for i, sc in enumerate(SC):
    a = 0 if i == 0 else sc["start"] - 0.25
    b = SC[i + 1]["start"] - 0.25 if i + 1 < len(SC) else 1e9
    WIN.append((sc["key"], a, b))
_static = {}
def content(key, p):
    if p >= 1.6 and key in _static: return _static[key]
    full = Image.new("RGB", (W, H), BG); g = ImageDraw.Draw(full)
    SCENE_FN[key](g, p)
    im = full.crop((0, 185, W, 945))
    if p >= 1.6: _static[key] = im
    return im

def frame(n):
    t = n / FPS; im = BASE.copy()
    off = int((t * 70) % TWID); im.paste(TSTRIP.crop((off, 0, off + W, 48)), (0, 126))
    for key, a, b in WIN:
        if a <= t < b:
            p = t - a; c = content(key, p); fade = min(1.0, p / 0.35)
            if fade < 1: c = Image.blend(Image.new("RGB", c.size, BG), c, fade)
            im.paste(c, (0, 185)); break
    s = seg_at(t)
    if s: im.paste(sub_img(s), (0, 988), sub_img(s))
    g = ImageDraw.Draw(im)
    g.rectangle((0, 1148, W, 1154), fill=LINE); g.rectangle((0, 1148, int(W * min(1, t / TOTAL)), 1154), fill=GOLD)
    return im

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "still":
        for ts in sys.argv[3:]: frame(int(float(ts) * FPS)).save(os.path.join(WORK, f"still_{ts}.png"))
        sys.exit()
    out = os.path.join(WORK, "video_noaudio.mp4")
    pr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(NF): pr.stdin.write(frame(n).tobytes())
    pr.stdin.close(); pr.wait(); print("frames", NF, "->", out)
