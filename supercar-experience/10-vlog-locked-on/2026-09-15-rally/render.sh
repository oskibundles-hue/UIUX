#!/usr/bin/env bash
# render.sh -- the whole build is one command (build.py). Extra args pass through.
#   ./render.sh                 full render -> exports/
#   ./render.sh --stage qa      QA only
#   FFMPEG=/path/to/ffmpeg VIDEO=/path/to/rally_ig.mp4 ./render.sh
set -euo pipefail
cd "$(dirname "$0")"
exec nice -n 10 python3 build.py "$@"
