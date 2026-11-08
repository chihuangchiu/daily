# Daily run: 「今天，誰改變了世界」

One vertical video of just under 3 minutes (so YouTube treats it as a Short) per day, about a person or event tied to
that day's date, posted at 06:00 Taiwan time to both the Facebook page 「今天，誰改變了世界」 and the YouTube channel 「今天 誰改變了世界」.

Rolling buffer (Nathan 2026-10-20): the run starts every evening (~19:50 Taiwan time) and makes sure the next
WINDOW days are already scheduled in Postiz. WINDOW = 3 for now (tomorrow, the day after, and the day after that);
Nathan plans to raise it to 7 once this is stable — only this number changes. Each video is made for its own
target date D (the publish date), never for the run date.

Fixed facts
- Repo: chihuangchiu/daily (public). Video files are never committed to main; they pass briefly through the `media` branch (step 8).
- Postiz integrations:
  - Facebook: id `cmvbzqyvs0002s67fq0dzr53e`, name 「今天，誰改變了世界」.
  - YouTube: id `cmvc7njup0001s673xhqhp5s8`, name 「今天 誰改變了世界」.
  - YouTube (English): id `cmvibixcp000ms67kkplrbxb1`, name "Who Changed the World Today" — see section E
    (Nathan 2026-10-22). Publishes at 06:00 Taipei on D, like every channel (Nathan 2026-10-22).
  - YouTube (Spanish): id `cmvic8oq3000os67kdsemvo3t`, name "¿Quién cambió el mundo hoy?" — same person as the
    English video of D, 06:00 Taipei on D (details in the scheduled task prompt until a section is added here).
- Timezone: Asia/Taipei. Get the run date from the current-time tool. In every step below, D = the target
  (publish) date of the video being made: its month/day drives the topic, the "N年前的今天" years, the folder
  episodes/D, the media file name and the publish time.

## 0a. Publish times per language (Nathan 2026-11-03) — overrides every "06:00 Taipei" / "(D−1)T22:00:00Z" below
Each channel publishes on the MORNING OF D in its audience's time zone, so "today, <date>" is true where it is watched:
zh FB+YT 07:00 Asia/Taipei; ja 07:00 Asia/Tokyo; de 07:00 Europe/Berlin; pt 08:00 America/Sao_Paulo;
en 08:00 America/New_York; es 08:00 America/Mexico_City. Get the exact UTC times (daylight saving handled) with
`python3 pipeline/tools/slots.py D1 D2 D3` (e.g. for 2026-11-06: zh 11-05T23:00Z, ja 11-05T22:00Z, de 11-06T06:00Z,
pt 11-06T11:00Z, en 11-06T13:00Z, es 11-06T14:00Z) and pass that time as `date` to integrationSchedulePostTool.
- Planning (step 0): list posts from (first D − 1 day)T15:00:00Z to (last D)T18:00:00Z. A post on a channel belongs to
  day D when its publishDate is in [D−1 15:00Z, D 18:00Z). Posts made before this change at the old time
  ((D−1)T22:00Z, i.e. 11/04 and 11/05 2026) still count as covering D — do not make or move those.
- If a slot is already in the past when scheduling, use now + 10 min.
- The report lists each channel with its own local time (and the Taipei time).

## 0c. Facebook pages for ja, en, es (Nathan 2026-11-08)
The Japanese video also goes to the Facebook page 「今日、世界を変えたのは誰」, integrationId `cmw7y6kw8004qs67z17nk77rm`, at the
same time as the Japanese YouTube post (Tokyo 07:00; slots.py lists it as "ja YT+FB"). So there are now 8 channels per day.
- Planning: the ja FB channel counts as its own channel. If the ja YouTube post exists but the ja FB post does not, do NOT make a new
  video: schedule only the FB post, reusing the ja YouTube post's video (find it in Postiz mediaListTool: the mp4 uploaded in that run,
  check the header frame shows 「今日、世界を変えたのは誰」 and the MM.DD) and `episodes/D-ja/post.txt`.
- Upload the ja video once and schedule both posts (YouTube + Facebook) in one integrationSchedulePostTool call, same date.
- Facebook content, like the Chinese FB post: first line the plain title (post.txt without 「タイトル：」), a blank line, the article,
  hashtag line WITHOUT #Shorts; every line wrapped in <p>…</p>; settings post_type=post, title=<title>.
- Report it as a separate channel (日 FB) with its preview link.
- 2026-11-08: FB posts for 11/09 (Lamarr), 11/10 (Schiller) and 11/11 (Brahe) were added from the already uploaded ja videos.
- **English Facebook page (Nathan 2026-11-08, same rules):** 「Who Changed the World Today?」, integrationId `cmw7yoef70051s67z38jq1cr5`,
  at the same time as the English YouTube post (New York 08:00; slots.py "en YT+FB"). Upload the en video once and schedule YouTube + FB
  in one call. FB content: plain title line (post.txt without "Title:"), blank line, article, hashtags WITHOUT #Shorts; settings
  post_type=post, title=<title>. If only the en YouTube post exists for D, add just the FB post with that video. With both FB pages there
  are now 9 channels per day. FB posts for 11/09–11/11 were added on 2026-11-08 from the already uploaded en videos.
- **Spanish Facebook page (Nathan 2026-11-08, same rules):** 「¿Quién cambió el mundo hoy?」, integrationId `cmw7zc3i40056s67z3tox2dbw`,
  at the same time as the Spanish YouTube post (Mexico City 08:00; slots.py "es YT+FB"); title line from post.txt without "Título:".
  Now 10 channels per day. FB posts for 11/09–11/11 were added on 2026-11-08 from the already uploaded es videos.
- Generic rule for any language with a FB page: one upload, one integrationSchedulePostTool call with YouTube + FB, FB content = plain
  title line + blank line + article + hashtags without #Shorts. slots.py lists every channel id per language.

## 0b. Length, hook and on-screen text (Nathan 2026-10-22) — overrides the older numbers below
- **Length: about 120 s** (TARGET=120 is now build.sh's default). Final video 112–128 s; speed in check 0.92–1.10.
  Narration size: Chinese ~460–500 characters (~40–45 lines, 7 scenes: hook/title → 4 chapters → legacy + question →
  end); English ~300–320 words; Spanish/Portuguese ~280–310; German ~270–290; Japanese ~600 characters.
  Keep the strongest 4 chapters; drop side facts rather than speeding up.
- **Hook in the first 2 seconds.** Line 0 of the title scene is a spoken hook: the single most surprising or emotional
  fact, said in under ~2 s (Chinese ≤ 16 characters, English ≤ 10 words), e.g. 「他一個人，讓全歐洲為鋼琴瘋狂。」 /
  "He made all of Europe go wild for a piano." The date line comes second and SPEAKS THE CHANNEL NAME, not
  「歷史上的今天」/"On this day" (Nathan 2026-10-26): zh 「今天，誰改變了世界？10月28日。」; en "Who changed the world
  today? October 28."; es "¿Quién cambió el mundo hoy? 28 de octubre."; pt "Quem mudou o mundo hoje? 28 de outubro.";
  ja 「今日、世界を変えたのは誰？10月28日。」; de "Wer hat heute die Welt verändert? Der 28. Oktober." (The on-screen
  kicker/date card stays as it is.) In the title `data` set `"hook": "<2 short rows split by \n>"` (same idea, ≤ 2 rows of ≤ 10 CJK
  characters or ≤ 22 Latin characters each). render.py shows the hook big over the clip from frame 0 (frame 0 is the
  Shorts thumbnail) and brings in the kicker + MM.DD date only when line 1 starts (`hook_until`, default 1).
  The title scene then needs only the date, `sub` (years) and `name` — drop the `middle` texts/pills.
  No subtitle under the spoken hook (Nathan 2026-10-28): the big hook text is already on screen, so render.py shows
  no subtitle for the hook line(s) and the clip stays clean; subtitles start with line 1. (`"hook_subtitle": true`
  in the title data brings it back.) Check sheet_00: frame 0 = hook text over the clip, no subtitle box.
- **On-screen text: only what earns its place.** Per phase at most 2 text items (one big keyword or number + at most
  one short line); never repeat the subtitle sentence on screen; a phase disappears as soon as its line has passed;
  chapter scenes may be just one big number or word. No footer line (render.py no longer draws it: the Shorts UI
  covers the bottom of the frame). Subtitles are narrower now to stay clear of the Shorts buttons: Western-language
  lines ≤ ~55 characters, CJK pieces between commas ≤ 14 characters. On-screen phase texts are one row only
  (`\n` works in `hook` only).
- **Question phase shows the WHOLE question (Nathan 2026-11-07).** The 11/07 video showed only the tail (「你會怎麼做？」) in red while
  the narration asked the full question, so it looked like a different question. From now on the question phase (kicker
  「她留下的問題」/"Her question"/…) shows the full question in exactly the same words as the spoken/subtitle line, and the subtitle
  stays on as usual (this one phase is an exception to "never repeat the subtitle on screen" and to "max 2 text items"). Split it into
  two text items (two rows) at the comma, same size: CJK `size` 40 (≤ ~12 characters per row), Latin `size` ~34 (≤ ~30 characters per
  row; shorten the wording of the spoken line if needed), e.g.
  `{"text":"如果別人只看見你的外表，","style":"head","size":40,"color":"red","at":4}, {"text":"你會怎麼證明自己？",…}`.
  Show the rows from the line where the question itself is spoken. Check it on the sheet: both rows fully visible, same words as the subtitle.
- **End scene names the channel too (Nathan 2026-10-26).** Replace 「歷史上的今天，10月28日，我們記得某某。」 with two
  lines that form one sentence (first ends with a comma, so Gemini gets one longer chunk): zh 「這裡是「今天，誰改變了
  世界」，」+「10月28日，我們記得沙克。」 (spoken without the 「」); en "This is Who Changed the World Today," + "and on
  October 28, we remember Jonas Salk."; es "Esto es Quién cambió el mundo hoy," + "y este 28 de octubre, recordamos a
  Jonas Salk."; pt "Aqui é Quem mudou o mundo hoje," + "e neste 28 de
  outubro, lembramos de Jonas Salk."; ja 「こちらは『今日、世界を変えたのは誰』、」+「10月28日、ジョナス・ソークを思い
  出します。」; de "Das ist Wer hat heute die Welt
  verändert," + "und am 28. Oktober erinnern wir an Jonas Salk." Then the subscribe/share/see-you-tomorrow line.
- **Subscribe, share & see-you-tomorrow line (Nathan 2026-10-25, "明天見" added the same evening).** The end scene gets
  one more line after "we remember …", spoken and shown as the subtitle: zh 「喜歡這個故事，記得追蹤訂閱、分享給朋友，我們明天見！」
  (the Chinese video also goes to Facebook, hence 追蹤訂閱); en "If you enjoyed this story, subscribe and share. See you
  tomorrow!"; es "Si te gustó, suscríbete y compártela. ¡Nos vemos mañana!"; pt "Se gostou, inscreva-se e compartilhe.
  Até amanhã!"; ja 「気に入ったら、チャンネル登録と共有を。また明日！」; de "Wenn's dir gefällt, abonniere und teile. Bis
  morgen!" It costs ~3.5–4 s and must fit the 112–128 s rule: cut a side sentence first, never speed up; drop the line
  only if it truly does not fit (say so in the report). No extra on-screen text or like/bell icons.
- **sherpa-onnx < 2** (requirements.txt): 2.0.0 skips almost every English word as OOV with the Kokoro lexicon
  (log full of "OOV word skipped", English narration half as long). Found 2026-10-24.
- **Narration voice: Gemini TTS (Nathan 2026-10-25), all six languages.** Voice Kore, model gemini-2.5-flash-tts,
  wav. The MCP tool can only be called by the agent, so:
  1. `python3 pipeline/narrate.py EP --gemini-plan` → `EP/tts/plan.json`: chunk `c00_hook` (title line 0, the hook)
     and then one chunk per sentence (lines are joined until a line ends with 。！？.!?). Each chunk has id, text,
     style; plan has language, voice, model.
  2. For every chunk call `generate_speech` (text, style, language, voice, model, format "wav") and
     `curl -sSf -o EP/tts/<id>.wav "<url>"` (the URL is on the Postiz host and downloads fine from here).
     Calls are independent: send several in one turn.
  3. `python3 pipeline/narrate.py EP --gemini` → cuts multi-line chunks at the pauses, shortens long pauses,
     writes narration.wav + timeline.json (no tempo change), prints the length. Then render sheets as usual
     (`python3 pipeline/render.py EP sheet` after `rm -rf EP/check`), and `build.sh video` (it reuses timeline.json).
  - Hook style (Nathan 2026-10-25 evening, replaces "dramatic and slower"): the first line uses the SAME brisk pace as
    the rest — never slower — with a genuinely amazed, astonished tone (styles in narrate.py GEMINI_STYLE). Keep hook
    styles short and descriptive: long instruction-like styles ("Primera frase: …") were read aloud by Gemini in
    es/pt/de. Never speed the audio up afterwards.
  - Gemini reads more slowly than the old engines and there is no speed knob: the script length decides the
    video length. 2026-10-25 test: the 480-character 10/27 Chinese script gave ~138 s, so Chinese needs about
    410–430 spoken characters for 112–128 s (hook alone ~6 s). For other languages measure on the first run, aim
    for 112–128 s by cutting or adding sentences, and note the working size here.
  - After editing lines, run --gemini-plan again and synthesize only the chunks whose text changed (keep the
    other wav files; a chunk id is c<scene+1>_<first line>, so check the text, not only the id).
  - Spoken field: write the real words (Chinese numerals for numbers are fine). Do not use homophone tricks meant
    for the old engine (e.g. 音月廳); Gemini reads normal text correctly. Check every video with Whisper as before.
  - Fallback: if the Gemini TTS tool is not connected after the usual retries, or keeps failing, use the local
    engine (`build.sh check` path, `--target 120`) for that video and say so in the report.
  - Cost: about US$0.03 per 2-minute video (25 audio tokens/s at $10 per 1M).
- **Gemini glitches (found 2026-10-25, Salk run): check EVERY chunk before building.** Gemini TTS sometimes
  (a) says a sentence twice, (b) reads the style text aloud before the sentence, or (c) adds words ("Compártela con
  tus amigos"). It happens mostly with SHORT single-sentence chunks (≤ ~8 words / ≤ ~12 CJK characters). Whisper on the
  whole chunk often hides a repeat, so: `python3 pipeline/tools/gemini_check.py EP <lang>` (needs
  /home/claude/models/sherpa-onnx-whisper-base; prints seconds/char, ASR text vs subtitle; `<<<` = text mismatch,
  `SLOW` = suspiciously long), then `pipeline/tools/halves.sh <lang> EP/tts/<id>.wav …` for every SLOW chunk (a
  repeat shows the same sentence in both halves). Re-synthesize bad chunks (2026-10-27 Paganini run: when a retry with the full body style glitches again, a retry with a SHORT style such as "Warm, brisk documentary narrator." / 「温かいドキュメンタリーのナレーター、速めのテンポ。」 fixed it every time; also check the byte size returned: ~48,000 bytes per second, so a chunk twice its expected size is a repeat); if a chunk fails twice, join it to its
  neighbour (end the line with a comma instead of a full stop) so the chunk gets longer. Write scripts with few
  very short stand-alone sentences. The 2026-10-28 zh video was scheduled before this was found (two repeated
  sentences); the fixed v2 went to Postiz as drafts for Nathan to swap.
- **Measured script sizes for 112–128 s (Gemini Kore, 2026-10-25):** zh ~420 spoken characters → 119.5 s;
  en ~237 words → 115.7 s (≈ 2 words/s); es ~272 words → 124 s; pt ~283 words → 126.7 s; de ~216 words (long
  compounds, years as words) → 120.5 s; ja ~600 characters → 112.1 s (aim ~630). Japanese subtitles: a line is split
  into at most 2 rows at the 、 nearest the middle, each row ≤ ~15 characters (600 px), so keep subtitle lines ≤ ~28
  characters with a 、 near the middle (subtitle-only shortening is fine).
- **2026-10-29 Pulitzer run (Gemini Kore):** zh 434 spoken chars → 121.1 s; en 276 words/1638 chars → 126.3 s;
  es 1627 chars → 127.6 s; pt 1529 chars → 124.2 s; ja 720 chars → 122.7 s; de 1576 chars → 125.1 s (chars = spoken
  field incl. spaces/punctuation, years as words). The long GEMINI_STYLE body style was read aloud in 6 of 21 English
  chunks; SHORT styles from the start ("Warm, brisk documentary narrator.", es "Narrador de documental cálido y ágil.",
  pt "Narradora de documentário calorosa e ágil.", de "Warme, zügige Dokumentar-Erzählerin.", ja
  「温かいドキュメンタリーのナレーター、速めのテンポ。」) gave no style read-outs; repeats still happen (re-check every chunk).
- **2026-10-30 Adams run (Gemini Kore, short styles):** zh 429 spoken chars (no punctuation) → 118.3 s; en 1638 chars → 133 s (too long), 1550 → 125.8 s;
  es 1508 → 121.2 s; pt 1503 → 131.5 s (pt reads slower; ~1430 → 126.7 s); ja 668 → 120.6 s; de 1570 → 124.1 s.
  Joining a very short sentence to its neighbour with a comma (one chunk) avoided glitches in es/pt/de.
- **2026-10-31 Keats run (Gemini Kore, short styles):** zh 438 spoken chars → 122.6 s; en 1487 chars → 126.5 s; es 1555 → 127.2 s;
  pt 1421 → 127.8 s; de 1524 → 126.8 s; ja 686 → 118.1 s. de chunk ending "…ebenfalls an Tuberkulose." was repeated twice
  ("…an Tuberkulose, auch an Tuberkulose") even with a short style; rewording the sentence fixed it.
  Calywood: a big pose change between start.png and opening.png (head down vs facing viewer, fewer blossoms) gave a
  visible cross-dissolve twice; a start frame with only a small change (head tilted down, same framing) gave clean motion.
- **2026-11-01 Wegener run (Gemini Kore, short styles):** zh 441 spoken chars → 122.5 s; en 1567 chars → 127.8 s (tight); es 1555 → 124.8 s;
  pt 1425 → 122.5 s; ja 665 → 118.6 s; de ~1540 → 126.6 s. es: "se doctoró en astronomía" was read twice as "se doctoró con acento
  agudo" (Gemini read a pronunciation note aloud); rewording to "obtuvo el doctorado" fixed it. de: "…: ein Weltrekord." was said twice;
  rewording fixed it. ja: "11月1日" at the end was heard as "11月2日" by Whisper twice; spoken "11月ついたち" fixed it.
  Image MCP edit-image tends to reframe/zoom the start frame even when asked to keep it pixel-identical; a moderate
  reframe (same pose family, head tilted down) still gave a clean Calywood clip.
- **2026-11-02 Boole run (Gemini Kore, short styles):** zh 430 spoken chars → 119.5 s; en 1546 → 126.5 s; es 1596 → 127.5 s (tight);
  pt 1457 → 126.5 s; ja 638 → 114.5 s; de 1553 → 128.0 s, 1530 → 125.3 s. ja: "1847年" was heard as "1887年" twice; spoken
  kanji numerals 「千八百四十七年」 fixed it. de: "zweihundertelf" was heard as "2011"; "zweihundertundelf" is unambiguous.
  pipeline/tools/halves.sh needs /tmp/claude-0/s/asr1.py (a tiny sherpa-onnx Whisper script); recreate it if missing.
  Splitting a sentence-final line into two shifts the next chunk id (rename its wav) and the stack phase indexes.
- **2026-11-03 Matisse run (Gemini Kore, short styles):** zh 437 spoken chars → 120.7 s; en 1584 → 128.7 s (too long), 1540 → 125.1 s;
  es 1563 → 123.6 s; pt 1465 → 125.7 s; ja 656 → 111.5 s (too short), ~690 → 115.5 s; de 1544 → 127.2 s (tight; aim ~1520).
  en "…, at eighty-four." was said twice ("at 84, at 84"); "at the age of eighty-four" fixed it. de short chunk "Zuerst war er Schreiber in
  einer Anwaltskanzlei." was repeated (7.4 s, flagged SLOW); rewording fixed it. ja subtitles: a line splits into 2 rows at the 、 nearest the
  middle and each ROW (not piece) must be ≤ ~15 characters; use [subtitle, spoken] pairs to shorten. de: one long compound like
  "Blinddarmentzündung" in a ~65-char line warns; shorten the subtitle. /tmp/claude-0/s/asr1.py must use wave+numpy (soundfile is not installed).
- **2026-11-04 Carter run (Gemini Kore, short styles):** zh 452 spoken chars (no punct.) → 127.9 s (too long), ~440 → 124.0 s; en 1581 → 133.8 s (!),
  1485 → 126.6 s (en read slower this time; aim ~1480); es 1534 → 126.4 s; pt 1496 → 129.1 s, 1457 → 127.5 s (aim ~1430); ja 721 → 123.0 s;
  de 1530 → 128.9 s, 1501 → 127.1 s (aim ~1480). Whisper base hears ja 「百四年前」 as "1004年前" even when Gemini says ひゃくよねん: harmless.
  A start frame with only the head turned down to the steps (same pose family) gave a clean Calywood clip on the first try.
- **2026-11-05 Maxwell run (Gemini Kore, short styles):** zh 441 spoken chars → 125.6 s; en 1531 → 128.2 s (too long), 1487 → 124.8 s;
  es 1551 → 126.1 s; pt 1473 → 129.4 s (too long), 1426 → 125.8 s (aim ~1420); ja 700 → 117.5 s; de 1502 → 124.2 s.
  Calywood refused the first opening.png ("偵測為含真人臉部") although it was a sepia drawing; redrawing with the RUNBOOK
  "Calywood refusals" wording (cross-hatching, old printed book) passed on the first try. Commons file pages could not be
  fetched with WebFetch, but Special:FilePath/James_Clerk_Maxwell_big.jpg worked as edit-image input.
- **2026-11-06 Naismith run (Gemini Kore, short styles):** zh 431 spoken chars → 116.5 s; en 1518 → 124.4 s; es 1547 → 126.2 s;
  pt 1520 → 130.1 s (too long), ~1470 → 126.7 s; ja 688 → 114.3 s; de 1522 → 127.8 s (tight; aim ~1490). zh chunk c05_00 (35 chars,
  long GEMINI_STYLE) was said twice (14.7 s, 707 kB); a retry with the short style 「溫暖、明快的台灣紀錄片旁白。」 fixed it.
  Commons file pages and the Commons API are unreachable from here (WebFetch url_not_found, proxy refuses commons.wikimedia.org);
  Special:FilePath/James_Naismith.jpg still worked as edit-image input. Calywood accepted the cross-hatched opening on the first try.
- **2026-11-07 Curie run (Gemini Kore, short styles; zh body used the plan GEMINI_STYLE):** zh 443 spoken chars → 125.8 s; en 1527 → 126.7 s;
  es 1558 → 127.0 s (tight); pt 1480 → 131.8 s (too long), 1424 → 126.5 s (aim ~1420); ja 697 → 121.0 s; de 1501 → 124.6 s.
  es: "Ella ocupó su cátedra" was read as "ocupó con acento agudo" (accent note read aloud again); "heredó" fixed it.
  Commons Special:FilePath/Marie_Curie_1903.jpg worked as edit-image input; Calywood accepted the cross-hatched opening first try (NT$16.5).
- **2026-11-08 Barnard run (Gemini Kore):** zh 439 spoken chars with the SHORT style 「溫暖、明快的台灣紀錄片旁白。」 → 139.7 s (too long,
  0.30 s/char); the same chunks re-synthesized with the plan GEMINI_STYLE (brisk) → 120.1 s. For zh keep the plan GEMINI_STYLE for the body.
  en 1498 → 122.8 s; es 1538 → 118.8 s; pt 1512 → 127.7 s (tight), 126.6 s after re-doing a slow date chunk; ja 668 → 117.5 s;
  de 1537 → 123.5 s. Whisper base hears ja 「十一月八日」 as "11月4日" and 「二千一年」 as "2011年" (probably mishearing; c07 八日 was heard right).
  Commons file page for Christiaan_Barnard_(1968).jpg could not be fetched (licence unverified); Special:FilePath worked as edit-image input.
  Calywood: first try "copyright restrictions", identical resend succeeded (NT$16.5).
- **2026-11-09 Lamarr run (Gemini Kore, short styles; zh body plan GEMINI_STYLE):** zh 447 spoken chars → 122.7 s; en 1524 → 127.5 s (tight);
  es 1580 → 124.1 s; pt 1456 → 125.9 s; ja 708 → 119.8 s; de 1536 → 125.1 s. zh short chunk 「一九九七年，科技界終於頒獎給她。」 was said twice
  (6.9 s); joining it to the next sentence with a comma fixed it. de chunk with style "Warme, zügige Dokumentar-Erzählerin." read the style
  aloud once; a retry with "Ruhig, warm, zügig." was clean. ja c06_01 lost its last syllables once (re-synth fixed it).
  Calywood: a moderate start pose (head down writing → facing viewer) gave a slight cross-dissolve around 2.3–2.8 s; accepted.
  Commons Special:FilePath/Hedy_Lamarr_Publicity_Photo_for_The_Heavenly_Body_1944.jpg worked as edit-image input. Helper scripts used
  this run (/tmp/claude-0/s/mk.py: build a language episode from the zh structure + a spec of lines/texts; subfix.py: subtitle-only patch).
- **2026-11-10 Schiller run (Gemini Kore, short styles; zh body plan GEMINI_STYLE):** zh 429 spoken chars → 120.9 s; en 1541 → 129.9 s (too long),
  1494 → 126.2 s; es 1563 → 124.5 s; pt 1489 → 132.1 s (too long), 1409 → 126.9 s (pt keeps reading slow: aim ~1400); ja 681 → 118.6 s;
  de 1542 → 125.4 s. en hook with the long plan hook style read the style aloud ("Same brisk pace as the rest…"); the short style
  "Amazed, brisk documentary narrator." was clean (use short hook styles in every language: es "Narrador de documental, asombrado y ágil.",
  pt "Narradora de documentário, admirada e ágil.", de "Staunende, zügige Erzählerin.", ja 「驚きをこめた、速めのテンポのナレーター。」 — all clean).
  Commons Special:FilePath/Anton_Graff_-_Friedrich_Schiller.jpg?width=800 → "Image URL did not return HTTP 200"; Special:FilePath/Friedrich_Schiller.jpg
  worked. Calywood accepted the cross-hatched opening first try (NT$16.5). Calywood 400 "resource inaccessible" = a mistyped signed URL.
- **2026-11-11 Tycho Brahe run (Gemini Kore, short styles; zh body plan GEMINI_STYLE):** zh 457 spoken chars → 131.2 s (too long), 425 → 122.9 s;
  en 1525 → 133.3 s (too long), 1437 → 125.6 s (en keeps reading slow: aim ~1440); es 1524 → 123.1 s; pt 1443 → 128.2 s, 1431 → 127.3 s
  (aim ~1400); de 1535 → 126.6 s; ja 649 → 115.8 s. No repeats or style read-outs this run (long sentences joined with commas).
  Commons Special:FilePath/Tycho_Brahe.JPG?width=800 worked as edit-image input. Calywood: first try "copyright restrictions", identical
  resend succeeded (NT$16.5). Image MCP drew a telescope-like sight tube for a 16th-century quadrant; "no telescope, only open sights" fixed it.
  The question rows' `at` is an absolute line index in the scene (not relative to the phase).
- A subtitle-only fix (spoken text unchanged) can be patched in both episode.json and timeline.json without
  re-running narrate.py.

## 0. Plan the run
1. Target dates = run date + 1 … run date + WINDOW.
2. Postiz `postsListTool` from (first target date − 1 day)T16:00:00 to (last target date)T16:00:00 UTC. For each target
   date D, look for posts at 06:00 Taipei on D on each channel (Facebook `cmvbzqyvs0002s67fq0dzr53e`, YouTube
   `cmvc7njup0001s673xhqhp5s8`); ignore errored/deleted ones.
   - Both channels have a post → D is covered, skip it.
   - Only one channel has a post → do not make a new video: schedule the missing channel only, reusing that post's
     attachment path and `episodes/D/post.txt` (step 8.3 for that channel alone).
   - Neither → D needs a video.
   - Also look for posts on the English (`cmvibixcp000ms67kkplrbxb1`) and Spanish (`cmvic8oq3000os67kdsemvo3t`)
     channels at the same 06:00 Taipei slot. No post → D needs that language's video (section E).
3. Make the missing videos one at a time, earliest date first, each through steps 2–9 completely before starting the
   next (finished and scheduled before the next one starts, so a later failure never loses an earlier video).
4. Topics: besides covered.md, also avoid the people already scheduled for the other dates in the window.
5. If a video fails (any STOP rule below, or a check it cannot pass), stop the whole run there: keep what was already
   scheduled, do not start later dates, and notify the user (which date failed, why, which dates are still covered).
   The next evening's run will try again.

## 1. Setup
```
git clone https://github.com/chihuangchiu/daily && cd daily        # skip if already present; then git pull
pip install --break-system-packages -q -r requirements.txt
which ffmpeg && fc-list | grep -q "Noto Serif CJK" && echo ok
```

## 2. Choose the subject for D
Search the web for D's month/day ("M月D日 歷史上的今天", "M月D日 台灣歷史", "On this day <Month D>").
Pick ONE, in this order of preference:
1. Taiwan history: a person (born, died, or did the defining act on this exact date) or an event centred on a person.
2. A person or event that changed the world (science, medicine, democracy, human rights, culture, technology, exploration).

Rules
- The date must match exactly (month and day) and be confirmed by two sources.
- The centre must be a person who can fairly be called a 偉人: lasting positive contribution. No disasters, atrocities or crimes as the main story; no figure whose legacy is mainly violence; no living active politicians.
- Do not repeat anyone listed in `covered.md` within the last 365 days.
- Contested political history: tell it factually and neutrally, no partisan framing.

## 3. Research and verify
Collect facts from at least two independent reliable sources (government, museums, encyclopedias, universities,
major news). Every date, number, name and quotation in the script must be confirmed by two sources;
drop anything that is not. Quote only well-documented sayings. Keep a source list for the run report.

## 4. Write `episodes/YYYY-MM-DD/episode.json`
Follow `TEMPLATES.md`; copy the structure of the most recent episode.
- Traditional Chinese, Taiwan usage. ~650–720 characters of narration (spoken field), 8–9 scenes, ~55–65 lines.
  The video must stay under 180 s: aim for 165–175 s.
- Shape: opening hook (title template, ~6 lines, ends with the name) → 5–6 chapters (timeline, document,
  tiles, stack…) → legacy today → one question for the viewer → end scene.
- Spoken text: Chinese numerals, no Latin letters/digits. Subtitle text may use digits.
- Pronunciation: check names and polyphones with
  `python3 -c "import sys;sys.path.insert(0,'pipeline');from tts import BakerProcessor as B;p=B(data_dir=None,loaded_mapper_path='pipeline/models/baker_mapper.json');print(p.text_to_phone('要檢查的句子'))"`
  and, if a reading is wrong, rewrite only the spoken field (homophone characters are fine).

## 4b. Opening image (required) — the real person, face visible, in a scene of the era (Nathan 2026-10-21)
Goal: a scene with context (place, objects, era) like the earlier openings, but with the person facing the viewer and
looking like the real person. The likeness comes from a real photograph used as a face reference. Only when no usable
photo exists does the person appear from behind / in silhouette / small in the distance (no invented face).

1. Find the photo. WebSearch with `allowed_domains: ["commons.wikimedia.org"]` for "<person name in English> portrait"
   (also try the Chinese name). Use only files on Wikimedia Commons whose page says Public domain, CC0, CC BY or CC BY-SA
   (Nathan 2026-10-20: all fine). Prefer a photo taken in the person's lifetime with the face clearly visible.
   Never use a photo of a living person. Record the file page URL, photographer/author and licence.
   The original file URL is `https://upload.wikimedia.org/wikipedia/commons/<h0>/<h0h1>/<File_name>` where h = md5 of the
   file name with spaces replaced by `_` (`python3 -c "import hashlib;f='File_name.jpg';h=hashlib.md5(f.encode()).hexdigest();print(h[0],h[:2])"`).
   The cloud workspace itself cannot download from Wikimedia (upload.wikimedia.org is blocked by the egress proxy);
   Image MCP fetches the URL itself. If Image MCP answers "Image URL did not return HTTP 200" for upload.wikimedia.org
   URLs, use `https://commons.wikimedia.org/wiki/Special:FilePath/<File_name>?width=800` instead (worked 2026-10-22
   when every upload.wikimedia.org URL, including thumbnails, failed).
2. Draw the scene with Image MCP `edit-image`: `image` = the original file URL, `size: "1024x1536"`, `quality: "high"`.
   Prompt in English (fill in the scene of the story's key place and era):
   "Use the person in this photograph only as the face and likeness reference, and create a full scene illustration
   of them. Scene: <place, era, objects, light>. The person, in <period clothing>, <stands/sits> <where>, facing the
   viewer, seen from the waist up, <one natural action>, calm expression. Their face must clearly match the person in
   the photograph: same face shape, eyes, nose, hairline, hairstyle and <beard/glasses…>. Vertical composition: the
   upper part is the quieter background (sky, wall, window), the person in the middle and lower part. " + STYLE.
   It must look hand-drawn, never like a photo. (Tested 2026-10-21 with Nobel: clear likeness, full lab scene.)
3. Fallback (no usable photo, or step 2 keeps failing): `create-image` with `size: "1024x1536"`, `quality: "high"`,
   `output_format: "png"`, the same kind of scene + STYLE; the person only from behind, in silhouette or small in the
   distance (no invented face without a photo).
4. Keep the download URL the tool returns (valid 24 h; 4d needs it) and save the file: `curl -sSf -o episodes/D/opening.png "<url>"`.
5. Open it with Read. Reject and regenerate (max 3 tries) if it has text or letters, warped hands or faces, a face that
   does not match the photo, a photo-realistic look, anachronisms, anything gory or offensive, a tone that differs from
   the house style (see "One tone" below), or it does not fit the story.
6. In the title scene's `data` set `"image": "opening.png"` and `"image_shift"`: the image model ignores "put the face
   low", and the title text covers the top 60% of the frame, so render.py moves the picture down by image_shift x
   height (0–0.4; the freed top band is filled with the picture's top-edge colour). Estimate where the face centre is in
   opening.png as a fraction of its height (f) and set image_shift = round(0.60 − f, 2), at least 0 (Nobel: face at
   ~0.35 → 0.25). The clip (4d) is shifted the same way. Then check check/sheet_00.png: the face must be visible between
   the name line and the subtitle box.
7. No on-screen AI label is shown (Nathan 2026-10-20). If a CC BY / CC BY-SA photo was used, add one line before the
   AI sentence in post.txt: `開場畫像依據 Wikimedia Commons 照片繪製（作者：<author>，授權：<licence>）。`
   (not needed for public domain / CC0).
8. If no picture can be made at all (Image MCP not connected after the retries, generation or download keeps failing,
   or 3 tries still give an unusable picture), STOP: do not build, upload or publish anything. Notify the user with
   which picture failed and the exact error (Nathan 2026-10-20).

### One tone for every picture and the clip (Nathan 2026-10-21)
All pictures of an episode (opening, chapter images) and the opening clip must look like one set:
- STYLE, word for word, at the end of every image prompt: "Style: warm sepia ink-wash illustration with fine pencil
  lines, soft paper texture, cream and brown palette with small touches of deep red. Hand-drawn look, not
  photographic. No text, no letters, no logos, no watermarks."
- No other colour words in the prompts (no "blue sky", "green field", "golden light" — describe light as warm/dim/soft).
- After saving all pictures, look at them side by side (e.g. `ffmpeg -i opening.png -i img1.png -i img2.png -filter_complex "[0]scale=-1:400[a];[1]scale=-1:400[b];[2]scale=-1:400[c];[a][b][c]hstack=3" tones.png`, then Read)
  and regenerate any picture whose colour, brightness or line style stands out.
- The clip is made only from opening.png and a start frame drawn from it (first/last-frame video, 4d), never from a text prompt, so it has the same tone.

## 4c. Chapter images (required: 4–5 more pictures; Nathan 2026-10-28, was 1–2)
Besides the opening image, every video shows 4–5 more AI pictures inside the chapters: at least one per chapter
(4 chapters), plus one for the legacy/today part when it fits, each at the story's key moments
(for example the place where it happened, the defining object or act, the legacy).
1. `create-image` with `size: "1536x1024"` (landscape; shown in a 560x420 frame, keep the subject centred, edges get
   cropped), `quality: "high"`, `output_format: "png"`, prompt ending with STYLE. Scenes, places and objects; if the
   person appears and a photo was found in 4b, you may use `edit-image` with the photo URL as face reference instead
   (same wording as 4b step 2, landscape size); without a photo, people only from behind or far away. Read every file,
   max 3 tries each, same rejection rules as 4b step 5, and check the tone against opening.png.
2. Save as `episodes/D/img1.png`, `episodes/D/img2.png` (curl the download URL, same as 4b).
3. Put each picture in its own phase of a stack scene, near the line that tells that moment:
   `{"at": N, "until": M, "items": [{"type":"image","src":"img1.png","caption":"<≤ 16 字說明>"}, {"text":"<short line>","style":"mid"}]}`.
   The caption names the place, moment or object (e.g. 「1840 年代倫敦的音樂廳」); never add 「示意」「示意圖」「AI 生成」
   or similar labels — every picture is plainly a drawing (Nathan 2026-10-21).
   At most one short text item next to it (the frame is ~460 px tall; the visual area is 677 px). Show it for at
   least 2 subtitle lines. Two images may share a scene only in separate phases (each ≥ 2 subtitle lines); if a
   chapter is too short for that, one image per chapter is enough. Name them img1.png … img5.png (all shared by every
   language of D, like the opening). Check all of them side by side for one tone (see "One tone").
4. Check the sheets (step 5) for overlap or clipping around the pictures. If a chapter picture cannot be made,
   stop exactly as in 4b.8; never publish a video with fewer pictures than required.

## 4d. Opening clip (Calywood first/last-frame video that ENDS on opening.png, 5 s) — Nathan 2026-10-21 (v2)
The clip must end exactly on opening.png, so the hand-over from the clip to the still is seamless (no jump), and it
must show real, natural action, not just a zoom. So opening.png is the LAST frame, and a matching START frame is drawn
from it: the same scene a few seconds earlier, with the person in a different pose.

1. Start frame: Image MCP `edit-image` with `image` = the download URL of opening.png (4b step 4), `size: "1024x1536"`,
   `quality: "high"`, prompt:
   "Show this exact same scene a few seconds earlier, as the first frame of a short film that ends on this picture.
   Keep everything identical: the same <place>, <objects>, the same person with the same face, hair and clothes, the
   same camera position and framing, the same drawing style and colours. Change only his/her pose: <an earlier moment
   of one clear action — e.g. bent over the piano keys playing / looking down into the microscope / writing at the desk /
   turned toward the window / walking in from the side>. " + STYLE.
   Save it as `episodes/D/start.png` (curl), Read it next to opening.png: same scene, framing, face and tone; only the
   pose differs. Max 3 tries.
2. Calywood `generate_video_from_image` with `image_url` = start.png's download URL, `last_frame_url` = opening.png's
   download URL, `duration: 5`, `resolution: "720p"`, English `prompt` describing the action that leads
   from the start pose to the final pose, with natural, realistic body motion (hands, head, shoulders, hair, cloth) and
   one or two small background motions (flames flicker, people in the background move, steam or smoke drifts), e.g.
   "The pianist plays a final chord, lifts his hands, raises his head and turns his face and shoulders toward the
   viewer, settling into a calm gaze with eyes open, exactly as in the last frame. The audience stirs, candle flames
   flicker. Natural, realistic body motion; the camera stays almost still. Silent, no music. Keep the hand-drawn sepia
   ink-wash style and colours exactly as in the images. No text."
   No camera zoom/push-in as the main motion; avoid "blink" (eyes can stay closed). Do not use `generate_video`
   (text-to-video) or `generate_video_multimodal` (results are not copied to the bucket below).
   Without a photo (4b fallback, person from behind), the action is still a real one (e.g. he lowers the lens and leans
   back; she walks to the window); the face stays hidden.
3. Poll `get_task` (about every 30 s, up to 10 min; a 4–5 s clip takes about 4–6 min). The link it returns (volces.com)
   is blocked here; a copy appears a few minutes later at
   `https://storage.googleapis.com/alchemy-dance-media-cacafly-nathan-project/videos/<task_id>.mp4`.
   Retry `curl -sSf -o episodes/D/opening.mp4 "<that url>"` every minute for up to 10 min (403 = not there yet), then
   check it with ffprobe (video stream, at least 4.9 s; about 786x1178, render.py crops it to 720x1280).
   A task can fail with "output audio may be related to copyright restrictions": just retry (it worked on the next try).
4. Grab frames at 1.0, 2.5, 4.0 s and the last frame (`ffmpeg -sseof -0.1 -i opening.mp4 -frames:v 1 last.png`) and
   Read them next to opening.png: the person must stay the same, the motion must look natural (no warped limbs or
   faces), the colours must stay those of opening.png, and the last frame must match opening.png. Retry with a revised
   prompt, max 3 tries.
5. In the title scene's `data` set `"video": "opening.mp4", "video_secs": 5, "video_align": "end"` (keep `"image"` and
   `"image_shift"`). With `video_align: "end"` render.py plays the LAST 5 s of the clip (Nathan 2026-10-21: 5 s opening) (ending on opening.png), crops
   it to 720x1280, shifts it like the still, applies the same sepia and darkening, and hands over to the still with a
   0.25 s cross-fade.
6. If the clip cannot be made (start frame or clip fails after the usual retries, Calywood not connected, the download
   keeps failing, or 3 tries are all unusable), STOP exactly as in 4b.8 (Nathan 2026-10-20): nothing is built or
   published, and the notification says the opening clip failed, with the exact error.

## 5. Check
```
pipeline/build.sh episodes/YYYY-MM-DD check
```
- Must print no `WARNING:`; narration speed should be 0.92–1.10 (otherwise lengthen/shorten the script).
- Open every `episodes/YYYY-MM-DD/check/sheet_*.png` with Read and look for overlaps, clipped text, empty
  screens, wrong facts. Fix the JSON and re-run until clean.

## 6. Build
```
pipeline/build.sh episodes/YYYY-MM-DD video
```
Expect `video.mp4`, 720x1280, 160–178 s (never 180 s or more, or YouTube will not count it as a Short), under 30 MB. Grab 3 frames with ffmpeg and look at them.

## 7. Write `episodes/YYYY-MM-DD/post.txt`
First line `標題：<title>` (≤ 40 chars, hook + name; it is also the video title and the first line of the post). Then the article: the narration rewritten as
readable paragraphs, plain text only (no #, **, --- or other markdown), then
`歡迎在留言分享你的答案。`, then `本片旁白為AI合成語音，影片由AI協作製作。內容如有錯誤，歡迎留言指正。`,
then 6–10 hashtags on one line, always including #歷史上的今天 #今天誰改變了世界.
The same text is used on Facebook and YouTube (step 8). Keep the whole post under 4,500 characters (YouTube limit 5,000).

## 8. Publish through Postiz
GitHub Releases cannot be created from Claude sessions, and branch deletion is blocked, so the video goes
through a throw-away `media` branch that only ever holds one file (force-pushed each time):
```
M=$(mktemp -d) && cd $M && git init -q -b media
cp <repo>/episodes/D/video.mp4 D.mp4 && echo "Temporary media for Postiz." > README.md
git add -A && git commit -qm "media D" && git remote add origin https://github.com/chihuangchiu/daily.git
git push -f origin media
curl -sI https://raw.githubusercontent.com/chihuangchiu/daily/media/D.mp4   # expect 200 and the right size
```
If the force-push is refused, use a normal push on top of the existing branch instead:
`git clone --depth 1 -b media https://github.com/chihuangchiu/daily.git m && cd m`, add `D.mp4`, commit, `git push origin media`;
after the Postiz upload, `git rm D.mp4`, commit, `git push origin media` (the branch tip again holds only README.md).
1. Postiz `uploadFromUrlTool` with `https://raw.githubusercontent.com/chihuangchiu/daily/media/D.mp4` → `{id, path}`.
2. Clear the branch right away: commit only README.md on a fresh orphan `media` and `git push -f origin media`.
3. One Postiz `integrationSchedulePostTool` call with two items in `socialPost`, both type `schedule`,
   date = 06:00 Taipei on D = `(D minus 1 day)T22:00:00Z` (if that has passed, now + 10 min),
   isPremium false, shortLink false, attachments `[path]` (the same uploaded video). Every line of content is
   wrapped in `<p>…</p>` (blank lines become `<p></p>`, HTML-escape the text).
   - Facebook (`cmvbzqyvs0002s67fq0dzr53e`): content = the title as the first line, a blank line, then the
     article (post.txt with `標題：` removed; post.txt already has the blank line, do not add another);
     settings `[{key:"post_type", value:"post"}, {key:"title", value:<title>}]`.
   - YouTube (`cmvc7njup0001s673xhqhp5s8`): content = the article only (no title line), with `#Shorts`
     added at the start of the hashtag line; settings `[{key:"title", value:<title> + " #Shorts"} (≤ 100 chars),
     {key:"type", value:"public"}, {key:"selfDeclaredMadeForKids", value:"no"},
     {key:"tags", value:[{value,label}, …]}]` with 5–6 tags: Shorts, 歷史上的今天, 今天誰改變了世界, the person, 1–2 topics.
4. Confirm with Postiz `postsListTool` that both posts are listed for the right time and channels. If only one
   of them was created, do not schedule the other again blindly: check the list first, then add only the missing one.

## 9. Record
As soon as D is scheduled (not when it is published), append `| D | person | event |` to `covered.md` (keep the
table in date order); commit `episodes/D/episode.json`, `episodes/D/post.txt`,
`covered.md` (never the mp4/wav/check files; .gitignore covers them) and push to main.

## E. English channel "Who Changed the World Today" (Nathan 2026-10-22)
An all-English YouTube Shorts channel for a worldwide audience: one video per day D, published at 06:00 Taipei on D
(`(D−1)T22:00:00Z`, the same time as every other channel), only on YouTube `cmvibixcp000ms67kkplrbxb1`.

Subject
- If the Chinese video of D is about someone who is not Taiwanese / not mainly Taiwan history, the English video
  shares it: the same person and story, retold in English, reusing that episode's pictures and opening clip
  (opening.png, img1/img2.png, opening.mp4: copy them from episodes/D, no new pictures and no Calywood cost).
  Pictures are not kept in git (episodes/*/*.png and *.mp4 are ignored), so make the English video in the same run
  as the Chinese one, right after it. If the pictures are gone (made in an earlier run), make new ones (4b–4d).
- If the Chinese subject is Taiwanese (Taiwan history, a person known mainly for Taiwan; e.g. 蔣渭水, 楊逵, 嚴家淦),
  choose a different person for D from world history: born, died or did the defining act on D's month/day, a lasting
  positive contribution, recognisable to a global audience, the same 偉人 rules as step 2. Not in covered-en.md within
  365 days, and not anyone scheduled on the other days of the window (either channel). Make all pictures and the clip
  new (4b–4d), and verify every fact with two sources (step 3).

Episode: `episodes/D-en/episode.json` with `"lang": "en"` (render.py then shows the header "Who Changed the World
Today", the kicker "On This Day", the end kicker "On This Day · MM.DD"; narrate.py uses the English Kokoro voice
af_heart, downloaded automatically on first use, ~350 MB, needs `pip install sherpa-onnx`).
- Copy the shape of `episodes/2026-10-24-en/episode.json`: title → 5–6 chapters → legacy → one question → end;
  8 scenes, ~45–50 lines, ~430–460 spoken words; chapter labels like "Chapter 1  The cloth merchant".
- One line = one subtitle = one TTS call, so each line must be a complete clause (do not cut a sentence in the middle
  of a phrase) and at most ~68 characters (subtitles wrap to two rows of 36 px; longer lines give a WARNING).
- Spoken text may use plain English; write years as words in the spoken field ("sixteen thirty-two"), and respell
  hard names phonetically in the spoken field only (Leeuwenhoek → "Layvenhook", Regnier de Graaf → "Rayneer de Grahf").
- Names on screen: a long full name does not fit the 420 px title name slot; use the surname as `name` and put the
  full name in `name_years` ("Antonie van Leeuwenhoek · 1632 – 1723"). No `seal` (Chinese seal characters).
- Pills and on-screen texts short (title pills ≤ ~14 characters each), captions ≤ ~32 characters, in English.
- Same length rules: `TARGET=170 pipeline/build.sh episodes/D-en check`, speed 0.92–1.10, final video 160–178 s.
  Optional pronunciation check: SenseVoice ASR with `language="en"` (see the stock-video tasks) — names may come out
  oddly spelled, everything else should match.
- Read every check sheet as for the Chinese video.

post.txt (English): first line `Title: <title>` (≤ 90 characters, e.g. "394 Years Ago Today, a Cloth Seller Saw a
Hidden World | Leeuwenhoek"), a blank line, the article (narration rewritten as plain paragraphs), then
`Tell us your answer in the comments.`, then `The narration is an AI voice, and this video was made with the help of AI.
If you spot a mistake, please let us know in the comments.`, then one hashtag line with 5–8 tags always including
#OnThisDay #WhoChangedTheWorldToday. If a CC BY / CC BY-SA photo was used for the opening, add before the AI line:
`Opening portrait drawn from a Wikimedia Commons photo (author: …, licence: …).`

Publish: media file name `D-en.mp4` (same media-branch steps as step 8), then one `integrationSchedulePostTool` call
with one item: integrationId `cmvibixcp000ms67kkplrbxb1`, type schedule, date `(D−1)T22:00:00Z`, content = the article
only with `#Shorts` added at the start of the hashtag line, settings title = <title> + " #Shorts" (≤ 100 chars),
type public, selfDeclaredMadeForKids no, tags (5–6): Shorts, On This Day, Who Changed the World Today, the person,
1–2 topics. Confirm with postsListTool. Then add `| D | person | event | shared? |` to `covered-en.md` and commit
`episodes/D-en/episode.json`, `episodes/D-en/post.txt` and covered-en.md to main.

## S. Spanish channel "¿Quién cambió el mundo hoy?" (Nathan 2026-10-22)
Same person and story as the English video of D (translated, not word for word), 06:00 Taipei on D, YouTube
`cmvic8oq3000os67kdsemvo3t`. Folder `episodes/D-es`, `"lang": "es"` (render.py: header "¿Quién cambió el mundo hoy?",
kicker "Un día como hoy"; narrate.py: Kokoro ef_dora, sid 28, `lang="es"`, no lexicon — tested 2026-10-22, Whisper
check passes). Copy opening.png/start.png/img1/img2/opening.mp4 from `episodes/D-en`. Copy `episodes/2026-10-22-es`.
- Spanish lines run longer: keep each line ≤ ~62 characters or the subtitle WARNS; translate every on-screen text,
  including timeline `big`/`small` and captions.
- Pronunciation check: sherpa-onnx Whisper base (`sherpa-onnx-whisper-base.tar.bz2`, `from_whisper(..., language="es")`).
- post.txt starts `Título: …`; record in `covered-es.md`; media file `D-es.mp4`.

## P/J/D. Portuguese, Japanese and German channels (Nathan 2026-10-22)
Same person and story as the English video of D, 06:00 Taipei on D (`(D−1)T22:00:00Z`), each on its own YouTube channel:
- Portuguese "Quem mudou o mundo hoje?" `cmviqybpp000ws67knh5z6wzo` — `episodes/D-pt`, `"lang": "pt"` (Kokoro pf_dora via
  sherpa-onnx, espeak pt-br; Brazilian Portuguese). Header "Quem mudou o mundo hoje?", kicker "Um dia como hoje".
  post.txt `Título: …`, closing lines "Conte sua resposta nos comentários." / "A narração é uma voz gerada por IA e este
  vídeo foi feito com ajuda de IA. Se encontrar algum erro, avise nos comentários.", hashtags incl. #UmDiaComoHoje
  #QuemMudouOMundoHoje; tags Shorts, Um dia como hoje, Quem mudou o mundo hoje, person, 1–2 topics.
- German "Wer hat heute die Welt verändert?" `cmvir7imd0011s67ky3vmkijj` — `episodes/D-de`, `"lang": "de"` (Piper
  de_DE thorsten-high, male; downloaded automatically). Header "Wer hat heute die Welt verändert?", kicker "An diesem
  Tag". post.txt `Titel: …`, "Schreib deine Antwort in die Kommentare." / "Die Erzählstimme ist KI-generiert, und
  dieses Video wurde mit Hilfe von KI erstellt. Wenn dir ein Fehler auffällt, schreib es gern in die Kommentare.",
  hashtags incl. #AnDiesemTag #WerHatHeuteDieWeltVerändert; tags Shorts, An diesem Tag, Wer hat heute die Welt
  verändert, person, 1–2 topics. Spoken years as words ("achtzehnhundertelf").
- Japanese "今日、世界を変えたのは誰" `cmvir44qg000zs67kevg8s72x` — `episodes/D-ja`, `"lang": "ja"` (misaki G2P →
  Kokoro jf_alpha via kokoro-onnx; render.py uses the JP font and CJK subtitle wrapping). Header 「今日、世界を変えたのは誰」,
  kicker 「今日は何の日」. Spoken text can stay in kanji/digits (misaki reads them). Kokoro Japanese is slow: about
  850 characters of narration for 170 s. Lines ≤ ~22 characters and every 、-separated piece ≤ 15 characters, or the
  subtitle WARNS. post.txt `タイトル：…`, 「あなたの答えをコメントで教えてください。」/「ナレーションはAI音声で、この動画はAIの協力で
  制作しています。内容に誤りがあれば、コメントでお知らせください。」, hashtags incl. #今日は何の日 #今日世界を変えたのは誰;
  tags Shorts, 今日は何の日, 今日世界を変えたのは誰, person, 1–2 topics.
- Template for all three: `episodes/2026-10-22-{pt,de,ja}`. Copy the pictures and clip from `episodes/D-en`;
  translate every line and every on-screen text (timeline big/small, captions, pills, chapters); media files `D-pt.mp4`
  etc.; record in `covered-pt.md`, `covered-de.md`, `covered-ja.md`.
- Japanese setup: `pip install misaki kokoro-onnx fugashi jaconv mojimoji pyopenjtalk-plus`; `unidic-lite` fails to build
  on this Python (setuptools install_layout): `pip download --no-binary :all: unidic-lite`, untar, and copy its
  `unidic_lite/` folder into site-packages. kokoro-onnx model files download automatically (~350 MB).
- Pronunciation check for pt/de/ja: sherpa-onnx Whisper base with the matching `language`.

## Calywood refusals (2026-10-22)
- "輸入的參考圖被 BytePlus 偵測為含真人臉部": the drawing looks too much like a photo. Redraw opening.png (and start.png)
  as a clearly drawn illustration: add to the 4b prompt "render it clearly as a drawing: loose pen-and-ink lines,
  visible cross-hatching on the face and clothes, slightly simplified features, flat washes of ink, like an
  illustration in an old printed history book". Worked for Ederle.
- "output video may be related to copyright restrictions" three times in a row for Pelé (a famous modern athlete):
  pick another person for that channel/day; prefer people who died before ~1980 or are less of a modern celebrity.

## 10. Report
Only when the run made or fixed something, or failed: send the user one short message listing, per date in the window
and per channel group (中文 FB+YT, English YT, Spanish YT; all 06:00), either "already scheduled" or what was made (who/what, title, length, publish time 06:00, both Postiz preview links,
sources, anything dropped or uncertain). Remind them each post can be deleted in Postiz before its 06:00 publish time.
If every date in the window was already covered, finish silently.

## If something fails
Never post a partial or unchecked video. If pushing the media branch is refused, or Postiz cannot fetch the
URL, send the user the video file (SendUserFile, it is under 30 MB) and the post text, and ask them to upload
it in Postiz; when they reply, schedule both posts as in step 8. Report the exact error.
