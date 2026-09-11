#!/usr/bin/env bash
# Build one Fast Cut reel end to end: plan -> split -> assemble -> his-voice words -> props
# -> Remotion overlay -> compose -> QC. Upload is deliberately NOT part of this script.
#
#   ./build_reel.sh MR1 "the shop before" "THE SHOP, BEFORE ANYTHING" 01 02
#
# Environment (all optional, sensible defaults):
#   ROOT   working root that holds cuts/ and exports/   default: $PWD
#   WORK   scratch dir for plans, props, logs           default: $ROOT/work
#   CUTS   graded single clips, named "NN words.mp4"    default: $ROOT/cuts
#   OUTDIR finished reels land here                     default: $ROOT/exports
#   KIT    path to creator-kit                          default: resolved from this script
#   LOGO   corner logo bug PNG, or empty for none
#   CHROME headless chromium for Remotion
exec </dev/null
set -uo pipefail

KIT="${KIT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ROOT="${ROOT:-$PWD}"
WORK="${WORK:-$ROOT/work}"
CUTS="${CUTS:-$ROOT/cuts}"
OUTDIR="${OUTDIR:-$ROOT/exports}"
S="$KIT/scripts"
RM="$KIT/remotion"
CHROME="${CHROME:-/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell}"
LOGO="${LOGO:-}"
TARGET="${TARGET:-56}"
mkdir -p "$WORK" "$OUTDIR"

r="$1"; slug="$2"; hook="$3"; shift 3; clips=("$@")
ev(){ echo "$(date +%H:%M) $*" | tee -a "$WORK/events.log"; }

paths=(); for c in "${clips[@]}"; do
  p=$(ls "$CUTS"/$c\ *.mp4 2>/dev/null | head -1)
  [ -n "$p" ] || { ev "$r ABORT: no cut found for clip $c in $CUTS"; exit 1; }
  paths+=("$p")
done

# 1. plan the shot windows, 2. split anything over 4.5 s, 3. assemble the master
if [ ! -s "$WORK/$r.master.mp4" ] || [ ! -s "$WORK/$r.props.json" ]; then
  python3 "$S/plan_reel.py" --target "$TARGET" --tdir "$WORK/tx" --drop-dir "$WORK" \
    --out "$WORK/$r.plan.json" "${paths[@]}" > "$WORK/$r.plan.log" 2>&1 \
    || { ev "$r PLAN FAIL - see $WORK/$r.plan.log"; exit 1; }
  python3 "$(dirname "${BASH_SOURCE[0]}")/split_plan.py" "$WORK/$r.plan.json" >> "$WORK/$r.plan.log"
  python3 "$S/assemble_reel.py" "$WORK/$r.plan.json" "$WORK/$r.master.mp4" "$WORK/$r.props.json" \
    > "$WORK/$r.assemble.log" 2>&1 || { ev "$r ASSEMBLE FAIL"; exit 1; }
fi

# 4. collect the other-voice ranges so only his lines get captioned
python3 - "$WORK" "$r" "${clips[@]}" <<'PY'
import json, sys, os
work, r = sys.argv[1], sys.argv[2]; drop = {}
for c in sys.argv[3:]:
    f = os.path.join(work, f'drop_{c}.json')
    if os.path.exists(f):
        d = json.load(open(f)); drop[c] = d if isinstance(d, list) else d.get(c, d.get('ranges', []))
json.dump(drop, open(os.path.join(work, f'{r}.drop.json'), 'w'))
PY

# 5. map word timings through the plan and drop the other-voice ranges
python3 "$S/rewords.py" "$WORK/$r.plan.json" "$WORK/$r.props.json" "$WORK/tx" \
  "$WORK/$r.drop.json" >> "$WORK/$r.plan.log" 2>&1

# 6. build the overlay props: title, chapters, lower thirds, follow cards, wipes, outro
WORK="$WORK" python3 "$(dirname "${BASH_SOURCE[0]}")/props.py" "$r" "$slug" "$hook" \
  >> "$WORK/$r.plan.log" 2>&1 || { ev "$r PROPS FAIL - see $WORK/$r.plan.log"; exit 1; }

# 7. render the overlay alone, with alpha
rm -rf "$RM/node_modules/.cache" "$RM/out/$r.overlay.mov"
(cd "$RM" && REMOTION_ALPHA=1 npx remotion render src/index.ts Motion4K "out/$r.overlay.mov" \
  --props="$WORK/$r.overlay.json" --codec=prores --prores-profile=4444 \
  --pixel-format=yuva444p10le --image-format=png --browser-executable="$CHROME" \
  --concurrency=4 --log=error) > "$WORK/$r.render.log" 2>&1 \
  || { ev "$r RENDER FAIL - see $WORK/$r.render.log"; exit 1; }

# 8. composite, normalise loudness, limit
OUT="$OUTDIR/$r $slug (fast cut, motion graphics).mp4"
logo_args=(); [ -n "$LOGO" ] && logo_args=(--logo "$LOGO")
"$S/compose_reel.sh" "$WORK/$r.master.mp4" "$RM/out/$r.overlay.mov" "$WORK/$r.final.json" \
  "$OUT" "${logo_args[@]}" --sharpen 0 --limit 0.84 > "$WORK/$r.compose.log" 2>&1 \
  || { ev "$r COMPOSE FAIL - see $WORK/$r.compose.log"; exit 1; }
rm -f "$RM/out/$r.overlay.mov" "$WORK/$r.master.mp4"

# 9. score it and build a six-frame QC strip
python3 "$S/reel_check.py" "$OUT" --props "$WORK/$r.overlay.json" --json "$WORK/$r.check.json" \
  > "$WORK/$r.check.log" 2>&1
dur=$(python3 -c "import json;print(json.load(open('$WORK/$r.overlay.json'))['durationSeconds'])")
i=0; args=()
for f in 0.03 0.18 0.36 0.54 0.72 0.92; do
  t=$(python3 -c "print(round($dur*$f,2))")
  ffmpeg -y -loglevel error -ss "$t" -i "$OUT" -frames:v 1 -vf scale=216:384 "$WORK/${r}_q$i.png"
  args+=(-i "$WORK/${r}_q$i.png"); i=$((i+1))
done
ffmpeg -y -loglevel error "${args[@]}" -filter_complex "[0][1][2][3][4][5]hstack=6" "$WORK/${r}_qc.png"

score=$(python3 -c "import json;print(round(json.load(open('$WORK/$r.check.json'))['score']))" 2>/dev/null || echo '?')
flags=$(python3 -c "import json;print('; '.join(json.load(open('$WORK/$r.check.json'))['flags']) or 'none')" 2>/dev/null || echo '?')
ev "$r DONE - score $score - flags: $flags"
ev "$r file: $OUT"
ev "$r QC strip: $WORK/${r}_qc.png"
