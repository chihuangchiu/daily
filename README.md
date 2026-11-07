# 每日ETF整理（台灣股市即時報）影片程式

給排程任務使用：每個交易日把當天資料寫成 `data.json`，配好每個場景的旁白音檔，就能輸出 720×1280 直式影片。
畫面風格沿用台灣股市即時報其他影片（深藍底、紅漲綠跌、▲▼），2026-11-07 用 11/6 資料定版（`sample/data.json`）。

## 流程

```
WORK=/home/claude/etfwork; mkdir -p $WORK/tts
# 1. 寫 $WORK/data.json（格式見下方與 sample/data.json）
python3 common.py $WORK          # 檢查旁白字數、字幕切段、送入 TTS 的文字
# 2. 每個場景用 Gemini TTS 合成，存成 $WORK/tts/<key>.wav（文字用 common.py 印出的 TTS 版本）
bash make.sh $WORK               # 拼接旁白、配樂、繪製畫面、合併 → $WORK/main.mp4，並產生 sheet1.png、sheet2.png 抽格
python3 asr.py $WORK MODEL_DIR   # 語音辨識回測 → $WORK/asr_report.txt
python3 perf.py perf_input.json  # 近一個月含息報酬排行（輔助計算）
```

依賴：python3、Pillow、numpy、ffmpeg、Noto Sans CJK（/usr/share/fonts/opentype/noto/）；asr.py 另需 `pip install sherpa-onnx` 與 SenseVoice 模型。

## data.json

| 欄位 | 說明 |
|---|---|
| `date`、`weekday` | 資料日期 YYYY-MM-DD、中文星期（一～五） |
| `scenes` | 依播放順序的 `{key, text}`；key 可用 hook、close、perf、flow、prem、div、event、end，可省略任一段（對應資料也可省略）。text 為顯示用旁白（代號寫阿拉伯數字、百分比寫 %），送 TTS 前由 `common.tts_text` 轉換 |
| `hook` | `badge`、`headline`、`card1{label,tag,value,sub,dir}`、`card2{label,value,dir,line,note}`（card2 可省略）。dir：1 紅、-1 綠、0 白 |
| `close` | 8 檔 `[代號, 名稱, 收盤價, 漲跌幅%]`，也用於跑馬燈 |
| `perf` | `subtitle`、`top`／`bottom` 各 5 筆 `[代號, 名稱, 報酬%]`、`scope`（範圍說明），可選 `top_label`、`bottom_label` |
| `flow` | `subtitle`、`in`／`out` 各 3 筆 `[代號, 名稱, 金額億元(整數), 單位數說明]` |
| `prem` | `subtitle`、`rows` 最多 5 筆 `[代號, 名稱, 市價, 預估淨值, 溢價%]`，可選 `title`、`note`（兩行） |
| `div` | `subtitle`、`rows` 最多 5 筆 `[日期（星期）, 標的, 金額說明, 最後買進日]`、`hot`（要強調的列索引，沒有就 -1）、可選 `note` |
| `event` | 可選：`title`、`subtitle`、`lines`（最多 4 行重點） |
| `end` | `points` 3 句重點 |
| `data_line` | 可選：覆寫畫面底部資料時點文字 |
