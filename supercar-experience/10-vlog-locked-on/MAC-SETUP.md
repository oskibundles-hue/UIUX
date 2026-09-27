# Running the vlog pipeline on the Mac

This is the same pipeline as the cloud one: `engine/` surveys and fetches the footage, and a day's build folder (like
`2026-09-15-rally-v2/`) renders the Locked-On vlog. On the Mac it can also read footage that is already on the
machine, so it doesn't need Dropbox download links. That footage can sit in the Dropbox folder, a camera card or the
drive you offload to. The pipeline also uses every core.

## One-time setup (about 10 minutes, mostly downloads)

1. Install Homebrew if the Mac doesn't have it. It's the one command on https://brew.sh. Open a new Terminal
   window afterwards.
2. Get the project and this branch:
   ```bash
   git clone https://github.com/oskibundles-hue/UIUX.git ~/UIUX
   cd ~/UIUX && git checkout claude/supercar-rental-ad-graphics-o64vo3
   ```
   If you already have the repo, run `git pull` on that branch instead.
3. Run the setup:
   ```bash
   cd ~/UIUX/supercar-experience/10-vlog-locked-on
   ./setup-mac.sh
   ```
   The setup does the following:
   - installs ffmpeg, node and Python 3.12 with Homebrew;
   - puts the Python packages in `.venv/`, and Playwright and its own Chromium in `.node/` (both inside this folder,
     not system-wide);
   - downloads the speech model and the speaker model once (about 0.5 GB);
   - runs `doctor.py`, which checks every tool and then runs the whole pipeline on a generated test clip.

   It ends with **READY** or with the list of what's missing. `doctor.py` also writes `vlog.env`, which holds this
   Mac's paths and settings: the ffmpeg to use, the number of cores, and the Dropbox folder it found.
   - On an Apple-silicon Mac, doctor also decodes a 4K HEVC 10-bit clip on the media engine (VideoToolbox) and
     compares it with the CPU decode, frame by frame. Hardware decode is switched on for `fetch` only if every frame
     is identical, and doctor prints both speeds.
   - Run `./setup-mac.sh --check` any time to re-check without reinstalling.

## A new vlog day on the Mac

```bash
cd ~/UIUX/supercar-experience/10-vlog-locked-on
DAY=~/vlogs/2026-10-02
./vlog links  $DAY --local "/Volumes/CARD/DCIM/DJI_001" --local "$HOME/Movies/phone-clips-2026-10-02"
./vlog ingest $DAY --local          # survey + transcripts, unattended
./vlog index  $DAY                  # day.md, moments.md, flags.json: what to cut, what never to use
#  ... write the cut (edl.json) from moments.md; check it against flags.json ...
./vlog plan   $DAY --edl edl.json
./vlog fetch  $DAY --out $DAY/mezz --local
```

- `--local FOLDER` registers every video in that folder, and you can repeat it for more folders. `ingest --local` and
  `fetch --local` then read the files straight from disk, with no links and no 15-minute clock.
- To use clips in the Dropbox folder, point `--local` at the day's folder, for example
  `"$VLOG_DROPBOX_ROOT/NQ Studio/raw footage/2026-10-02"` after `source vlog.env`.
  - **Online-only files:** reading one makes the Dropbox app download the whole file. Before it reads anything,
    `ingest --local` adds up the online-only files. It stops if they would not fit on the disk, and otherwise says
    how much will be downloaded.
  - **Fastest source:** the card or the offload drive. Otherwise, mark the day's Dropbox folder *Available offline*
    first.
- Days that are only in Dropbox, too big for the Mac, can still be surveyed through Dropbox links (streaming, no disk
  needed), the way the cloud session does it. See `engine/README.md`.

Rendering happens in the day's build folder, a copy of `2026-09-15-rally-v2/` adapted to the day. Its `config.json`
paths point at the files. On the Mac, put a `config.local.json` next to it (git-ignored) that points at this Mac's
folders:

```json
{ "paths": { "mezz": "~/vlogs/2026-10-02/mezz", "transcripts": "~/vlogs/2026-10-02/tr", "scratch": "~/vlogs/2026-10-02" } }
```

Then:

```bash
./render.sh --draft     # 540x960 review cut in a few minutes (the gates run first)
./render.sh             # full quality; review fixes re-render only what they touch
```

`render.sh` reads `../vlog.env`, so it uses this Mac's Python, ffmpeg, Playwright and all its cores (`NPROC`).

## The Sep 15 vlog on the Mac (optional)

The Sep 15 fixes can keep rendering in the cloud session, where its clips already are. To render them on the Mac
instead:

```bash
DAY=~/vlogs/2026-09-15; R="$VLOG_DROPBOX_ROOT"      # after: source vlog.env
./vlog links  $DAY --local "$R/NQ Studio/raw footage/2026-09-15" --local "$R/Mobile Uploads/2026-09-15"
./vlog ingest $DAY --local --edl 2026-09-15-rally-v2/data/edl.json   # only the 21 clips the cut uses
./vlog plan   $DAY --edl 2026-09-15-rally-v2/data/edl.json
./vlog fetch  $DAY --out $DAY/mezz --local
```

- The 21 clips the cut uses add up to about 112 GB. If they are online-only, the Dropbox app needs that much free
  space to download them; the disk check above says so before anything is read.
- Once `fetch` has finished, the mezzanines take about 2 GB, and you can free the rest in Finder: right-click the
  folder > Remove Download.
- Then put a `config.local.json` in `2026-09-15-rally-v2/`, as above with the 2026-09-15 paths, and run `./render.sh`.

## Having Claude run it on the Mac

In Terminal, in `~/UIUX`, run `claude` (Claude Code) or `claude remote-control`, or open the folder in the Claude
desktop app. That session runs the commands above on the Mac itself: its cores, its disk, its Dropbox folder. The
cloud session can't reach the Mac directly.

## What was tested where

- **In the cloud container (Linux), end to end:**
  - `doctor.py` passes on its generated clip;
  - local mode surveyed and cut real Sep 15 DJI clips, with Dropbox paths matched regardless of upper/lower case;
  - a clip missing from the machine is reported by name;
  - the online-only disk check stops a survey that wouldn't fit;
  - the Sep 15 build renders with the new path handling.
- **On Omarie's Mac (2026-09-27):** `setup-mac.sh` ran and `doctor.py` reported **READY**, which covers the tool
  checks and the end-to-end run on the generated clip. Whether VideoToolbox was switched on is in that Mac's
  `vlog.env` (`VLOG_HWACCEL`).
