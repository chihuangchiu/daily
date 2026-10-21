# episode.json schema

Full working example (3-minute format): `episodes/2026-10-17-short/episode.json`.

```json
{
  "date": "2026-10-17",
  "mmdd": "10.17",
  "person": "蔣渭水",
  "event": "台灣文化協會成立",
  "title": "105年前的今天，一位醫生替整個台灣看了病｜蔣渭水",
  "footer": "蔣渭水 1890–1931　｜　台灣文化協會成立 105 週年",
  "scenes": [ { "template": "...", "chapter": "第一章　...", "lines": [...], "data": {...}, "effects": [...] } ]
}
```

## lines
Each scene has `lines`: the narration, one subtitle per line.
- `"text"` when subtitle and speech are identical, or `["subtitle", "spoken"]`.
- Spoken text: Chinese numerals only, no Latin letters or digits (narrate.py refuses them), no quote marks.
  e.g. `["1921年10月17日，", "一九二一年十月十七日，"]`.
- Keep subtitles short (about 8–18 characters). Long lines wrap to two rows automatically.
- Commas inside a line become short pauses.

## timing references
Every visual element has `at` = index of the line (0-based, within the scene) when it appears,
optional `delay` (seconds after that line starts), optional `until` = line index when it disappears.

## templates

### title (opening scene, no chapter)
`kicker`, `big` (defaults to mmdd), `sub` + `sub_at`,
`middle`: list of `{type:"text", text, at, until}` or `{type:"pills", items:[...], at, until}` shown at y≈700,
`name`, `name_years`, `seal` (2–4 chars red seal), `name_at`,
`image` (file in the episode folder, e.g. `"opening.png"`): shown full-screen behind the title, darkened, with all
title text switched to light colours; `image_label` is empty by default (no on-screen AI label since 2026-10-20).
`image_shift` (0–0.4): moves the picture (and the clip) down by that fraction of the height so the face sits
below the title (RUNBOOK 4b step 6).
`video` (e.g. `"opening.mp4"`, needs `image` too) + `video_secs` (default 3): a clip played full-screen over the
still from t=0, cropped to 720x1280 with the same sepia/darkening and label, then faded to the still (RUNBOOK 4d).

### timeline
`bg_char` (one faint big glyph, optional), `nodes`: up to 5 × `{big, small, at, delay, color}`.

### document (a historical document / record card)
`title`, `subtitle`, `at`, `rows`: `{label, value, at, delay, red}`,
`list`: `{label, at, tag, tag_at, items:[{text, at, delay}]}`, `footer`: `{label, value, at}`.
Max about 4 rows + 5 list items.

### tiles (up to 6 activities / achievements)
`header`, `tiles`: `{text, at, delay}`, `arrow`: `{from, to, at, to_at}` (optional).

### stack (the general-purpose scene)
`bg_char` optional; `phases`: list of `{at, until, items:[...], seal, stamp, bg}`.
Items in a phase are stacked vertically and centred; a phase disappears at `until`.
Item types:
- text: `{text, style, size, color, at, delay}`; style = huge | big | title | head | mid | body | small | kicker; color = ink | red | muted
- `{type:"rule", width, color}`
- `{type:"pill", text}` red label
- `{type:"pills", items:[...]}`
- `{type:"pair", left, right, right_at}` two labels on one row
- `{type:"cards", cards:[{head, sub, color, at}]}` two side-by-side cards
- `{type:"vtext", size, columns:[{text, color, at, delay}]}` vertical columns, read right→left (slogans, couplets)
- `{type:"sign", top, main, small}` green road sign
- `{type:"film", main, sub}` film-strip frame
- `{type:"barred", small, big}` text behind prison bars
- `{type:"checks", items:[...]}` list with red check marks
- `{type:"image", src, height, width, caption, label}` framed picture (default 560x420, no label)
Phase extras: `seal: {chars, grid:[2,2], size, at, x, y, angle}`, `stamp: {top, main, at, y}` (diagonal red stamp), `bg: {char, color}` faint glyph.

### end
`name`, `years`, `seal`, `kicker` (defaults to 歷史上的今天 + mmdd).

## effects (per scene)
`{type:"rain", from: lineIndex, to: lineIndex}`.

## layout limits
Visual area is y=195–872 (720 wide); subtitles sit at y≈948. `render.py` prints `WARNING:` for
text too wide, phases too tall, or overlong subtitles. Fix every warning and look at
`check/sheet_*.png` before building the video.
