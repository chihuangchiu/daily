# -*- coding: utf-8 -*-
"""近一個月含息報酬排行。輸入 JSON：{"rows": {"代號": ["名稱", 起點收盤, 終點收盤, 期間現金股利合計, 規模億元], ...}}
報酬＝(終點收盤＋期間股利)÷起點收盤－1。用法：python3 perf.py perf_input.json"""
import json, sys
U = json.load(open(sys.argv[1], encoding="utf-8"))["rows"]
rows = sorted([(c, v[0], round(((v[2] + v[3]) / v[1] - 1) * 100, 2)) for c, v in U.items()], key=lambda r: -r[2])
for i, r in enumerate(rows, 1): print(f"{i:3d} {r[0]:7s} {r[1]:12s} {r[2]:+7.2f}%")
print(json.dumps({"top": [list(r) for r in rows[:5]], "bottom": [list(r) for r in rows[::-1][:5]]}, ensure_ascii=False))
