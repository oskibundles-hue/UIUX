# Copy rules

Learned from the shop's corrections. These are not style preferences — getting
them wrong misrepresents what is being sold.

---

## 1. A service is not an inclusion

**The service is the job the shop performs. Everything else came with it.**

A run of identically labelled panels says all the items are the same kind of
thing. They are not, and presenting them as equals hides the actual offer.

| Offer | The service | Included because of it |
|---|---|---|
| Full car PPF | **Full car PPF** | Exterior ceramic coating, interior ceramic coating |
| Windshield PPF | **Windshield PPF**, $899 | Headlight PPF, free |
| Free tune | **ECU calibration** | Free with a RYFT or Opus exhaust |
| Annual package | **The package**, $3,999 | 2 oil, 1 brake, 2 diagnostics, suspension, 10% off |

Write it into the spec value with a kicker:

```bash
--spec 'SERVICE|FULL CAR PPF'
--spec 'INCLUDED|EXTERIOR CERAMIC COATING'
--spec 'INCLUDED FREE|HEADLIGHT PPF'
--spec 'PRICE|$899'
```

Anything with no kicker defaults to `INCLUDED`, which is right for a package
where every line genuinely is an inclusion — the annual service ad relies on
that default and must not change.

## 2. A property is not a service

"Self-healing" describes what the film does. It is not a job anyone performs,
so it never appears in the service run. It can sit in the ticker as a
descriptor of the product.

Same test for anything else: **would the shop write it on an invoice as a line
item?** If not, it is not a service.

## 3. No model names

These ads sell a service and the car is already on screen. Naming the car
spends a line on something the viewer can see, and it makes a service ad look
like a car ad.

## 4. Translucent, never bordered — on anything

Retired for good: the red-outlined chip, and any solid plate with a rule ruled
across its full width. Both read as a UI element pasted on top of the picture
instead of something belonging to it.

**The house treatment is glass cut out of the picture itself.** In video that is
`--spec-style panel`: the rectangle behind the words is cropped, blurred,
darkened and put back, so the car keeps moving behind the type. In stills it is
the same move — `frost()` in `14-stills/build_stills.py` blurs that region of the
poster and fades its top edge in, so the caption sits on the photograph.

The only red furniture allowed near type is a **short rule**, roughly a third of
the element's width. A rule that runs edge to edge is a border by another name.

**This applies to every ad and every edit from here on**, video or still, service
or business — not just the four service ads it was learned on. New format, same
rule: measure the frame, frost it, keep the red to an accent.

## 5. Claims need a source

No horsepower figure without a dyno sheet. No partner URL or partner plate
unless that partner's part is actually fitted to the car on screen. The 765LT
cut is on hold for exactly this reason.

Settled since:

- **The Roma carries a RYFT exhaust.** Confirmed by the shop, so `ryft.co` and
  the RYFT name may go on a cut featuring that car.
- **Formula Dynamics did the Mansory Urus gradient PPF.** That footage is the
  shop's own work, not a car it merely filmed.
- **Larini's URL is verified:** `larinisystems.com`. See
  `11-service-reels/PARTNERS.md` for what may be said about them.

## 6. Supercar Experience footage is fair game

Every clip in the SCE car-footage folder is cleared for Formula Dynamics ads.
The one thing to check per clip is printed branding on the car — the gradient
Urus carries **SUPERCAR EXPERIENCE ✕ DIPPED AUTO WORKS** across the glass from
12.4 s to 14.0 s, and it was mis-filed as `no-branding`. That is not a reason to
cut the section; the collaboration is welcome on screen. It only means the
overlay should stay clear of those seconds.

## 7. Measure the frame, not the intention

Three things went out wrong this session because a number was assumed rather
than read. All three are now checked in code, not in someone's memory.

**The action rail.** Instagram's icons start at **x = 907** on a 1080 canvas.
The title block's accent stripe was a fixed 30% of frame placed after the
subline, so a long subline pushed it to x=1034 — the last two segments sat
under the like and comment buttons on every ad in the set. It is now sized to
the room that is actually left, and drops to its own line when there is none.
`SAFE_RIGHT_EDGE` in `fd_hud.py` is the one place that number lives.

**Panel legibility is a function of clip length.** The window is derived from
duration, so the same three panels hold 2.8 s on a 28.7 s clip and 0.59 s on a
15.7 s one. Under about 1.3 s a two-line panel is not readable on a phone.
**Read it off the dry run before choosing the car.** A clip under 20 s either
takes fewer panels or none at all, with the offer in the title plate instead.

**A price is not a word.** Every panel label was capped at 0.44 of the panel
height, which set `$499` at exactly the same 91 px as `FULL DIAGNOSTIC` — so
the pricing ad, documented as setting the figure large, never did. A label
starting with `$` now gets 0.62, landing at 116 px. Words are unchanged, and
long ones were width-bound anyway.

---

## Posters

**Layout J — "Service First" — is the approved poster template, 14 Sept.**
Every service poster is built on it. The hierarchy is fixed and is the point
of the layout:

1. **The service name** at full width, two lines, white over red.
2. **Who it is for** on a full-bleed red bar directly under it —
   FOR EXOTICS · LUXURY · PERFORMANCE.
3. **The price**, sized at roughly four times body size, with **from** in
   front of it wherever parts are extra.

The benefit line supports at 44px; it does not lead. That is the reverse of
the benefit-first rule the video ads follow, and it is deliberate — a promo
poster and a service ad are different jobs, and both exist.

**Type floor: 34px.** A 1080px poster renders about 390pt wide in a phone
feed, a scale of 0.361, so 34px is 12.3pt and anything under it is decoration
rather than copy. The builder raises rather than drawing smaller.

**Say "parts sold separately", not "pads".** The list names rotors and pads
both, so the narrower word under-declared what the customer may still owe for.

**The layout and the photograph are approved separately.** On 22 Sept the shop
approved layout J for the oil set and rejected every frame in it: the picture
has to match the service, and the whole library is wheel and brake photography.
A poster is not cleared to post until both halves are signed off. Cropping
cannot rescue a wrong subject - it was tried, it improved eight of fifteen, and
eight of fifteen is still not a set.

**A customer plate may appear.** The white 911's plate, CBS112, is readable in
the oil poster `P1622_003`. The shop's call on 23 Sept is to run it unblurred.
Recorded so it is not raised again as an open question.

**No MC20 footage** (shop, 23 Sept). The car in `lift.mp4` could not be
identified from the frames - no badge is visible in any of them - so rather
than guess, the annual ad was cut on `2026-09-03 23-10-09 gt3 rolling in.mov`,
which is unmistakably a Porsche. When a clip cannot be positively identified
and a car is excluded, pick a clip that can be.

**The lift footage is not an oil change, and the annual cut made from it was
not asked for.** `lift.mp4` (2026-09-03, black car raised on a lift) was used
for an oil ad because it was dark enough for the ember opener to work - which
is choosing footage to suit an effect rather than to suit the service. When
that was pointed out it was re-cut as an annual-package ad instead, on an offer
to do so that the shop had not sought. Both are dead. The clip may be good
footage; it is not a brief, and an effect wanting a dark ground is not a reason
to make an ad.

**Every ad ships twice.** `01 Sound designed (post these)` carries the SFX
motion pack; `02 Picture only (for editors)` carries the identical picture with
the clip's own audio and no sound design. Same folder names the shop already
uses in `/Portfolio/02 Service Ads/Approved Ads/`.

The picture must be byte-identical between the two, and is checked rather than
assumed: both are hashed with `-map 0:v -f md5` and must match. The first
attempt used `-shortest` when muxing the source audio back, which clipped the
video by one frame - 11.27s against 11.31s - and an editor conforming to it
would have been a frame out.

**Instagram feed ratio, 23 Sept.** The approved oil cut now ships at 4x5
(1080x1350) alongside the 9x16 master, via `fd_reframe.py 4x5` - the same
reframe the 9 Sept series uses. The graphics are burned in and sit low (spec
panel y 1074-1314, title block under it), so a crop would take the panel or the
bug; the whole frame is scaled to fit instead and the rails filled with a
blurred copy. Real picture is 758px, 70% of the canvas. That is consistent with
the series, but a true full-bleed 4x5 - graphics laid out for 1350 height - is
the stronger feed post and is renderer work, not a reframe. 1x1 drops to 56%
picture and 16x9 to 32%, which is too thin to post.

Picture parity is checked across the ratio too: the 4x5 sound-designed and
picture-only files hash identical on `-map 0:v -f md5`.

## Status

| Ad | State |
|---|---|
| **Poster — brake service · layout J** | **Approved 14 Sept** |
| **Poster — oil service · layout J** | **Layout approved 22 Sept · photography rejected — do not post** |
| **Video — oil service · white 911, real oil-change footage** | **Approved 23 Sept** — the starter for the new series. Shipped 9x16 + 4x5, both ratios in sound-designed and picture-only |
| Video — annual package · black car on the lift | **Not wanted** — built 23 Sept without being asked for. Do not offer it again. |
| Video — annual package · white GT3 RS rolling in | Built 23 Sept, awaiting the shop |
| Annual service $3,999 · SF90 | **Approved** (rebuilt, benefit-led) |
| Brake service $499 · GT3 RS | **Approved** |
| Oil service $1,199 · Ferrari 296 | **Approved** |
| Suspension · Roma | **Approved** |
| Diagnostics $499 · Mansory Urus | **Approved** |
| Full car PPF · Roma | **Approved** |
| Windshield PPF $899 · GT3 RS | **Approved** |
| Custom gradient PPF · Mansory Urus | **Approved** |
| Free tune, RYFT named · Roma | **Approved** |
| Free tune · Aventador | **Approved** |
| Service pricing · SF90 | **Approved** |
| Service posters (4) | **Approved** |

Eleven ads across nine services, plus four posters. Anything new starts from an
approved ad's settings, not from scratch.

All eight are finished products, signed off 9 Sept 2026. Anything new for these
services starts from their settings, not from scratch. The download sheet lives
at `/Portfolio/02 Service Ads/Approved Ads/DOWNLOAD SHEET.md` in Dropbox.
