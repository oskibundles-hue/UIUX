# Service ads cut from real footage

The R1–R8 reels in `11-service-reels/` are pure motion graphics — they were
built because there was no service footage to cut against. These are the other
thing: **the shop's own video with the graphic system burned onto it.** Same
brand kit, same overlay set, real cars.

Use these for the specials. A motion-graphic reel explains an offer; footage of
a real car carries it.

---

## There is no footage of the services themselves

No oil change on camera, no brake job, no film going onto glass. So the
services are explained **through the cars**: the hero clips carry the argument,
the spec chips name the work, and the ticker carries the conditions. The cars
are the reason someone buys a $3,999 package in the first place, so leading
with them is not a compromise.

When service footage does exist — a lift, a torque wrench, film being squeegeed
onto a windshield — these same ads get stronger by swapping shots, not by being
rebuilt.

---

## How one gets made

Three steps, and only the first needs judgement.

**1. Read the source at one-second resolution, then pick shots.**

```bash
ffmpeg -nostdin -y -i gt3.mov -vf "fps=1,scale=150:-1,tile=10x3" -frames:v 1 sheet.png
```

A sheet at two-second intervals is not precise enough — shots picked off one
landed on the wrong frames twice. Every second, or the choice is a guess.

**2. Cut the shots and concatenate, re-encoding.**

```bash
while read src st du; do
  ffmpeg -nostdin -y -ss $st -i $src -t $du \
    -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1" \
    -c:v libx264 -crf 17 -c:a aac -video_track_timescale 30000 seg$n.mp4
done < shots.txt
ffmpeg -nostdin -y -f concat -safe 0 -i list.txt -c:v libx264 -crf 18 ... out.mp4
```

`-nostdin` matters: without it ffmpeg swallows the shot list and the remaining
shots vanish silently. And **do not `-c copy` the concat** — copying segments
whose sources have different timebases yields a file with the right duration
and a broken frame timeline.

**3. Burn the overlays on, then again with `--motion`.**

```bash
python3 ../99-toolkit/build_edit.py montage.mp4 -t service \
  --title-text 'ANNUAL SERVICE|$3,999' --title-scrim \
  --title-block 'ANNUAL SERVICE PACKAGE|$3,999 PER YEAR' \
  --ticker 'OIL INCLUDED|PADS NOT INCLUDED' \
  --spec '2 OIL SERVICES' --spec '1 BRAKE SERVICE' \
  --spec '2 DIAGNOSTICS' --spec '10% OFF UPGRADES' \
  --none badge --bitrate 9M -o out.mp4
```

The `--motion` pass is a separate deliverable, not a replacement — the plain
cut still ships. Always `--dry-run` first; the cue sheet is where the problems
are visible.

---

## What we learned building these

**Chip legibility is a function of clip length.** The spec window is derived
from the duration, so the same four chips got 0.42 s each on a 19-second cut
and 0.35 s on a 17-second one — unreadable both times. At **22 seconds they
hold 1.4 s each**. If four chips matter, the cut has to be long enough to carry
them. Read it off the dry run; don't guess.

**Put conditions in the ticker, not a chip.** "Oil included / pads not
included" has to be legible or it is not a disclosure. In a chip it gets about
a second; in the ticker it holds for six.

**Drop the badge when specs are running.** They share a band, and the first
render stacked "1 BRAKE SERVICE" on top of "SERVICE" — both illegible.
`--none badge`, and the badge was redundant against the title block anyway.

**Check the CTA name.** `--cta` takes the slug alone — `we-service-what-we-build`
— because the group comes from the template. Passing the group with it silently
drops the CTA and produces an ad with no ask. Nothing errors; the layer just is
not in the cue sheet.

**Keep the ticker clear of Instagram's action rail.** Measured on a rendered
frame, a three-segment ticker ran to x=1043 of 1080 — the rail starts at 907,
so the last segment sat under the like and share buttons. That segment was
"CERAMIC INCLUDED", the offer's whole point. Two segments end at x=819, clear.
Measure it rather than eyeball it:

```python
band = frame[int(H*0.79):int(H*0.87), :]
ink  = np.where(band.max(axis=0) > 200)[0]
assert ink.max() <= W*0.84    # IG action rail
```

Put the segment that must survive **first**, on the left, where nothing covers
it.

**Set `--bitrate 9M`.** The 20M default put 42 MB behind 19 seconds. 9M is
13 MB for the same picture.

---

## Built

### Annual Service Package — $3,999

`FD-Annual-Service-3999.mp4` · 22.5 s · SF90, GT3 RS and Roma

| | Shot | Carries |
|---|---|---|
| 1 | SF90 gold rolling on the highway | The buyer's car |
| 2 | Forged wheel, yellow ceramic caliper | Brake service |
| 3 | GT3 RS nose and headlight | Inspection |
| 4 | Wheel arch, wheel spinning | Suspension |
| 5 | Roma rolling through the canyon | The range of cars we keep |
| 6 | GT3 RS rear, wing up | — |
| 7 | SF90 rear, Ferrari badge | Payoff, CTA and end card |

Three cars rather than one, deliberately: the package is not about a single
car, it is about the shop keeping cars of this kind for a year.

Conditions run in the ticker — **oil included, pads not included** — where they
hold long enough to be read. The 10%-off line moved to a spec chip so the ticker
stays short enough to clear the action rail.

### Full Car PPF — ceramic coating included

`FD-Roma-Full-Car-PPF.mp4` · 21.1 s · Roma throughout

The shop's own note said *"Using Roma Video. PPF focused video."* This is it.

| | Shot | Carries |
|---|---|---|
| 1 | Parked on the desert road | Establishing |
| 2 | Satin red panel, roofline, mirror | **The film itself — the hero shot** |
| 3 | Interior, wheel and red stitching | Interior ceramic is included |
| 4 | Rear, quad exhaust, diffuser | Film over complex curves |
| 5 | Wide canyon road | Breath |
| 6 | Wheel, low and spinning | Detail |
| 7 | Rolling into the sun | Payoff, CTA and end card |

It opens on the paint rather than on the car, because the paint is what the
product protects. The copy avoids the word "gloss" — this car is satin, and the
film is the point, not the shine.

---

## Still to build

| Special | Footage it needs | Have it? |
|---|---|---|
| Free tune with a RYFT or Opus exhaust | Exhaust work, dyno, or a RYFT part on camera | The Roma rear with quad exhaust could carry it; "teal brakes and ryft wheels" is RYFT-branded but is wheels |
| Windshield PPF 899 + free headlights | Film onto glass, a headlight | No |

The exhaust special is the one that wants the partner URL graphic from
`11-service-reels/partner.js` — `ryft.co` typed on while a RYFT part is on
screen. A URL bar over a wheel shot is a claim about the wrong product, so that
one waits for exhaust footage or a confirmed RYFT exhaust car.
