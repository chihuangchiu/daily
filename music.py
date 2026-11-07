# -*- coding: utf-8 -*-
# 原創配樂（numpy 即時合成）＋依旁白時間軸 ducking，混音輸出 WORK/mix_raw.wav。用法：python3 music.py WORK
import json, wave, numpy as np
SR = 48000
import sys, os
WORK = sys.argv[1]
tl = json.load(open(os.path.join(WORK, "timeline.json")))
T = tl["total"]
N = int(T * SR)
t = np.arange(N) / SR
bpm = 92; beat = 60 / bpm; bar = 4 * beat

def midi(m): return 440 * 2 ** ((m - 69) / 12)
# 和弦進行（Dmaj7 - Bm7 - Gmaj7 - A6），偏冷靜的財經節目底
prog = [[50, 57, 61, 64, 66], [47, 54, 57, 61, 62], [43, 50, 54, 57, 59], [45, 52, 57, 61, 64]]
pad = np.zeros(N); bass = np.zeros(N); arp = np.zeros(N)
nb = int(np.ceil(T / bar)) + 1
for b in range(nb):
    ch = prog[b % 4]; s0 = int(b * bar * SR); s1 = min(N, int((b + 1) * bar * SR))
    if s0 >= N: break
    tt = t[s0:s1] - b * bar
    env = np.minimum(1, tt / 0.6) * np.minimum(1, (bar - tt) / 0.6)
    for m in ch[1:]:
        f = midi(m + 12)
        pad[s0:s1] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt + 0.5)) * 0.12
    fb = midi(ch[0] - 12 + 12)
    for k in range(4):
        a = int((b * bar + k * beat) * SR); e = min(N, a + int(beat * SR))
        if a >= N: break
        u = t[a:e] - (b * bar + k * beat)
        bass[a:e] += np.sin(2 * np.pi * fb * u) * np.exp(-u * 3.0) * 0.35
    notes = ch[1:] + ch[2:4][::-1]
    for k in range(8):
        a = int((b * bar + k * beat / 2) * SR); e = min(N, a + int(beat * SR))
        if a >= N: break
        u = t[a:e] - (b * bar + k * beat / 2)
        f = midi(notes[k % len(notes)] + 24)
        arp[a:e] += np.sin(2 * np.pi * f * u) * np.exp(-u * 6) * 0.10
music = pad + bass + arp
music = np.convolve(music, np.ones(24) / 24, mode="same")  # 柔化高頻
music /= np.abs(music).max()
# fade in/out
fi = int(1.5 * SR); fo = int(2.5 * SR)
music[:fi] *= np.linspace(0, 1, fi); music[-fo:] *= np.linspace(1, 0, fo)

# ducking：旁白中 0.075、無旁白 0.26；間隔 < 0.6 秒不回升
spans = [(sc["start"], sc["end"]) for sc in tl["scenes"]]
merged = []
for a, b in spans:
    if merged and a - merged[-1][1] < 0.6: merged[-1] = (merged[-1][0], b)
    else: merged.append((a, b))
g = np.full(N, 0.26)
for a, b in merged:
    g[int(max(0, a - 0.15) * SR):int(b * SR)] = 0.075
k = int(0.2 * SR)
g = np.convolve(g, np.ones(k) / k, mode="same")
music *= g

w = wave.open(os.path.join(WORK, "narration.wav")); v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
v = np.pad(v, (0, max(0, N - len(v))))[:N]
mix = v + music
mix /= max(1.0, np.abs(mix).max() / 0.95)
st = np.stack([mix, mix], 1)
o = wave.open(os.path.join(WORK, "mix_raw.wav"), "w"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
o.writeframes((st * 32767).astype(np.int16).tobytes()); o.close()
print("ok", N / SR)
