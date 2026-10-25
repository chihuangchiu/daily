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

## 0b. Length, hook and on-screen text (Nathan 2026-10-22) — overrides the older numbers below
- **Length: about 120 s** (TARGET=120 is now build.sh's default). Final video 112–128 s; speed in check 0.92–1.10.
  Narration size: Chinese ~460–500 characters (~40–45 lines, 7 scenes: hook/title → 4 chapters → legacy + question →
  end); English ~300–320 words; Spanish/Portuguese ~280–310; German ~270–290; Japanese ~600 characters.
  Keep the strongest 4 chapters; drop side facts rather than speeding up.
- **Hook in the first 2 seconds.** Line 0 of the title scene is a spoken hook: the single most surprising or emotional
  fact, said in under ~2 s (Chinese ≤ 16 characters, English ≤ 10 words), e.g. 「他一個人，讓全歐洲為鋼琴瘋狂。」 /
  "He made all of Europe go wild for a piano." The date line ("歷史上的今天，10月22日" / "On this day, October 22")
  comes second. In the title `data` set `"hook": "<2 short rows split by \n>"` (same idea, ≤ 2 rows of ≤ 10 CJK
  characters or ≤ 22 Latin characters each). render.py shows the hook big over the clip from frame 0 (frame 0 is the
  Shorts thumbnail) and brings in the kicker + MM.DD date only when line 1 starts (`hook_until`, default 1).
  The title scene then needs only the date, `sub` (years) and `name` — drop the `middle` texts/pills.
- **On-screen text: only what earns its place.** Per phase at most 2 text items (one big keyword or number + at most
  one short line); never repeat the subtitle sentence on screen; a phase disappears as soon as its line has passed;
  chapter scenes may be just one big number or word. No footer line (render.py no longer draws it: the Shorts UI
  covers the bottom of the frame). Subtitles are narrower now to stay clear of the Shorts buttons: Western-language
  lines ≤ ~55 characters, CJK pieces between commas ≤ 14 characters. On-screen phase texts are one row only
  (`\n` works in `hook` only).
- **Subscribe & share line (Nathan 2026-10-25).** The end scene gets one more line after "we remember …", spoken and
  shown as the subtitle, inviting viewers to subscribe and share: zh 「喜歡這個故事，記得追蹤訂閱，也分享給朋友。」
  (the Chinese video also goes to Facebook, hence 追蹤訂閱); en "If you enjoyed this story, subscribe and share it with
  a friend."; es "Si te gustó esta historia, suscríbete y compártela."; pt "Se gostou desta história, inscreva-se e
  compartilhe."; ja 「気に入ったら、チャンネル登録と、共有をお願いします。」 (subtitle; spoken without the second 、);
  de "Wenn dir die Geschichte gefällt, abonniere und teile sie." It costs ~3 s and must fit the 112–128 s / speed
  0.92–1.10 rules: cut a side sentence first, never speed up; drop the line only if it truly does not fit (say so
  in the report). No extra on-screen text or like/bell icons.
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
  - The hook style is dramatic and a bit slower; the rest is brisk ("像 YouTube Shorts 的說書人"). Nathan:
    first line dramatic and slower, then faster; never speed the audio up afterwards.
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
  repeat shows the same sentence in both halves). Re-synthesize bad chunks; if a chunk fails twice, join it to its
  neighbour (end the line with a comma instead of a full stop) so the chunk gets longer. Write scripts with few
  very short stand-alone sentences. The 2026-10-28 zh video was scheduled before this was found (two repeated
  sentences); the fixed v2 went to Postiz as drafts for Nathan to swap.
- **Measured script sizes for 112–128 s (Gemini Kore, 2026-10-25):** zh ~420 spoken characters → 119.5 s;
  en ~237 words → 115.7 s (≈ 2 words/s); es ~272 words → 124 s; pt ~283 words → 126.7 s; de ~216 words (long
  compounds, years as words) → 120.5 s; ja ~600 characters → 112.1 s (aim ~630). Japanese subtitles: a line is split
  into at most 2 rows at the 、 nearest the middle, each row ≤ ~15 characters (600 px), so keep subtitle lines ≤ ~28
  characters with a 、 near the middle (subtitle-only shortening is fine).
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

## 4c. Chapter images (required: 1–2 more pictures)
Besides the opening image, every video shows 1–2 more AI pictures inside the chapters, at the story's key moments
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
   least 2 subtitle lines. Do not put two images in the same scene.
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
