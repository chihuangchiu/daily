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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--target", type=float, default=238.0)
    a = ap.parse_args()
    ep = json.load(open(os.path.join(a.episode_dir, "episode.json")))
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
