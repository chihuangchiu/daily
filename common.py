# -*- coding: utf-8 -*-
"""每日ETF整理（台灣股市即時報）共用設定：讀 data.json、TTS 文字轉換、字幕切段。"""
import json, os, re

def load(work):
    return json.load(open(os.path.join(work, "data.json"), encoding="utf-8"))

DIG = dict(zip("0123456789", "零一二三四五六七八九"))

def tts_text(s):
    """送入 Gemini TTS 的文字：ETF 代號逐位念（0050→零零五零、00981A→零零九八一 A），百分比寫成「百分之…」。"""
    s = re.sub(r'(?<![\d.])(0\d{3,5})([A-Z]?)(?![\d.])',
               lambda m: "".join(DIG[c] for c in m.group(1)) + (" " + m.group(2) if m.group(2) else ""), s)
    s = re.sub(r'(\d+(?:\.\d+)?)%', r'百分之\1', s)
    s = s.replace("投等債", "投資等級債")
    return s

def subtitle_segments(s, maxlen=30):
    """字幕段：每段 30 字以內，在，。：、；處斷開，句號後一定斷開。"""
    parts = re.findall(r'[^，。：、；]+[，。：、；]?', s)
    segs, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= maxlen and not cur.endswith("。"):
            cur += p
        else:
            if cur: segs.append(cur)
            cur = p
    if cur: segs.append(cur)
    return segs

if __name__ == "__main__":
    import sys
    d = load(sys.argv[1])
    tot = 0
    for sc in d["scenes"]:
        tot += len(sc["text"])
        print(f'[{sc["key"]}] {len(sc["text"])}字')
        print("  TTS:", tts_text(sc["text"]))
        for g in subtitle_segments(sc["text"]):
            flag = "  <-- 超過30字" if len(g) > 30 else ""
            print("   ", len(g), g, flag)
    print("總字數", tot, "預估秒數", round(tot / 5.6, 1))
