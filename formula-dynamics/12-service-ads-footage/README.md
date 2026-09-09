# Service ads cut from real footage

The R1–R8 reels in `11-service-reels/` are pure motion graphics — they were
built because there was no service footage to cut against. These are the other
thing: **the shop's own video with the graphic system burned onto it.** Same
brand kit, same overlay set, real cars.

Use these for the specials. A motion-graphic reel explains an offer; footage of
a real car carries it.

**One car per ad. Footage is never mixed between cars.** A cut that jumps from
a Ferrari to a Porsche to another Ferrari reads as a showreel, not as an ad for
one offer — and it quietly implies the shop is showing you someone else's car.
Each offer instead gets a variation per car, so the same special can be run
against three different audiences.

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

**The footage is not re-cut.** Each source clip plays whole, in its own order,
exactly as shot. Variations change the overlay and nothing else — see
`STYLES.md`. A montage assembled from re-ordered shots was tried and dropped: it
made every variation a different edit, so nothing could be compared, and mixing
cars in one cut read as a showreel rather than an ad.

Two steps:

**1. Survey the clip.** Read it at one-second resolution to know what is in it,
and measure the bug corner to decide the logo:

```bash
ffmpeg -nostdin -y -i car.mov -vf "fps=1,scale=150:-1,tile=10x3" -frames:v 1 sheet.png
```

**2. Burn the overlays on, once per style.**

```bash
python3 ../99-toolkit/build_edit.py car.mov -t service --service service \
  --title-text 'ANNUAL SERVICE|$3,999' --title-scrim \
  --title-block 'ANNUAL SERVICE PACKAGE|$3,999 PER YEAR' \
  --ticker 'OIL INCLUDED|PADS NOT INCLUDED' \
  --spec '2 OIL SERVICES' --spec '1 BRAKE SERVICE' \
  --spec '2 DIAGNOSTICS' --spec '10% OFF UPGRADES' \
  --none badge --none bug --bitrate 9M -o out.mp4
```

Add `--motion` for the sound-designed version — a separate deliverable, not a
replacement. Always `--dry-run` first; the cue sheet is where the problems are
visible.

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

**Measure the logo corner; don't assume a tone.** Sampling the bug's own
rectangle (x 54–360, y 211–320) four times a second across each montage, then
counting the frames where each colour would be lost:

| Cut | White logo fails | Black logo fails | Decision |
|---|---|---|---|
| Annual · SF90 | 14.9% | 23.0% | **Drop the bug** |
| Annual · GT3 RS | 58.6% | 8.0% | **Black logo** |
| Annual · Roma | 22.2% | 29.6% | **Drop the bug** |
| Windshield PPF · GT3 RS | 53.2% | 7.6% | **Black logo** |
| Free tune · Roma | 29.6% | 25.9% | **Drop the bug** |

The white GT3 RS lives against bright sky, so a white logo is gone in more than
half the frames and a black one is safe — the same conclusion the original
GT3 RS car ad reached. The Ferraris cut between near-black interiors and blown
sky, so neither colour survives and the corner logo comes off entirely; the
monogram still appears in the title block and on the end card, so nothing is
lost. This is exactly what the Roma and Aventador ads already do.

**Set `--bitrate 9M`.** The 20M default put 42 MB behind 19 seconds. 9M is
13 MB for the same picture.

---

## Built

Six ads across four offers. Shot lists for all of them are in `shots.txt`.

### Annual Service Package — $3,999 · three variations

| File | Car | Length | Logo |
|---|---|---|---|
| `FD-Annual-Service-3999-SF90.mp4` | Ferrari SF90 | 21.8 s | dropped |
| `FD-Annual-Service-3999-GT3RS.mp4` | Porsche GT3 RS | 21.8 s | black |
| `FD-Annual-Service-3999-Roma.mp4` | Ferrari Roma | 20.1 s | dropped |

Same copy on all three, so they can be A/B tested against each other with only
the car changing. Each carries its own brake shot (SF90 red caliper, GT3 RS
yellow caliper, Roma wheel), its own cockpit shot for diagnostics, and its own
arch shot for suspension. Conditions run in the ticker: **oil included, pads
not included.** The 10%-off line is a spec chip so the ticker stays clear of
Instagram's action rail.

### Full Car PPF — ceramic included · Roma

`FD-Roma-Full-Car-PPF.mp4` · 21.1 s. The shop's own note said *"Using Roma
Video. PPF focused video."* Opens on the paint rather than the car, because the
paint is what the product protects. Copy avoids "gloss" — that car is satin.

### Windshield PPF — $899, headlights free · GT3 RS

`FD-Windshield-PPF-899-GT3RS.mp4` · 19.8 s. Second shot is a headlight close-up,
which is the free half of the offer. The white car against sky is the one case
where the measurement said keep the logo, in black.

### Free ECU tune with a RYFT or Opus exhaust · Roma

`FD-Free-Tune-Exhaust-Roma.mp4` · 20.1 s. Opens on the quad exhaust.

**No partner URL on this one.** `partner.js` can put `ryft.co` on screen, but
only where that exhaust is actually fitted, and this Roma's exhaust has not been
confirmed as RYFT. The ad states the offer — which is true regardless of what is
on this car — without making a claim about the car in shot. Confirm the fitment
and the URL bar can go on.

## Still open

**Footage of the work itself.** Everything here is beauty footage. A lift, a
torque wrench, film being squeegeed onto glass, a car on the dyno — any of those
would swap straight into these ads as shot 2 or 3 and make them proof rather
than assertion. The shot lists in `shots.txt` are the swap points.

**Confirm the Roma's exhaust.** *Closed — it is a RYFT.* The RYFT name is on
screen in `pending/Roma-FreeTune-RYFT.mp4`, and `ryft.co` may go on any cut
featuring that car.

**Opus.** *Closed —* `opusinnovations.com/exhaust`, researched and written up in
`11-service-reels/PARTNERS.md`. **Larini too:** `larinisystems.com`.

**Mansory Urus, custom gradient PPF.** *Closed — footage arrived through
Supercar Experience and the ad is built* (`pending/Urus-GradientPPF.mp4`).
Formula Dynamics did the car.

**Two more cars are available.** The Aventador S and 765LT plates are committed
on the campaign branch, so the annual package could take a fourth and fifth
variation without new footage. The 765LT's own ad is on hold for invented spec
figures, but its plate footage is clean.
