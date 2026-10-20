# Daily run: 「今天，誰改變了世界」

Every morning (run starts ~06:00 Taiwan time) one vertical video of just under 3 minutes (so YouTube treats it as a Short) about a person or event tied to
today's date, posted at 07:00 Taiwan time to both the Facebook page 「今天，誰改變了世界」 and the YouTube channel 「今天 誰改變了世界」.

Fixed facts
- Repo: chihuangchiu/daily (public). Video files are never committed to main; they pass briefly through the `media` branch (step 8).
- Postiz integrations:
  - Facebook: id `cmvbzqyvs0002s67fq0dzr53e`, name 「今天，誰改變了世界」.
  - YouTube: id `cmvc7njup0001s673xhqhp5s8`, name 「今天 誰改變了世界」.
- Timezone: Asia/Taipei. "Today" = the Taipei date at run time (get it from the current-time tool).

## 1. Setup
```
git clone https://github.com/chihuangchiu/daily && cd daily        # skip if already present; then git pull
pip install --break-system-packages -q -r requirements.txt
which ffmpeg && fc-list | grep -q "Noto Serif CJK" && echo ok
```

## 2. Choose today's subject
Search the web for today's month/day ("M月D日 歷史上的今天", "M月D日 台灣歷史", "On this day <Month D>").
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

## 4b. Opening image (required)
Every video opens on at least one AI-generated picture, made with the Image MCP:
1. `create-image` with `size: "1024x1536"`, `quality: "high"`, `output_format: "png"`. Prompt in English:
   vertical composition; main subject in the lower half (the title sits over the upper half);
   style "warm sepia ink-wash illustration, soft paper texture, cream and brown palette with small touches of deep red";
   always end with "No text, no letters, no logos, no watermarks."
2. Real people: never attempt a realistic portrait or likeness of a real, identifiable person. Show the place,
   era, objects or event, or the person from behind, in silhouette, or small in the distance.
3. The tool returns a download URL (valid 24 h). Save it: `curl -sSf -o episodes/D/opening.png "<url>"`.
4. Open it with Read. Reject and regenerate (max 3 tries) if it has text or letters, warped hands or faces,
   anachronisms, anything gory or offensive, or does not fit the story.
5. Set `"image": "opening.png"` in the title scene's `data`. The on-screen label `AI 生成示意圖` is added automatically; keep it.
6. If any picture cannot be made (Image MCP not connected after the retries, generation or download keeps failing,
   or 3 tries still give an unusable picture), STOP: do not build, upload or publish anything. Notify the user with
   which picture failed and the exact error (Nathan 2026-10-20).

## 4c. Chapter images (required: 1–2 more pictures)
Besides the opening image, every video shows 1–2 more AI pictures inside the chapters, at the story's key moments
(for example the place where it happened, the defining object or act, the legacy).
1. Same `create-image` call, rules and checks as 4b (style line, "No text, no letters, no logos, no watermarks.",
   no realistic likeness of real people, Read every file, max 3 tries each), but `size: "1536x1024"` (landscape)
   because it is shown in a 560x420 frame. Keep the subject centred; edges get cropped.
2. Save as `episodes/D/img1.png`, `episodes/D/img2.png` (curl the download URL, same as 4b).
3. Put each picture in its own phase of a stack scene, near the line that tells that moment:
   `{"at": N, "until": M, "items": [{"type":"image","src":"img1.png","caption":"<≤ 16 字說明>"}, {"text":"<short line>","style":"mid"}]}`.
   At most one short text item next to it (the frame is ~460 px tall; the visual area is 677 px). Show it for at
   least 2 subtitle lines. Do not put two images in the same scene.
4. Check the sheets (step 5) for overlap or clipping around the pictures. If a chapter picture cannot be made,
   stop exactly as in 4b.6; never publish a video with fewer pictures than required.

## 4d. Opening clip (Calywood, 3 s)
STATUS: NOT ACTIVE YET. The clip download host (storage.googleapis.com) is blocked by this environment's network
allowlist. Skip 4d entirely until Nathan has allowed that domain and this STATUS line has been removed.

When active, the opening is a 3-second AI clip that plays full-screen under the title, then cross-fades to opening.png:
1. Calywood `generate_video` with `duration: 4` (the minimum), `resolution: "720p"`, and an English prompt built from the
   opening image prompt: same scene, era and style ("warm sepia ink-wash illustration, soft paper texture, cream and brown
   palette with small touches of deep red"), vertical 9:16 framing, slow gentle camera move or small natural motion,
   main subject in the lower half, no realistic likeness or identifiable face of a real person, "No text, no letters,
   no logos, no watermarks." Calywood is text-to-video only: it cannot animate opening.png itself.
2. Poll `get_task` (about every 20 s, up to 10 min) until it succeeds; save the video link with
   `curl -sSf -o episodes/D/opening.mp4 "<url>"` and check it with ffprobe (has a video stream, at least 3 s).
3. Grab frames at 0.5, 1.5 and 2.5 s with ffmpeg and look at them with Read: same rules as 4b.4 (no text, no warped hands
   or faces, no anachronisms, nothing offensive). Retry with a revised prompt, max 3 tries.
4. In the title scene's `data` set `"video": "opening.mp4", "video_secs": 3` (keep `"image": "opening.png"`; the clip
   needs it). render.py crops the clip to 720x1280, gives it the same sepia and darkening as the still, keeps the
   `AI 生成示意圖` label, plays seconds 0–3 and fades to the still over the last 0.5 s.
5. If the clip cannot be made (Calywood not connected after the usual retries, the task fails, the download keeps
   failing, or 3 tries are all unusable), STOP exactly as in 4b.6 (Nathan 2026-10-20): nothing is built or published,
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
   date = 07:00 Taipei on D = `(D minus 1 day)T23:00:00Z` (if that has passed, now + 10 min),
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
Append `| D | person | event |` to `covered.md`; commit `episodes/D/episode.json`, `episodes/D/post.txt`,
`covered.md` (never the mp4/wav/check files; .gitignore covers them) and push to main.

## 10. Report
Send the user one short message: who/what, title, scheduled time, both Postiz preview links (Facebook and YouTube), sources,
and anything dropped or uncertain. Remind them they can delete it in Postiz before 07:00.

## If something fails
Never post a partial or unchecked video. If pushing the media branch is refused, or Postiz cannot fetch the
URL, send the user the video file (SendUserFile, it is under 30 MB) and the post text, and ask them to upload
it in Postiz; when they reply, schedule both posts as in step 8. Report the exact error.
