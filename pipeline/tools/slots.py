#!/usr/bin/env python3
"""Publish slots per channel (Nathan 2026-11-03): each language posts on the morning of D in its audience's time zone.
usage: python3 pipeline/tools/slots.py 2026-11-06 [2026-11-07 ...]
Prints, for each D and channel, the UTC publish time to pass to Postiz (handles daylight saving time).
A post on channel C belongs to day D when its publishDate is in [D-1 15:00Z, D 18:00Z)."""
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo
UTC = ZoneInfo("UTC")
CH = [  # (label, integrationId(s), tz, local hour)
    ("zh FB+YT", "cmvbzqyvs0002s67fq0dzr53e,cmvc7njup0001s673xhqhp5s8", "Asia/Taipei", 7),
    ("ja YT+FB", "cmvir44qg000zs67kevg8s72x,cmw7y6kw8004qs67z17nk77rm", "Asia/Tokyo", 7),
    ("de YT+FB", "cmvir7imd0011s67ky3vmkijj,cmw9cakfg0089s67zdx0fzndb", "Europe/Berlin", 7),
    ("pt YT+FB", "cmviqybpp000ws67knh5z6wzo,cmw9c60vf0084s67z864vjqtb", "America/Sao_Paulo", 8),
    ("en YT+FB", "cmvibixcp000ms67kkplrbxb1,cmw7yoef70051s67z38jq1cr5", "America/New_York", 8),
    ("es YT+FB", "cmvic8oq3000os67kdsemvo3t,cmw7zc3i40056s67z3tox2dbw", "America/Mexico_City", 8),
]
for a in sys.argv[1:]:
    d = date.fromisoformat(a)
    for lab, ids, tz, h in CH:
        t = datetime(d.year, d.month, d.day, h, tzinfo=ZoneInfo(tz)).astimezone(UTC)
        tp = t.astimezone(ZoneInfo("Asia/Taipei"))
        print(f"{a}  {lab:9s} {t:%Y-%m-%dT%H:%M:00Z}  (local {h:02d}:00 {tz}; Taipei {tp:%m-%d %H:%M})  {ids}")
