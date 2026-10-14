#!/usr/bin/env bash
# setup-mac.sh: one-time setup of the SE vlog pipeline on a Mac (Apple Silicon or Intel).
#
#   ./setup-mac.sh           install everything, then prove it works (doctor.py, about 3-5 min the first time)
#   ./setup-mac.sh --check   only run the checks again
#
# What it installs (nothing outside Homebrew and this folder):
#   Homebrew:  ffmpeg (with zscale, libx264 10-bit, VideoToolbox), node, python@3.12
#   .venv/     the Python packages in requirements.txt
#   .node/     Playwright + its own Chromium (draws the Locked-On motion-graphics layer)
#   caches     the whisper small.en model and the speaker-voice model (about 0.5 GB, downloaded once)
# Then doctor.py writes vlog.env (this machine's paths and settings) and runs a small end-to-end test.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

if [ "$(uname -s)" != Darwin ]; then
  echo "setup-mac.sh is for macOS. In the cloud container everything is already installed."
  exit 1
fi

if [ "${1:-}" != "--check" ]; then
  if ! command -v brew >/dev/null 2>&1; then
    for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      if [ -x "$b" ]; then eval "$("$b" shellenv)"; fi
    done
  fi
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is needed first (it installs ffmpeg, node and Python)."
    echo "Install it with the one command on https://brew.sh, open a new Terminal window, then run this again."
    exit 1
  fi

  say "1/4  ffmpeg, node, Python (Homebrew)"
  brew install ffmpeg node python@3.12

  say "2/4  Python packages -> $HERE/.venv"
  PY="$(brew --prefix python@3.12)/bin/python3.12"
  [ -x .venv/bin/python ] || "$PY" -m venv .venv
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt

  say "3/4  Playwright + Chromium -> $HERE/.node"
  mkdir -p .node
  if [ ! -f .node/package.json ]; then (cd .node && npm init -y >/dev/null); fi
  (cd .node && npm install --silent --no-fund --no-audit playwright@1.56.1)
  (cd .node && npx --yes playwright install chromium)

  say "4/4  speech and speaker models (downloaded once)"
  .venv/bin/python - <<'PYEOF'
from faster_whisper import WhisperModel
WhisperModel('small.en', device='cpu', compute_type='int8')
from huggingface_hub import hf_hub_download
hf_hub_download('Wespeaker/wespeaker-voxceleb-resnet34-LM', 'voxceleb_resnet34_LM.onnx')
print('models cached')
PYEOF
fi

say "Checks (doctor.py)"
PYBIN=.venv/bin/python
[ -x "$PYBIN" ] || PYBIN=python3
"$PYBIN" doctor.py --write-env
