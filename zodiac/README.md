# zodiac — 卡卡夫人占星館「今日星座運勢」

Daily vertical horoscope video (1080x1920, ~88 s, ~16 MB) for the Facebook page 卡卡夫人占星館,
built by a scheduled Claude run at 04:49 Taipei and published via Postiz at 06:00. The run follows `ROUTINE.md`.

- `pipeline/sky.py D` — moon/sun/planets for the Taipei day + a suggested ranking (needs `ephem`)
- `pipeline/build.py EP plan|video` — TTS plan, then the full render (opening lip-sync alignment, subtitles,
  ranking cards, 開運推薦 cards, outro, music, two-pass encode)
- `assets/` — stage background, 12 zodiac emblems, 卡卡夫人 photo (fallback opening), reusable outro clip
- `episodes/D/` — `episode.json`, `post.txt`, `sky.json` (TTS, clips, images and renders are not committed)

Host: 卡卡夫人, an AI-generated virtual presenter (Calywood portrait asset `asset-20261119101855-dz79b`, voice Gemini TTS Sulafat).
