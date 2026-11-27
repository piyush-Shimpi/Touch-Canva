#!/usr/bin/env bash
# frames (50%) -> 1080x1920, light grain, captions, soundtrack at -14 LUFS -> output/final.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p output
ffmpeg -v error -y -framerate 30 -i frames/f_%04d.png -i audio/mix.wav \
  -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.45,noise=alls=4:allf=t,ass=audio/captions.ass,format=yuv420p" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=9" -ar 48000 \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k -shortest -movflags +faststart output/final.tmp.mp4
mv output/final.tmp.mp4 output/final.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 output/final.mp4
