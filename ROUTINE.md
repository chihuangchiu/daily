# 排程指示：「今天，誰改變了世界」歷史影片預排

這份檔案是兩個排程任務共用的完整指示（Nathan 2026-11-10 起）。排程訊息本身只寫「這次的範圍」，其餘一律照這份檔案做：
- 每週三晚上（週任務）：範圍是「明天（週四）到下週日」，共 11 天。
- 其他每天晚上（每日檢查，週三不跑）：範圍是「未來 3 天」（明天、後天、大後天），只補缺的。
以下用「範圍內的每一天 D」稱呼要確保排好的日子。修改流程時改這份檔案即可（推上 main），兩個排程都會照新版執行。

你負責「今天，誰改變了世界」的每日歷史影片（擁有者：Nathan，台北），共 12 個頻道，六種語言各有 YouTube 與 Facebook：中文 Facebook 粉專「今天，誰改變了世界」與 YouTube「今天 誰改變了世界」；英文 YouTube「Who Changed the World Today」與英文 Facebook 粉專「Who Changed the World Today?」；西班牙文 YouTube 與 Facebook 粉專「¿Quién cambió el mundo hoy?」；葡萄牙文 YouTube 與 Facebook 粉專「Quem mudou o mundo hoje?」；日文 YouTube 與 Facebook 粉專「今日、世界を変えたのは誰」；德文 YouTube 與 Facebook 粉專「Wer hat heute die Welt verändert?」（細節照 RUNBOOK 0c）。執行日期與時間請用 current_time 工具確認（沒有這個工具就用 `TZ=Asia/Taipei date`），時區 Asia/Taipei。

## 目標
確保範圍內每一天 D，12 個頻道都已在 Postiz 排好。某一天某個頻道已有排程，就不再製作那一支。每支影片都以「目標發布日 D」為準（選題、N年前的今天、資料夾、檔名、發布時間），不是執行當天。

## 發布時間（Nathan 2026-11-03，細節照 RUNBOOK 0a）
每個頻道在 D 當天、觀眾當地的早上發布；同一語言的 YouTube 與 Facebook 同一時間：
- 中文 FB＋YT：台北 07:00（UTC 前一天 23:00Z）
- 日文 YT＋FB：東京 07:00（UTC 前一天 22:00Z，即台北 06:00）
- 德文 YT＋FB：柏林 07:00（冬令時間 UTC D 06:00Z，夏令時間 05:00Z）
- 葡萄牙文 YT＋FB：聖保羅 08:00（UTC D 11:00Z）
- 英文 YT＋FB：紐約 08:00（冬令時間 UTC D 13:00Z，夏令時間 12:00Z）
- 西班牙文 YT＋FB：墨西哥城 08:00（UTC D 14:00Z）
確切的 UTC 時間一律用 `python3 pipeline/tools/slots.py D1 D2 …`（範圍內每一天都列上）算，把印出的時間當作 integrationSchedulePostTool 的 date。排程時若該時間已過，改用現在加 10 分鐘。

## 每支影片的規格
直式 720x1280、約 120 秒（最終 112–128 秒）、旁白與字幕都用該頻道的語言；開場先播 Calywood 做成的 5 秒動態片段（人物有真實、自然的動作，最後一格就是開場圖），接著無縫接到開場圖本身（人物在時代場景中、正面、長相依真實照片），章節裡再放 4–5 張 Image MCP 示意圖（每一章至少一張；RUNBOOK 4b、4c、4d、4e）。同一語言的 YouTube 與 Facebook 用同一支影片。

## 旁白語音：Gemini TTS（細節照 RUNBOOK 0b「Narration voice: Gemini TTS」）
- 六種語言都用 Gemini_TTS 的 generate_speech：voice Kore、model gemini-2.5-flash-tts、format wav、language 依 plan.json（cmn-tw／en-US／es-ES／pt-BR／ja-JP／de-DE）。
- 流程：`python3 pipeline/narrate.py EP --gemini-plan` 產生 EP/tts/plan.json → 每一段呼叫 generate_speech（text、style、language、voice、model、format 照 plan.json；外語可用 RUNBOOK 0b 記錄的短 style），用 `curl -sSf -o EP/tts/<id>.wav` 下載（各段可一次送出多個呼叫）→ 逐段檢查（見下）→ `python3 pipeline/narrate.py EP --gemini` → `rm -rf EP/check` 後 `python3 pipeline/render.py EP sheet` 檢查 → `pipeline/build.sh EP video`。
- 語氣：第一句鉤子用和後面一樣明快的語速、帶真心的驚訝與讚嘆；之後明快緊湊的說書語調。絕不事後把音檔加速（不要 atempo、不要調 speed）。
- 長度只靠稿子長短：--gemini 印出的長度不在 112–128 秒就刪或補句子，改完重跑 --gemini-plan，只重新合成文字有變的段落（比對 text），再跑 --gemini。各語言合適的字數看 RUNBOOK 0b 最新的實測紀錄。
- Gemini 出錯檢查：每支都跑 `python3 pipeline/tools/gemini_check.py EP <lang>`（sherpa-onnx Whisper base 模型放在 /home/claude/models/sherpa-onnx-whisper-base，沒有就從 k2-fsa 的 asr-models release 下載 sherpa-onnx-whisper-base.tar.bz2），標 <<< 或 SLOW 的段落用 `pipeline/tools/halves.sh <lang> EP/tts/<id>.wav` 檢查前後半（halves.sh 需要 /tmp/claude-0/s/asr1.py，見 RUNBOOK 0b），有重複、念出 style 或多加字就重新合成；同一段失敗兩次，就把那句和前後句用逗號接成一段。人名或數字念錯就改寫該句重合成。
- spoken 欄位寫正確的字（數字可用該語言的文字或中文數字），不要用同音字技巧。
- 備案：Gemini TTS 試了 3 次、間隔合計超過 5 分鐘仍找不到，或某段重試 3 次仍失敗，那一支改用本機語音（`pipeline/build.sh EP check`，語速 0.92–1.10），照常排程，並在完成訊息註明「這支用本機語音」。

## 開頭鉤子與畫面文字（細節照 RUNBOOK 0b）
- title 場景第 0 行旁白是鉤子：這個人最驚人或最動人的一件事（中文 16 字內、英文 10 個字內）。鉤子那一行不顯示字幕（render.py 自動處理），sheet_00 第 0 格只有鉤子大字與畫面。
- 第 1 行旁白念頻道名稱和日期：中「今天，誰改變了世界？M月D日。」（spoken 用中文數字）；英 "Who changed the world today? <Month D>."；西 "¿Quién cambió el mundo hoy? D de <mes>."；葡 "Quem mudou o mundo hoje? D de <mês>."；日「今日、世界を変えたのは誰？M月D日。」；德 "Wer hat heute die Welt verändert? Der D. <Monat>."
- title 的 data 加 "hook"（1–2 行、用 \n 分行；中日文每行 10 字內、西方語言每行約 22 字元內）；title 只需要日期、sub（年份）與 name。
- 畫面文字精簡：每個 phase 最多 2 個文字項目；不重複字幕那句話；不放頁尾出處行。字幕：西方語言每行約 55 字元內、中日文每個逗號分段 14 字內（日文一行最多約 28 字，中間要有「、」；『…』書名前加「、」避免在書名中間斷行）。畫面文字不要用 \n（只有 hook 支援）。
- 問題 phase 照 RUNBOOK 0b：兩列顯示完整的問題，和字幕同一句話。

## 片尾
end 場景旁白依序：
1. 兩行合成一句、念出頻道名稱（第一行以逗號結尾）：中「這裡是「今天，誰改變了世界」，」＋「M月D日，我們記得某某。」（spoken 不要「」）；英 "This is Who Changed the World Today," ＋ "and on <Month D>, we remember <name>."；西 "Esto es Quién cambió el mundo hoy," ＋ "y este D de <mes>, recordamos a <name>."；葡 "Aqui é Quem mudou o mundo hoje," ＋ "e neste D de <mês>, lembramos de <name>."；日「こちらは『今日、世界を変えたのは誰』、」＋「M月D日、<name>を思い出します。」；德 "Das ist Wer hat heute die Welt verändert," ＋ "und am D. <Monat> erinnern wir an <name>."
2. 訂閱分享明天見：中「喜歡這個故事，記得追蹤訂閱、分享給朋友，我們明天見！」；英 "If you enjoyed this story, subscribe and share. See you tomorrow!"；西 "Si te gustó, suscríbete y compártela. ¡Nos vemos mañana!"；葡 "Se gostou, inscreva-se e compartilhe. Até amanhã!"；日「気に入ったら、チャンネル登録と共有を。また明日！」；德 "Wenn's dir gefällt, abonniere und teile. Bis morgen!"
這些都算進 112–128 秒；放不下時先刪支線內容，真的放不下才省略訂閱分享句並在完成訊息說明。畫面不另加文字或圖示。

## 人物與共用
- 中文版選題：優先台灣歷史，其次影響世界的偉人（RUNBOOK 第 2 步的規則）。
- 英文版：中文主角不是台灣人 → 共用同一位人物；中文主角是台灣人 → 從全世界另選一位在 D 的月日出生、過世或做出關鍵事蹟、對世界有正面影響、全球觀眾認得的人物（兩個來源查證；不可重複 covered-en.md 一年內的人物，也不可和範圍內任何頻道已排定的人物重複）。
- 西、葡、日、德文版：人物和故事一律和同一天的英文版相同，翻寫成該語言的自然說法，事實、日期、數字不增不減。
- 同一位人物的圖片與開場片段（opening.png、start.png、img1–img5.png、opening.mp4）所有語言共用，不另外產圖、不另花 Calywood。圖片不存在 git，所以同一個 D 要在同一次執行裡依序做完：中文 → 英文 → 西 → 葡 → 日 → 德；若圖片已不在，就照 4b–4e 重做一次再給所有語言用。
- 選題盡量換領域：避免連續同一領域（看 covered.md 最近幾集，也看範圍內這次已選的人物），輪換科學、醫學、人權、探險、文學、音樂、科技、法治民主等領域。
- Calywood 拒絕：「偵測為含真人臉部」→ 開場圖照 RUNBOOK「Calywood refusals」改畫成更明顯的手繪；同一位現代名人連續 3 次「copyright restrictions」→ 改選另一位人物（以約 1980 年前過世、非當代名人為佳）。

## 各語言的程式與寫法（細節照 RUNBOOK 第 0b、0c、E、S、P/J/D 節；範本是 episodes 裡最近一天的 D、D-en、-es、-pt、-ja、-de）
- 資料夾 episodes/D（中文）、D-en、D-es、D-pt、D-ja、D-de；episode.json 的 "lang" 分別是 zh、en、es、pt、ja、de。
- 每行一個完整子句。spoken 欄位年份寫成該語言的文字（英德葡西），日文 spoken 可用漢字數字。長名字的 name 只放姓，全名放 name_years；外語版不要 seal。所有畫面文字都要翻譯。
- 只改字幕、不改 spoken 時，可直接改 episode.json 與 timeline.json 裡對應那行的 text。
- 外語版可以寫一個小工具：以中文版 episode.json 為骨架、維持每個場景的行數與 phase 結構，換掉 lines、chapter、畫面文字與 hook，並把共用圖片連結過去（RUNBOOK 0b 記過 mk.py、subfix.py、post.py、dl.sh 的做法）。
- post.txt：中文「標題：」、英文「Title:」、西文「Título:」、葡文「Título:」、日文「タイトル：」、德文「Titel:」開頭，空一行後是文章，再加該語言的「歡迎留言分享答案」句、照片出處句（用了 Commons 照片時）與 AI 說明句（照 RUNBOOK），最後一行 hashtag：中 #歷史上的今天 #今天誰改變了世界；英 #OnThisDay #WhoChangedTheWorldToday；西 #UnDíaComoHoy #QuiénCambióElMundoHoy；葡 #UmDiaComoHoje #QuemMudouOMundoHoje；日 #今日は何の日 #今日世界を変えたのは誰；德 #AnDiesemTag #WerHatHeuteDieWeltVerändert。標題前半句就放人名或熟悉的關鍵字，盡量 50 字元內。中文文末固定加「本片旁白為AI合成語音，影片由AI協作製作。內容如有錯誤，歡迎留言指正。」

## 工具連線（開始前先做）
- Postiz（My_Postiz）、Image MCP（Image_MCP）、Calywood 與 Gemini TTS（Gemini_TTS）的工具剛開始時可能還在連線中。開始時用 ToolSearch 搜尋「+My_Postiz posts」、「+Image_MCP create」、「+Calywood generate」與「+Gemini_TTS generate」；找不到就先做不需要它們的步驟，每做完一大步再搜尋一次，也可以呼叫 RefreshMcpTools。
- 只有在需要用到該工具時試了至少 3 次、間隔合計超過 5 分鐘仍然找不到，才算失敗。Postiz 連不上就不製作任何影片，直接通知 Nathan「Postiz 沒連上，今晚無法預排」，並提醒他可能需要到 Customize → Connectors 重新連線。Image MCP 或 Calywood 失敗：照下面「產圖或片段失敗就停止」（若工具在這個排程裡載不到、但 connector 已連線，提醒他到排程設定把該 connector 加進去）。Gemini TTS 失敗：照旁白語音的備案。
- 背景執行的程式在回覆結束後可能被停掉，build.sh 等長時間步驟請在前景執行（timeout 設到 600000 毫秒，一次指令只 build 一支，一支約 4–6 分鐘）。

## 步驟
1. 取得 repo chihuangchiu/daily：若尚未在工作階段中，呼叫 add_repo（owner chihuangchiu、repo daily、access push），clone 到 /home/claude/daily；已存在就 git pull（若在 detached HEAD，先 git checkout main；git pull 可能較慢，timeout 設長一點）。`pip install --break-system-packages -r requirements.txt`。
2. 閱讀 RUNBOOK.md 與 TEMPLATES.md（第 0a、0b、0c、4e 節優先於舊的時間、長度與模型設定）。做 RUNBOOK 第 0 步「Plan the run」：用 slots.py 算出範圍內每一天各頻道的 UTC 發布時間；用 Postiz postsListTool 從第一個 D 的前一天 15:00:00Z 查到最後一個 D 的 18:00:00Z（範圍長時可分段查；結果很長時會存成檔案，用 jq 依 publishDate 與 integrationId 整理）。某頻道的貼文 publishDate 落在 [D 前一天 15:00Z, D 18:00Z) 之間，就算那個頻道的 D 已排好。state 為 DRAFT 的草稿不算已排好，但若某頻道同時有草稿，回報時要提到。每個語言分開判斷：YouTube 與 Facebook 都有就不做；只有一個就只補另一個（沿用已上傳的影片：從已排好那則貼文的附件，或用 mediaListTool 找到那次上傳的 mp4、抽畫面確認頁首語言與 MM.DD；文章用 episodes/D…/post.txt，不重做影片）；都沒有就製作該語言影片。
3. 缺片的日子從最早的 D 開始，同一個 D 依序做 中文 → 英文 → 西 → 葡 → 日 → 德，每支完整做完 RUNBOOK 第 1 到第 9 步（含 4b–4e）並排程成功後，才開始下一支。不可重複 covered 檔一年內的人物，也不可和範圍內已排定或這次已選的人物重複。每個日期、數字、名稱都用兩個可靠來源查證。Calywood 片段要等幾分鐘，開場圖與起始圖一做好就先送出片段，再去做章節圖（章節圖之間可以一次送出多個 create-image）。
4. 避免和另一個排程撞車（週任務可能跑很久，隔天晚上的每日檢查會同時開始）：
   - 選某一天的人物之前先 `git pull`，看最新的 covered 檔。
   - 每一種語言上傳到 media 分支之前，再用 postsListTool 查一次那一天那個語言的兩個頻道；若已經有排程（另一個排程剛排好），就不要上傳、不要排程、不要記 covered，直接做下一支。
   - media 分支上若已有別的 mp4（另一個排程正在用），等 2 分鐘再看，最多等 10 分鐘；推送前一律先 git pull 該分支。
5. 範圍內所有頻道都已經排好、沒有任何需要做的事：不發任何通知，也不要用 SendUserMessage，直接結束。

## 長度
- 中文：約 7 個場景、約 40 行：鉤子＋開場 → 4 章 → 今天的影響＋一個問題 → 片尾；用 Gemini 時 spoken 約 420–440 字（不含標點）。其他語言照 RUNBOOK 0b 記錄的字數。寧可刪支線也不要加速。
- narrate.py --gemini 印出的長度要在 112–128 秒；build.sh video 後用 ffprobe 再確認，達到或超過 180 秒絕不發布。

## 影片畫面
- 每一格左上角的頁首是該頻道名稱、右上角是 D 的 MM.DD，由 render.py 依 lang 自動處理。用 Read 檢查 sheet 時順便確認頁首文字。
- 圖片與片段上不顯示「AI 生成示意圖」標示；章節圖的 caption 不寫「示意」之類的字。貼文文末的 AI 說明照常保留。

## 圖片與開場片段（必要，細節照 RUNBOOK 4b、4c、4d、4e 與「One tone」）
- 開場圖（4b）：時代場景（地點、物件、光線），人物正面朝向觀眾、腰部以上，長相要是真實的那個人。先在 Wikimedia Commons 找照片（WebSearch 加 allowed_domains commons.wikimedia.org；公有領域、CC0、CC BY、CC BY-SA 都可以；在世人物一律不用照片），記下檔案頁網址、作者與授權。用 Image MCP edit-image，image 用 `https://commons.wikimedia.org/wiki/Special:FilePath/<檔名>?width=800`（不行就去掉 ?width 或換檔名），size 1024x1536、quality high，prompt 照 RUNBOOK 4b 第 2 步，並加上「Calywood refusals」的手繪字句（cross-hatching、old printed history book）。找不到可用照片或 edit-image 一直失敗時，才改用 create-image 畫同樣的場景，但人物只畫背影、剪影或遠景。存成 episodes/D/opening.png，保留下載網址（24 小時有效）。title data 加 "image": "opening.png" 和 "image_shift"（臉的中心高度比例 f，image_shift = 0.60 − f，0–0.4）。用了 CC BY／CC BY-SA 照片時，post.txt 加照片出處（作者、授權）。
- 色調一致：每個圖片 prompt 結尾一字不差加上 STYLE：「Style: warm sepia ink-wash illustration with fine pencil lines, soft paper texture, cream and brown palette with small touches of deep red. Hand-drawn look, not photographic. No text, no letters, no logos, no watermarks.」；prompt 裡不寫其他顏色字。圖都做好後用 ffmpeg 並排成一張，用 Read 看，不一致的重做。
- 開場片段（4d、4e）：5 秒，最後一格就是開場圖，要有真實、自然的動作。
  1. 起始圖：edit-image，image 用開場圖的下載網址，size 1024x1536、quality high，prompt：「Show this exact same scene a few seconds earlier, as the first frame of a short film that ends on this picture. Keep everything identical: the same <地點>, <物件>, the same person with the same face, hair and clothes, the same camera position, zoom and framing, the same drawing style and colours. Change only his/her pose: <早幾秒的一個明確動作>.」再加 STYLE。姿勢改變不要太大（例如頭低下看著手邊的東西），大幅轉身容易出現交叉溶接。存成 start.png，和開場圖並排檢查（最多 3 次）。
  2. Calywood generate_video_from_image，**model 一律用 "minimax"**（Nathan 2026-11-10；MiniMax H3，5 秒 720p NT$15，送出時鎖價、失敗不收費）：image_url 用起始圖的下載網址，last_frame_url 用開場圖的下載網址，duration 5、resolution 720p；英文 prompt（MiniMax 必填）描述從起始姿勢到最後姿勢的自然動作，加一兩個背景小動作，結尾寫「Natural, realistic body motion; the camera stays almost still. Silent, no music. Keep the hand-drawn sepia ink-wash style and colours exactly as in the images. No text.」。不要以鏡頭推近為主要動作；不要寫 blink。不要用 generate_video 或 generate_video_multimodal。
  3. 用 get_task 每 30 秒查一次（最多等 10 分鐘）。下載用 get_task 回傳的影片連結；工作區連不到那個網址時，改用 `https://storage.googleapis.com/alchemy-dance-media-cacafly-nathan-project/videos/<task_id>.mp4`（403 代表還沒好，每分鐘試一次，最多 10 分鐘；下載迴圈在單次指令裡跑完，timeout 設 600000 毫秒）。存成 opening.mp4，ffprobe 確認至少 4.9 秒，抽 1.0、2.5、4.0 秒與最後一格和開場圖並排檢查（同一個人、動作自然、色調一致、最後一格和開場圖相同）。不合格或失敗就修改 prompt 重送（同一人物 MiniMax 最多 3 次；「copyright restrictions」直接重送）。MiniMax 3 次都不行，才不帶 model（預設 Seedance）再試一次，並在完成訊息註明。
  4. title data 加 "video": "opening.mp4", "video_secs": 5, "video_align": "end"（保留 image 與 image_shift）。
- 章節示意圖 4–5 張（4c）：create-image，size 1536x1024、quality high、png，prompt 結尾加 STYLE；畫故事的關鍵時刻、地點、物件，四章每章至少一張，「今天的影響」可再放一張。人物出現時只用背影或遠景（膚色、髮型符合真實人物）。存成 img1.png … img5.png，各放在 stack 場景自己的一個 phase：{type:"image", src, caption}（中文 16 字內、外語約 32 字元內），旁邊最多一行短文字，每張至少停留 2 行字幕。
- 下載網址用 curl 存檔，再用 Read 逐張檢查：不得有文字、扭曲的手或臉、臉和照片不像、像照片的寫實感、色調不一致、時代錯置或不當內容（16 世紀的儀器不要畫成望遠鏡之類），不合格就重產（每張最多 3 次）。
- 產圖或片段失敗就停止（Nathan 2026-10-20）：某一位人物的開場圖、起始圖、開場片段做不出來，或章節圖做不到至少 4 張（「用照片畫臉」做不到不算失敗，改用背影版即可；現代名人因 copyright 被拒時可先換人一次），用到這位人物的影片就不製作、不上傳、不排程、不記 covered，而且整次執行停在這裡；已經排好的保留。立刻用 PushNotification 通知 Nathan（內容用 <routine_summary> 包起來），第一句寫「M/D 的歷史影片因產圖失敗而停止，沒有排程」（起始圖或片段失敗就寫「因開場片段失敗」），接著寫哪一項失敗、確切錯誤訊息、已選好的人物與題目，以及範圍內各天哪些頻道已排好；若是工具沒連上，提醒他到 Customize → Connectors 重新連線。

## 重要設定（repo 讀不到時以此為準）
- Postiz integrationId：中文 Facebook cmvbzqyvs0002s67fq0dzr53e；中文 YouTube cmvc7njup0001s673xhqhp5s8；英文 YouTube cmvibixcp000ms67kkplrbxb1；英文 Facebook cmw7yoef70051s67z38jq1cr5；西班牙文 YouTube cmvic8oq3000os67kdsemvo3t；西班牙文 Facebook cmw7zc3i40056s67z3tox2dbw；葡萄牙文 YouTube cmviqybpp000ws67knh5z6wzo；葡萄牙文 Facebook cmw9c60vf0084s67z864vjqtb；日文 YouTube cmvir44qg000zs67kevg8s72x；日文 Facebook cmw7y6kw8004qs67z17nk77rm；德文 YouTube cmvir7imd0011s67ky3vmkijj；德文 Facebook cmw9cakfg0089s67zdx0fzndb。
- 上傳與排程：每個語言的影片只上傳一次，然後用一次 integrationSchedulePostTool 呼叫排 YouTube 與 Facebook 兩則（同一時間、同一個影片路徑）。media 分支檔名 D.mp4、D-en.mp4、D-es.mp4、D-pt.mp4、D-ja.mp4、D-de.mp4。
- Facebook（六種語言都相同格式）：content 第一行是影片標題（post.txt 第一行去掉「標題：」等前綴），空一行後是文章；純文字（hashtag 行不加 #Shorts）；每行包成 <p>…</p>，空行 <p></p>，HTML 跳脫。settings：post_type=post、title=影片標題。
- YouTube：content 只放文章（不含標題行），hashtag 行最前面加 #Shorts；settings：title=影片標題 + " #Shorts"（100 字內）、type=public、selfDeclaredMadeForKids=no、tags 5–6 個：Shorts、該語言的「歷史上的今天」與頻道名（中：歷史上的今天、今天誰改變了世界；英：On This Day、Who Changed the World Today；西：Un día como hoy、Quién cambió el mundo hoy；葡：Um dia como hoje、Quem mudou o mundo hoje；日：今日は何の日、今日世界を変えたのは誰；德：An diesem Tag、Wer hat heute die Welt verändert）、人物名、1–2 個主題。
- 排程後用 postsListTool 確認每則都在、時間與頻道正確；若一次呼叫只成功一則，先查清單再補缺的那一則，不要重複排。
- 上傳方式：把影片放到 chihuangchiu/daily 的暫存分支 media（分支上只多這一個 mp4），用 `https://raw.githubusercontent.com/chihuangchiu/daily/media/<檔名>` 給 Postiz uploadFromUrlTool，成功後立刻讓 media 分支回到只剩 README.md，再做下一支。用一般 push：`git clone --depth 1 -b media https://github.com/chihuangchiu/daily.git` 到暫存資料夾，加入 mp4 後 commit、`git push origin media`；上傳完 `git rm` 該 mp4、commit、`git push origin media`。Nathan 已於 2026-10-17 同意這樣短暫公開影片。上傳後若又重做影片，要重新推送並重新上傳。
- 每個語言的 YT 與 FB 都排好後，記進對應的 covered.md、covered-en.md、covered-es.md、covered-pt.md、covered-ja.md、covered-de.md，連同 episode.json、post.txt 推上 main（不要提交 mp4、wav、png 或 check 檔）。結束前把這次的實測字數與長度補進 RUNBOOK 0b。
- 已排程的貼文若要換影片：有 deleteUnpublishedPost 就刪掉舊的再排新的；沒有就把新版排成草稿（type draft），請 Nathan 刪舊的、把草稿改成排程，絕不讓同一頻道同一天有兩則排程中的貼文。

## 安全原則
沒通過 RUNBOOK 檢查的影片絕不排程。產圖或片段失敗照上面停止。其他步驟失敗（包括上傳到 media 分支被拒、Postiz 抓不到檔），那一支就用 SendUserFile 把影片（status: proactive）和 post.txt 傳給 Nathan，說明原因，請他在 Postiz 上傳後回覆，再由你排程；這次執行停在這裡。（例外：某一種語言的語音做不出來時只跳過那個語言。）

## 完成後
只要這次有製作或補排任何東西，就用 SendUserMessage 傳一則簡短中文訊息給 Nathan，逐日列出範圍內每一天的狀態，按語言分開寫（中文 FB＋YT、日 YT＋FB、德 YT＋FB、葡 YT＋FB、英 YT＋FB、西 YT＋FB，各附當地發布時間與台北時間）。原本就排好的日子一行帶過；這次新做或補排的寫：人物、鉤子那一句、標題、長度、每個頻道的 Postiz 預覽連結；每位人物附 Calywood 花費與用的模型（MiniMax，或改用 Seedance 的原因）、英文是「共用中文版人物」還是「另選世界人物」、開場圖是「照片當臉部參考」還是「背影版」（用了照片就附 Commons 檔案頁與授權）、開場片段的動作、章節圖幾張（各畫什麼）、主要來源、刪掉或不確定的內容；哪幾支用 Gemini 語音、哪幾支改用本機語音；片尾訂閱分享句若因長度省略也要寫。範圍很長時，每做完一整天（6 種語言）就先用 SendUserMessage 傳那一天的結果，最後再傳一則總結。最後提醒他每則貼文在發布前都可以到 Postiz 刪除。若這次沒做完整個範圍（時間不夠或執行中斷），總結裡寫明還缺哪幾天，那些會由之後每晚的檢查補上。
