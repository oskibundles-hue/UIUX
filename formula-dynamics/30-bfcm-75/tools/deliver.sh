#!/bin/bash
# deliver.sh DATE SLOT : render one carousel into the Drive delivery folder and refresh source, ledger, PROGRESS.md
set -euo pipefail
cd "$(dirname "$0")/.."
# the Google Drive mount is named after the signed-in account, so find it rather than writing the address here
DRV=$(ls -d "$HOME"/Library/CloudStorage/GoogleDrive-* | head -1)
DEL="$DRV/My Drive/Formula Dynamics - Black Friday Sale ads/SALE CONTENT BLACKFRIDAY/04 — Claude design handoff and returns/FROM-CLAUDE TO-CODEX - FD-BFCM-75 production delivery"
D=$1; S=$2; SRC=source/$D/$S; OUT="$DEL/exports/$D/$S"
mkdir -p "$OUT" "$DEL/ledger" "$DEL/editable source"
~/.local/bin/uv run -q --with playwright --with pillow python tools/render.py "$OUT" $SRC/slide-0{1,2,3}.html >/dev/null
rm -rf "$OUT/_phone"
cp $SRC/Caption.txt "$OUT/Caption.txt"
rsync -a --exclude '.DS_Store' --exclude ref --exclude out source assets tools "$DEL/editable source/"
python3 tools/build_meta.py "$DEL"
ls "$OUT"
