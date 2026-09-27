#!/usr/bin/env bash
# render.sh -- the whole build is one command (build.py). Extra args pass through. Every stage is cached: re-running
# after a change only redoes what the change touches (see README "Render and review loop").
#   ./render.sh --draft                 540x960 review cut in a few minutes -> exports/draft/ (runs the gates first)
#   ./render.sh                         full render -> exports/ (stops on a gate error; --force to override)
#   MUSIC=0 ./render.sh                 the master WITHOUT music (the no-music master is exported every time anyway)
#   NPROC=3 ./render.sh                 fewer capture processes when the machine is shared
#   FFMPEG=/path/to/ffmpeg ./render.sh
set -euo pipefail
cd "$(dirname "$0")"
# this machine's settings (the Mac setup writes ../vlog.env: VLOG_PY, FFMPEG, PLAYWRIGHT_MODULE, NPROC)
if [ -f ../vlog.env ]; then . ../vlog.env; fi
exec nice -n 10 "${VLOG_PY:-python3}" build.py "$@"
