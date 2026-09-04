#!/usr/bin/env bash
#
# contact_sheet.sh - eight frames across a finished Reel, side by side.
#
# For checking that a file's name matches what is actually in it. Names get
# derived from a few thumbnails of a whole take, but each export is a specific
# 60-second window out of that take - and the window can easily show something
# other than what the take is "about". A Reel called "part closeup to camera"
# that opens on someone cutting trim strips is worse than no name at all,
# because the whole point of the naming is that you can pick a clip without
# opening it.
#
# Usage:
#   ./contact_sheet.sh <video> <out.png> [frames]
# No -e here on purpose: `ffmpeg -i <file>` with no output file exits 1, so
# under `set -e` with pipefail the duration probe below kills the script.
set -uo pipefail
export PATH="/root/bin:$PATH"
V="${1:?usage: contact_sheet.sh <video> <out.png> [frames]}"
OUT="${2:?missing output}"
N="${3:-8}"
[ -f "$V" ] || { echo "not found: $V" >&2; exit 1; }

secs=$(ffmpeg -hide_banner -i "$V" 2>&1 | sed -n 's/.*Duration: \([0-9:.]*\),.*/\1/p' | head -1 \
       | awk -F: '{print $1*3600+$2*60+$3}')
[ -n "${secs:-}" ] || { echo "could not read a duration from $V" >&2; exit 1; }
TD=$(mktemp -d); trap 'rm -rf "$TD"' EXIT
args=(); filt=""
for i in $(seq 0 $((N-1))); do
  t=$(python3 -c "print(max(0.2, $secs*($i+0.5)/$N))")
  ffmpeg -v error -y -ss "$t" -i "$V" -frames:v 1 -vf scale=300:533 "$TD/$i.png"
  args+=(-i "$TD/$i.png"); filt+="[$i]"
done
# image2's glob demuxer stops after the first frame when the PNGs differ in
# pixel format, so name every input explicitly instead.
ffmpeg -v error -y "${args[@]}" -filter_complex "${filt}hstack=inputs=$N" -frames:v 1 "$OUT"
echo "$OUT"
