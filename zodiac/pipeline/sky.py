#!/usr/bin/env python3
"""Sky of the day (Asia/Taipei) + a suggested zodiac ranking for 卡卡夫人占星館.

usage: python3 zodiac/pipeline/sky.py 2026-11-20 [--json out.json]

Prints the moon sign (and a sign change during the day, if any), moon phase, sun sign,
planet signs / retrogrades, tight aspects, and a suggested 12→1 ranking with 1–5 star
scores for love / work / money. The ranking is a starting point: the run may reorder
neighbours, but rank 1 should stay one the sky clearly favours.
"""
import json, math, sys, random
import ephem

SIGNS = ["牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女", "天秤", "天蠍", "射手", "摩羯", "水瓶", "雙魚"]
KEYS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
ELEM = ["火", "土", "風", "水"] * 3
BODIES = {"太陽": ephem.Sun, "月亮": ephem.Moon, "水星": ephem.Mercury, "金星": ephem.Venus,
          "火星": ephem.Mars, "木星": ephem.Jupiter, "土星": ephem.Saturn}
ASPECTS = [(0, "合相", 6), (60, "六分相", 4), (90, "四分相", 5), (120, "三分相", 5), (180, "對分相", 6)]
# sign-distance relation weights (0 = same sign)
REL = {0: 3.0, 1: 0.3, 2: 1.5, 3: -2.0, 4: 2.5, 5: -0.5, 6: -1.5, 7: -0.5, 8: 2.5, 9: -2.0, 10: 1.5, 11: 0.3}
REL_TXT = {0: "在本座", 2: "六分相", 3: "四分相", 4: "三分相", 6: "對沖", 8: "三分相", 9: "四分相", 10: "六分相"}

def lon(body_cls, d):
    b = body_cls(); b.compute(d, epoch=d)
    return math.degrees(ephem.Ecliptic(b, epoch=d).lon) % 360

def sign_of(l): return int(l // 30)

def main():
    D = sys.argv[1]
    y, m, dd = map(int, D.split("-"))
    # Taipei day: 06:00 and 23:59 local = 22:00 and 15:59 UTC
    t_morning = ephem.Date(f"{y}/{m}/{dd} 06:00") - 8 * ephem.hour
    t_night = ephem.Date(f"{y}/{m}/{dd} 23:59") - 8 * ephem.hour
    t_noon = ephem.Date(f"{y}/{m}/{dd} 12:00") - 8 * ephem.hour
    L = {n: lon(c, t_noon) for n, c in BODIES.items()}
    moon_m, moon_n = lon(ephem.Moon, t_morning), lon(ephem.Moon, t_night)
    moon = ephem.Moon(); moon.compute(t_noon)
    prev_new, next_new = ephem.previous_new_moon(t_noon), ephem.next_new_moon(t_noon)
    age = t_noon - prev_new
    phase_txt = ("新月" if age < 1.5 else "眉月" if age < 6.4 else "上弦月" if age < 8.9 else "盈凸月" if age < 13.8
                 else "滿月" if age < 15.8 else "虧凸月" if age < 21 else "下弦月" if age < 23.5 else "殘月" if age < 28 else "新月")
    retro = []
    for n in ["水星", "金星", "火星", "木星", "土星"]:
        a, b = lon(BODIES[n], t_noon - 1), lon(BODIES[n], t_noon + 1)
        if ((b - a + 540) % 360) - 180 < 0: retro.append(n)
    aspects = []
    names = list(L)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            diff = abs((L[names[i]] - L[names[j]] + 180) % 360 - 180)
            for ang, txt, orb in ASPECTS:
                if abs(diff - ang) <= (orb if "月亮" in (names[i], names[j]) else orb - 2):
                    aspects.append(f"{names[i]}{txt}{names[j]}（差 {abs(diff - ang):.1f}°）")
    ms = sign_of(L["月亮"])
    # ---- suggested ranking
    rng = random.Random(D)
    rows = []
    for s in range(12):
        def rel(body): return REL[(s - sign_of(L[body])) % 12]
        score = 2.0 * rel("月亮") + 0.8 * rel("太陽") + 0.5 * rel("金星") + 0.4 * rel("木星") + 0.3 * rel("火星") \
            - (0.6 if (s - sign_of(L["土星"])) % 12 in (0, 3, 6, 9) else 0) + rng.uniform(0, 1.6)
        love = 2.2 * rel("金星") + 1.5 * rel("月亮") + rng.uniform(0, 2)
        work = 1.8 * rel("太陽") + 1.2 * rel("火星") + 0.8 * rel("土星") + 0.8 * rel("月亮") + rng.uniform(0, 2)
        money = 1.8 * rel("木星") + 1.2 * rel("金星") + 0.8 * rel("月亮") + rng.uniform(0, 2)
        why = []
        d = (s - ms) % 12
        if d in REL_TXT: why.append(f"月亮{REL_TXT[d]}")
        d = (s - sign_of(L["太陽"])) % 12
        if d in (0,): why.append("太陽在本座")
        d = (s - sign_of(L["金星"])) % 12
        if d in (0, 4, 8): why.append("金星助愛情")
        d = (s - sign_of(L["木星"])) % 12
        if d in (0, 4, 8): why.append("木星助財運")
        rows.append(dict(sign=SIGNS[s] + "座", key=KEYS[s], score=round(score, 2), love_raw=love, work_raw=work,
                         money_raw=money, why="、".join(why) or "平穩"))
    rows.sort(key=lambda r: -r["score"])
    mean = {k: sum(x[k + "_raw"] for x in rows) / 12 for k in ("love", "work", "money")}
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        base = 5 - i * 3.2 / 11          # rank 1 ≈ 5, rank 12 ≈ 1.8
        for k in ("love", "work", "money"):
            v = base + (r[k + "_raw"] - mean[k]) * 0.25
            r[k] = int(min(5, max(1, round(v))))
            del r[k + "_raw"]
        if i == 0: r["love"], r["work"], r["money"] = max(r["love"], 4), max(r["work"], 4), max(r["money"], 4)
    out = dict(date=D, moon_sign=SIGNS[ms] + "座", moon_degree=round(L["月亮"] % 30, 1),
               moon_morning=SIGNS[sign_of(moon_m)] + "座", moon_night=SIGNS[sign_of(moon_n)] + "座",
               moon_phase=phase_txt, moon_illumination=round(moon.phase), sun_sign=SIGNS[sign_of(L["太陽"])] + "座",
               planets={n: f"{SIGNS[sign_of(v)]}座 {v % 30:.0f}°" for n, v in L.items()}, retrograde=retro,
               aspects=aspects, ranking_12_to_1=[r for r in reversed(rows)])
    print(f"{D} 月亮：{out['moon_morning']}→{out['moon_night']}（中午 {out['moon_sign']} {out['moon_degree']}°），"
          f"{phase_txt} {out['moon_illumination']}%｜太陽 {out['sun_sign']}｜逆行：{'、'.join(retro) or '無'}")
    print("行星：" + "，".join(f"{k} {v}" for k, v in out["planets"].items()))
    print("相位：" + ("；".join(aspects) or "無緊密相位"))
    print("建議排名（12→1）：")
    for r in out["ranking_12_to_1"]:
        print(f"  {r['rank']:>2} {r['sign']} 愛{r['love']} 事{r['work']} 財{r['money']}  {r['why']}")
    if "--json" in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
