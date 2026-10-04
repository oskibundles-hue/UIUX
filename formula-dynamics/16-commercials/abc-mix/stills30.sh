#!/bin/bash
# QA / hero stills for one direction: capture the layer at chosen times, composite, one JPG per time.
#   ./stills30.sh <A|B|C> <tag> t1,t2,...     -> qa/<D>_<tag>/t*.jpg
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; cd "$T"
D=$1; TAG=$2; TIMES=$3
L="$HOME/.local/vlogtools/work/lockedon_0901"
export PATH="$HOME/.local/vlogtools/node/bin:$PATH" PW_MODULE="$L/node/node_modules/playwright" PLAYWRIGHT_BROWSERS_PATH="$L/node/browsers"
PY="$HOME/nq-reel-fix/tools/instagram-one-post/.venv/bin/python"; export ACCUM_PY="$PY"
TS=$("$PY" -c "import sys; F=30000/1001; print(','.join('%.3f'%(round(float(t)*F)/F) for t in sys.argv[1].split(',')))" "$TIMES")
LD=".work/$D/stills_$TAG"; rm -rf "$LD"; mkdir -p "$LD" "qa/${D}_$TAG"
nice -n 19 node lib/kcapture.js "${PAGE:-dir$D.html}" "$LD" at "$TS" --workers 2 2>&1 | tail -1
for t in ${TS//,/ }; do nice -n 19 "$PY" compose30.py "$D" still "$LD" "t$t" "qa/${D}_$TAG/t$t.jpg"; done
