#!/usr/bin/env bash
# encode.sh <base.mov> <layerDir> <out.mp4> -- lay the HUD layer (RGBA PNGs 00000.png...) over the clip and deliver one
# Instagram-ready file: 1080x1920, H.264 High two-pass ~11.5 Mb/s, AAC 48 kHz, fast start, the clip's own sound at -14 LUFS.
set -euo pipefail
base=$1; layer=$2; out=$3
j=$(ffmpeg -hide_banner -i "$base" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
v() { echo "$j" | python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }
AF="loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(v input_i):measured_TP=$(v input_tp):measured_LRA=$(v input_lra):measured_thresh=$(v input_thresh):offset=$(v target_offset):linear=true,aresample=48000"
FC="[0:v][1:v]overlay=format=auto,format=yuv420p[v]"
X="-c:v libx264 -profile:v high -preset slow -b:v 11.5M -maxrate 14M -bufsize 23M -passlogfile /tmp/hud_x264 -r 30000/1001"
ffmpeg -v error -y -i "$base" -framerate 30000/1001 -i "$layer/%05d.png" -filter_complex "$FC" -map "[v]" -an $X -pass 1 -f mp4 /dev/null
ffmpeg -v error -y -i "$base" -framerate 30000/1001 -i "$layer/%05d.png" -filter_complex "$FC" -map "[v]" -map 0:a -af "$AF" -c:a aac -b:a 192k -ar 48000 $X -pass 2 -movflags +faststart "$out"
ffmpeg -hide_banner -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -E " I:| Peak:" | tail -2
