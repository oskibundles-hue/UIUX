# Edit references: reusable tools

Tools for the edit references Muse relayed, built for the Anti Stock / @nq.young channel and layered on
the **Fast Cut** spec (2160x3840, 29.97 fps, -14 LUFS with the 0.84 limiter). They were built and
self-tested on **synthetic clips only**, because Dropbox's download host is blocked in the build container.
**Nothing here has been run on Omarie's footage yet**, and nothing in `tests/out/` is a cut or a preview.

| tool | what it does | reference |
|---|---|---|
| `rapid_zoom.py` | the rapid-zoom open: 10 clips x 3 frames, duplicate layer on Add, a radial/zoom blur that peaks on each cut, a sharp land on the payoff by 2.0 s, optional splice ahead of the rest of the reel | @cinamiti, https://www.instagram.com/reel/Dd4TKFYpsxH/ |
| `../../sfx/kit-v2/` + `gen_sfx_kit.py` | synthesised SFX palette: click trains, mechanical keys, button, whoosh, big flash, whoosh+flash, 3 glitches, zoom riser | @jerrzyo, https://www.instagram.com/reel/DczYt6Zvvam/ (palette), @tgmhoracio, https://www.instagram.com/reel/DdhI13HKeMv/, @cinamiti (riser) |
| `davinci_fx.py` | Anderson Tai's three DaVinci effects: `flashbox`, `flicker` (inverted flicker), `burn` (Difference light leak); `chain` runs several windows in one pass | Anderson Tai (@anderson.taii), https://www.instagram.com/reel/DexGqmKRJEC/ |
| `beats_to_spec.py` | car-only teaser, cut on drum hits: hit times to a Kinetic Cut spec, built by `../kinetic/build_kinetic.py` (mono grade, letterbox, flashes) | @olafmotion, https://www.instagram.com/reel/De8qfjUMPZr/ and @jonasblk_, https://www.instagram.com/reel/Dc9W92HMyq_/ |
| `master_loudness.py` | re-masters any video's audio: two-pass loudnorm -14 LUFS, then `alimiter limit=0.84 level=false` | the Fast Cut chain in `../../scripts/compose_reel.sh` |
| `media.py` | shared ffmpeg pipes, WAV I/O, the loudness chain | |

## How each effect is made

**Rapid zoom.** ffmpeg has no radial blur, so each frame is processed in numpy and Pillow. The blur
averages `--samples` (12) copies of the frame scaled up about the centre, from 1.0 to 1+`--blur` (0.22),
on top of a punch-in of 1+`--punch` (112%). Both are keyed per frame: full strength on the cut frame,
then `(1 - k/3)^2` over the next frames (1.0, 0.44, 0.11 across a 3-frame clip). The duplicate layer is a
copy of the run with each clip trimmed by 2 frames (`--trim-from tail` keeps the first frame, so the
doubled frame sits on the cut). Add is `base + top`, clipped to 1.0, so that frame doubles in brightness
and the highlights blow out. The blur is applied over the composite, like an adjustment layer over both
tracks. The payoff comes in sharp on frame 30 (1.001 s) and holds for `--hold` (1.0 s). The tool refuses a
setup that lands after 2.0 s. Each run writes `<out>.json` with every frame's source, strength and Add flag,
the land frame and where each SFX was placed.

**Flashbox.** Over 4–6 frames around a cut (`--frames`, split `--before`/after). `white` ramps a white
flash up into the cut, holds full white on the cut frame, then decays. `box` grows a white box from the
centre to fill the frame by the cut, then opens the incoming shot through a growing box-shaped hole with
a thin white rule.

**Inverted flicker.** Inverted frames alternate with normal ones (`--period` frames each) across the
window. Resolve uses Magic Mask on the subject, and there is none here. `--mode full` inverts the whole
frame. `--mode luma` inverts only a soft luminance key (`--thresh` 0.6, `--soft` 0.1), so only the bright
parts flip: paint highlights, sky, lights. On a light car against a dark background, luma is the
nearest thing to a subject mask. On a dark car it keys the background, so use full.

**Difference burn.** The overlay is procedural, and no stock overlay is used. It combines value noise
keyed every 0.4 s on a coarse grid and eased between keys, a radial glow drifting across the frame and a
streak from one edge. It is tinted (`--tint`, default warm amber `FF963C`, which is not a brand colour)
and runs toward white at the hot core. It is composited as `|base - overlay|` at `--opacity`, with
`--fade` in and out. `--seed` changes the leak.

## SFX kit v2

`python3 gen_sfx_kit.py` writes `../../sfx/kit-v2/*.wav`, `audition.wav` and `kit.json`. The output is
deterministic, at 48 kHz 24-bit stereo with a -1 dBFS peak. The full list with hit times is in
`../../sfx/MANIFEST.md`, and the licence (synthesised in-repo, free to use) is in `../../sfx/kit-v2/LICENCE.md`.

## Self-test

    python3 tests/selftest.py          # full res, about 6.5 min on 4 cores
    python3 tests/selftest.py --quick  # rapid_zoom at --work-res 1080x1920

It builds testsrc2 clips and checks the kit's format and peaks. For rapid_zoom and each davinci_fx effect
it checks duration, 2160x3840 and 29.97 fps. It also checks that the land frame has a higher Laplacian
variance than every blurred cut frame, that loudness is -14 LUFS ±1 with the master peak at or below 0.84,
and that the teaser path (beats_to_spec, build_kinetic, master_loudness) runs end to end. Outputs go to
`tests/out/` (git-ignored).

## The real-footage runs (for the lead, once Dropbox is reachable)

Run from this folder. `F` is wherever the clips land. Feed graded clips (`../../scripts/cut_clip.sh`,
the vlog grade) if the opening should match the rest of a Fast Cut reel; the tools don't grade.

### Test 1: rapid-zoom open on the stock M2 clips

Pick 10 run clips with an in-point each (a moment with movement or a strong shape), plus the payoff shot
(the best M2 angle).

    F=/path/to/m2-stock
    python3 rapid_zoom.py \
      --clips "$F/m2_01.mp4@2.0" "$F/m2_02.mp4@5.4" "$F/m2_03.mp4@1.2" "$F/m2_04.mp4@3.3" \
              "$F/m2_05.mp4@0.8" "$F/m2_06.mp4@7.1" "$F/m2_07.mp4@2.6" "$F/m2_08.mp4@4.0" \
              "$F/m2_09.mp4@1.5" "$F/m2_10.mp4@6.2" \
      --payoff "$F/m2_hero.mp4" --payoff-in 3.0 --hold 1.5 \
      --sfx --out out/test1_m2_open.mp4

Opening plus the rest of the reel in one file:

    ... --remainder "$F/m2_rest.mp4" --remainder-in 0 --remainder-dur 12 --out out/test1_m2_full.mp4

To try the DaVinci effects on that result (times are on the output; cut times are in `out/test1_m2_full.json`):

    cat > out/fx_test1.json <<'J'
    [{"fx": "flashbox", "at": 2.50, "frames": 5, "mode": "box"},
     {"fx": "flicker", "start": 4.0, "end": 4.6, "mode": "luma", "period": 1},
     {"fx": "burn", "start": 6.0, "end": 8.5, "opacity": 0.7, "seed": 2}]
    J
    python3 davinci_fx.py chain --in out/test1_m2_full.mp4 --spec out/fx_test1.json --out out/test1_m2_fx.mp4

Check a contact sheet before showing anything (frame numbers stamped):

    ffmpeg -v error -i out/test1_m2_open.mp4 -vf "select='lt(n\,60)',scale=320:-2,drawtext=text='%{n}':x=6:y=6:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6,tile=10x6" -frames:v 1 out/test1_sheet.jpg

Speed: on 4 cores the full-res self-test open (60 frames plus a 3 s remainder) took 115 s. `--work-res 1080x1920` is about
4x faster and still writes 2160x3840 (upscaled at encode), so use it for drafts.

### Test 3: MC20 car-only teaser, 15–20 s, cut on drum hits, no talking

**What cutting on hits needs that isn't in the repo:** a music bed and its drum-hit times. There is no
licensed bed in the repo. Once there is one, list its hits one per line in seconds (tap them in any editor,
or detect them with `ffmpeg -i bed.wav -af "highpass=f=60,lowpass=f=180,silencedetect=n=-24dB:d=0.05" -f null -`,
where each `silence_end` is a kick onset; check them by ear). Keep only the hits you want cuts on, 15–20 s worth.

    F=/path/to/mc20
    python3 beats_to_spec.py --beats out/mc20_hits.txt \
      --clips "MC20 front.mp4@4.0" "MC20 wheel.mp4@2.2" "MC20 rear.mp4@6.5" "MC20 badge.mp4@1.0" \
              "MC20 pan.mp4@3.4" "MC20 interior.mp4@0.5" \
      --audio-track out/bed.wav --flash --max-seconds 20 --out out/spec_mc20.json
    python3 ../kinetic/build_kinetic.py --spec out/spec_mc20.json --footage "$F" \
      --work out/mc20_work --out out/mc20_kinetic.mp4 --width 2160 --height 3840
    # film grain (B&W look), then master the audio
    ffmpeg -v error -y -i out/mc20_kinetic.mp4 -vf "noise=alls=14:allf=t" -c:v libx264 -crf 16 -c:a copy out/mc20_grain.mp4
    python3 master_loudness.py out/mc20_grain.mp4 out/test3_mc20.mp4

`--saturation 0 --contrast 1.35` is the high-contrast B&W default. For the night grade instead, pass
`--saturation 0.35 --brightness -0.08 --gamma 0.9` (a cool cast needs a separate `colorbalance=bs=0.08`
pass, since the kinetic grade is eq only). Optional accents on hits: add `{"file":
"../../sfx/kit-v2/big_flash.wav", ...}` entries only if the bed lacks them. build_kinetic.py
plays `audio_track` without its `audio` list, so mix those into the bed first.

## Limits found

- **Shot fps.** build_kinetic.py takes an integer `--fps` (30), not 29.97. Teaser outputs are 30 fps unless
  that builder changes. The rapid-zoom and DaVinci tools write 29.97.
- **True peak.** `alimiter` is a sample-peak limiter. The WAV master holds 0.84 (-1.5 dBFS), but the AAC
  encode adds intersample peak: the self-test open measured -13.83 LUFS at -1.10 dBTP. This is the same
  chain as the Fast Cut reels.
- **Peaky audio can't reach -14.** A sparse bed (clicks with silence between) can't reach -14 LUFS under
  the 0.84 ceiling. loudnorm backs off and the master lands quiet (a click bed came out at -23 LUFS).
  Forcing the gain into the limiter was tried: it reached -20 LUFS with +1.5 dBTP overs, so it was dropped.
  The master now prints a warning when it lands more than 1 LU off. A real music bed or the dense
  whoosh_flash open is fine. Master once over the whole piece (`--remainder`, or `master_loudness.py` on
  the final), not per section.
- **No Magic Mask.** The luma key in `flicker --mode luma` is not a subject mask (see above).
- **Speed.** It's per-frame Python. Fine for a 2 s open or a few short windows. `davinci_fx.py` decodes
  and re-encodes the whole input, so on a long reel run `chain` once with all windows rather than one effect
  at a time.
- **Interpretation.** "2 frames trimmed off each top clip" is read as each duplicate clip keeping one
  frame (the first, by default) over the 3-frame base clip. `--trim-from head` keeps the last frame.
  `--trim 1` keeps two.
