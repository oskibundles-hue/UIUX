#!/usr/bin/env bash
#
# prep_clip.sh - work out how to cut and grade one clip, without keeping it.
#
# Downloads a clip once and gets two things out of it:
#
#   1. cut plans at several silence thresholds, so you can pick the pacing
#      before committing to an encode
#   2. a per-clip grade LUT, matched to your reference
#
# The per-clip LUT matters because one shared LUT is a fixed curve: it leaves
# bright scenes bright and flat scenes flat. Across a session whose clips range
# YAVG 90-122, that means posts will not match each other on the grid. Matching
# each clip to the reference separately puts them all in the same place.
#
# The clip is deleted afterwards. Only the plan and the LUT are kept.
#
# Usage:
#   ./prep_clip.sh <name> <url> <outdir> <ref-frames-glob>
#
# Example:
#   ./prep_clip.sh 22-51-35 "https://..." prep "hm/ref_*.ppm"

set -uo pipefail

NAME="${1:?usage: prep_clip.sh <name> <url> <outdir> <ref-glob>}"
URL="${2:?missing url}"
OUT="${3:?missing outdir}"
REF="${4:?missing reference frame glob}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }
mkdir -p "$OUT/src_$NAME"
TMP="$OUT/.$NAME.mov"
trap 'rm -f "$TMP"; rm -rf "$OUT/src_$NAME"' EXIT

echo "=== $NAME ==="
if ! curl -sSL --max-time 900 -o "$TMP" "$URL"; then
  echo "  FAILED: download error"; exit 1
fi

# curl exiting 0 is not proof of a usable file. A temporary download link that
# expired mid-transfer, or a truncated body, still yields exit 0 and a file
# ffmpeg cannot read - which then produces an empty grade and a LUT that was
# never written. Verify the video before doing anything with it.
secs=$(ffmpeg -hide_banner -i "$TMP" 2>&1 \
       | sed -n 's/.*Duration: \([0-9:.]*\),.*/\1/p' | head -1 \
       | awk -F: '{print int($1*3600+$2*60+$3)}')
if [ -z "${secs:-}" ] || [ "$secs" -lt 1 ]; then
  echo "  FAILED: downloaded $(du -h "$TMP" 2>/dev/null | cut -f1) but ffmpeg reads no duration."
  echo "          The link probably expired mid-transfer - fetch a fresh one."
  exit 1
fi
echo "  length ${secs}s"

# 1. Cut plans. Silence thresholds do not carry between clips - one that suits
#    a quiet walkthrough removes almost nothing from a clip recorded next to
#    running tools - so sweep rather than assume.
echo "  cut plans:"
for n in -26 -22 -20 -18; do
  plan=$(python3 "$HERE/autocut.py" "$TMP" --noise "$n" --min-silence 0.25 --dry-run 2>/dev/null)
  kept=$(sed -n 's/^length *: .*-> *\([0-9.]*\)s .*/\1/p' <<<"$plan")
  pct=$(grep -oE '[0-9]+%' <<<"$plan" | head -1)
  segs=$(sed -n 's/^silences *: .*-> *\([0-9]*\) segments.*/\1/p' <<<"$plan")
  avg=$(sed -n 's/^shot len *: *\([0-9.]*\)s.*/\1/p' <<<"$plan")
  printf "    noise %4s  ->  %6ss kept  %4s cut  %3s segs  %ss avg\n" \
         "$n" "${kept:-?}" "${pct:-?}" "${segs:-?}" "${avg:-?}"
done

# 2. Per-clip grade LUT. Sample across the whole clip so the histogram reflects
#    the clip rather than one moment in it.
for p in 10 25 40 55 70 85; do
  t=$((secs * p / 100))
  ffmpeg -y -loglevel error -ss "$t" -i "$TMP" -frames:v 1 \
         -vf "scale=216:384" -pix_fmt rgb24 "$OUT/src_$NAME/f$p.ppm" 2>/dev/null
done

if python3 "$HERE/match_grade.py" \
     --ref "$REF" --src "$OUT/src_$NAME/*.ppm" \
     --out "$OUT/AK_${NAME}.cube" --name "AK_${NAME}" 2>&1 | sed 's/^/    /'
   [ -f "$OUT/AK_${NAME}.cube" ]; then
  echo "  LUT: $OUT/AK_${NAME}.cube"
else
  echo "  FAILED: no LUT written"; exit 1
fi
