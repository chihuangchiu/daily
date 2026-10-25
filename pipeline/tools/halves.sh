#!/bin/bash
# halves.sh lang wav...
L=$1; shift; fs=()
for f in "$@"; do d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f); h=$(python3 -c "print($d/2)"); b=$(basename $f .wav)
ffmpeg -loglevel error -y -t $h -i $f /tmp/h_${b}_1.wav; ffmpeg -loglevel error -y -ss $h -i $f /tmp/h_${b}_2.wav; fs+=(/tmp/h_${b}_1.wav /tmp/h_${b}_2.wav); done
python3 /tmp/claude-0/s/asr1.py $L "${fs[@]}" 2>/dev/null
