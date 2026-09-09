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

---

## Status

| Ad | State |
|---|---|
| Annual service $3,999 · SF90 | **Approved** |
| Full car PPF · Roma | **Approved** |
| Windshield PPF $899 · GT3 RS | **Approved** |
| Free tune · Aventador | **Approved** |
| Service pricing — oil / brake / diagnostics · SF90 | **Approved** |
| Free tune, RYFT named · Roma | **Approved** |
| Custom gradient PPF · Mansory Urus | **Approved** |
| Service posters (4) | **Approved** |

All eight are finished products, signed off 9 Sept 2026. Anything new for these
services starts from their settings, not from scratch. The download sheet lives
at `/Portfolio/02 Service Ads/Approved Ads/DOWNLOAD SHEET.md` in Dropbox.
