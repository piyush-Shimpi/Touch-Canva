#!/usr/bin/env bash
# frames (any size) -> 1080x1920 + captions + soundtrack -> penny-drop.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
ffmpeg -v error -y -framerate 30 -i frames/f_%04d.png -i audio/mix.wav \
  -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,ass=audio/captions.ass" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart \
  "${1:-penny-drop.mp4}"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "${1:-penny-drop.mp4}"
