# Daily run: 「今天，誰改變了世界」

Every morning one ~4-minute vertical video about a person or event tied to today's date,
posted to the Facebook page 「今天，誰改變了世界」 at 20:00 Taiwan time.

Fixed facts
- Repo: chihuangchiu/daily (public). Video files are never committed to main; they pass briefly through the `media` branch (step 8).
- Postiz integration: id `cmvbzqyvs0002s67fq0dzr53e`, name 「今天，誰改變了世界」, platform facebook.
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
- Traditional Chinese, Taiwan usage. ~950–1050 characters of narration, 10–11 scenes, ~75–90 lines.
- Shape: opening hook (title template, ~6 lines, ends with the name) → 7–8 chapters (timeline, document,
  tiles, stack…) → legacy today → one question for the viewer → end scene.
- Spoken text: Chinese numerals, no Latin letters/digits. Subtitle text may use digits.
- Pronunciation: check names and polyphones with
  `python3 -c "import sys;sys.path.insert(0,'pipeline');from tts import BakerProcessor as B;p=B(data_dir=None,loaded_mapper_path='pipeline/models/baker_mapper.json');print(p.text_to_phone('要檢查的句子'))"`
  and, if a reading is wrong, rewrite only the spoken field (homophone characters are fine).

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
Expect `video.mp4`, 720x1280, 225–250 s, under 40 MB. Grab 3 frames with ffmpeg and look at them.

## 7. Write `episodes/YYYY-MM-DD/post.txt`
First line `標題：<title>` (≤ 40 chars, hook + name). Then the article: the narration rewritten as
readable paragraphs, plain text only (no #, **, --- or other markdown), then
`歡迎在留言分享你的答案。`, then `本片旁白為AI合成語音，影片由AI協作製作。內容如有錯誤，歡迎留言指正。`,
then 6–10 hashtags on one line, always including #歷史上的今天 #今天誰改變了世界.

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
1. Postiz `uploadFromUrlTool` with `https://raw.githubusercontent.com/chihuangchiu/daily/media/D.mp4` → `{id, path}`.
2. Clear the branch right away: commit only README.md on a fresh orphan `media` and `git push -f origin media`.
3. Postiz `integrationSchedulePostTool`:
   type `schedule`, date `D T12:00:00Z` (20:00 Taipei; if that has passed, now + 15 min),
   integrationId above, isPremium false, shortLink false,
   content = the article with every line wrapped in `<p>…</p>` (blank lines become `<p></p>`, HTML-escape the text),
   attachments `[path]`, settings `[{key:"post_type", value:"post"}, {key:"title", value:<title>}]`.
4. Confirm with Postiz `postsListTool` that the post is listed for the right time and channel.

## 9. Record
Append `| D | person | event |` to `covered.md`; commit `episodes/D/episode.json`, `episodes/D/post.txt`,
`covered.md` (never the mp4/wav/check files; .gitignore covers them) and push to main.

## 10. Report
Send the user one short message: who/what, title, scheduled time, Postiz preview link, sources,
and anything dropped or uncertain. Remind them they can delete it in Postiz before 20:00.

## If something fails
Never post a partial or unchecked video. If pushing the media branch is refused, or Postiz cannot fetch the
URL, send the user the video file (SendUserFile, it is under 30 MB) and the post text, and ask them to upload
it in Postiz; when they reply, schedule the post as in step 8. Report the exact error.
