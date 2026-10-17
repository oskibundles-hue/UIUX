#!/usr/bin/env bash
# render.sh -- the whole kit build is one command (build.py). Extra args pass through.
#   ./render.sh                    prep, layer, reel (master), delivery copy, mockups + board, QA
#   ./render.sh --stage mocks      mockups/*.jpg + mockups/BOARD.jpg only
#   ./render.sh --stills 1.5,12.3  composite single reel times -> .work/stills/
#   FFMPEG=/path/to/ffmpeg ./render.sh
set -euo pipefail
cd "$(dirname "$0")"
exec nice -n 10 python3 build.py "$@"
