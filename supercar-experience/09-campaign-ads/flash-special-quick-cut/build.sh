#!/usr/bin/env bash
# Quick cut of the 2-hour flash special story (Lamborghini Huracan STO), 15 s 9:16.
# Usage: ./build.sh /path/to/SCE_Lamborghini-Huracan-STO_green_no-branding.mp4 /path/to/sfx.wav [ffmpeg]
# Source clip: Dropbox "Supercar Experience/01 Car Footage/". Footage and renders stay out of git.
set -euo pipefail
cd "$(dirname "$0")"
SRC=${1:?source clip}; SFX=${2:?sfx wav}; FF=${3:-ffmpeg}
mkdir -p .work/seq
# plate: [src_in:duration] -> 1.5 hook (front-on canopy) | 1.4 crest | 1.5 STO badge | 3.0 rolling | 3.0 night drive | 4.6 Convention Center
SEG="8.4:1.5 2.2:1.4 6.2:1.5 11.0:3.0 14.6:3.0 19.4:4.6"; i=0; F=""; C=""
for s in $SEG; do a=${s%%:*}; d=${s##*:}; F="$F[0:v]trim=start=$a:duration=$d,setpts=PTS-STARTPTS,format=yuv420p,fps=24[v$i];"; C="$C[v$i]"; i=$((i+1)); done
"$FF" -y -loglevel error -i "$SRC" -filter_complex "${F}${C}concat=n=$i:v=1:a=0,eq=contrast=1.05:saturation=1.05[out]" -map "[out]" -c:v libx264 -crf 14 -pix_fmt yuv420p -r 24 .work/plate.mp4
node render.js seq .work/seq 24
"$FF" -y -loglevel error -i .work/plate.mp4 -framerate 24 -i .work/seq/%05d.png -i "$SFX" \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  exports/SCE_Lamborghini-Huracan-STO_Flash-Special-11AM-1PM_QUICK-CUT_15s-9x16.mp4
