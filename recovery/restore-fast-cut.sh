#!/usr/bin/env bash
# Restore the 26 Anti Stock source files that have no copy in Dropbox.
#
# Context: on 2026-09-22 a review of the artifacts page ("Download Everything")
# confirmed that /Portfolio/03 Personal Vlogs/Fast Cut Series/ does not exist in
# Dropbox at all, and Singles/ next to it holds only its README.md. That is 8
# Fast Cut masters + 18 graded Singles = 26 files, 8.60 GB, whose only surviving
# copies are CloudFront URLs published on the artifacts page. A CDN is a cache,
# not storage. All 26 were verified reachable on 2026-09-22 (HTTP 206, sizes in
# the manifest); they are not guaranteed to stay reachable.
#
# The Fast Cut re-render scheduled 2026-09-22 (wrong red #DE1A22 -> #FE0F13,
# Telemetry overlay + FD icon, rebuild MR3/MR4/MR6 captions) cannot run until
# these are back, because every Fast Cut is assembled from the Singles.
#
# Run this on a machine where Dropbox syncs. It is safe to re-run: existing
# files of the right size are skipped, partial downloads resume.
#
# Usage:
#   ./restore-fast-cut.sh                     # writes into the default Dropbox path below
#   DEST="/path/to/Dropbox/Portfolio/03 Personal Vlogs" ./restore-fast-cut.sh
#   DRY_RUN=1 ./restore-fast-cut.sh           # check reachability + sizes, download nothing

set -uo pipefail

DEST="${DEST:-$HOME/Dropbox/Portfolio/03 Personal Vlogs}"
MANIFEST="${MANIFEST:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fast-cut-manifest.tsv}"
DRY_RUN="${DRY_RUN:-0}"

[ -f "$MANIFEST" ] || { echo "manifest not found: $MANIFEST" >&2; exit 1; }

if [ "$DRY_RUN" != "1" ]; then
  if [ ! -d "$DEST" ]; then
    echo "Destination does not exist: $DEST" >&2
    echo "Set DEST to your Dropbox '03 Personal Vlogs' folder and re-run." >&2
    exit 1
  fi
  mkdir -p "$DEST/Fast Cut Series" "$DEST/Singles"
fi

ok=0; skip=0; fail=0; failed_names=()

while IFS=$'\t' read -r status folder name size url; do
  [ "$status" = "OK" ] || continue

  case "$folder" in
    FastCutSeries) sub="Fast Cut Series" ;;
    Singles)       sub="Singles" ;;
    *)             echo "unknown folder in manifest: $folder" >&2; fail=$((fail+1)); continue ;;
  esac

  out="$DEST/$sub/$name"

  if [ "$DRY_RUN" = "1" ]; then
    live=$(curl -sS -o /dev/null -D - -r 0-1 --max-time 60 "$url" 2>/dev/null \
            | sed -nE 's@^[Cc]ontent-[Rr]ange:.*/([0-9]+).*@\1@p' | tail -1)
    if [ "$live" = "$size" ]; then
      echo "reachable  $sub/$name  ($size bytes)"; ok=$((ok+1))
    else
      echo "UNREACHABLE or size changed  $sub/$name  (expected $size, got ${live:-none})" >&2
      fail=$((fail+1)); failed_names+=("$sub/$name")
    fi
    continue
  fi

  if [ -f "$out" ] && [ "$(wc -c < "$out" | tr -d ' ')" = "$size" ]; then
    echo "have     $sub/$name"; skip=$((skip+1)); continue
  fi

  echo "fetching $sub/$name  ($size bytes)"
  # --continue-at resumes a partial file; retries cover transient CDN/network errors.
  if curl -fL --continue-at - --retry 5 --retry-delay 3 --retry-all-errors \
          --connect-timeout 30 -o "$out" "$url"; then
    got=$(wc -c < "$out" | tr -d ' ')
    if [ "$got" = "$size" ]; then
      echo "  ok     $got bytes"; ok=$((ok+1))
    else
      echo "  SIZE MISMATCH: got $got, expected $size" >&2
      fail=$((fail+1)); failed_names+=("$sub/$name")
    fi
  else
    echo "  DOWNLOAD FAILED" >&2
    fail=$((fail+1)); failed_names+=("$sub/$name")
  fi
done < "$MANIFEST"

echo
echo "----------------------------------------"
if [ "$DRY_RUN" = "1" ]; then
  echo "reachable: $ok   problems: $fail"
else
  echo "downloaded: $ok   already had: $skip   failed: $fail"
fi

if [ "$fail" -gt 0 ]; then
  echo
  echo "These still have no Dropbox copy:" >&2
  for n in "${failed_names[@]}"; do echo "  - $n" >&2; done
  echo "Re-run to retry (completed files are skipped)." >&2
  exit 1
fi

echo "All $((ok + skip)) accounted for. Do not start the re-render until this reports 26."
