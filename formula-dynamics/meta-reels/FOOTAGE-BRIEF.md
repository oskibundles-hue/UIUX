# Footage brief — what to add to Dropbox

The five reels are complete and runnable as pure motion graphics. This is
what would make them materially stronger, in priority order.

**Why footage matters here:** motion-graphics-only ads are clean and safe,
but on Meta the top performers in the exotic/performance category almost
always show the real thing — the car, the part, the hands. Graphics carry
the message; footage carries the proof. The reels are built so footage can
be dropped in behind the existing overlays without re-cutting anything.

## What's in Dropbox now, and why I didn't use it

`/Anti Stock Media/01 Raw D-Log/` is all shop-buildout vlog footage —
ceiling panels, epoxy, LED trim, the forklift, the frame. That's the vlog
story, not the service story, and you asked for none of the cut footage.
The few car clips that do exist (Aston brakes, teal brakes + Ryft wheels,
GT3 rolling in, matte black wheel work) are single moments, not enough
coverage to carry a service ad on their own.

---

## Priority 1 — product/service hero shots

These unlock the biggest quality jump. Shoot on a clean lift or in the
detail bay, controlled light, car clean.

**Exhaust (R1)**
- Larini system laid out on a bench or blanket, slow push-in — the whole
  system as one object. This is the money shot for the exhaust ad.
- Close macro: weld beads, tip laser etching, valve actuator, flange.
- Tips installed on the car, low rear three-quarter, engine off.
- **Sound**: a clean start-up and 2–3 revs, valve closed then valve open,
  recorded from ~10 ft rear quarter. Even though the ads run muted, an
  unmuted sound moment is what makes people turn audio on.

**Tuning (R2)**
- Car strapped on the dyno, wide, fans running.
- Laptop/handheld screen with a graph on it (blur or crop anything you
  don't want public).
- Someone at the wheel during a pull, over-shoulder.

**PPF (R3)**
- Film being squeegeed onto a panel — the single most watchable PPF shot.
- Film unrolling off the roll.
- Water beading on a finished panel.
- Slow pan down a finished, protected front end.

**Builds (R4)**
- Before/after on the *same* car from the *same* camera position. Mark the
  spot with tape so the two shots line up exactly — this is what makes a
  before/after land.
- Wheel-off, car on the lift, wide.
- Parts staged on the floor before install.

**Brand (R5)**
- Wide establishing shot of the shop, clean, lights on.
- 2–3 cars in the bay together.
- Team working — hands, tools, focus. Faces optional.

## Priority 2 — the cars themselves

Rolling and static exotics are the connective tissue for every ad:
- Static three-quarter, front, rear on a clean background.
- Slow orbit around a finished car.
- Rolling shots if you can get them safely.
- Details: badge, wheel, brake caliper, exhaust tip, interior stitching.

## Priority 3 — proof

- A customer collecting their car (get written permission before this runs
  as a paid ad).
- Any dyno sheet, certification, or distributor documentation you're happy
  to show on screen.

---

## Shooting spec

To match the existing 4K library and drop straight into these reels:

- **4K, shot vertical or with vertical crop in mind** — keep the subject
  centred so a 9:16 crop works. Existing library is 2160×3840.
- **29.97 fps** to match the library; 60 fps for anything you want slowed.
- **D-Log** if you're on the same body as the existing raws, so one grade
  covers everything. The `--look vlog` recipe from the last session already
  matches this.
- **Lock the camera off** for hero product shots. Handheld reads as vlog;
  locked-off reads as advertising. This is the single biggest difference
  between the vlog footage and what these ads need.
- 8–15 seconds per shot is plenty.

## Where to put it

```
/Anti Stock Media/06 Product B-Roll/
    exhaust/    tuning/    ppf/    builds/    cars/    shop/
```

Drop clips in named by subject and I'll cut them into the existing reels
without changing the graphics or the timing.

There is already a Dropbox file-request link from the earlier session that
lets you upload straight from your phone without the Dropbox app:
<https://www.dropbox.com/request/cw52bjv1jh0edz6s4mhf>
(it points at the Fast Cut folder — either use it and tell me, or make a new
request against `06 Product B-Roll` and send me that link instead).

## What already exists that I did NOT reuse

The 60 files indexed in the "Anti Stock Downloads" artifact are all vlog
material — the R1–R8 reel series, the VR1–VR8 vlog cuts, the MR1–MR8 fast
cuts, and 18 graded singles. Per your brief none of it appears in these ads.

Two things from that library ARE reused here, because they're brand assets
rather than footage:

- The **SFX pack** (17 synthesised sounds) — now the sound design on all
  five reels.
- The **brand spec** (FD red, gold, Anton, the 5-segment stripe), carried
  through Vertiso Memory from the earlier ad session.

Worth knowing: the artifact's closing note says "the FD overlay pack was
yours to begin with and is already in Dropbox", but `/Anti Stock Media/05
Overlays/` is **empty**, and a Dropbox search turns up no image files. The
creator-kit zip contains a *Supercar Experience* overlay pack, not a Formula
Dynamics one. That's why I rebuilt the FD mark and overlay set from scratch
this session. If a real FD overlay pack exists somewhere else, send it and
I'll match to it instead.

---

## Standing practice: harvest audio from our own footage

As footage lands in Dropbox and reels get made, the source clips are also a
**sound library** — real exhaust notes, shop ambience, tool and impact
sounds. Formula Dynamics' own audio beats any downloadable library for
Formula Dynamics' own ads, and it costs nothing but processing.

**Verified 2026-09-08:** the CloudFront masters carry AAC 48 kHz stereo
192 kbps audio. A probe of "09 gt3 rolling in" measured peak -4.5 dBFS with
**82.7% of its energy between 30 and 250 Hz** — an engine/exhaust signature,
not room tone. The material is real.

### Where the usable audio is

| Source | What's in it |
|---|---|
| CloudFront car clips (09 gt3 rolling in, 18 red supercar, 13 black car on the lift, 17 matte black wheel work, the SF90 reels) | Engine and exhaust |
| Dropbox `01 Raw D-Log/` | Shop and tool sounds — drilling, trim cutting, forklift, epoxy |
| FD campaign ads on `claude/formula-dynamics-ad-qpuh4m` (765LT, Aventador S) | Source clips' own engine audio |

### Method

The masters are 2160×3840 at ~49 Mbps, so files run 250–560 MB and the audio
is interleaved — the whole file has to come down to get all of it. Two
practical constraints:

- **Work one file at a time**: download, extract audio, delete the video,
  move on. Disk is a fixed per-session allowance.
- **ffmpeg cannot stream these URLs through the agent proxy.** `curl` the
  file to disk first, then extract. A direct `ffmpeg -i <url>` returns no
  streams and looks like "no audio" when the audio is fine.

Then find the clean isolated moments, denoise, trim, normalise to -3 dBFS /
48 kHz, and add them to `sfx/` under an `fd_` prefix so they sit alongside
the designed and Kenney-sourced groups.

### What to capture on new shoots

Record sound deliberately rather than taking whatever the camera got:

- **Start-up, idle, 2–3 revs**, valve closed then open, from ~10 ft rear
  quarter. This is the single most valuable recording available.
- **Cold start** separately — it has character an idle doesn't.
- **Shop ambience** with nothing happening, 30 s. Useful as a bed under
  anything.
- **Tools in isolation** — impact wrench, torque click, ratchet, lift
  ascending, a wheel nut dropping on concrete.
- **Door and panel sounds** — an exotic's door closing is a signature.

Away from traffic and compressor noise where possible; a clean recording can
be layered, a noisy one can only be filtered.
