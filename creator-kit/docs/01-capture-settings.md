# Osmo Action 6 — capture settings for Instagram

Everything downstream is limited by what you record. These settings are chosen
for footage that has to survive a 4K → 1080 downscale *and* Instagram's
re-encode, while staying gradeable.

## The one-screen version

| Setting | Value | Why |
|---|---|---|
| Resolution | **4K 4:3** | Full sensor height. Gives you vertical room to crop 9:16 in post and still be oversampled. |
| Frame rate | **60fps** (24/30 for talking head) | Smooth motion, and you can slow to 50% on a 30p timeline. |
| Colour | **D-Log M, 10-bit** | Already doing this. 10-bit is what makes skies and skin gradeable instead of banded. |
| Codec | **HEVC** | Required for 10-bit. |
| Bitrate | **High** (up to 120 Mbps) | Storage is cheap, detail is not. |
| Shutter | **1/120 at 60fps** (double your fps) | The 180° rule. This is what makes motion look cinematic instead of strobed. |
| ISO | **Manual, cap at 3200** | Stops auto-ISO from pumping brightness mid-shot. |
| White balance | **Manual. Always.** | See below — this is the big one. |
| Stabilisation | **RockSteady 3.0**, HorizonBalancing for fights | HorizonSteady crops hardest; save it for when you need it. |
| FOV | **Wide** for arm's length, **Dewarp** for faces | Wide up close distorts features. |

## Why 4K 4:3 instead of 4K 16:9

A 9:16 crop out of 4K 4:3 (3840×2880) leaves you roughly **1620×2880**. That is
still 1.5× larger than the 1080×1920 you deliver, so the downscale *adds*
sharpness rather than just throwing pixels away.

The same crop out of 4K 16:9 (3840×2160) gives you 1215×2160 — usable, but you
have burned most of your margin, and you cannot reframe vertically at all.

**Shoot 4K 9:16 natively instead when** you know a clip is Reels-only and you
want maximum possible sharpness on the delivered frame. You lose all reframing
latitude, so only do this when the shot is locked.

## The three settings that matter most

**1. Lock your white balance.** Auto WB drifting mid-shot is the single most
obvious amateur tell, and it is genuinely hard to fix afterwards because the
shift is non-linear. Set it manually and leave it:

- Daylight / overcast — 5600K
- Shade / blue hour — 7000K
- Tungsten indoors — 3200K
- Firelight, torches, tavern scenes — 2800–3200K

If the light changes, stop and re-set it. A visible WB change between shots
reads as a deliberate cut. A WB change *inside* a shot reads as a mistake.

**2. Get ND filters.** To hold 1/120 shutter in daylight you need to cut light.
The variable f/2.0–f/4.0 aperture helps but will not get you there on a bright
day, and stopping all the way down softens the image via diffraction.

- ND8 — overcast, golden hour
- ND16 — normal daylight
- ND32 — bright sun, snow, open water

Without ND your camera pushes the shutter to 1/2000 and your fight scenes
strobe. This is the difference between "action camera footage" and "a film".

**3. Audio is half your retention.** People swipe away from bad audio faster
than from bad video. Use a DJI Mic if you have one; if not, enable wind noise
reduction and keep the camera out of direct wind. Record a few seconds of room
tone at each location — it makes cuts invisible.

## LARP-specific notes

- **Fights**: 60fps + 1/120 shutter + HorizonBalancing. Slow the best 2 seconds
  to 50% in post; keep everything else at speed.
- **Firelight and torches**: lock WB warm (2800–3200K) and let it be warm.
  Correcting firelight to neutral kills the whole mood.
- **Forest cover**: light is green and 2–3 stops darker than open ground.
  Expose for faces, not for the background — you can recover a blown gap in the
  canopy far more easily than a crushed face.
- **Costume detail** is your differentiator. Shoot deliberate close-ups of
  armour, stitching, weapons, hands. These are the shots that get saved and sent.

## Card and storage discipline

At 4K60 high-bitrate HEVC you are writing roughly 1 GB per 70–90 seconds. Use a
V30 or faster card. Offload before every shoot — running out of card mid-event
is how you miss the shot that would have been the post.
