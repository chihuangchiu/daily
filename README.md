# daily — 今天，誰改變了世界

Automated "歷史上的今天" vertical videos (720x1280, ~4 min, narrated, subtitled) for the Facebook page
「今天，誰改變了世界」. A scheduled Claude run follows `RUNBOOK.md` each morning.

- `pipeline/` — narration (offline Mandarin TTS, ONNX), template renderer, build script
- `episodes/YYYY-MM-DD/` — `episode.json` (script + scene data) and `post.txt` (Facebook text)
- `TEMPLATES.md` — episode.json schema
- `covered.md` — subjects already used

Build locally:
```
pip install -r requirements.txt
pipeline/build.sh episodes/2026-10-17 check   # narration + contact sheets
pipeline/build.sh episodes/2026-10-17 video   # final mp4
```
Requires ffmpeg and Noto CJK fonts.

Voice: fastspeech2 + mb-melgan from [zhtts](https://github.com/jackiexiao/zhtts) (MIT), converted to ONNX.
The model was trained on the Databaker (標貝) Mandarin corpus, which is released for non-commercial use.
