#!/usr/bin/env bash
# render.sh -- the whole build is one command (build.py). Extra args pass through.
#   ./render.sh                         full render -> exports/
#   MUSIC=0 ./render.sh --stage audio,compose,qa     the master WITHOUT music (the no-music master is exported every time anyway)
#   FFMPEG=/path/to/ffmpeg ./render.sh
set -euo pipefail
cd "$(dirname "$0")"
exec nice -n 10 python3 build.py "$@"
