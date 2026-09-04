#!/usr/bin/env bash
#
# cut_clip.sh - turn one downloaded raw clip into an upload-ready Reel.
#
# Runs the whole edit off a SINGLE local file: build a grade matched to that
# clip, pick the silence threshold that lands on your cutting rhythm, cut,
# grade and export 4K. The source is left alone; downloading and deleting is
# the caller's job, because temporary Dropbox links expire and a script that
# holds one while it encodes for half an hour will fail.
#
# Two decisions are made for you, both from measurements rather than taste:
#
#   THE GRADE is matched per clip. One shared LUT is a fixed curve, and this
#   session's clips range YAVG 90-122, so a single LUT leaves the bright ones
#   bright and the posts do not match each other on the grid.
#
#   THE SILENCE THRESHOLD is swept, and the one whose average shot length
#   lands closest to --rhythm is chosen. Your published edit averages ~4s
#   shots; -26 dB removes almost nothing from a clip recorded next to running
#   tools, while -18 dB shreds a quiet walkthrough. Sweeping per clip is the
#   only thing that holds the pacing steady across a session.
#
#   THE WINDOW. A nine-minute take silence-cut end to end is a seven-minute
#   file, which is not a Reel and is not something you would ever upload. Past
#   --window seconds, speech_window.py picks the most talkative stretch and only
#   that stretch is edited. It is also 10x cheaper to encode, because ffmpeg
#   then decodes a minute of 4K instead of nine.
#
# Usage:
#   ./cut_clip.sh <source.mov> <output.mp4> [--rhythm 4.0] [--window 60]
#                 [--ref 'glob'] [--target-mb 75]
#
# Example:
#   ./cut_clip.sh work/raw.mov "exports/06 wall trim install.mp4"

set -uo pipefail

SRC="${1:?usage: cut_clip.sh <source> <output> [--rhythm N] [--ref glob]}"
OUT="${2:?missing output}"
shift 2

RHYTHM=4.0
REF="/home/user/footage/hm/ref_*.ppm"
TARGET_MB=75
WINDOW=60
while [ $# -gt 0 ]; do
  case "$1" in
    --rhythm) RHYTHM="$2"; shift 2 ;;
    --ref)    REF="$2"; shift 2 ;;
    --target-mb) TARGET_MB="$2"; shift 2 ;;
    --window) WINDOW="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/root/bin:$PATH"
command -v ffmpeg >/dev/null || { echo "ffmpeg not found on PATH" >&2; exit 1; }
[ -f "$SRC" ] || { echo "source not found: $SRC" >&2; exit 1; }

NAME="$(basename "$OUT" .mp4)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$(dirname "$OUT")"

echo "=== $NAME ==="

# A file that downloaded with exit 0 is not necessarily a file ffmpeg can read.
# An expired link yields a truncated body and a clean exit code.
secs=$(ffmpeg -hide_banner -i "$SRC" 2>&1 \
       | sed -n 's/.*Duration: \([0-9:.]*\),.*/\1/p' | head -1 \
       | awk -F: '{print int($1*3600+$2*60+$3)}')
if [ -z "${secs:-}" ] || [ "$secs" -lt 1 ]; then
  echo "  FAILED: $(du -h "$SRC" | cut -f1) on disk but ffmpeg reads no duration."
  echo "          Truncated download - fetch a fresh link."
  exit 1
fi
echo "  source   ${secs}s"

# 0. If the take runs long, edit only its most talkative window. Stream-copied,
#    so pulling the window out costs no quality and almost no time - the seek
#    lands on the nearest keyframe, which is close enough at 60fps.
CLIP="$SRC"
if [ "$secs" -gt "$(python3 -c "print(int($WINDOW*1.4))")" ]; then
  read -r wstart wlen < <(python3 "$HERE/speech_window.py" "$SRC" \
                          --window "$WINDOW" --noise -22 --report 2>"$WORK/win.txt")
  sed 's/^/  /' "$WORK/win.txt"
  ffmpeg -y -loglevel error -ss "$wstart" -t "$wlen" -i "$SRC" -c copy "$WORK/window.mov"
  if [ ! -s "$WORK/window.mov" ]; then echo "  FAILED: could not cut the window"; exit 1; fi
  CLIP="$WORK/window.mov"
  secs=$(python3 -c "print(int($wlen))")
  echo "  window   ${wstart}s +${wlen}s"
fi

# 1. Grade matched to this clip. Sample across the whole clip so the histogram
#    reflects the clip and not one moment in it.
for p in 10 25 40 55 70 85; do
  ffmpeg -y -loglevel error -ss $((secs * p / 100)) -i "$CLIP" -frames:v 1 \
         -vf "scale=216:384" -pix_fmt rgb24 "$WORK/f$p.ppm" 2>/dev/null
done
nsrc=$(ls "$WORK"/f*.ppm 2>/dev/null | wc -l)
if [ "$nsrc" -lt 3 ]; then
  echo "  FAILED: only $nsrc source frames extracted; cannot match a grade."
  exit 1
fi
LUT="$WORK/grade.cube"
python3 "$HERE/match_grade.py" --ref "$REF" --src "$WORK/*.ppm" \
        --out "$LUT" --name "AK_${NAME// /_}" 2>&1 | sed 's/^/  /'
if [ ! -f "$LUT" ]; then echo "  FAILED: no LUT written"; exit 1; fi

# 2. Sweep the silence threshold and take the one closest to the target rhythm.
echo "  cut plans:"
best_n=""; best_d=""
for n in -26 -24 -22 -20 -18; do
  plan=$(python3 "$HERE/autocut.py" "$CLIP" --noise "$n" --min-silence 0.25 --dry-run 2>/dev/null)
  avg=$(sed -n 's/^shot len *: *\([0-9.]*\)s.*/\1/p' <<<"$plan")
  kept=$(sed -n 's/^length *: .*-> *\([0-9.]*\)s .*/\1/p' <<<"$plan")
  pct=$(grep -oE '[0-9]+%' <<<"$plan" | head -1)
  [ -z "${avg:-}" ] && { printf "    %4s  (no plan)\n" "$n"; continue; }
  d=$(python3 -c "print('%.4f' % abs($avg - $RHYTHM))")
  printf "    %4s dB  ->  %6ss kept  %4s cut  %ss avg shot\n" "$n" "${kept:-?}" "${pct:-?}" "$avg"
  if [ -z "$best_d" ] || [ "$(python3 -c "print(1 if $d < $best_d else 0)")" = 1 ]; then
    best_d="$d"; best_n="$n"
  fi
done
[ -n "$best_n" ] || { echo "  FAILED: no usable cut plan"; exit 1; }
echo "  chosen   ${best_n} dB (closest to a ${RHYTHM}s rhythm)"

# 3. Cut, grade, export. One decode of the source for the whole thing.
python3 "$HERE/autocut.py" "$CLIP" -l "$LUT" -o "$OUT" \
        --noise "$best_n" --min-silence 0.25 --target-mb "$TARGET_MB" 2>&1 | sed 's/^/  /'

if [ ! -f "$OUT" ]; then echo "  FAILED: no output written"; exit 1; fi
mb=$(( $(stat -c%s "$OUT") / 1048576 ))
dur=$(ffmpeg -hide_banner -i "$OUT" 2>&1 | sed -n 's/.*Duration: \([0-9:.]*\),.*/\1/p' | head -1)
dim=$(ffmpeg -hide_banner -i "$OUT" 2>&1 | grep -o '[0-9]\{3,4\}x[0-9]\{3,4\}' | head -1)
echo "  DONE     $OUT  ${dim}  ${dur}  ${mb} MB"
