#!/usr/bin/env bash
# Usage:
#   pipeline/build.sh EP_DIR check   -> narration.wav, timeline.json, check/sheet_*.png (review before rendering)
#   pipeline/build.sh EP_DIR video   -> EP_DIR/video.mp4 (720x1280, under 3 min, < 30 MB)
set -euo pipefail
EP="$(cd "$1" && pwd)"
MODE="${2:-video}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${TARGET:-170}"

if [ "$MODE" = "check" ]; then
  python3 "$HERE/narrate.py" "$EP" --target "$TARGET"
  rm -rf "$EP/check"
  python3 "$HERE/render.py" "$EP" sheet
  exit 0
fi

[ -f "$EP/timeline.json" ] || python3 "$HERE/narrate.py" "$EP" --target "$TARGET"
TOTAL=$(python3 -c "import json;print(json.load(open('$EP/timeline.json'))['total'])")
MID=$(python3 -c "print(round($TOTAL/2*30)/30)")
WORK="$EP/.work"; mkdir -p "$WORK"
python3 "$HERE/render.py" "$EP" seg 0 "$MID" "$WORK/a.mp4" &
python3 "$HERE/render.py" "$EP" seg "$MID" "$TOTAL" "$WORK/b.mp4"
wait
printf "file '%s'\nfile '%s'\n" "$WORK/a.mp4" "$WORK/b.mp4" > "$WORK/concat.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/concat.txt" -c copy "$WORK/v.mp4"
python3 "$HERE/pad.py" "$TOTAL" "$WORK/pad.wav"
ffmpeg -y -loglevel error -i "$WORK/v.mp4" -i "$EP/narration.wav" -i "$WORK/pad.wav" -filter_complex \
 "[1:a]aresample=48000,highpass=f=70,lowpass=f=9000,acompressor=threshold=-20dB:ratio=3:attack=5:release=120[n];[2:a]aresample=48000,volume=0.075[m];[n][m]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest "$WORK/full.mp4"
( cd "$WORK" && ffmpeg -y -loglevel error -i full.mp4 -c:v libx264 -preset slow -b:v 850k -pass 1 -an -f null /dev/null && \
  ffmpeg -y -loglevel error -i full.mp4 -c:v libx264 -preset slow -b:v 850k -pass 2 -c:a aac -b:a 128k -movflags +faststart "$EP/video.mp4" )
rm -rf "$WORK"
ffprobe -v error -show_entries format=duration,size:stream=width,height -of compact "$EP/video.mp4"
