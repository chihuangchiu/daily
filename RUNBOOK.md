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
- Timezone: Asia/Taipei. Get the run date from the current-time tool. In every step below, D = the target
  (publish) date of the video being made: its month/day drives the topic, the "N年前的今天" years, the folder
  episodes/D, the media file name and the publish time.

## 0. Plan the run
1. Target dates = run date + 1 … run date + WINDOW.
2. Postiz `postsListTool` from (first target date − 1 day)T16:00:00 to (last target date)T16:00:00 UTC. For each target
   date D, look for posts at 06:00 Taipei on D on each channel (Facebook `cmvbzqyvs0002s67fq0dzr53e`, YouTube
   `cmvc7njup0001s673xhqhp5s8`); ignore errored/deleted ones.
   - Both channels have a post → D is covered, skip it.
   - Only one channel has a post → do not make a new video: schedule the missing channel only, reusing that post's
     attachment path and `episodes/D/post.txt` (step 8.3 for that channel alone).
   - Neither → D needs a video.
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

## 4b. Opening image (required) — portrait from a real photo when possible (Nathan 2026-10-20)
Goal: the opening shows the person, drawn by hand from a real photograph, instead of only a background or a figure seen
from behind. Flow: find a photo → Image MCP redraws it as a drawing → Calywood animates that drawing (4d).

1. Find the photo. WebSearch with `allowed_domains: ["commons.wikimedia.org"]` for "<person name in English> portrait"
   (also try the Chinese name). Use only files on Wikimedia Commons whose page says Public domain, CC0, CC BY or CC BY-SA
   (Nathan 2026-10-20: both are fine). Prefer an old portrait photo taken in the person's lifetime, face clearly visible.
   Never use a photo of a living person. Record the file page URL, photographer/author and licence.
   The original file URL is `https://upload.wikimedia.org/wikipedia/commons/<h0>/<h0h1>/<File_name>` where h = md5 of the
   file name with spaces replaced by `_` (`python3 -c "import hashlib;f='File_name.jpg';h=hashlib.md5(f.encode()).hexdigest();print(h[0],h[:2])"`).
   The cloud workspace cannot download from Wikimedia (upload.wikimedia.org is blocked by the egress proxy, 2026-10-20).
2. Redraw it with Image MCP `edit-image` (photo as `image`), `size: "1024x1536"`, `quality: "high"`. Prompt in English:
   "Redraw this photograph as a hand-drawn portrait illustration: warm sepia ink-wash and pencil sketch, soft paper
   texture, cream and brown palette with small touches of deep red. Keep the person's recognizable features, hairstyle
   and clothing. Vertical composition: the person from the chest up in the lower half of the frame, with a faint
   <era/place> background; the upper half is plain soft paper (the title sits there). No text, no letters, no logos,
   no watermarks." It must look hand-drawn, never like a photo.
   STATUS 2026-10-20: `edit-image` in cloud mode only accepts base64 image data, not a URL, and the photo cannot be
   downloaded here, so this step cannot run yet. Until Nathan adds image-URL input to `edit-image` (or allows
   upload.wikimedia.org in this environment's network settings), go straight to step 3.
3. Fallback (no usable photo, or step 2 not possible): `create-image` with `size: "1024x1536"`, `quality: "high"`,
   `output_format: "png"`, an English prompt with the same style line, main subject in the lower half; real people only
   from behind, in silhouette or small in the distance (no invented face without a photo).
4. Keep the download URL the tool returns (valid 24 h; 4d needs it) and save the file: `curl -sSf -o episodes/D/opening.png "<url>"`.
5. Open it with Read. Reject and regenerate (max 3 tries) if it has text or letters, warped hands or faces,
   anachronisms, anything gory or offensive, a photo-realistic look, or does not fit the story. For a portrait, also
   compare it with what the sources say about the person (age, beard, clothing of the era).
6. Set `"image": "opening.png"` in the title scene's `data`. No on-screen AI label is shown (Nathan 2026-10-20: the pictures are clearly hand-drawn; AI use is disclosed in the post text, which must keep its AI sentence).
   If a CC BY / CC BY-SA photo was used, add one line before the AI sentence in post.txt:
   `開場畫像依據 Wikimedia Commons 照片改繪（作者：<author>，授權：<licence>）。` (not needed for public domain / CC0).
7. If no picture can be made at all (Image MCP not connected after the retries, generation or download keeps failing,
   or 3 tries still give an unusable picture), STOP: do not build, upload or publish anything. Notify the user with
   which picture failed and the exact error (Nathan 2026-10-20).

## 4c. Chapter images (required: 1–2 more pictures)
Besides the opening image, every video shows 1–2 more AI pictures inside the chapters, at the story's key moments
(for example the place where it happened, the defining object or act, the legacy).
1. Same `create-image` call, rules and checks as 4b step 3 and 5 (style line, "No text, no letters, no logos, no watermarks.",
   no realistic likeness of real people, Read every file, max 3 tries each), but `size: "1536x1024"` (landscape)
   because it is shown in a 560x420 frame. Keep the subject centred; edges get cropped.
2. Save as `episodes/D/img1.png`, `episodes/D/img2.png` (curl the download URL, same as 4b).
3. Put each picture in its own phase of a stack scene, near the line that tells that moment:
   `{"at": N, "until": M, "items": [{"type":"image","src":"img1.png","caption":"<≤ 16 字說明>"}, {"text":"<short line>","style":"mid"}]}`.
   At most one short text item next to it (the frame is ~460 px tall; the visual area is 677 px). Show it for at
   least 2 subtitle lines. Do not put two images in the same scene.
4. Check the sheets (step 5) for overlap or clipping around the pictures. If a chapter picture cannot be made,
   stop exactly as in 4b.7; never publish a video with fewer pictures than required.

## 4d. Opening clip (Calywood image-to-video, 3 s)
Since 2026-10-20 the clip animates opening.png itself (tested 2026-10-20: keeps the drawing and its style; about NT$13).

1. Calywood `generate_video_from_image` with `image_url` = the Image MCP download URL of opening.png (from 4b step 4),
   `duration: 4` (the minimum), `resolution: "720p"`, and a short English `prompt`: slow gentle camera push-in plus one
   or two small natural motions that fit the picture (a lamp flickers, the person blinks or slightly turns the head,
   cloth moves), "Keep the hand-drawn sepia ink-wash style. No text."
   Do not use `generate_video_multimodal`: its results are not copied to the storage bucket below (2026-10-20), so they
   cannot be downloaded here.
2. Poll `get_task` (about every 30 s, up to 10 min; a 4 s clip took about 4 min). The link it returns (volces.com) is
   blocked here; a copy appears a few minutes later at
   `https://storage.googleapis.com/alchemy-dance-media-cacafly-nathan-project/videos/<task_id>.mp4`.
   Retry `curl -sSf -o episodes/D/opening.mp4 "<that url>"` every minute for up to 10 min (403 = not there yet), then
   check it with ffprobe (video stream, at least 3 s; image-to-video keeps the picture's 2:3 shape, about 786x1178, which
   render.py crops to 720x1280).
3. Grab frames at 0.5, 1.5 and 2.5 s with ffmpeg and look at them with Read: same rules as 4b.5 (no text, no warped hands
   or faces, the face must stay the same person, no anachronisms, nothing offensive). Retry with a revised prompt, max 3 tries.
   If image-to-video keeps failing, one last try with text-to-video `generate_video` (prompt starting
   "Vertical 9:16 portrait video.", same scene and style) before stopping.
4. In the title scene's `data` set `"video": "opening.mp4", "video_secs": 3` (keep `"image": "opening.png"`; the clip
   needs it). render.py crops the clip to 720x1280, gives it the same sepia and darkening as the still, plays seconds 0–3 and fades to the still over the last 0.5 s.
5. If the clip cannot be made (Calywood not connected after the usual retries, the task fails, the download keeps
   failing, or 3 tries are all unusable), STOP exactly as in 4b.7 (Nathan 2026-10-20): nothing is built or published,
   and the notification says the opening clip failed, with the exact error.

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

## 10. Report
Only when the run made or fixed something, or failed: send the user one short message listing, per date in the window,
either "already scheduled" or what was made (who/what, title, length, publish time 06:00, both Postiz preview links,
sources, anything dropped or uncertain). Remind them each post can be deleted in Postiz before its 06:00 publish time.
If every date in the window was already covered, finish silently.

## If something fails
Never post a partial or unchecked video. If pushing the media branch is refused, or Postiz cannot fetch the
URL, send the user the video file (SendUserFile, it is under 30 MB) and the post text, and ask them to upload
it in Postiz; when they reply, schedule both posts as in step 8. Report the exact error.
