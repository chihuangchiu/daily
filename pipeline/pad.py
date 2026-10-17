"""Quiet ambient pad (Am-F-C-G) for background. Usage: python3 pad.py SECONDS OUT.wav"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
dur, out_path = float(sys.argv[1]) + 1.0, sys.argv[2]
n = int(SR * dur)
t = np.arange(n) / SR


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


chords = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62]]
seg = 8.0
out = np.zeros(n, np.float32)
rng = np.random.default_rng(1)
k, start = 0, -1.5
while start < dur:
    s0, s1 = max(0, int(start * SR)), min(n, int((start + seg + 3) * SR))
    if s1 > s0:
        tt = np.arange(s1 - s0) / SR
        env = np.sin(np.pi * np.clip(tt / ((s1 - s0) / SR), 0, 1)) ** 1.5
        sig = np.zeros(s1 - s0, np.float32)
        for m in chords[k % 4]:
            f = hz(m)
            for det in (-0.0018, 0.0018):
                ph = rng.uniform(0, 2 * np.pi)
                sig += np.sin(2 * np.pi * f * (1 + det) * tt + ph) + 0.25 * np.sin(4 * np.pi * f * (1 + det) * tt + ph)
        out[s0:s1] += sig * env / 5
    start += seg
    k += 1
b, a = signal.butter(2, 1400 / (SR / 2))
out = signal.lfilter(b, a, out)
irt = np.arange(int(2.2 * SR)) / SR
ir = rng.normal(0, 1, len(irt)) * np.exp(-irt * 2.6)
ir /= np.sqrt((ir ** 2).sum())
mix = 0.55 * out + 0.45 * signal.fftconvolve(out, ir)[:n]
mix *= 1 + 0.08 * np.sin(2 * np.pi * 0.11 * t)
fade = np.ones(n)
fade[:3 * SR] = np.linspace(0, 1, 3 * SR)
fade[-4 * SR:] = np.linspace(1, 0, 4 * SR)
mix *= fade
mix = mix / np.abs(mix).max() * 0.9
wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))
