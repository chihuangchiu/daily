"""Template renderer: episode.json + timeline.json -> 720x1280 frames.

Usage:
  python3 render.py EP_DIR seg START END OUT.mp4   # render a time range (video only)
  python3 render.py EP_DIR sheet                    # contact sheets of every reveal state -> EP_DIR/check/
  python3 render.py EP_DIR stills T1 T2 ...         # single frames -> EP_DIR/check/
See TEMPLATES.md for the episode.json schema.
"""
import json, os, random, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 720, 1280, 30
VIS_TOP, VIS_BOT = 195, 872          # visual area between header and subtitles
SUB_Y = 948

PAPER = (241, 232, 214)
PAPER_LT = (250, 245, 233)
INK = (42, 33, 26)
MUTED = (112, 96, 80)
RED = (163, 48, 42)
CREAM = (247, 239, 222)
GREEN = (31, 107, 69)
COLORS = dict(ink=INK, red=RED, muted=MUTED, cream=CREAM, green=GREEN)

WARN = []

# ---------------------------------------------------------------- fonts
FD = "/usr/share/fonts/opentype/noto/"
_idx, _fc = {}, {}
FONT_FILES = {
    "serif-black": "NotoSerifCJK-Black.ttc", "serif-bold": "NotoSerifCJK-Bold.ttc",
    "serif-med": "NotoSerifCJK-Medium.ttc", "serif": "NotoSerifCJK-Regular.ttc",
    "sans-black": "NotoSansCJK-Black.ttc", "sans-bold": "NotoSansCJK-Bold.ttc",
    "sans-med": "NotoSansCJK-Medium.ttc", "sans": "NotoSansCJK-Regular.ttc",
}


def F(kind, size):
    path = FD + FONT_FILES[kind]
    if path not in _idx:
        for i in range(12):
            try:
                f = ImageFont.truetype(path, 20, index=i)
            except Exception:
                break
            if f.getname()[0].endswith("TC"):
                _idx[path] = i
                break
    key = (path, size)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(path, size, index=_idx[path])
    return _fc[key]


def col(c, default=INK):
    if c is None:
        return default
    if isinstance(c, (list, tuple)):
        return tuple(c)
    return COLORS.get(c, default)


# ---------------------------------------------------------------- primitives
def text_img(s, font, color):
    l, t, r, b = font.getbbox(s)
    im = Image.new("RGBA", (max(1, r - l + 4), max(1, b - t + 4)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), s, font=font, fill=color)
    return im


def fit_text(s, kind, size, color, maxw=600, minsize=18):
    f = F(kind, size)
    while f.getlength(s) > maxw and size > minsize:
        size -= 2
        f = F(kind, size)
    if f.getlength(s) > maxw:
        WARN.append(f"text too wide even at {size}px: {s}")
    return text_img(s, f, color + (255,) if len(color) == 3 else color)


def vtext_img(s, kind, size, color, step):
    f = F(kind, size)
    ims = [text_img(c, f, color + (255,)) for c in s]
    w = max(i.width for i in ims)
    im = Image.new("RGBA", (w, step * len(s) + 6), (0, 0, 0, 0))
    for k, ci in enumerate(ims):
        im.paste(ci, ((w - ci.width) // 2, k * step + (step - ci.height) // 2), ci)
    return im


def rough(im, amount=0.18, seed=1):
    rng = np.random.default_rng(seed)
    a = np.array(im.getchannel("A")).astype(np.float32)
    n = rng.random(a.shape)
    n = np.array(Image.fromarray((n * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))) / 255.0
    a = a * np.clip((n - amount) / (0.5 - amount) + 0.35, 0, 1)
    im = im.copy()
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def box_img(w, h, fill=None, outline=None, width=2, radius=10):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius,
                                         fill=(fill + (255,)) if fill else None,
                                         outline=(outline + (255,)) if outline else None, width=width)
    return im


def seal_img(chars, size, grid=None, angle=-6, seed=3):
    n = len(chars)
    cols, rows = grid or (1, n)
    pad = int(size * 0.18)
    w, h = cols * size + pad * 2, rows * size + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=int(size * 0.12), fill=RED + (255,))
    d.rounded_rectangle((pad * 0.45, pad * 0.45, w - 1 - pad * 0.45, h - 1 - pad * 0.45),
                        radius=int(size * 0.08), outline=CREAM + (255,), width=max(2, size // 28))
    f = F("serif-black", int(size * 0.86))
    for k, c in enumerate(chars):
        cx_ = cols - 1 - k // rows
        ry = k % rows
        ci = text_img(c, f, CREAM + (255,))
        im.paste(ci, (pad + cx_ * size + (size - ci.width) // 2, pad + ry * size + (size - ci.height) // 2), ci)
    return rough(im, seed=seed).rotate(angle, expand=True, resample=Image.BICUBIC)


def stamp_img(top, main, angle=-12):
    f = F("serif-black", 66)
    mw = int(f.getlength(main))
    sw, sh = max(300, mw + 80), 150 if top else 120
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((3, 3, sw - 4, sh - 4), fill=PAPER_LT + (245,), outline=RED + (255,), width=6)
    d.rectangle((14, 14, sw - 15, sh - 15), outline=RED + (255,), width=2)
    y = 20
    if top:
        a = text_img(top, F("sans-black", 28), RED + (255,))
        im.paste(a, ((sw - a.width) // 2, y), a)
        y = 56
    b = text_img(main, f, RED + (255,))
    im.paste(b, ((sw - b.width) // 2, y if top else (sh - b.height) // 2), b)
    return rough(im, 0.12, seed=7).rotate(angle, expand=True, resample=Image.BICUBIC)


# ---------------------------------------------------------------- animated element
class El:
    def __init__(self, img, x, y, t0, t1=None, anim="rise", dur=0.55):
        self.img, self.x, self.y = img, int(x), int(y)
        self.t0, self.t1, self.anim, self.dur = t0, t1, anim, dur

    def draw(self, frame, t):
        if t < self.t0 or (self.t1 is not None and t >= self.t1):
            return
        p = min(1.0, (t - self.t0) / self.dur)
        e = 1 - (1 - p) ** 3
        a = e
        if self.t1 is not None:
            a *= min(1.0, (self.t1 - t) / 0.35)
        img, x, y = self.img, self.x, self.y
        if self.anim == "rise":
            y += int((1 - e) * 18)
        elif self.anim == "stamp":
            s = 1 + 0.45 * (1 - e)
            a = min(a, p * 3)
            if s != 1:
                nw, nh = int(img.width * s), int(img.height * s)
                img = img.resize((nw, nh), Image.BILINEAR)
                x -= (nw - self.img.width) // 2
                y -= (nh - self.img.height) // 2
        elif self.anim == "wipe":
            img = img.crop((0, 0, max(1, int(img.width * e)), img.height))
            a = 1.0 if self.t1 is None else min(1.0, (self.t1 - t) / 0.35)
        elif self.anim == "wipedown":
            img = img.crop((0, 0, img.width, max(1, int(img.height * e))))
            a = 1.0 if self.t1 is None else min(1.0, (self.t1 - t) / 0.35)
        if a <= 0.003:
            return
        if a < 0.999:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v, a=a: int(v * a)))
        frame.paste(img, (x, y), img)


# ---------------------------------------------------------------- scene context
class Ctx:
    def __init__(self, sc, tl):
        self.sc, self.tl, self.d = sc, tl, sc.get("data", {})

    def t(self, at=None, delay=0.0):
        """start time of line index `at` (+delay seconds). None -> scene start."""
        if at is None:
            base = self.tl["start"]
        else:
            at = max(0, min(int(at), len(self.tl["lines"]) - 1))
            base = self.tl["lines"][at]["start"]
        return base + (delay or 0.0)

    def until(self, u):
        if u is None:
            return None
        if u >= len(self.tl["lines"]):
            return self.tl["end"] + 1
        return self.tl["lines"][int(u)]["start"]


def place(im, cx, cy, t0, t1=None, anim="rise", dur=0.55):
    return El(im, cx - im.width / 2, cy - im.height / 2, t0, t1, anim, dur)


def chapter_el(label, t0):
    im = text_img(label, F("serif-bold", 26), RED + (255,))
    full = Image.new("RGBA", (im.width + 44, max(im.height, 6)), (0, 0, 0, 0))
    ImageDraw.Draw(full).rectangle((0, full.height // 2 - 1, 30, full.height // 2 + 1), fill=RED + (255,))
    full.paste(im, (44, 0), im)
    return El(full, 60, 160 - full.height / 2, t0, None, "fade", 0.5)


def rule_el(x0, x1, y, t0, color=RED, width=3, t1=None):
    return El(Image.new("RGBA", (x1 - x0, width), color + (255,)), x0, y - width // 2, t0, t1, "wipe", 0.7)


# ---------------------------------------------------------------- stack items
STYLES = {
    "huge": ("serif-black", 170, INK), "big": ("serif-black", 110, INK), "title": ("serif-black", 80, INK),
    "head": ("serif-black", 62, INK), "mid": ("serif-med", 48, INK), "body": ("serif-bold", 36, INK),
    "small": ("sans-med", 31, MUTED), "kicker": ("serif-med", 42, MUTED),
}


LIGHT = (232, 222, 204)
AI_LABEL = ""  # no on-screen AI label (Nathan 2026-10-20: hand-drawn style, AI use is disclosed in the post text)


def load_photo(src, w, h, sepia=0.3):
    """cover-crop an image from the episode dir to w x h, lightly warmed to match the paper palette"""
    path = src if os.path.isabs(src) else os.path.join(EP_DIR, src)
    im = Image.open(path).convert("RGB")
    sc = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * sc + 0.5)), max(h, int(im.height * sc + 0.5))), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((l, t, l + w, t + h))
    if sepia:
        g = np.array(im.convert("L")).astype(np.float32)[..., None] / 255.0
        tone = np.array([[[255, 236, 205]]], np.float32) * g
        im = Image.fromarray(np.clip(np.array(im).astype(np.float32) * (1 - sepia) + tone * sepia, 0, 255).astype(np.uint8))
    return im


def label_img(text=AI_LABEL, color=LIGHT, alpha=210):
    ti = text_img(text, F("sans-med", 20), color + (alpha,))
    bg = Image.new("RGBA", (ti.width + 20, ti.height + 10), (20, 16, 12, 120 if color == LIGHT else 0))
    bg.paste(ti, (10, 5), ti)
    return bg


_SHADE = None


def cover_finish(im, label=AI_LABEL):
    """darken a full-screen W x H picture so the light title text reads on top, and add the AI label"""
    global _SHADE
    if _SHADE is None:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        a = 0.40 + 0.18 * (1 - np.clip(yy / 0.12, 0, 1)) + 0.35 * np.clip((yy - 0.62) / 0.38, 0, 1) ** 1.3
        shade = np.zeros((H, W, 4), np.uint8)
        shade[..., :3] = (18, 14, 10)
        shade[..., 3] = (np.clip(a, 0, 0.92) * 255).astype(np.uint8).repeat(W, 1)
        _SHADE = Image.fromarray(shade, "RGBA")
    im = im.convert("RGBA")
    im.alpha_composite(_SHADE)
    if label:
        lb = label_img(label)
        im.alpha_composite(lb, (W - 60 - lb.width, 128))
    return im


def shift_down(im, shift):
    """move a full-screen W x H picture down by `shift` x H (title scene `image_shift`, 0-0.4) so the face sits
    below the title; the freed top band is filled with the picture's own top-edge colour, blended in softly"""
    s = int(H * max(0.0, min(0.4, float(shift or 0))))
    if s <= 0:
        return im
    a = np.array(im.convert("RGB")).astype(np.float32)
    top = a[: max(4, H // 40)].mean(axis=(0, 1))
    out = np.empty_like(a)
    out[:s] = top
    out[s:] = a[: H - s]
    blend = min(120, H - s)
    w = np.linspace(0, 1, blend, dtype=np.float32)[:, None, None]
    out[s:s + blend] = top * (1 - w) + out[s:s + blend] * w
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def cover_img(src, label=AI_LABEL, shift=0):
    return cover_finish(shift_down(load_photo(src, W, H, 0.25), shift), label)


def sepia_arr(a, sepia=0.25):
    g = a.astype(np.float32).mean(axis=2, keepdims=True) / 255.0
    tone = np.array([[[255, 236, 205]]], np.float32) * g
    return np.clip(a.astype(np.float32) * (1 - sepia) + tone * sepia, 0, 255).astype(np.uint8)


class VideoCover:
    """full-screen opening clip (title scene `video`): plays from t0 for `secs` seconds (its first or, with align="end", its last seconds), then fades out
    over the last `fade` seconds to reveal the still opening image underneath. Frames are decoded lazily,
    only by the process that renders that time range."""

    def __init__(self, src, t0, secs, label=AI_LABEL, fade=0.5, shift=0, align="start"):
        self.path = src if os.path.isabs(src) else os.path.join(EP_DIR, src)
        self.t0, self.secs, self.label, self.fade, self.shift = t0, secs, label, fade, shift
        # align="end": play the LAST `secs` seconds of the clip (its last frame is opening.png itself,
        # RUNBOOK 4d), so the hand-over to the still is seamless
        self.align = align
        self.t1 = t0 + secs
        self.frames = None

    def _load(self):
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
        seek = ["-sseof", f"-{self.secs + 0.05:.2f}"] if self.align == "end" else []
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", *seek, "-i", self.path, "-t", str(self.secs), "-vf", vf,
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        n = len(raw) // (W * H * 3)
        if n == 0:
            raise SystemExit(f"opening video {self.path} has no frames")
        self.frames = np.frombuffer(raw[: n * W * H * 3], np.uint8).reshape(n, H, W, 3)

    def draw(self, frame, t):
        if t < self.t0 - 1.0 or t >= self.t1:
            return
        if self.frames is None:
            self._load()
        k = min(len(self.frames) - 1, max(0, int((t - self.t0) * FPS)))
        im = cover_finish(shift_down(Image.fromarray(sepia_arr(self.frames[k])), self.shift), self.label)
        a = min(1.0, (self.t1 - t) / self.fade)
        if a < 0.999:
            im.putalpha(im.getchannel("A").point(lambda v, a=a: int(v * a)))
        frame.paste(im, (0, 0), im)


def item_imgs(it):
    """returns list of (img, dx, dy, at, delay, anim) relative to item box, and box (w,h)"""
    typ = it.get("type", "text")
    if typ == "text":
        kind, size, c = STYLES[it.get("style", "head")]
        im = fit_text(it["text"], kind, it.get("size", size), col(it.get("color"), c))
        return [(im, 0, 0, None, 0, "rise")], im.size
    if typ == "rule":
        w = it.get("width", 320)
        im = Image.new("RGBA", (w, 3), col(it.get("color"), RED) + (255,))
        return [(im, 0, 0, None, 0, "wipe")], (w, 3)
    if typ == "pill":
        f = F("sans-bold", 26)
        tw = int(f.getlength(it["text"]))
        im = box_img(tw + 60, 52, col(it.get("color"), RED), None, 0, 26)
        ti = text_img(it["text"], f, CREAM + (255,))
        im.paste(ti, ((im.width - ti.width) // 2, (52 - ti.height) // 2), ti)
        return [(im, 0, 0, None, 0, "rise")], im.size
    if typ == "pills":
        out, x = [], 0
        f = F("serif-black", 38)
        for k, s in enumerate(it["items"]):
            w = int(f.getlength(s)) + 64
            im = box_img(w, 72, None, RED, 3, 36)
            ti = text_img(s, f, RED + (255,))
            im.paste(ti, ((w - ti.width) // 2, (72 - ti.height) // 2), ti)
            out.append((im, x, 0, None, 0.25 * k, "rise"))
            x += w + 20
        return out, (x - 20, 72)
    if typ == "pair":
        f = F("serif-bold", it.get("size", 34))
        a = text_img(it["left"], f, col(it.get("left_color"), INK) + (255,))
        b = text_img(it["right"], f, col(it.get("right_color"), RED) + (255,))
        gap = 60
        w = a.width + gap + b.width
        h = max(a.height, b.height)
        return [(a, 0, (h - a.height) // 2, None, 0, "rise"),
                (b, a.width + gap, (h - b.height) // 2, it.get("right_at"), it.get("right_delay", 0), "rise")], (w, h)
    if typ == "vtext":
        cols_ = it["columns"]  # right-to-left reading order
        size = it.get("size", 70)
        step = int(size * 1.08)
        ims = [vtext_img(c["text"], "serif-black", size, col(c.get("color"), INK), step) for c in cols_]
        gap = int(size * 1.3)
        cw = max(i.width for i in ims)
        w = cw * len(ims) + gap * (len(ims) - 1)
        h = max(i.height for i in ims)
        out = []
        for k, (c, im) in enumerate(zip(cols_, ims)):
            x = w - cw - k * (cw + gap) + (cw - im.width) // 2
            out.append((im, x, 0, c.get("at"), c.get("delay", 0), "rise"))
        return out, (w, h)
    if typ == "sign":
        sign = Image.new("RGBA", (560, 250), (0, 0, 0, 0))
        d = ImageDraw.Draw(sign)
        d.rounded_rectangle((0, 0, 559, 249), 22, fill=GREEN + (255,))
        d.rounded_rectangle((10, 10, 549, 239), 16, outline=(255, 255, 255, 255), width=4)
        for s, kind, size, y, c in [(it.get("top", ""), "sans-black", 42, 36, (255, 255, 255)),
                                    (it["main"], "serif-black", 60, 98, (255, 255, 255)),
                                    (it.get("small", ""), "sans-med", 28, 186, (225, 240, 228))]:
            if s:
                ti = fit_text(s, kind, size, c, 500)
                sign.paste(ti, ((560 - ti.width) // 2, y), ti)
        full = Image.new("RGBA", (560, 400), (0, 0, 0, 0))
        ImageDraw.Draw(full).rectangle((272, 250, 288, 399), fill=(90, 90, 90, 255))
        full.paste(sign, (0, 0), sign)
        return [(full, 0, 0, None, 0, "rise")], full.size
    if typ == "film":
        strip = Image.new("RGBA", (660, 330), (0, 0, 0, 0))
        d = ImageDraw.Draw(strip)
        d.rectangle((0, 0, 659, 329), fill=(30, 24, 19, 255))
        for k in range(15):
            x = 14 + k * 44
            d.rounded_rectangle((x, 12, x + 22, 34), 4, fill=PAPER + (255,))
            d.rounded_rectangle((x, 296, x + 22, 318), 4, fill=PAPER + (255,))
        yy, xx = np.mgrid[0:236, 0:560]
        r = np.sqrt(((xx - 280) / 300) ** 2 + ((yy - 118) / 160) ** 2)
        arr = np.array([150, 132, 104], np.float32) * (1.05 - 0.55 * np.clip(r, 0, 1))[..., None]
        rng = np.random.default_rng(5)
        arr += rng.normal(0, 7, arr.shape)
        fr = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        fd = ImageDraw.Draw(fr)
        for _ in range(9):
            x = int(rng.integers(10, 550))
            fd.line((x, 0, x + int(rng.integers(-6, 6)), 236), fill=(200, 186, 160), width=1)
        ti = fit_text(it["main"], "serif-black", 56, (246, 236, 214), 500)
        fr.paste(ti, ((560 - ti.width) // 2, 70 if it.get("sub") else (236 - ti.height) // 2), ti)
        if it.get("sub"):
            t2 = fit_text(it["sub"], "serif-med", 24, (230, 218, 196), 500)
            fr.paste(t2, ((560 - t2.width) // 2, 158), t2)
        strip.paste(fr, (50, 47))
        return [(strip, 0, 0, None, 0, "rise")], strip.size
    if typ == "barred":
        out, y = [], 0
        if it.get("small"):
            s1 = text_img(it["small"], F("serif-med", 38), MUTED + (255,))
            out.append((s1, (540 - s1.width) // 2, 0, None, 0, "rise"))
            y = s1.height + 22
        blk = Image.new("RGBA", (520, 220), (226, 214, 192, 255))
        s2 = fit_text(it["big"], "serif-black", 128, INK, 480)
        blk.paste(s2, ((520 - s2.width) // 2, (220 - s2.height) // 2), s2)
        out.append((blk, 10, y + 10, None, 0, "rise"))
        bars = Image.new("RGBA", (540, 240), (0, 0, 0, 0))
        d = ImageDraw.Draw(bars)
        d.rectangle((0, 0, 539, 14), fill=INK + (255,))
        d.rectangle((0, 226, 539, 239), fill=INK + (255,))
        for k in range(7):
            x = 22 + k * 82
            d.rectangle((x, 0, x + 9, 239), fill=INK + (215,))
        out.append((bars, 0, y, None, 0.6, "wipedown"))
        return out, (540, y + 240)
    if typ == "checks":
        out, y = [], 0
        f = F("serif-black", it.get("size", 64))
        tis = [text_img(s, f, INK + (255,)) for s in it["items"]]
        mw = max(t.width for t in tis)
        for k, ti in enumerate(tis):
            ck = Image.new("RGBA", (60, 50), (0, 0, 0, 0))
            ImageDraw.Draw(ck).line((6, 26, 22, 42, 54, 6), fill=RED + (255,), width=8, joint="curve")
            out.append((ti, (mw - ti.width) // 2, y, None, 0.55 * k, "rise"))
            out.append((ck, mw + 28, y + (ti.height - 50) // 2, None, 0.55 * k + 0.25, "stamp"))
            y += ti.height + 26
        return out, (mw + 88, y - 26)
    if typ == "cards":
        out = []
        cs = it["cards"][:2]
        for k, cd in enumerate(cs):
            im = box_img(280, 200, PAPER_LT, INK, 2, 14)
            hi = fit_text(cd["head"], "serif-black", 56, col(cd.get("color"), INK), 250)
            im.paste(hi, ((280 - hi.width) // 2, 34), hi)
            if cd.get("sub"):
                si = fit_text(cd["sub"], "sans-med", 30, MUTED, 250)
                im.paste(si, ((280 - si.width) // 2, 128), si)
            out.append((im, k * 320, 0, cd.get("at"), cd.get("delay", 0), "rise"))
        return out, (320 * len(cs) - 40, 200)
    if typ == "image":
        h = it.get("height", 420)
        w = it.get("width", 560)
        ph = load_photo(it["src"], w, h, it.get("sepia", 0.3)).convert("RGBA")
        if it.get("label", AI_LABEL):
            lb = label_img(it.get("label", AI_LABEL))
            ph.alpha_composite(lb, (w - lb.width - 8, h - lb.height - 8))
        fr = Image.new("RGBA", (w + 36, h + 36), (0, 0, 0, 0))
        sh = Image.new("RGBA", fr.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle((10, 12, fr.width - 2, fr.height - 2), fill=(60, 40, 20, 70))
        fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
        ImageDraw.Draw(fr).rectangle((0, 0, w + 23, h + 23), fill=PAPER_LT + (255,), outline=INK + (120,), width=1)
        fr.paste(ph, (12, 12), ph)
        out = [(fr, 0, 0, None, 0, "rise")]
        hh = fr.height
        if it.get("caption"):
            cp = fit_text(it["caption"], "sans-med", 26, MUTED, w)
            out.append((cp, (w + 36 - cp.width) // 2, hh + 4, None, 0.3, "rise"))
            hh += cp.height + 8
        return out, (w + 36, hh)
    raise ValueError(f"unknown item type {typ}")


ITEM_GAP = {"rule": 26, "pill": 22, "small": 20}


def b_stack(c):
    els = []
    d = c.d
    if d.get("bg_char"):
        g = text_img(d["bg_char"], F("serif-black", 430), INK + (20,))
        els.append(El(g, 690 - g.width, 330, c.t(), None, "fade", 1.2))
    for ph in d["phases"]:
        p_at = ph.get("at", 0)
        t1 = c.until(ph.get("until"))
        if ph.get("bg"):
            g = text_img(ph["bg"]["char"], F("serif-black", 520), col(ph["bg"].get("color"), RED) + (26,))
            els.append(El(g, 360 - g.width / 2, 520 - g.height / 2, c.t(p_at), t1, "fade", 1.0))
        blocks = []
        for it in ph["items"]:
            parts, (w, h) = item_imgs(it)
            blocks.append((it, parts, w, h))
        total = sum(b[3] for b in blocks)
        gaps = [ITEM_GAP.get(b[0].get("type"), ITEM_GAP.get(b[0].get("style"), 30)) for b in blocks[1:]]
        total += sum(gaps)
        avail = VIS_BOT - VIS_TOP - 20
        if total > avail:
            WARN.append(f"stack phase at line {p_at} too tall ({total}px > {avail}px): "
                        + " / ".join(b[0].get("text", b[0].get("type", "")) for b in blocks))
        y = (VIS_TOP + 10 + VIS_BOT) / 2 - total / 2 + ph.get("shift", 0)
        for k, (it, parts, w, h) in enumerate(blocks):
            x0 = (W - w) / 2 + it.get("dx", 0)
            it_at = it.get("at", p_at)
            for im, dx, dy, at, delay, anim in parts:
                t0 = c.t(at if at is not None else it_at, it.get("delay", 0) + delay)
                els.append(El(im, x0 + dx, y + dy, t0, t1, anim, 0.7 if anim in ("wipe", "wipedown") else 0.55))
            y += h + (gaps[k] if k < len(gaps) else 0)
        if ph.get("seal"):
            s = ph["seal"]
            im = seal_img(s["chars"], s.get("size", 50), tuple(s["grid"]) if s.get("grid") else None, s.get("angle", -6))
            els.append(place(im, s.get("x", 590), s.get("y", 300), c.t(s.get("at", p_at), s.get("delay", 0)), t1, "stamp", 0.35))
        if ph.get("stamp"):
            s = ph["stamp"]
            im = stamp_img(s.get("top"), s["main"], s.get("angle", -12))
            els.append(place(im, s.get("x", 360), s.get("y", 640), c.t(s.get("at", p_at), s.get("delay", 0)), t1, "stamp", 0.3))
    return els


def b_title(c):
    d, ep = c.d, EP
    dark = bool(d.get("image"))
    ink, muted = (CREAM, LIGHT) if dark else (INK, MUTED)
    els = []
    if dark:
        cov = cover_img(d["image"], d.get("image_label", AI_LABEL), d.get("image_shift", 0))
        # already fully visible on frame 0 (the first frame doubles as the thumbnail)
        els.append(El(cov, 0, 0, -1.0, None, "fade", 0.6))
        if d.get("video"):
            # a short AI clip plays over the still image first (frame 0 = video frame 0)
            align = d.get("video_align", "start")
            els.append(VideoCover(d["video"], 0.0, float(d.get("video_secs", 3)), d.get("image_label", AI_LABEL),
                                  fade=0.25 if align == "end" else 0.5, shift=d.get("image_shift", 0), align=align))
    els += [
        place(text_img(d.get("kicker", "歷史上的今天"), F("serif-med", 44), muted + (255,)), 360, 262, -1.0),
        place(fit_text(d.get("big", ep["mmdd"]), "serif-black", 220, ink, 640), 360, 410, -1.0),
    ]
    if d.get("sub"):
        els.append(rule_el(170, 550, 540, c.t(d.get("sub_at", 1)), (214, 96, 84) if dark else RED))
        els.append(place(fit_text(d["sub"], "serif-med", 40, ink), 360, 592, c.t(d.get("sub_at", 1), 0.2)))
    for m in d.get("middle", []):
        t0, t1 = c.t(m.get("at", 0), m.get("delay", 0)), c.until(m.get("until"))
        if m.get("type", "text") == "text":
            els.append(place(fit_text(m["text"], "serif-med", 40, ink if dark else col(m.get("color"), INK)), 360, 700, t0, t1))
        else:
            if dark:
                f = F("serif-black", 38)
                parts, x = [], 0
                for k, s_ in enumerate(m["items"]):
                    w_ = int(f.getlength(s_)) + 64
                    im = box_img(w_, 72, None, CREAM, 3, 36)
                    ti = text_img(s_, f, CREAM + (255,))
                    im.paste(ti, ((w_ - ti.width) // 2, (72 - ti.height) // 2), ti)
                    parts.append((im, x, 0, None, 0.25 * k, "rise"))
                    x += w_ + 20
                w, h = x - 20, 72
            else:
                parts, (w, h) = item_imgs({"type": "pills", "items": m["items"]})
            for im, dx, dy, _, delay, anim in parts:
                els.append(El(im, (W - w) / 2 + dx, 700 - h / 2 + dy, t0 + delay, t1, anim))
    if d.get("name"):
        ta = c.t(d.get("name_at", len(c.tl["lines"]) - 1))
        nm = fit_text(d["name"], "serif-black", 112, ink, 420)
        cx = 330 if d.get("seal") else 360
        els.append(place(nm, cx, 712, ta))
        if d.get("name_years"):
            els.append(place(text_img(d["name_years"], F("sans-med", 30), muted + (255,)), cx, 800, ta + 0.3))
        if d.get("seal"):
            im = seal_img(d["seal"], 52 if len(d["seal"]) <= 3 else 44, None, -7)
            els.append(place(im, min(650, cx + nm.width / 2 + 60), 722, ta + 0.6, None, "stamp", 0.35))
    return els


def b_timeline(c):
    d = c.d
    els = []
    if d.get("bg_char"):
        g = text_img(d["bg_char"], F("serif-black", 430), INK + (20,))
        els.append(El(g, 690 - g.width, 330, c.t(), None, "fade", 1.2))
    nodes = d["nodes"]
    n = len(nodes)
    sp = 140 if n < 2 else min(140, 440 / (n - 1))
    y0 = 520 - sp * (n - 1) / 2
    line = Image.new("RGBA", (4, int(sp * (n - 1) + 150)), INK + (255,))
    els.append(El(line, 148, y0 - 50, c.t(nodes[0].get("at", 0)), None, "wipedown", 2.5))
    for k, nd in enumerate(nodes):
        y = y0 + k * sp
        t0 = c.t(nd.get("at", 0), nd.get("delay", 0))
        dot = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
        ImageDraw.Draw(dot).ellipse((2, 2, 27, 27), fill=RED + (255,), outline=PAPER + (255,), width=4)
        els.append(El(dot, 135, y - 35, t0, None, "stamp", 0.3))
        big = fit_text(nd["big"], "serif-black", 58, col(nd.get("color"), INK), 480)
        els.append(El(big, 192, y - 22 - big.height / 2, t0))
        if nd.get("small"):
            sm = fit_text(nd["small"], "sans-med", 30, MUTED, 480)
            els.append(El(sm, 194, y + 36 - sm.height / 2, t0 + 0.2))
    return els


def b_document(c):
    d = c.d
    rows = d.get("rows", [])
    lst = d.get("list")
    foot = d.get("footer")
    h = 150 + len(rows) * 50 + (40 + len(lst["items"]) * 42 if lst else 0) + (70 if foot else 0) + 20
    x0, y0 = 60, max(VIS_TOP, (VIS_TOP + VIS_BOT + 10) / 2 - h / 2)
    if y0 + h > VIS_BOT + 15:
        WARN.append(f"document card too tall ({h}px)")
    card = Image.new("RGBA", (616, int(h) + 16), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((10, 12, card.width - 2, card.height - 2), 8, fill=(60, 40, 20, 60))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    dr = ImageDraw.Draw(card)
    dr.rounded_rectangle((0, 0, 600, h), 8, fill=PAPER_LT + (255,), outline=INK + (255,), width=2)
    dr.rectangle((10, 10, 590, h - 10), outline=INK + (110,), width=1)
    hd = fit_text(" ".join(d["title"]) if len(d["title"]) <= 5 else d["title"], "serif-black", 54, INK, 520)
    card.paste(hd, ((600 - hd.width) // 2, 28), hd)
    if d.get("subtitle"):
        sb = fit_text(d["subtitle"], "sans", 21, MUTED, 540)
        card.paste(sb, ((600 - sb.width) // 2, 98), sb)
    dr.line((30, 132, 570, 132), fill=INK + (255,), width=2)
    dr.line((30, 138, 570, 138), fill=INK + (255,), width=1)
    els = [El(card, x0, y0, c.t(d.get("at", 0), d.get("delay", 0.4)), None, "rise", 0.7)]
    y = y0 + 185

    def row(label, value, t0, red=False, bold=False):
        lab = text_img(label, F("serif-bold", 28), MUTED + (255,))
        els.append(El(lab, 96, y - lab.height / 2, t0, None, "fade"))
        v = fit_text(value, "serif-black" if bold else "serif-med", 32 if not bold else 31, RED if red else INK, 400)
        els.append(El(v, 232, y - v.height / 2, t0 + 0.1))

    for r in rows:
        row(r["label"], r["value"], c.t(r.get("at", 0), r.get("delay", 0)), r.get("red"))
        y += 50
    if lst:
        y -= 18
        els.append(rule_el(90, 630, y, c.t(lst.get("at", 0)), INK, 1))
        y += 34
        lab = text_img(lst["label"], F("serif-bold", 28), MUTED + (255,))
        els.append(El(lab, 96, y - lab.height / 2, c.t(lst.get("at", 0)), None, "fade"))
        for k, itm in enumerate(lst["items"]):
            v = fit_text(itm["text"], "serif-med", 31, INK, 300)
            els.append(El(v, 232, y - v.height / 2, c.t(itm.get("at", lst.get("at", 0)), itm.get("delay", 0))))
            if lst.get("tag"):
                tg = text_img(lst["tag"], F("serif-black", 31), RED + (255,))
                els.append(El(tg, 600 - tg.width, y - tg.height / 2, c.t(lst.get("tag_at", 0), 0.15 * k), None, "stamp", 0.4))
            y += 42
    if foot:
        y += 4
        els.append(rule_el(90, 630, y - 28, c.t(foot.get("at", 0)), INK, 1))
        row(foot["label"], foot["value"], c.t(foot.get("at", 0), foot.get("delay", 0)), foot.get("red", True), True)
    return els


def b_tiles(c):
    d = c.d
    els = [place(fit_text(d["header"], "serif-black", 78, INK), 360, 262, c.t(d.get("header_at", 0)))]
    tiles = d["tiles"][:6]
    rows = (len(tiles) + 1) // 2
    ytop = 345 if rows == 3 else 380
    for k, tl_ in enumerate(tiles):
        im = box_img(280, 112, PAPER_LT, INK, 2, 12)
        ti = fit_text(tl_["text"], "serif-black", 46, INK, 250)
        im.paste(ti, ((280 - ti.width) // 2, (112 - ti.height) // 2 + 4), ti)
        ni = text_img(f"0{k + 1}", F("sans-bold", 18), RED + (255,))
        im.paste(ni, (14, 10), ni)
        els.append(El(im, 70 + (k % 2) * 300, ytop + (k // 2) * 132, c.t(tl_.get("at", 0), tl_.get("delay", 0))))
    a = d.get("arrow")
    if a:
        y = ytop + rows * 132 + 50
        t0 = c.t(a.get("at", 0))
        els += [place(fit_text(a["from"], "serif-black", 48, INK, 180), 190, y, t0),
                rule_el(250, 470, y + 2, t0 + 0.4, RED, 4),
                place(text_img("▶", F("sans-black", 30), RED + (255,)), 478, y + 1, t0 + 1.0),
                place(fit_text(a["to"], "serif-black", 48, RED, 180), 548, y, c.t(a.get("to_at", a.get("at", 0))))]
    return els


def b_end(c):
    d, s = c.d, c.t()
    els = [place(fit_text(d["name"], "serif-black", 132, INK, 600), 360, 400, s)]
    if d.get("years"):
        els.append(place(text_img(d["years"], F("sans-med", 34), MUTED + (255,)), 360, 500, s + 0.4))
    if d.get("seal"):
        els.append(place(seal_img(d["seal"], 62 if len(d["seal"]) <= 3 else 50, None, -5), 360, 655, s + 1.0, None, "stamp", 0.35))
    els.append(place(text_img(d.get("kicker", f"歷史上的今天　{EP['mmdd']}"), F("serif-bold", 36), RED + (255,)), 360, 820, s + 1.6))
    return els


BUILD = dict(title=b_title, timeline=b_timeline, document=b_document, tiles=b_tiles, stack=b_stack, end=b_end)


# ---------------------------------------------------------------- background, overlay, subtitles
def make_bg():
    rng = np.random.default_rng(11)
    yy, xx = np.mgrid[0:H, 0:W]
    base = np.array(PAPER, np.float32)[None, None, :].repeat(H, 0).repeat(W, 1)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2)
    base *= (1 - 0.20 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]
    n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n = np.array(Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
                 .filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) - 128
    base += (n * 0.18 + rng.normal(0, 3.5, (H, W)).astype(np.float32))[..., None]
    bl = np.zeros((H, W), np.float32)
    for _ in range(14):
        cx, cy, rad = rng.integers(0, W), rng.integers(0, H), rng.integers(60, 220)
        bl += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2))) * rng.uniform(4, 10)
    base -= bl[..., None] * np.array([0.6, 0.8, 1.2])[None, None, :]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def make_overlay(dark=False):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hi = text_img("今天，誰改變了世界", F("serif-bold", 30), ((226, 120, 104) if dark else RED) + (255,))
    ov.paste(hi, (60, 72 - hi.height // 2), hi)
    hr = text_img(EP["mmdd"], F("serif-black", 34), (CREAM if dark else INK) + (255,))
    ov.paste(hr, (660 - hr.width, 72 - hr.height // 2), hr)
    ImageDraw.Draw(ov).line((60, 108, 660, 108), fill=(CREAM if dark else INK) + (90,), width=1)
    if EP.get("footer"):
        ft = fit_text(EP["footer"], "sans", 21, LIGHT if dark else MUTED, 640)
        ov.paste(ft, ((W - ft.width) // 2, 1196), ft)
    return ov


def clean_sub(s):
    return re.sub(r"[，、；：。]", "　", s).strip("　 ")


def sub_img(s):
    f = F("sans-med", 40)
    s = clean_sub(s)
    lines = [s]
    if f.getlength(s) > 600:
        sp = [i for i, ch in enumerate(s) if ch == "　"]
        mid = len(s) / 2
        cut = min(sp, key=lambda i: abs(i - mid)) if sp else int(mid)
        lines = [s[:cut].strip("　"), s[cut:].strip("　")]
        for ln in lines:
            if f.getlength(ln) > 640:
                WARN.append(f"subtitle line too long: {ln}")
    tis = [text_img(x, f, CREAM + (255,)) for x in lines]
    w, h = max(t.width for t in tis) + 52, 56 * len(tis) + 26
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), 14, fill=(35, 27, 21, 222))
    for k, t in enumerate(tis):
        im.paste(t, ((w - t.width) // 2, 13 + k * 56 + (56 - t.height) // 2), t)
    return im


def rain(frame, t, t0, t1):
    if t < t0 or t > t1 + 0.4:
        return
    a = min(1, (t - t0) / 0.8) * (1 if t < t1 else max(0, 1 - (t - t1) / 0.4))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    rng = random.Random(42)
    for _ in range(150):
        x0, sp, ln = rng.uniform(-200, W + 50), rng.uniform(900, 1400), rng.uniform(26, 60)
        y = (rng.uniform(0, H) + t * sp) % (H + 200) - 100
        x = x0 + (y / H) * 160
        d.line((x, y, x + ln * 0.14, y + ln), fill=(70, 70, 85, int(70 * a)), width=2)
    frame.paste(ov, (0, 0), ov)


# ---------------------------------------------------------------- load
EP_DIR = sys.argv[1]
EP = json.load(open(os.path.join(EP_DIR, "episode.json")))
TLJ = json.load(open(os.path.join(EP_DIR, "timeline.json")))
TL = TLJ["scenes"]
TOTAL = TLJ["total"]
BG = make_bg()
OVER = make_overlay()
OVER_DARK = make_overlay(True)

SCN = []
for sc, tl in zip(EP["scenes"], TL):
    c = Ctx(sc, tl)
    els = []
    if sc.get("chapter"):
        els.append(chapter_el(sc["chapter"], tl["start"]))
    els += BUILD[sc["template"]](c)
    fx = []
    for e in sc.get("effects", []):
        if e["type"] == "rain":
            fx.append(("rain", c.t(e.get("from", 0)), c.until(e.get("to")) or tl["end"]))
    dark = sc["template"] == "title" and bool(sc.get("data", {}).get("image"))
    SCN.append((tl, els, fx, dark))

SUBS = []
for tl in TL:
    for li, ln in enumerate(tl["lines"]):
        nxt = tl["lines"][li + 1]["start"] if li + 1 < len(tl["lines"]) else ln["end"] + 0.45
        SUBS.append((ln["start"] - 0.05, nxt - 0.02, sub_img(ln["text"])))

XF = 0.35


def scene_frame(idx, t):
    tl, els, fx, _ = SCN[idx]
    fr = BG.copy()
    for el in els:
        el.draw(fr, t)
    for kind, a, b in fx:
        if kind == "rain":
            rain(fr, t, a, b)
    p = min(1, max(0, (t - tl["start"]) / (tl["end"] - tl["start"])))
    s = 1.0 + 0.035 * p
    if s > 1.001:
        nw, nh = int(W * s), int(H * s)
        big = fr.resize((nw, nh), Image.BILINEAR)
        left, top = int(nw / 2 - W / 2), int(520 * s - 520)
        fr = big.crop((left, top, left + W, top + H))
    return fr


def frame_at(t):
    idx = 0
    for i, s_ in enumerate(SCN):
        if t >= s_[0]["start"] - (XF if i else 0):
            idx = i
    tl = SCN[idx][0]
    fr = scene_frame(idx, t)
    if idx > 0 and t < tl["start"] + XF:
        k = max(0, min(1, (t - (tl["start"] - XF)) / (2 * XF)))
        fr = Image.blend(scene_frame(idx - 1, t), fr, k * k * (3 - 2 * k))
    ov = OVER_DARK if SCN[idx][3] else OVER
    fr.paste(ov, (0, 0), ov)
    ImageDraw.Draw(fr).rectangle((0, 0, int(W * min(1, t / TOTAL)), 5), fill=RED)
    for s0, s1, im in SUBS:
        if s0 <= t < s1:
            a = min(1, (t - s0) / 0.12)
            if a < 1:
                im = im.copy()
                im.putalpha(im.getchannel("A").point(lambda v, a=a: int(v * a)))
            fr.paste(im, ((W - im.width) // 2, int(SUB_Y - im.height / 2)), im)
            break
    dark = Image.new("RGB", (W, H), (20, 16, 12))
    if t > TOTAL - 1.2:
        fr = Image.blend(fr, dark, min(1, (t - (TOTAL - 1.2)) / 1.2))
    return fr


def check_times():
    """one frame just before each element disappears, plus each scene's final state"""
    ts = []
    for tl, els, _, _ in SCN:
        ends = sorted({e.t1 for e in els if e.t1 is not None and tl["start"] < e.t1 <= tl["end"] + 0.5})
        ts += [x - 0.3 for x in ends] + [tl["end"] - 0.5]
    return ts


if __name__ == "__main__":
    mode = sys.argv[2]
    chk = os.path.join(EP_DIR, "check")
    if mode in ("stills", "sheet"):
        os.makedirs(chk, exist_ok=True)
    if mode == "stills":
        for ts in sys.argv[3:]:
            frame_at(float(ts)).save(os.path.join(chk, f"f_{float(ts):07.2f}.png"))
    elif mode == "sheet":
        ts = check_times()
        ims = [frame_at(t).resize((360, 640)) for t in ts]
        per = 6
        for k in range(0, len(ims), per):
            grp = ims[k:k + per]
            sh = Image.new("RGB", (370 * len(grp) - 10, 640), (255, 255, 255))
            for i, im in enumerate(grp):
                sh.paste(im, (i * 370, 0))
            sh.save(os.path.join(chk, f"sheet_{k // per:02d}.png"))
        print(f"{len(ims)} frames -> {chk}/sheet_*.png")
    elif mode == "seg":
        a, b, out = float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
        n0, n1 = int(round(a * FPS)), int(round(b * FPS))
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                              "-crf", "19", "-pix_fmt", "yuv420p", "-threads", "1", out], stdin=subprocess.PIPE)
        for n in range(n0, n1):
            p.stdin.write(frame_at(n / FPS).tobytes())
        p.stdin.close()
        p.wait()
    for w in dict.fromkeys(WARN):
        print("WARNING:", w)
