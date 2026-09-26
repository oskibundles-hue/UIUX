#!/usr/bin/env bash
# render.sh -- thin wrapper: the whole build is one command (build.py). Extra args pass through.
#   ./render.sh                 full render -> exports/
#   ./render.sh --qa            QA-gate stills only
#   FFMPEG=/path/to/ffmpeg ./render.sh
set -euo pipefail
cd "$(dirname "$0")"
exec nice -n 10 python3 build.py "$@"
