# -*- coding: utf-8 -*-
"""每個場景抽一格（動畫結束後）拼成 WORK/sheet.png，方便用 Read 目視檢查。用法：python3 sheet.py WORK"""
import json, os, subprocess, sys
from PIL import Image
WORK = sys.argv[1]; K = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(WORK, "timeline.json"), encoding="utf-8"))
ts = [f"{min(sc['end'] - 0.3, sc['start'] + 2.2):.1f}" for sc in tl["scenes"]]
subprocess.run(["python3", os.path.join(K, "render.py"), WORK, "still"] + ts, check=True)
ims = [Image.open(os.path.join(WORK, f"still_{t}.png")) for t in ts]
for part in range(0, len(ims), 4):
    grp = ims[part:part + 4]
    s = Image.new("RGB", (730 * len(grp), 1280), (255, 255, 255))
    for i, im in enumerate(grp): s.paste(im, (i * 730, 0))
    s.save(os.path.join(WORK, f"sheet{part // 4 + 1}.png"))
print("stills:", ts)
