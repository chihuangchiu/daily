"""episode.json -> narration.wav + timeline.json

Usage: python3 narrate.py EPISODE_DIR [--target 238]
episode.json "lang": "zh" (default, Baker FastSpeech2), "en" (Kokoro af_heart), "es" (Kokoro ef_dora),
"pt" (Kokoro pf_dora), "de" (Piper thorsten-high) or "ja" (misaki G2P + Kokoro jf_alpha via kokoro-onnx).
Synthesises every subtitle line (comma phrases separately), auto-tunes the
speaking speed so the whole narration lands near --target seconds, and writes
per-line timings that render.py uses for subtitles and reveals.
"""
import argparse, json, os, re, sys
import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import onnxruntime as ort

SR = 24000
LEAD, SUB_GAP, LINE_GAP, SCENE_GAP, TAIL = 0.8, 0.18, 0.40, 1.1, 2.5


KOKORO_DIR = os.path.join(HERE, "models", "kokoro-multi-lang-v1_0")
KOKORO_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2"
EN_VOICE = 3  # af_heart (Kokoro v1.0): warm US female voice, used for every English episode
ES_VOICE = 28  # ef_dora (Kokoro v1.0): Spanish female voice, used for every Spanish episode


class EnTTS:
    """English / Spanish narration (lang "en" / "es"): Kokoro via sherpa-onnx, one call per subtitle line."""
    def __init__(self, lang="en"):
        self.sid = ES_VOICE if lang == "es" else EN_VOICE
        import sherpa_onnx
        if not os.path.exists(os.path.join(KOKORO_DIR, "model.onnx")):
            print("downloading Kokoro (~350 MB) ...", flush=True)
            os.system(f'cd "{os.path.dirname(KOKORO_DIR)}" && curl -sSfL "{KOKORO_URL}" | tar xj')
        d = KOKORO_DIR + "/"
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
                data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
                lexicon=("" if lang == "es" else d + "lexicon-us-en.txt,lexicon-zh.txt"),
                lang=("es" if lang == "es" else "")), num_threads=4))
        self.tts = sherpa_onnx.OfflineTts(cfg)

    def phrase(self, text, speed=1.0):
        # narrate.py's speed is a duration ratio (>1 = slower, as in FastSpeech2); Kokoro's speed is a rate
        a = self.tts.generate(text, sid=self.sid, speed=1.0 / speed)
        x = np.asarray(a.samples, np.float32)
        if a.sample_rate != SR:
            n = int(len(x) * SR / a.sample_rate)
            x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
        return x


def _resample(x, sr):
    x = np.asarray(x, np.float32)
    if sr != SR:
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return x


def _fetch(url, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    print("downloading", url, flush=True)
    if url.endswith(".tar.bz2"):
        os.system(f'cd "{dest_dir}" && curl -sSfL "{url}" | tar xj')
    else:
        os.system(f'cd "{dest_dir}" && curl -sSfLO "{url}"')


class PtTTS:
    """Portuguese (lang "pt"): Kokoro pf_dora (sid 42) via sherpa-onnx, espeak pt-br."""
    def __init__(self):
        import sherpa_onnx
        if not os.path.exists(os.path.join(KOKORO_DIR, "model.onnx")):
            _fetch(KOKORO_URL, os.path.dirname(KOKORO_DIR))
        d = KOKORO_DIR + "/"
        self.tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
                data_dir=d + "espeak-ng-data", dict_dir=d + "dict", lexicon="", lang="pt-br"), num_threads=4)))

    def phrase(self, text, speed=1.0):
        a = self.tts.generate(text, sid=42, speed=1.0 / speed)
        return _resample(a.samples, a.sample_rate)


PIPER_DE = os.path.join(HERE, "models", "vits-piper-de_DE-thorsten-high")
PIPER_DE_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-de_DE-thorsten-high.tar.bz2"


class DeTTS:
    """German (lang "de"): Piper de_DE thorsten-high (male) via sherpa-onnx (Kokoro has no German voice)."""
    def __init__(self):
        import sherpa_onnx
        if not os.path.exists(os.path.join(PIPER_DE, "de_DE-thorsten-high.onnx")):
            _fetch(PIPER_DE_URL, os.path.dirname(PIPER_DE))
        d = PIPER_DE + "/"
        self.tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=d + "de_DE-thorsten-high.onnx", tokens=d + "tokens.txt",
                                                       data_dir=d + "espeak-ng-data"), num_threads=4)))

    def phrase(self, text, speed=1.0):
        a = self.tts.generate(text, sid=0, speed=1.0 / speed)
        return _resample(a.samples, a.sample_rate)


KOKORO_ONNX = os.path.join(HERE, "models", "kokoro-onnx")
KOKORO_ONNX_URLS = ["https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
                    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"]


class JaTTS:
    """Japanese (lang "ja"): misaki G2P (pyopenjtalk) -> phonemes -> Kokoro jf_alpha via kokoro-onnx.
    sherpa-onnx's Kokoro drops kanji and espeak's Japanese is unusable, so this path is required."""
    def __init__(self):
        from kokoro_onnx import Kokoro
        from misaki import ja
        for u in KOKORO_ONNX_URLS:
            if not os.path.exists(os.path.join(KOKORO_ONNX, os.path.basename(u))):
                _fetch(u, KOKORO_ONNX)
        self.k = Kokoro(os.path.join(KOKORO_ONNX, "kokoro-v1.0.onnx"), os.path.join(KOKORO_ONNX, "voices-v1.0.bin"))
        self.g2p = ja.JAG2P()

    def phrase(self, text, speed=1.0):
        ps = self.g2p(text)
        ps = ps[0] if isinstance(ps, tuple) else ps
        a, sr = self.k.create(ps, voice="jf_alpha", speed=max(0.5, min(2.0, 1.0 / speed)), lang="ja", is_phonemes=True)
        return _resample(a, sr)


class TTS:
    def __init__(self):
        from tts import BakerProcessor
        m = os.path.join(HERE, "models")
        self.proc = BakerProcessor(data_dir=None, loaded_mapper_path=os.path.join(m, "baker_mapper.json"))
        so = ort.SessionOptions()
        so.log_severity_level = 3
        self.ac = ort.InferenceSession(os.path.join(m, "fs2.onnx"), so)
        self.voc = ort.InferenceSession(os.path.join(m, "melgan.onnx"), so)

    def phrase(self, text, speed=1.0):
        ids = self.proc.text_to_sequence(text, inference=True)
        mel = self.ac.run(None, {
            "input_ids": np.array([ids], np.int32),
            "speaker_ids": np.array([0], np.int32),
            "speed_ratios": np.array([speed], np.float32),
            "f0_ratios": np.array([1.0], np.float32),
            "energy_ratios": np.array([1.0], np.float32),
        })[1]
        name = self.voc.get_inputs()[0].name
        return self.voc.run(None, {name: mel.astype(np.float32)})[0][0, :, 0]


def trim(a, thr=0.004):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - int(0.02 * SR)): min(len(a), idx[-1] + int(0.05 * SR))]


def norm_line(ln):
    if isinstance(ln, str):
        return ln, ln
    disp, spoken = ln[0], (ln[1] if len(ln) > 1 and ln[1] else ln[0])
    return disp, spoken


def spoken_parts(spoken, lang="zh"):
    if lang == "ja":
        sp = re.sub(r"[「」『』〈〉《》（）()\"“”]", "", spoken).strip()
        return [sp] if sp else []
    if lang != "zh":
        # one natural phrase per subtitle line: Kokoro keeps the intonation, commas become its own short pauses
        sp = re.sub(r"[\"“”«»()\[\]]", "", spoken).strip()
        return [sp] if sp else []
    spoken = re.sub(r"[「」〈〉《》『』──…\"“”‘’'()（）]", "", spoken)
    return [p for p in re.split(r"[，、；：。！？,;:!?]", spoken) if p.strip()]


def check_digits(scenes):
    bad = []
    for sc in scenes:
        for ln in sc["lines"]:
            _, sp = norm_line(ln)
            if re.search(r"[0-9A-Za-z]", sp):
                bad.append(sp)
    return bad


def synth(tts, scenes, speed, lang="zh"):
    cache, out, t = {}, [np.zeros(int(LEAD * SR), np.float32)], LEAD
    timeline, speech = [], 0.0
    for si, sc in enumerate(scenes):
        s0, lines = t, []
        for li, ln in enumerate(sc["lines"]):
            disp, spoken = norm_line(ln)
            parts = spoken_parts(spoken, lang)
            start = t
            for pi, p in enumerate(parts):
                key = (p, speed)
                if key not in cache:
                    cache[key] = trim(tts.phrase(p, speed))
                a = cache[key]
                out.append(a)
                t += len(a) / SR
                speech += len(a) / SR
                if pi < len(parts) - 1:
                    out.append(np.zeros(int(SUB_GAP * SR), np.float32))
                    t += SUB_GAP
            lines.append(dict(text=disp, start=round(start, 3), end=round(t, 3)))
            last = li == len(sc["lines"]) - 1
            gap = LINE_GAP if not last else (SCENE_GAP if si < len(scenes) - 1 else TAIL)
            out.append(np.zeros(int(gap * SR), np.float32))
            t += gap
        timeline.append(dict(start=round(s0, 3), end=round(t, 3), lines=lines))
    return np.concatenate(out), timeline, speech, t


# ---------------------------------------------------------------- Gemini TTS (Nathan 2026-10-25)
# The Gemini TTS MCP tool can only be called by the agent, so this is a two-step flow:
#   narrate.py EP --gemini-plan   -> EP/tts/plan.json (one chunk for the hook line, then one chunk per scene)
#   (agent) generate_speech for every chunk, curl each result to EP/tts/<id>.wav
#   narrate.py EP --gemini        -> splits every chunk back into its subtitle lines at the pauses and writes
#                                    narration.wav + timeline.json exactly like the local engines (no tempo change)
GEMINI_LANG = {"zh": "cmn-tw", "en": "en-US", "es": "es-ES", "pt": "pt-BR", "ja": "ja-JP", "de": "de-DE"}
GEMINI_STYLE = {
    "zh": ("台灣口音的短影音紀錄片旁白。這是影片的第一句：用和後面一樣明快的語速，不要放慢；語氣帶著真心的驚訝和讚嘆，像在說「你絕對想不到」的事。",
           "台灣口音的短影音紀錄片旁白，溫暖、有一點神秘感。語速明顯偏快、節奏明快緊湊，像 YouTube Shorts 的說書人；句子之間只做很短的停頓，不要拖長尾音。"),
    "en": ("Short-form documentary narrator. Opening line: same brisk pace as the rest, do not slow down; sound genuinely amazed and astonished, like revealing something the viewer would never guess.",
           "Warm, intriguing short-form documentary narrator. Noticeably brisk, energetic pace like a YouTube Shorts storyteller; keep pauses between sentences short and do not drag the ends of sentences."),
    "es": ("Narrador de documental para videos cortos, con ritmo ágil (igual que el resto, nada lento) y un tono de asombro sincero.",
           "Narrador de documental cálido e intrigante para videos cortos. Ritmo claramente ágil y enérgico, como un narrador de YouTube Shorts; pausas breves entre frases, sin alargar los finales."),
    "pt": ("Narrador de documentário para vídeos curtos, português do Brasil, com ritmo ágil (igual ao resto, nada lento) e tom de espanto sincero.",
           "Narrador de documentário caloroso e intrigante para vídeos curtos, português do Brasil. Ritmo claramente ágil e enérgico, como um narrador de YouTube Shorts; pausas curtas entre as frases, sem arrastar os finais."),
    "ja": ("ショート動画のドキュメンタリーのナレーター。最初の一文：後と同じテンポの速さで、ゆっくりにしない。「信じられない！」という本気の驚きと感嘆を込めて。",
           "温かく引き込まれるショート動画のドキュメンタリーのナレーター。はっきりと速めの、テンポのよい語り口で。文と文の間は短く、語尾を伸ばさない。"),
    "de": ("Erzähler einer kurzen Doku, zügiges Tempo (wie der Rest, nicht langsamer) und ein Ton echten Staunens.",
           "Warmer, fesselnder Erzähler einer kurzen Doku. Deutlich zügiges, lebendiges Tempo wie ein YouTube-Shorts-Erzähler; kurze Pausen zwischen den Sätzen, Satzenden nicht dehnen."),
}
GEMINI_VOICE = "Kore"


def _clean_for_gemini(spoken, lang):
    sp = re.sub(r"[─—]+", "，" if lang in ("zh", "ja") else ", ", spoken)
    return re.sub(r"\s+", " ", sp).strip()


def gemini_plan(ep, ep_dir):
    lang = ep.get("lang", "zh")
    hook_style, body_style = GEMINI_STYLE[lang]
    chunks = []
    for si, sc in enumerate(ep["scenes"]):
        idx = list(range(len(sc["lines"])))
        if si == 0 and idx:
            chunks.append(dict(id="c00_hook", lines=[[0, 0]], style=hook_style,
                               text=_clean_for_gemini(norm_line(sc["lines"][0])[1], lang)))
            idx = idx[1:]
        joiner = "" if lang in ("zh", "ja") else " "
        group = []
        for li in idx:  # one chunk per sentence: lines are joined until a line ends a sentence
            group.append(li)
            sp = norm_line(sc["lines"][li])[1]
            if _is_final(sp) or li == idx[-1]:
                text = joiner.join(_clean_for_gemini(norm_line(sc["lines"][g])[1], lang) for g in group)
                chunks.append(dict(id=f"c{si + 1:02d}_{group[0]:02d}", lines=[[si, g] for g in group],
                                   style=body_style, text=text))
                group = []
    plan = dict(language=GEMINI_LANG[lang], voice=GEMINI_VOICE, model="gemini-2.5-flash-tts", format="wav",
                chunks=chunks)
    os.makedirs(os.path.join(ep_dir, "tts"), exist_ok=True)
    json.dump(plan, open(os.path.join(ep_dir, "tts", "plan.json"), "w"), ensure_ascii=False, indent=1)
    for c in chunks:
        assert len(c["text"].encode()) <= 4000, c["id"]
    print(f"{len(chunks)} chunks -> {ep_dir}/tts/plan.json (language {plan['language']}, voice {plan['voice']})")


def _is_final(sp):
    return bool(re.search(r"[。！？.!?]\s*[」”\"»）)]*\s*$", sp))


def _weight(s, lang):
    s = re.sub(r"[\s，、。！？：；,.!?:;\"“”«»「」()（）'’‘—─-]", "", s)
    return max(1, len(s))


def _silences(a, win=0.01, min_len=0.06):
    n = int(win * SR)
    m = len(a) // n
    rms = np.sqrt(np.mean(a[: m * n].reshape(m, n) ** 2, axis=1))
    thr = max(0.006, 0.04 * np.percentile(rms, 95))
    quiet = rms < thr
    out, i = [], 0
    while i < m:
        if quiet[i]:
            j = i
            while j < m and quiet[j]:
                j += 1
            if (j - i) * win >= min_len:
                out.append(((i) * win, j * win))
            i = j
        else:
            i += 1
    return out


def cap_pauses(a, cap):
    """Shorten every pause inside a clip to at most cap seconds (keeps the delivery, removes dead air)."""
    keep, t0 = [], 0
    for b, e in _silences(a, min_len=cap + 0.02):
        bi, ei = int(b * SR), int(e * SR)
        keep.append(a[t0: bi + int(cap / 2 * SR)])
        t0 = ei - int(cap / 2 * SR)
    keep.append(a[t0:])
    return np.concatenate(keep)


def split_chunk(a, weights, debug=False, finals=None):
    """Cut one chunk into len(weights) pieces at pauses. The n-1 cut points are chosen together (dynamic
    programming over all pauses): long pauses are preferred, and each cut should sit near its
    character-proportional estimate (estimates use speaking time only, pauses excluded)."""
    a = trim(a)
    n = len(weights)
    if n == 1:
        return [a]
    dur = len(a) / SR
    sil = [s for s in _silences(a, min_len=0.05) if s[0] > 0.05 and s[1] < dur - 0.05]
    speech = dur - sum(e - b for b, e in sil)

    def speech_time(t):  # speaking time elapsed at t
        return t - sum(min(e, t) - b for b, e in sil if b < t)

    tot, cum, est = sum(weights), 0, []
    for w in weights[:-1]:
        cum += w
        est.append(speech * cum / tot)
    m = len(sil)
    if m < n - 1:
        print(f"WARNING: only {m} pauses for {n - 1} cuts; cutting by proportion")
        bounds = [(dur * e / speech,) * 2 for e in est]
    else:
        fin = finals or [True] * (n - 1)

        def score(k, j):  # cut k placed at pause j; sentence ends want long pauses, commas short ones
            b, e = sil[j]
            d = e - b
            if fin[k]:
                r = 4.0 * min(d, 0.6)
            else:
                r = 2.0 * min(d, 0.25) - 3.0 * max(0.0, d - 0.3)
            return r - abs(speech_time(b) - est[k])
        NEG = -1e9
        best = [[NEG] * m for _ in range(n - 1)]
        prev = [[-1] * m for _ in range(n - 1)]
        for j in range(m):
            best[0][j] = score(0, j)
        for k in range(1, n - 1):
            run, arg = NEG, -1
            for j in range(m):
                if j - 1 >= 0 and best[k - 1][j - 1] > run:
                    run, arg = best[k - 1][j - 1], j - 1
                if arg >= 0:
                    best[k][j] = run + score(k, j)
                    prev[k][j] = arg
        j = max(range(m), key=lambda j: best[n - 2][j])
        idx = []
        for k in range(n - 2, -1, -1):
            idx.append(j)
            j = prev[k][j]
        idx.reverse()
        bounds = [sil[j] for j in idx]
    if debug:
        print("pauses", [(round(b, 2), round(e - b, 2)) for b, e in sil])
        print("cuts  ", [round(b[0], 2) for b in bounds])
    pieces, t0 = [], 0.0
    for b, e in bounds:
        pieces.append(trim(a[int(t0 * SR): int(b * SR)]))
        t0 = e
    pieces.append(trim(a[int(t0 * SR):]))
    return pieces


def gemini_assemble(ep, ep_dir):
    lang = ep.get("lang", "zh")
    plan = json.load(open(os.path.join(ep_dir, "tts", "plan.json")))
    seg = {}
    for c in plan["chunks"]:
        f = os.path.join(ep_dir, "tts", c["id"] + ".wav")
        if not os.path.exists(f):
            print("ERROR: missing", f)
            sys.exit(2)
        sr, x = wavfile.read(f)
        x = x.astype(np.float32)
        if x.ndim > 1:
            x = x.mean(axis=1)
        if np.abs(x).max() > 2:
            x /= 32768.0
        x = _resample(x, sr)
        sps = [norm_line(ep["scenes"][si]["lines"][li])[1] for si, li in c["lines"]]
        ws = [_weight(sp, lang) for sp in sps]
        fins = [_is_final(sp) for sp in sps[:-1]]
        for (si, li), p in zip(c["lines"], split_chunk(x, ws, finals=fins)):
            seg[(si, li)] = cap_pauses(p, 0.35 if (si, li) == (0, 0) else 0.45)
    out, t, timeline = [np.zeros(int(LEAD * SR), np.float32)], LEAD, []
    for si, sc in enumerate(ep["scenes"]):
        s0, lines = t, []
        for li, ln in enumerate(sc["lines"]):
            a = seg[(si, li)]
            lines.append(dict(text=norm_line(ln)[0], start=round(t, 3), end=round(t + len(a) / SR, 3)))
            out.append(a)
            t += len(a) / SR
            last = li == len(sc["lines"]) - 1
            gap = 0.3 if not last else (0.9 if si < len(ep["scenes"]) - 1 else TAIL)  # Gemini keeps its own breaths
            if si == 0 and li == 0:
                gap = 0.6  # let the dramatic hook breathe
            out.append(np.zeros(int(gap * SR), np.float32))
            t += gap
        timeline.append(dict(start=round(s0, 3), end=round(t, 3), lines=lines))
    audio = np.concatenate(out)
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.89
    wavfile.write(os.path.join(ep_dir, "narration.wav"), SR, (audio * 32767).astype(np.int16))
    json.dump(dict(total=round(t, 3), speed=1.0, engine="gemini", scenes=timeline),
              open(os.path.join(ep_dir, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    note = "" if 112 <= t <= 128 else "  WARNING: outside 112-128 s, lengthen/shorten the script"
    print(f"narration {t:.1f}s (gemini, no tempo change){note}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--target", type=float, default=238.0)
    ap.add_argument("--gemini-plan", action="store_true", help="write tts/plan.json for the Gemini TTS MCP tool")
    ap.add_argument("--gemini", action="store_true", help="build narration from tts/*.wav made by Gemini TTS")
    a = ap.parse_args()
    ep = json.load(open(os.path.join(a.episode_dir, "episode.json")))
    if a.gemini_plan:
        return gemini_plan(ep, a.episode_dir)
    if a.gemini:
        return gemini_assemble(ep, a.episode_dir)
    lang = ep.get("lang", "zh")
    bad = check_digits(ep["scenes"]) if lang == "zh" else []
    if bad:
        print("ERROR: spoken text must use Chinese numerals / no Latin letters:", *bad, sep="\n  ")
        sys.exit(2)
    tts = {"zh": TTS, "pt": PtTTS, "de": DeTTS, "ja": JaTTS}.get(lang, lambda: EnTTS(lang))()
    audio, tl, speech, total = synth(tts, ep["scenes"], 1.0, lang)
    fixed = total - speech
    speed = (a.target - fixed) / speech
    if not 0.85 <= speed <= 1.15:
        print(f"WARNING: script length off target (needs speed {speed:.2f}); clamped. "
              f"At speed 1.0 the narration is {total:.1f}s; adjust the script length.")
    speed = min(1.15, max(0.85, speed))
    audio, tl, speech, total = synth(tts, ep["scenes"], speed, lang)
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.89
    wavfile.write(os.path.join(a.episode_dir, "narration.wav"), SR, (audio * 32767).astype(np.int16))
    json.dump(dict(total=round(total, 3), speed=round(speed, 3), scenes=tl),
              open(os.path.join(a.episode_dir, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print(f"narration {total:.1f}s at speed {speed:.3f}")


if __name__ == "__main__":
    main()
