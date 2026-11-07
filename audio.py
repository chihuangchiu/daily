# -*- coding: utf-8 -*-
"""拼接 WORK/tts/<key>.wav（Gemini 24 kHz 單聲道），對齊字幕，輸出 timeline.json、narration_raw.wav、narration.wav（48 kHz）。
用法：python3 audio.py WORK"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, tts_text, subtitle_segments

WORK = sys.argv[1]
D = load(WORK)
LEAD, GAP, TAIL = 0.8, 0.5, 2.0

def read(p):
    with wave.open(p) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    return sr, x

def trim(x, sr, th=0.01):
    idx = np.where(np.abs(x) > th)[0]
    a = max(0, idx[0] - int(0.03 * sr)); b = min(len(x), idx[-1] + int(0.08 * sr))
    return x[a:b]

def silences(x, sr):
    win = int(0.01 * sr); n = len(x) // win
    rms = np.sqrt(np.mean(x[:n * win].reshape(n, win) ** 2, axis=1))
    th = max(0.006, 0.04 * np.percentile(rms, 95))
    sil = rms < th; out, i = [], 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            if (j - i) * 0.01 >= 0.05: out.append((i * 0.01, j * 0.01))
            i = j
        else: i += 1
    return out

SR = None; timeline = []; chunks = []; t = LEAD
for k, sc in enumerate(D["scenes"]):
    sr, x = read(os.path.join(WORK, "tts", sc["key"] + ".wav"))
    if SR is None:
        SR = sr; chunks.append(np.zeros(int(LEAD * SR), np.float32))
    assert sr == SR, "各場景取樣率不一致"
    x = trim(x, SR); dur = len(x) / SR
    segs = subtitle_segments(sc["text"])
    w = np.array([len(tts_text(s)) for s in segs], float)
    est = np.cumsum(w)[:-1] / w.sum() * dur
    sil = silences(x, SR); bounds = []
    for e in est:
        c = [(abs((a + b) / 2 - e) - 2 * (b - a), a, b) for a, b in sil if abs((a + b) / 2 - e) <= 0.8]
        if c: _, a, b = min(c); bounds.append((a, b))
        else: bounds.append((e, e))
    starts = [0.0] + [b for _, b in bounds]; ends = [a for a, _ in bounds] + [dur]
    timeline.append({"key": sc["key"], "start": t, "end": t + dur,
                     "segs": [{"text": s, "start": t + s0, "end": t + e0} for s, s0, e0 in zip(segs, starts, ends)]})
    chunks.append(x); t += dur
    if k < len(D["scenes"]) - 1:
        chunks.append(np.zeros(int(GAP * SR), np.float32)); t += GAP
chunks.append(np.zeros(int(TAIL * SR), np.float32)); t += TAIL
y = np.concatenate(chunks)
raw = os.path.join(WORK, "narration_raw.wav")
with wave.open(raw, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
json.dump({"total": len(y) / SR, "scenes": timeline}, open(os.path.join(WORK, "timeline.json"), "w"), ensure_ascii=False, indent=1)
proc = os.path.join(WORK, "narration_proc.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                "highpass=f=70,equalizer=f=3200:t=q:w=0.9:g=1.5,acompressor=threshold=-21dB:ratio=2:attack=6:release=140:makeup=1.5,aresample=48000",
                "-ar", "48000", "-ac", "1", proc], check=True)
sr2, z = read(proc); z = z / np.abs(z).max() * 0.89
with wave.open(os.path.join(WORK, "narration.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr2)
    w.writeframes((z * 32767).astype(np.int16).tobytes())
print("旁白總長", round(len(y) / SR, 2), "秒")
for sc in timeline:
    print(sc["key"], round(sc["start"], 2), round(sc["end"], 2))
    for s in sc["segs"]: print("   ", round(s["start"], 2), round(s["end"], 2), s["text"])
