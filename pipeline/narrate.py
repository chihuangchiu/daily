"""episode.json -> narration.wav + timeline.json

Usage: python3 narrate.py EPISODE_DIR [--target 238]
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
from tts import BakerProcessor

SR = 24000
LEAD, SUB_GAP, LINE_GAP, SCENE_GAP, TAIL = 0.8, 0.18, 0.40, 1.1, 2.5


class TTS:
    def __init__(self):
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


def spoken_parts(spoken):
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


def synth(tts, scenes, speed):
    cache, out, t = {}, [np.zeros(int(LEAD * SR), np.float32)], LEAD
    timeline, speech = [], 0.0
    for si, sc in enumerate(scenes):
        s0, lines = t, []
        for li, ln in enumerate(sc["lines"]):
            disp, spoken = norm_line(ln)
            parts = spoken_parts(spoken)
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
    bad = check_digits(ep["scenes"])
    if bad:
        print("ERROR: spoken text must use Chinese numerals / no Latin letters:", *bad, sep="\n  ")
        sys.exit(2)
    tts = TTS()
    audio, tl, speech, total = synth(tts, ep["scenes"], 1.0)
    fixed = total - speech
    speed = (a.target - fixed) / speech
    if not 0.85 <= speed <= 1.15:
        print(f"WARNING: script length off target (needs speed {speed:.2f}); clamped. "
              f"At speed 1.0 the narration is {total:.1f}s; adjust the script length.")
    speed = min(1.15, max(0.85, speed))
    audio, tl, speech, total = synth(tts, ep["scenes"], speed)
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.89
    wavfile.write(os.path.join(a.episode_dir, "narration.wav"), SR, (audio * 32767).astype(np.int16))
    json.dump(dict(total=round(total, 3), speed=round(speed, 3), scenes=tl),
              open(os.path.join(a.episode_dir, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print(f"narration {total:.1f}s at speed {speed:.3f}")


if __name__ == "__main__":
    main()
