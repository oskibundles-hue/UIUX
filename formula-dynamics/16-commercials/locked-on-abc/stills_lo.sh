#!/bin/bash
# QA stills for Locked-On ABC: capture the layer at chosen times (s), composite, one JPG per time.  ./stills_lo.sh <tag> t1,t2,...
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; cd "$T"
TAG=$1; TIMES=$2
L="$HOME/.local/vlogtools/work/lockedon_0901"
export PATH="$HOME/.local/vlogtools/node/bin:$PATH" PW_MODULE="$L/node/node_modules/playwright" PLAYWRIGHT_BROWSERS_PATH="$L/node/browsers"
PY="$HOME/nq-reel-fix/tools/instagram-one-post/.venv/bin/python"; export ACCUM_PY="$PY"
TS=$("$PY" -c "import sys; F=30000/1001; print(','.join('%.3f'%(round(float(t)*F)/F) for t in sys.argv[1].split(',')))" "$TIMES")
LD=".work/${LO_D:-M}/stills_$TAG"; rm -rf "$LD"; mkdir -p "$LD" "qa/${LO_D:-M}_$TAG"
nice -n 19 node lib/kcapture.js "${PAGE:-lo.html}" "$LD" at "$TS" --workers 2 2>&1 | tail -2
for t in ${TS//,/ }; do nice -n 19 "$PY" compose_lo.py still "$LD" "t$t" "qa/${LO_D:-M}_$TAG/t$t.jpg"; done
