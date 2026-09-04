#!/usr/bin/env bash
#
# index_clip.sh - catalogue one clip, then delete it.
#
# Downloads a clip from a temporary URL, records its format and exposure,
# writes graded thumbnails, and removes the file. Peak disk stays at one clip
# rather than the whole shoot, which is what makes indexing a 20 GB session
# possible on a 25 GB disk.
#
# Also classifies raw vs edited. The tell is dynamic range, not saturation:
# D-Log M sits in a narrow band with no true black (YMIN ~30, never reaching
# 255), while a finished grade uses the full 0-255. Judging by saturation
# alone gets this backwards, because the published grade is deliberately
# desaturated.
#
# Usage:
#   ./index_clip.sh <name> <url> <outdir> [lut]
#
# Appends a tab-separated row to <outdir>/index.tsv:
#   name  duration  WxH  fps  Mbps  YMIN  YAVG  YMAX  SAT  verdict

set -uo pipefail

NAME="${1:?usage: index_clip.sh <name> <url> <outdir> [lut]}"
URL="${2:?missing url}"
OUT="${3:?missing outdir}"
LUT="${4:-}"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }
mkdir -p "$OUT"
TMP="$OUT/.$NAME.download"

cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

if ! curl -sSL --max-time 700 -o "$TMP" "$URL"; then
  printf '%s\tDOWNLOAD FAILED\n' "$NAME" >> "$OUT/index.tsv"
  exit 1
fi

probe=$(ffmpeg -hide_banner -i "$TMP" 2>&1)
dur=$(sed -n 's/.*Duration: \([0-9:.]*\),.*/\1/p' <<<"$probe" | head -1)
secs=$(awk -F: '{print int($1*3600+$2*60+$3)}' <<<"${dur:-0:0:0}")
res=$(grep -oE '[0-9]{3,4}x[0-9]{3,4}' <<<"$probe" | head -1)
fps=$(grep -oE '[0-9.]+ fps' <<<"$probe" | head -1 | cut -d' ' -f1)
mbps=$(sed -n 's/.*bitrate: \([0-9]*\) kb\/s.*/\1/p' <<<"$probe" | head -1 | awk '{printf "%.1f", $1/1000}')

# signalstats must run BEFORE any 16-bit format conversion, or the numbers
# come back on a 16-bit scale and read ~257x too high.
mid=$((secs / 2))
stats=$(ffmpeg -hide_banner -ss "$mid" -t 3 -i "$TMP" \
        -vf "signalstats,metadata=print" -f null - 2>&1 \
        | sed 's/.*signalstats\.//' \
        | awk -F= '/^Y|^SAT/{s[$1]+=$2;n[$1]++}
                   END{printf "%.0f %.0f %.0f %.1f", s["YMIN"]/n["YMIN"], s["YAVG"]/n["YAVG"],
                                                     s["YMAX"]/n["YMAX"], s["SATAVG"]/n["SATAVG"]}')
read -r ymin yavg ymax sat <<<"$stats"

verdict="raw D-Log"
if [ "${ymin:-99}" -le 8 ] && [ "${ymax:-0}" -ge 250 ]; then
  verdict="EDITED (full range)"
fi

printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "$NAME" "$dur" "$res" "$fps" "$mbps" "$ymin" "$yavg" "$ymax" "$sat" "$verdict" \
  >> "$OUT/index.tsv"

# Three graded frames, evenly spaced, small enough to tile into a contact sheet.
i=1
for p in 20 50 80; do
  t=$((secs * p / 100))
  if [ -n "$LUT" ]; then
    vf="format=gbrp16le,lut3d=file=${LUT}:interp=tetrahedral,scale=180:-1"
  else
    vf="scale=180:-1"
  fi
  ffmpeg -y -loglevel error -ss "$t" -i "$TMP" -frames:v 1 -vf "$vf" \
         "$OUT/${NAME}_${i}.png" 2>/dev/null
  i=$((i + 1))
done

echo "indexed $NAME  ${dur}  ${res}  ${verdict}"
