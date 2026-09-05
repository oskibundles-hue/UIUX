#!/usr/bin/env bash
#
# compose_reel.sh - one-pass finish: master footage + optional look LUT +
# punch-in zooms + transparent graphics render + logo bug + sharpen +
# loudness, straight to the delivery encode.
#
# The earlier chain (LUT pass -> Remotion re-encode of the footage -> delivery
# encode) put the footage through three lossy generations and Remotion's JPEG
# frame capture. That is where the softness came from. Here the footage is
# decoded once from the master and encoded once; Remotion renders only the
# graphics, on alpha, and they are composited in this pass.
#
# Usage:
#   compose_reel.sh <master.mp4> <overlay.mov> <props.json> <out.mp4> \
#       [--lut file.cube] [--logo png] [--crf 17] [--maxrate 28M] [--sharpen 0.6]
#
# props.json is the Remotion props file; its `punches` list drives the zooms.
set -euo pipefail
die() { echo "error: $*" >&2; exit 1; }
MASTER="${1:?}"; OVERLAY="${2:?}"; PROPS="${3:?}"; OUT="${4:?}"; shift 4
LUT=""; LOGO=""; CRF=17; MAXRATE="28M"; SHARPEN=0.6; FPS=29.97
while [ $# -gt 0 ]; do case "$1" in
  --lut) LUT="$2"; shift 2;; --logo) LOGO="$2"; shift 2;; --crf) CRF="$2"; shift 2;;
  --maxrate) MAXRATE="$2"; shift 2;; --sharpen) SHARPEN="$2"; shift 2;; --fps) FPS="$2"; shift 2;;
  *) die "unknown option $1";; esac; done
for f in "$MASTER" "$OVERLAY" "$PROPS"; do [ -f "$f" ] || die "not found: $f"; done

read -r W H < <(ffmpeg -hide_banner -i "$MASTER" 2>&1 | sed -n 's/.*Stream #0:0.*, \([0-9]\+\)x\([0-9]\+\).*/\1 \2/p' | head -1)

# Zoom factor as an ffmpeg expression of t, from the punches in props.json:
# ramp up over 0.12s, hold, ease back over 0.35s. Applied as a per-frame
# upscale then a centre crop back to the frame size.
ZOOM=$(python3 - "$PROPS" <<'PY'
import json, sys
p = json.load(open(sys.argv[1])); terms = []
for q in p.get("punches", []):
    a, h, s = q["at"], q.get("hold", 1.2), q.get("scale", 1.12)
    up = f"clip((t-{a})/0.12,0,1)"; down = f"(1-clip((t-{a+h})/0.35,0,1))"
    terms.append(f"({s-1:.4f}*{up}*{down})")
print("1+" + "+".join(terms) if terms else "1")
PY
)
echo "zoom    : $ZOOM"

vf="[0:v]format=yuv420p"
[ -n "$LUT" ] && vf+=",lut3d=${LUT}:interp=tetrahedral" && echo "lut     : $LUT"
if [ "$ZOOM" != "1" ]; then
  vf+=",scale=w='trunc(iw*(${ZOOM})/2)*2':h='trunc(ih*(${ZOOM})/2)*2':eval=frame:flags=lanczos"
  vf+=",crop=${W}:${H}:'(iw-${W})/2':'(ih-${H})/2'"
fi
vf+="[base];[1:v]format=rgba[gfx];[base][gfx]overlay=0:0:format=auto:shortest=1[v1]"
inputs=(-i "$MASTER" -i "$OVERLAY"); last="[v1]"
if [ -n "$LOGO" ]; then
  inputs+=(-i "$LOGO"); vf+=";[2:v]scale=${W}:${H}:flags=lanczos[logo];[v1][logo]overlay=0:0[v2]"; last="[v2]"
  echo "logo    : $(basename "$LOGO")"
fi
if [ "$SHARPEN" != "0" ]; then
  vf+=";${last}unsharp=5:5:${SHARPEN}:5:5:0[vs]"; last="[vs]"
fi
vf+=";${last}format=yuv420p[vout];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"

ffmpeg -y -hide_banner -loglevel error -stats "${inputs[@]}" -filter_complex "$vf" \
  -map "[vout]" -map "[aout]" -r "$FPS" \
  -c:v libx264 -preset medium -profile:v high -level 5.1 -crf "$CRF" -maxrate "$MAXRATE" -bufsize "$(( ${MAXRATE%M} * 2 ))M" \
  -x264-params "aq-mode=3:aq-strength=1.0" \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "done: $OUT ($(du -m "$OUT" | cut -f1) MB)"
