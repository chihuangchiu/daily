# -*- coding: utf-8 -*-
"""語音辨識回測：逐場景、逐字幕段辨識 WORK/narration_raw.wav，與送入 TTS 的文字比對。
需先下載 SenseVoice 模型到 MODEL_DIR（見 README）。用法：python3 asr.py WORK [MODEL_DIR]"""
import json, os, sys, wave
import numpy as np, sherpa_onnx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import tts_text
WORK = sys.argv[1]
d = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/models/sv/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/"
rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=os.path.join(d, "model.int8.onnx"), tokens=os.path.join(d, "tokens.txt"), language="zh", use_itn=False)
w = wave.open(os.path.join(WORK, "narration_raw.wav")); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
tl = json.load(open(os.path.join(WORK, "timeline.json"), encoding="utf-8"))
def rec_text(a, b):
    st = rec.create_stream(); st.accept_waveform(sr, x[int(a * sr):int(b * sr)]); rec.decode_stream(st); return st.result.text
out = []
for sc in tl["scenes"]:
    out.append(f"== {sc['key']} | {rec_text(sc['start'], sc['end'])}")
    for s in sc["segs"]:
        out.append(f"   原文 {tts_text(s['text'])}")
        out.append(f"   辨識 {rec_text(s['start'], s['end'])}")
open(os.path.join(WORK, "asr_report.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
