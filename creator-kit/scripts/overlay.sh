#!/usr/bin/env bash
#
# overlay.sh - burn timed overlays onto a finished Reel.
#
# The Formula Dynamics pack is full-frame 1080x1920 PNGs with alpha, meant to
# sit on a track above the video. This does the same thing without opening an
# editor, and keeps the output at 4K.
#
# On upscaling: the overlays are 1080x1920 and our masters are 2160x3840, so
# each one is scaled 2x. Tested against a native-1080 composite - lanczos on
# these clean vector-derived PNGs holds up; letterform edges soften slightly
# but stay crisp. Worth it to keep the 4K master rather than drop the whole
# video to 1080 for the sake of the graphics.
#
# Usage:
#   ./overlay.sh <video> <output> <spec> [<spec> ...]
#
# A spec is  PATH:START:END  in seconds. END may be omitted to run to the end.
#
# Example:
#   ./overlay.sh reel.mp4 out.mp4 \
#     "pack/corner-logo-bugs/bug_9x16_top-left_logo-white.png:0" \
#     "pack/lower-thirds/lt_9x16_service_detailing.png:2:7" \
#     "pack/cta-captions/cta_9x16_soft_follow-for-more_bar.png:24:30"
#
# The logo bug takes no END, so it stays up for the whole video.

set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }
command -v ffmpeg >/dev/null || die "ffmpeg not found"

VIDEO="${1:?usage: overlay.sh <video> <output> <png:start[:end]> ...}"
OUT="${2:?missing output}"
shift 2
[ $# -gt 0 ] || die "give at least one overlay spec (PATH:START[:END])"
[ -f "$VIDEO" ] || die "video not found: $VIDEO"

# Output size comes from the video, so a 1080 master and a 4K master both work.
read -r W H < <(ffmpeg -hide_banner -i "$VIDEO" 2>&1 \
  | sed -n 's/.*Stream #0:0.*, \([0-9]\+\)x\([0-9]\+\).*/\1 \2/p' | head -1)
[ -n "${W:-}" ] || die "could not read the video's dimensions"
echo "video   : ${W}x${H}"

inputs=(-i "$VIDEO")
filter=""
label="[0:v]"
idx=1

for spec in "$@"; do
  png="${spec%%:*}"
  rest="${spec#*:}"
  start="${rest%%:*}"
  if [ "$rest" = "$start" ]; then end=""; else end="${rest#*:}"; fi
  [ -f "$png" ] || die "overlay not found: $png"

  inputs+=(-i "$png")
  # Scale each overlay to the video rather than assuming it matches. Overlays
  # authored at 1080x1920 land on a 4K master at 2x with no extra handling.
  filter+="[${idx}:v]scale=${W}:${H}:flags=lanczos[ov${idx}];"
  if [ -n "$end" ]; then
    enable="between(t,${start},${end})"
    echo "overlay : $(basename "$png")  ${start}s -> ${end}s"
  else
    enable="gte(t,${start})"
    echo "overlay : $(basename "$png")  ${start}s -> end"
  fi
  filter+="${label}[ov${idx}]overlay=0:0:enable='${enable}'[v${idx}];"
  label="[v${idx}]"
  idx=$((idx + 1))
done

# Strip the trailing ; and name the final link so -map can find it.
filter="${filter%;}"
filter="${filter%\[v$((idx-1))\]}[vout]"

echo
set -x
ffmpeg -y -hide_banner -loglevel error "${inputs[@]}" \
  -filter_complex "$filter" \
  -map "[vout]" -map 0:a? \
  -c:v libx264 -preset medium -crf 18 \
  -profile:v high -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a copy -movflags +faststart "$OUT"
set +x

echo
echo "done: $OUT"
