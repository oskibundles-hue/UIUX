#!/usr/bin/env bash
# Copy the assets Remotion needs into public/. They live elsewhere in the kit;
# Remotion can only serve from public/, so they are duplicated at build time
# rather than committed twice.
#
# Also selects which cut Remotion renders:
#   ./prepare-assets.sh                                 base cue
#   ./prepare-assets.sh ../variants/cue-b-get-a-quote.json   a variant
set -euo pipefail
cd "$(dirname "$0")"
CUE="${1:-../cue.json}"
KIT=../../..
mkdir -p public
cp ../source/plate-1080x1920.mp4                                    public/plate.mp4
cp $KIT/07-fonts/BebasNeue-Regular.ttf                              public/
cp $KIT/03-overlays/cta-captions/cta_9x16_booking_book-your-build_bar.png public/cta.png
cp $KIT/03-overlays/end-cards/endcard_9x16_dark.png                 public/endcard.png
python3 -c "import cairosvg; cairosvg.svg2png(url='$KIT/02-logos/svg-vector/fd-icon-mark-only--white.svg', write_to='public/fd-mark-white.png', output_width=400)"
cp "$CUE" src/cue.json
echo "public/ ready — cue: $CUE"
