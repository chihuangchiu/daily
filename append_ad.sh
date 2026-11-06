#!/usr/bin/env bash
# 用法：bash append_ad.sh <主影片.mp4> <輸出.mp4> [YYYY-MM-DD]
# 在台灣股市即時報影片結尾接上江文忠（永豐金證券）片尾廣告。
# 日期 <= 2026-11-20 用含 AAA 抽票活動的版本，之後用一般版本。
set -euo pipefail
MAIN="$1"; OUT="$2"; D="${3:-$(TZ=Asia/Taipei date +%F)}"
DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "$D" < "2026-11-21" ]]; then AD="$DIR/ad-jiang-aaa.mp4"; else AD="$DIR/ad-jiang-general.mp4"; fi
ffmpeg -y -v error -i "$MAIN" -i "$AD" -filter_complex \
"[0:v]scale=720:1280,fps=30,format=yuv420p,setsar=1[v0];[1:v]scale=720:1280,fps=30,format=yuv420p,setsar=1[v1];\
[0:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=mono[a0];[1:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=mono[a1];\
[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
-c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "appended $(basename "$AD") -> $OUT"
