#!/bin/bash
# FD MC20 PPF full process, Locked-On ABC (D=L PAGE=lo.html; generalised from render_v2.sh): layer capture (true motion blur, 2 workers) -> composite (lossless RGB intermediate)
# -> two-pass x264 ~11.5 Mb/s BT.709 + AAC 256k. Markers: .work/F/render.ok / render.failed ; log .work/F/render.log
# Resumable: the capture skips if all 899 layer frames exist; the intermediate is reused if complete.
set -uo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; cd "$T"
WD=".work/${D:-F}"; mkdir -p "$WD" exports; export LO_D="${D:-M}"; rm -f "$WD/render.ok" "$WD/render.failed"
exec > "$WD/render.log" 2>&1
fail() { echo "FAILED: $*"; touch "$WD/render.failed"; kill 0 2>/dev/null; exit 1; }
L="$HOME/.local/vlogtools/work/lockedon_0901"
export PATH="$HOME/.local/vlogtools/node/bin:$PATH" PW_MODULE="$L/node/node_modules/playwright" PLAYWRIGHT_BROWSERS_PATH="$L/node/browsers"
PY="$HOME/nq-reel-fix/tools/instagram-one-post/.venv/bin/python"; export ACCUM_PY="$PY"
FF="$HOME/.local/vlogtools/bin/ffmpeg"
NF=899; DUR=$("$PY" -c "print($NF*1001/30000)")
OUT="exports/${OUTNAME}"
# memory watchdog (24 GB Mac, another agent may be rendering): stop if free memory drops under 8 %
( while sleep 10; do f=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub("%","",$2);print $2}'); \
  if [ -n "$f" ] && [ "$f" -lt 8 ]; then echo "WATCHDOG: free memory $f% -- stopping"; touch "$WD/render.failed"; pkill -f "kcapture.js $PAGE"; pkill -f "compose_lo.py video"; exit; fi; done ) &
WDOG=$!
date; echo "frames $NF dur $DUR"
LAYER="$WD/layer"; mkdir -p "$LAYER"
N=$(ls "$LAYER" | grep -c '^[0-9]*\.png$')
if [ "$N" != "$NF" ]; then
  nice -n 19 node lib/kcapture.js "$PAGE" "$LAYER" seq 30000/1001 "$DUR" --workers 2 || fail "layer capture"
  N=$(ls "$LAYER" | grep -c '^[0-9]*\.png$'); [ "$N" = "$NF" ] || fail "layer has $N of $NF frames"
fi
date; echo "layer ok"
MID="$WD/comp_rgb.mkv"
if [ ! -f "$WD/comp.ok" ]; then
  nice -n 19 "$PY" compose_lo.py video "$LAYER" | nice -n 19 "$FF" -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30000/1001 -i - \
    -c:v libx264rgb -qp 0 -preset ultrafast -frames:v $NF "$MID" || fail "composite"
  touch "$WD/comp.ok"
fi
date; echo "composite ok"
VF="scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"
X="-c:v libx264 -preset slow -b:v 11500k -maxrate 14000k -bufsize 23000k -profile:v high -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv"
cd "$WD"
nice -n 19 "$FF" -v error -y -i comp_rgb.mkv -vf "$VF" $X -pass 1 -passlogfile x264pass -an -f null /dev/null || fail "pass 1"
nice -n 19 "$FF" -v error -y -i comp_rgb.mkv -i mix.wav -map 0:v -map 1:a -vf "$VF" $X -pass 2 -passlogfile x264pass \
  -c:a aac_at -b:a 256k -ar 48000 -frames:v $NF -movflags +faststart "$T/$OUT" || fail "pass 2"
cd "$T"
kill $WDOG 2>/dev/null
ls -l "$OUT"; date
touch "$WD/render.ok"
