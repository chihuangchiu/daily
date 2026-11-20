# 排程指示：卡卡夫人占星館「今日星座運勢」每日影片

Nathan 2026-11-19 設定。排程任務每天台北時間 04:49 開始，做好當天（D = 執行當天的台北日期）的影片，
在台北 06:00 發到 Facebook 粉專「卡卡夫人占星館」（facebook.com/zodiac.signs.zh）。
修改流程時改這份檔案（推上 main），排程會照最新版執行。

影片結構（約 85–90 秒，直式 1080×1920）：
1. 開場約 15 秒：真人版卡卡夫人（Calywood 對嘴影片）打招呼、聊天氣、問一個互動問題，最後說「今天月亮在X座，十二星座運勢，從第十二名倒數！」。她的動作和手上的道具每天換（見 2 的 `open_scene`），不一定拿水晶球。畫面只有字幕（胸前道具的正下方）、左邊直式日期牌、右邊直式「卡卡夫人」名牌，不放資訊框，也不放頂部標題條。
2. 十二星座第 12 名到第 1 名的圖卡：名次、星座圖、一句提醒（兩短句）、愛情／事業／財運星星、幸運色、幸運數字，旁白一句話。
3. 開運推薦兩張卡：第一張吃的，第二張依星期輪換（見 4c）。
4. 結尾約 6 秒：固定的卡卡夫人道別片段（assets/outro，每天重複用，不必再做），疊上今日前三名與追蹤提示。

程式都在 zodiac/pipeline/：`sky.py`（星象＋建議排名）、`build.py`（plan：列出要合成的旁白；video：做影片）。
範本：zodiac/episodes/2026-11-19/episode.json（第一集）。

## 0. 準備
1. 用 current_time 工具確認現在時間（Asia/Taipei），D = 今天的日期（YYYY-MM-DD）。EP = zodiac/episodes/D。
2. repo 在 /home/claude/daily（排程訊息會交代如何取得）。`pip install --break-system-packages -q ephem`（numpy、scipy、pillow 通常已有，缺了就裝）。
3. 用 ToolSearch 一次載入要用的工具：Gemini_TTS 的 generate_speech；Image_MCP 的 create-image；Calywood 的 generate_video_multimodal、get_task；My_Postiz 的 postsListTool、uploadFromUrlTool、integrationSchedulePostTool；以及 WebFetch。工具剛開始可能還在連線，找不到就隔一兩分鐘再搜，或呼叫 RefreshMcpTools。試 3 次、間隔合計超過 5 分鐘仍缺 Gemini_TTS 或 My_Postiz，就照第 9 節通知並停止。
4. 防重複：postsListTool 查 (D 前一天)T20:00:00 到 DT06:00:00（UTC），只看 integrationId `cmwmx1fgl0074s680z7fug2uf`。已經有 D 的貼文（QUEUE 或 PUBLISHED）就什麼都不做、不通知，直接結束。

## 1. 星象與天氣
1. `python3 zodiac/pipeline/sky.py D --json EP/sky.json`：印出月亮星座（含當天是否換座）、月相、太陽、逆行、緊密相位，以及建議排名與星星分數。
2. 天氣（台北）：先用 WebFetch 讀
   https://api.open-meteo.com/v1/forecast?latitude=25.03&longitude=121.56&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&timezone=Asia%2FTaipei&forecast_days=1
   取當天最高、最低溫（°C）、降雨機率、天氣代碼（0 晴、1–3 多雲、45/48 霧、51–57 毛毛雨、61–67 雨、80–82 陣雨、95+ 雷雨）。讀不到就用 WebSearch「台北 今天 天氣」找中央氣象署或可靠來源；都失敗就開場不提溫度，只說季節性的貼心提醒。
3. 讀昨天的 zodiac/episodes/(D-1)/episode.json（如果有），避免和昨天重複：排名前三、提醒句、幸運色、幸運數字、互動問題、開運推薦。開場動作與道具（`open_scene`）則要和 D-1、D-2 都不同。

## 2. 寫 episode.json
格式照範本（zodiac/episodes/2026-11-19/episode.json），欄位：
- `date`：D。`weather`：{city, summary}（給貼文用）。`sky`：一句星象（給貼文用，例「月亮在雙魚，火星木星在獅子座合相」）。
- `opening`：開場旁白，也是字幕來源。50 字以內，結構：招呼（可帶星期、節氣、節日）＋天氣與一句貼心提醒＋一個互動問題（每天換，例如「你是什麼星座？留言跟我說！」「今天心情幾分？留言告訴我！」「你最想把好運用在哪裡？」）＋固定收尾「今天月亮在X座，十二星座運勢，從第十二名倒數！」（月亮當天換座可說「月亮走進X座」）。數字寫成中文（十五度），只用「，。！？、」標點，不用英文、引號、括號。
- `signs`：12 項，`rank` 12→1，每項：
  - `key`：aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces。
  - 排名從 sky.json 的建議出發，可以調換相鄰名次增加變化，但第 1 名要是星象明顯有利的星座（月亮所在或三分相）；盡量不要和昨天的前三名完全相同。
  - `love` `work` `money`：1–5，名次越前面整體越高，第 1 名至少都 4。
  - `color`：2–3 字中文色名；`hex`：對應色碼；`num`：1–99。都不要和昨天同一星座一樣。
  - `tip`（畫面）：兩短句用「，」分開，每句 13 字內，結尾「。」或「！」，例「心思容易飄，重要的事先寫下來。」。
  - `say`（旁白第二句，前面「第X名，X座。」程式會自己加）：12 字內，兩段用「，」分開，結尾「。」或「！」，意思同 tip 但更短，例「重要的事，先寫下來。」。
  - 語氣正面、實用；後段名次是溫柔提醒，不要觸霉頭。不寫健康醫療斷言、不給投資或理財標的建議、不提賭博。12 句要各不相同，也不要照抄昨天。
- `bonus`：2 張卡。第 1 張固定吃的（chip「今日開運美食」或「今日開運飲品」），依天氣和月亮星座的元素挑；第 2 張依星期輪換：一 今日開運去處、二 今日開運小習慣、三 今日開運去處、四 今日開運穿搭、五 週末開運去處、六 今日開運活動、日 今日開運去處。去處用一般類型或知名公共場所（美術館、河濱公園、溫泉、老街、圖書館…），不寫特定店家或品牌；下雨就選室內。每張欄位：
  - `chip` 6 字內；`title` 9 字內；`lines` 兩行各 12 字內（第一行帶星象理由，第二行生活提醒）。
  - `say`：旁白 40 字內；第 1 張開頭固定「最後是卡卡夫人的開運推薦！」。
  - `img_prompt`（英文）：描述畫面主體，最後固定加上：「Square illustration for a horoscope video card. Cute, friendly modern 2D illustration with soft cel shading, crisp clean outlines, rich jewel tones (royal blue, purple, teal, gold), cozy mood, a few tiny sparkles. No people, no text, no letters, no logos.」
- `open_scene`：開場影片裡卡卡夫人的動作和手上的道具，一句中文、40 字內、結尾不加標點，會原樣填進第 4 節 prompt 的 {open_scene}。每天換，依當天主題挑（天氣、季節、節日、月亮星座的元素、開運推薦），和 D-1、D-2 不同；水晶球可以偶爾用，一週最多一次。規則：
  - 道具一兩件，拿在胸前或放在胸前的桌面上，不要遮到臉和嘴，也不要舉到臉旁邊。
  - 動作小而慢（雙手捧著、輕輕翻開、舉起來給鏡頭看、輕輕搖一下、手心托著轉一轉）；不要喝東西、吃東西或把東西靠近嘴邊，不要大幅揮手、站起來或走動（會影響對嘴）。
  - 道具上不要有文字、商標、品牌；不用手機、電腦等螢幕。
  - 範例（可自行發揮）：雙手捧著一杯冒著熱氣的花草茶暖手｜在胸前把一副星星圖案的塔羅牌攤成扇形，抽出一張翻給鏡頭看｜翻開一本燙金封面的星座書，手指輕點書頁｜拿著一張畫滿星座圖案的星盤轉向鏡頭｜手心托著一顆紫水晶原石輕輕轉動｜輕輕搖晃一串月亮星星吊飾｜捧著一盞發出暖光的星星小夜燈｜手裡拿著一小束乾燥花，輕輕聞一下花香｜雙手在胸前捧著微微發光的水晶球。
- 星座名稱、日期區間程式會自己帶，不用寫。

## 3. 旁白（Gemini TTS）
1. `python3 zodiac/pipeline/build.py EP plan` → EP/tts/plan.json（16 段：open、s12…s1、bonus1、bonus2）。程式已把「雙」換成同音的「霜」（Gemini 念不好「雙」），畫面字幕仍是「雙」，不要自己再改。
2. 每段呼叫 generate_speech，text、style、voice（Sulafat）、language（cmn-tw）、model（gemini-2.5-flash-tts）、format（wav）都照 plan.json；可一次送出多個呼叫。用 `curl -sSf -o EP/tts/<id>.wav "<url>"` 下載。open 那段的 url 留著，第 4 步要用。
3. 檢查：wav 約 48,000 bytes/秒，一個中文字約 0.28 秒。某段比預期長一倍以上（可能把 style 念出來或重複）或明顯太短，就重新合成；同一段失敗 3 次就停止並通知。style 只能用英文（中文 style 會被念出來）。

## 4. 開場對嘴影片（Calywood）
open 那段一好就先送出（要 5–10 分鐘），等待時去做其他旁白和圖片：
- generate_video_multimodal：model `seedance`，portrait_asset_ids `["asset-20261119101855-dz79b"]`（真人素材庫「卡卡夫人」），audio_urls `[open 的 url]`，duration = open.wav 秒數無條件進位（最多 30），aspect_ratio `9:16`，resolution `720p`，prompt 用這個範本，把 {open_scene} 換成 episode.json 的 `open_scene`，其餘一字不改：
  「[Asset 1] 坐在溫馨的占星工作室裡，正面對著鏡頭，{open_scene}，像親切的主持人一樣笑著跟觀眾聊天說早安。她說話的嘴型與 [Audio 1] 的語音完全同步，表情自然生動，有自然的眨眼、微笑和輕微點頭，偶爾頭稍微側一下。手上的動作輕柔緩慢，道具保持在胸前，不遮住臉和嘴。鏡頭固定不動，中景構圖，人物保持在畫面中央，背景的燭光和小燈泡微微閃爍。寫實影像風格，柔和光線。」
- 約每 60 秒 get_task 一次；完成後 `curl -sSf -o EP/open.mp4 "<影片連結>"`。失敗就同樣參數重送一次。到台北 05:40 仍沒有可用的影片，就不等了：不放 open.mp4，build 會自動改用卡卡夫人照片的備案開場（字幕一樣），照常發布，並在通知裡註明。
- 費用約 NT$3.3/秒（20 秒約 NT$65）。不要用 minimax（音訊上限 15 秒，也不支援真人素材庫）。

## 5. 開運推薦圖片（Image MCP）
create-image 兩張：prompt 用 img_prompt，size 1024x1024，quality high，background opaque，下載成 EP/bonus1.png、EP/bonus2.png。用 Read 看過：主題對、沒有文字或人物。不合格重做一次。

## 6. 做影片與檢查
1. `python3 zodiac/pipeline/build.py EP video`（約 3 分鐘）。它會：處理音訊（加速 1.33 倍）、把 Calywood 影片的嘴型對齊旁白、算開場字幕時間、畫圖卡、混音、壓成約 16 MB 的 EP/video.mp4（檔案大於約 20 MB 時 Postiz 發 FB 會失敗），並輸出 EP/check/sheet.jpg。
2. 檢查輸出：長度 80–92 秒（太長就縮短開場或開運推薦的旁白，只重新合成改過的段落）；大小 ≤ 18.5 MB；印出的 path cost ≤ 0.35（太高代表對嘴對不上：把 open.mp4 移走改用備案再 build 一次）。
3. 用 Read 打開 EP/check/sheet.jpg：開場字幕完整、日期牌是 D、圖卡文字沒有超出或重疊、第 1 名和前三名正確、推薦圖片與標題相符。有問題就修 episode.json 再 build。開場若道具遮到臉或嘴、道具上出現文字或商標，或動作怪異，當作 Calywood 失敗：台北 05:40 前還來得及就同樣參數重送一次，否則移走 open.mp4 改用備案開場再 build（並照第 9 節通知）。

## 7. 貼文文字（EP/post.txt）
純文字，不用 #、**、--- 等 Markdown，不加 AI 說明（Nathan 會寫在粉專簡介）。格式：
```
M/D（週X）卡卡夫人今日星座運勢 🔮

台北今天…（天氣一句＋貼心提醒）

今日星象：（sky 一句）

今日運勢排行
1 X座　2 X座　3 X座
4 X座　5 X座　6 X座
7 X座　8 X座　9 X座
10 X座　11 X座　12 X座

卡卡夫人今日開運推薦
吃：（第 1 張 title），（第 1 張 lines 第一行）
（第 2 張的短標，例「去」「穿」「做」）：（title），（lines 第一行）

（開場的互動問題）留言告訴卡卡夫人 👇
記得追蹤，明天早上見！

#星座 #今日運勢 #星座運勢 #十二星座 #卡卡夫人
```
貼文標題（Postiz 的 title 設定）：「M/D 今日星座運勢排行｜卡卡夫人占星館」。

## 8. 上傳與排程
影片經由公開 repo 的暫存分支 `media-zodiac` 交給 Postiz。這個分支只給本任務用，平時只有 README.md；不要動 main 以外的其他分支（media、media-taronews、media-sci、media-stock 是別的任務的）。
1. `mkdir -p /home/claude/zodiac-media && cd /home/claude/zodiac-media && git init -q -b up && git remote add origin https://github.com/chihuangchiu/daily`（已存在就清掉重建），寫 README.md 一行「Temporary media for Postiz (卡卡夫人占星館). Removed right after upload.」，複製 EP/video.mp4 成 zodiac-D.mp4，commit（作者 `-c user.name="Claude" -c user.email="noreply@anthropic.com"`），`git push -f origin up:media-zodiac`。
2. `curl -sI https://raw.githubusercontent.com/chihuangchiu/daily/media-zodiac/zodiac-D.mp4` 確認 200 且大小正確（剛推送可等幾秒，最多重試 5 次），再用 uploadFromUrlTool 上傳，取得 {id, path}；`curl -sI <path>` 確認 Postiz 那份大小相同。
3. 立刻清空分支：`git checkout -q --orphan clean && git rm -rq --cached . && git add README.md && git commit -qm "clean" && git push -f origin clean:media-zodiac`。force push 被拒時改用一般 push：fetch media-zodiac、在上面加檔 commit push，上傳後 git rm 那個檔再 commit push。
4. integrationSchedulePostTool：integrationId `cmwmx1fgl0074s680z7fug2uf`，isPremium false，shortLink false，type `schedule`，date = (D 前一天)T22:00:00Z（台北 06:00；若已過，用現在加 5 分鐘），settings `[{"key":"post_type","value":"post"},{"key":"title","value":"M/D 今日星座運勢排行｜卡卡夫人占星館"}]`，postsAndComments 一項：attachments `[path]`，content 是 post.txt 每一行包成 `<p>…</p>`、空行 `<p></p>`、HTML 跳脫。
5. postsListTool 確認已排在正確時間。接著等到台北 06:03（Bash 每次 sleep 不超過 9 分鐘），再查一次：PUBLISHED 就完成；ERROR 就用同一個 path、type `now` 重發一次，再等 2 分鐘確認；仍是 ERROR 照第 9 節通知。

## 9. 記錄與回報
1. 把 EP/episode.json、EP/post.txt、EP/sky.json commit 到 main（先 git pull --rebase；其他產物都被 .gitignore 排除），訊息「Zodiac D」，push。
2. 一切順利（發布成功、開場是 Calywood 對嘴影片）：不發任何通知，直接結束。
3. 用了備案開場、重發過，或任何一步失敗：用 PushNotification 通知 Nathan，內容用 <routine_summary> 包起來，第一句寫明今天影片發了沒、幾點、哪裡出問題與確切錯誤。影片做好但沒能發布時，用 SendUserFile（status proactive）傳 EP/video.mp4，並用 SendUserMessage 附上 post.txt 全文，讓他手動發。需要他處理的（例如到 Customize → Connectors 對 Calywood、Gemini TTS 或 My Postiz 按 Reconnect、Calywood 儲值）要寫清楚。
4. 絕不發布沒檢查過或不完整的影片。
