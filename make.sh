#!/usr/bin/env bash
# 用法：bash make.sh WORK   （WORK 內需有 data.json 與 tts/<場景key>.wav）
# 產出：WORK/main.mp4（不含片尾廣告）、timeline.json、narration_raw.wav、still 抽格與 sheet.png
set -euo pipefail
K="$(cd "$(dirname "$0")" && pwd)"; WORK="$1"
python3 "$K/audio.py" "$WORK"
python3 "$K/music.py" "$WORK"
ffmpeg -y -v error -i "$WORK/mix_raw.wav" -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 "$WORK/mix.wav"
python3 "$K/render.py" "$WORK"
ffmpeg -y -v error -i "$WORK/video_noaudio.mp4" -i "$WORK/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$WORK/main.mp4"
python3 "$K/sheet.py" "$WORK"
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,duration -of compact "$WORK/main.mp4"
ffmpeg -v error -i "$WORK/main.mp4" -f null - && echo "完整解碼 OK"
ffmpeg -v info -i "$WORK/main.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+I:|Peak:" | tail -2
