#!/usr/bin/env bash
#
# ig_export.sh - Osmo Action 6 -> Instagram Reel master
#
# Takes a DJI Osmo Action 6 clip (typically 10-bit HEVC D-Log M) and produces
# the sharpest file Instagram will actually accept: 1080x1920, H.264 High,
# yuv420p, correctly tagged bt709, faststart, loudness-normalised audio.
#
# Why 1080x1920 and not 4K: Instagram re-encodes everything and downscales
# anything above 1080 on the long edge. Handing it a clean, correctly-tagged
# 1080x1920 master means you control the downscale (good lanczos resampling,
# your own sharpening) instead of letting their encoder do it badly. Uploading
# 4K spends bandwidth on pixels that get thrown away, and often looks softer.
#
# Requires: ffmpeg (with libx264, lut3d, unsharp, loudnorm)
#
# Usage:
#   ./ig_export.sh input.mp4 [options]
#
# Options:
#   -c, --convert-lut FILE   D-Log M -> Rec.709 conversion LUT (.cube)
#                            Get the official one from https://www.dji.com/lut
#   -l, --look FILE          Creative look LUT, applied after the conversion
#   -m, --mode MODE          fill | fit | blur   (default: fill)
#                              fill - centre-crop to 9:16, no bars, loses sides
#                              fit  - letterbox with black bars
#                              blur - fit with a blurred fill behind
#   -f, --fps N              output frame rate (default: keep source)
#   -s, --start TIME         trim start, e.g. 00:00:03.5
#   -t, --duration SECS      trim duration
#   -b, --bitrate RATE       max bitrate (default 14M)
#       --crf N              quality, lower is better (default 17)
#       --sharpen AMOUNT     0 disables (default 0.7)
#       --tonemap            input is HLG/HDR; tonemap to SDR
#       --assume-hlg         with --tonemap, treat an untagged source as
#                            HLG/BT.2020 instead of trusting its (missing) tags
#       --no-loudnorm        skip audio loudness normalisation
#   -o, --output FILE        output path (default: <input>_IG.mp4)
#
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }

command -v ffmpeg >/dev/null || die "ffmpeg not found on PATH"

IN=""; CONV_LUT=""; LOOK_LUT=""; MODE="fill"; FPS=""; START=""; DUR=""
BITRATE="14M"; CRF="17"; SHARPEN="0.7"; TONEMAP=0; LOUDNORM=1; OUT=""
ASSUME_HLG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--convert-lut) CONV_LUT="$2"; shift 2 ;;
    -l|--look)        LOOK_LUT="$2"; shift 2 ;;
    -m|--mode)        MODE="$2"; shift 2 ;;
    -f|--fps)         FPS="$2"; shift 2 ;;
    -s|--start)       START="$2"; shift 2 ;;
    -t|--duration)    DUR="$2"; shift 2 ;;
    -b|--bitrate)     BITRATE="$2"; shift 2 ;;
    --crf)            CRF="$2"; shift 2 ;;
    --sharpen)        SHARPEN="$2"; shift 2 ;;
    --tonemap)        TONEMAP=1; shift ;;
    --assume-hlg)     ASSUME_HLG=1; TONEMAP=1; shift ;;
    --no-loudnorm)    LOUDNORM=0; shift ;;
    -o|--output)      OUT="$2"; shift 2 ;;
    -h|--help)        sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)               die "unknown option: $1" ;;
    *)                IN="$1"; shift ;;
  esac
done

[[ -n "$IN" ]]    || die "no input file given (see --help)"
[[ -f "$IN" ]]    || die "input not found: $IN"
[[ -z "$CONV_LUT" || -f "$CONV_LUT" ]] || die "conversion LUT not found: $CONV_LUT"
[[ -z "$LOOK_LUT" || -f "$LOOK_LUT" ]] || die "look LUT not found: $LOOK_LUT"
case "$MODE" in fill|fit|blur) ;; *) die "mode must be fill, fit or blur" ;; esac

[[ -n "$OUT" ]] || OUT="${IN%.*}_IG.mp4"

W=1080; H=1920

# lut3d paths are parsed by ffmpeg's filter grammar, so : \ and ' need escaping.
esc_path() { printf '%s' "$1" | sed -e "s/\\\\/\\\\\\\\/g" -e "s/:/\\\\:/g" -e "s/'/\\\\'/g"; }

VF=""
add() { [[ -z "$VF" ]] && VF="$1" || VF="$VF,$1"; }

# HDR/HLG sources need tonemapping before anything else touches the pixels.
if [[ $TONEMAP -eq 1 ]]; then
  # tonemap only accepts linear-light float input, hence the gbrpf32le hop.
  # Dropping it gives an opaque "Generic error in an external library".
  # An untagged source makes zscale fail with "no path between colorspaces".
  # zscale's own tin/min/pin overrides do not fix it - they describe the
  # conversion, not the stream - so stamp the tags on with setparams first.
  if [[ $ASSUME_HLG -eq 1 ]]; then
    add "setparams=color_primaries=bt2020:color_trc=arib-std-b67:colorspace=bt2020nc"
  fi
  add "zscale=t=linear:npl=100"
  add "format=gbrpf32le"
  add "tonemap=hable:desat=0"
  add "zscale=t=bt709:m=bt709:p=bt709:r=tv"
fi

# Work at 16-bit RGB through the LUT stage. LUTs are defined on RGB, and doing
# this at 8-bit is where banding in skies and shadows comes from.
if [[ -n "$CONV_LUT" || -n "$LOOK_LUT" ]]; then
  add "format=gbrp16le"
  [[ -n "$CONV_LUT" ]] && add "lut3d=file='$(esc_path "$CONV_LUT")':interp=tetrahedral"
  [[ -n "$LOOK_LUT" ]] && add "lut3d=file='$(esc_path "$LOOK_LUT")':interp=tetrahedral"
fi

# Reframe to 1080x1920. Scaling happens in one lanczos step for maximum detail
# retention on the big 4K -> 1080 downscale.
case "$MODE" in
  fill)
    add "scale=w=${W}:h=${H}:force_original_aspect_ratio=increase:flags=lanczos"
    add "crop=${W}:${H}"
    ;;
  fit)
    add "scale=w=${W}:h=${H}:force_original_aspect_ratio=decrease:flags=lanczos"
    add "pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:black"
    ;;
  blur)
    VF="${VF:+$VF,}split=2[bg][fg];\
[bg]scale=w=${W}:h=${H}:force_original_aspect_ratio=increase:flags=bilinear,\
crop=${W}:${H},gblur=sigma=28[bgb];\
[fg]scale=w=${W}:h=${H}:force_original_aspect_ratio=decrease:flags=lanczos[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2"
    ;;
esac

# Sharpen AFTER the downscale. Instagram's encoder eats fine detail, so a
# little pre-sharpening survives where the original detail would not. Too much
# and the transcode turns edges into ringing artefacts - 0.7 is a safe ceiling.
if [[ "$SHARPEN" != "0" ]]; then
  add "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=${SHARPEN}:chroma_amount=0"
fi

[[ -n "$FPS" ]] && add "fps=${FPS}"

# Force square pixels. Scaling can leave a fractional sample aspect ratio
# behind (e.g. 10240:10239), and some players honour it and letterbox the
# result. Reels must be exactly 1080x1920 with 1:1 pixels.
add "setsar=1"
add "format=yuv420p"

AF=""
[[ $LOUDNORM -eq 1 ]] && AF="loudnorm=I=-14:TP=-1.5:LRA=11"

# VBV buffer of 2x the max bitrate. Computed here because ffmpeg's -bufsize
# takes a plain number with an optional K/M suffix, not an expression.
case "$BITRATE" in
  *[Mm]) BUFSIZE="$(( ${BITRATE%[Mm]} * 2 ))M" ;;
  *[Kk]) BUFSIZE="$(( ${BITRATE%[Kk]} * 2 ))K" ;;
  *)     BUFSIZE="$(( BITRATE * 2 ))" ;;
esac

TRIM=()
[[ -n "$START" ]] && TRIM+=(-ss "$START")
[[ -n "$DUR" ]]   && TRIM+=(-t "$DUR")

echo "input   : $IN"
echo "output  : $OUT"
echo "mode    : $MODE  ->  ${W}x${H}"
[[ -n "$CONV_LUT" ]] && echo "convert : $CONV_LUT" || echo "convert : (none - source assumed already Rec.709)"
[[ -n "$LOOK_LUT" ]] && echo "look    : $LOOK_LUT"
echo

if [[ $TONEMAP -eq 1 && $ASSUME_HLG -eq 0 ]]; then
  echo "note: --tonemap reads the source's colour tags. If this fails with"
  echo "      'Generic error in an external library', the file is untagged -"
  echo "      re-run with --assume-hlg."
  echo
fi

set -x
ffmpeg -y -hide_banner "${TRIM[@]}" -i "$IN" \
  -filter_complex "$VF" \
  ${AF:+-af "$AF"} \
  -c:v libx264 -preset slow -crf "$CRF" \
  -maxrate "$BITRATE" -bufsize "$BUFSIZE" \
  -profile:v high -level 4.2 \
  -x264-params "ref=4:bframes=3:aq-mode=2:aq-strength=1.0" \
  -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 256k -ar 48000 -ac 2 \
  -movflags +faststart \
  "$OUT"
set +x

echo
echo "done: $OUT"
# ffprobe ships with most ffmpeg builds but not all, so fall back to ffmpeg -i.
if command -v ffprobe >/dev/null; then
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate,pix_fmt,color_space,profile \
    -show_entries format=duration,size,bit_rate -of default=noprint_wrappers=1 "$OUT" || true
else
  ffmpeg -hide_banner -i "$OUT" 2>&1 | grep -E "Stream #|Duration" || true
fi
