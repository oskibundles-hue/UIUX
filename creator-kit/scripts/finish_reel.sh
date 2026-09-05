#!/usr/bin/env bash
#
# finish_reel.sh - last pass on a rendered Reel: timed overlays, loudness,
# and a size-targeted 4K H.264 encode, all in one generation.
#
# Usage:
#   finish_reel.sh <in.mp4> <out.mp4> [--target-mb 75] [--fps 29.97] \
#                  [<png:start[:end]> ...]
#
# Overlay specs are the same as overlay.sh (full-frame PNGs, scaled to the
# video). Doing overlays and the delivery encode together avoids a second
# lossy generation between Remotion and Instagram.
#
set -euo pipefail
die() { echo "error: $*" >&2; exit 1; }
IN="${1:?usage: finish_reel.sh <in> <out> [--target-mb N] [png:start[:end] ...]}"
OUT="${2:?missing output}"; shift 2
TARGET_MB=75; FPS=29.97; specs=()
while [ $# -gt 0 ]; do
  case "$1" in
    --target-mb) TARGET_MB="$2"; shift 2;;
    --fps) FPS="$2"; shift 2;;
    *) specs+=("$1"); shift;;
  esac
done
[ -f "$IN" ] || die "not found: $IN"

info=$(ffmpeg -hide_banner -i "$IN" 2>&1 || true)
read -r W H < <(sed -n 's/.*Stream #0:0.*, \([0-9]\+\)x\([0-9]\+\).*/\1 \2/p' <<<"$info" | head -1)
DUR=$(sed -n 's/.*Duration: \([0-9]*\):\([0-9]*\):\([0-9.]*\).*/\1 \2 \3/p' <<<"$info" | head -1 \
      | awk '{print $1*3600+$2*60+$3}')
[ -n "${W:-}" ] && [ -n "${DUR:-}" ] || die "could not probe $IN"

# Bitrate that lands on the target, clamped to the 10-35 Mbps upload window.
AUDIO_K=192
VK=$(awk -v mb="$TARGET_MB" -v d="$DUR" -v a="$AUDIO_K" \
     'BEGIN{v=(mb*8*1024*1000/1000)/d - a; if(v<10000)v=10000; if(v>35000)v=35000; printf "%d", v}')
echo "in      : ${W}x${H}, ${DUR}s"
echo "target  : ${TARGET_MB} MB -> ${VK} kb/s video + ${AUDIO_K} kb/s audio"

inputs=(-i "$IN"); filter=""; label="[0:v]"; idx=1
for spec in "${specs[@]}"; do
  png="${spec%%:*}"; rest="${spec#*:}"; start="${rest%%:*}"
  if [ "$rest" = "$start" ]; then end=""; else end="${rest#*:}"; fi
  [ -f "$png" ] || die "overlay not found: $png"
  inputs+=(-i "$png")
  filter+="[${idx}:v]scale=${W}:${H}:flags=lanczos[ov${idx}];"
  if [ -n "$end" ]; then enable="between(t,${start},${end})"; else enable="gte(t,${start})"; fi
  echo "overlay : $(basename "$png")  ${start}s -> ${end:-end}"
  filter+="${label}[ov${idx}]overlay=0:0:enable='${enable}'[v${idx}];"
  label="[v${idx}]"; idx=$((idx+1))
done
filter+="${label}format=yuv420p[vout];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"

PASSLOG="$(mktemp -d)/x264"
common=(-filter_complex "$filter" -map "[vout]" -map "[aout]"
  -r "$FPS" -c:v libx264 -preset medium -profile:v high -level 5.1
  -b:v "${VK}k" -maxrate "$((VK*12/10))k" -bufsize "$((VK*2))k"
  -colorspace bt709 -color_primaries bt709 -color_trc bt709
  -passlogfile "$PASSLOG")
echo; echo "pass 1"
ffmpeg -y -hide_banner -loglevel error -stats "${inputs[@]}" "${common[@]}" -pass 1 -an -f mp4 /dev/null
echo; echo "pass 2"
ffmpeg -y -hide_banner -loglevel error -stats "${inputs[@]}" "${common[@]}" -pass 2 \
  -c:a aac -b:a "${AUDIO_K}k" -ar 48000 -movflags +faststart "$OUT"
echo; echo "done: $OUT ($(du -m "$OUT" | cut -f1) MB)"
