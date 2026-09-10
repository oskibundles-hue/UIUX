# Approved ads

One per service. These are the finished products — the shop signed them off, or
they are the current candidate awaiting sign-off. Copy rules that govern them
are in `../COPY-RULES.md`.

All 1080×1920, footage untouched and in its own order, frosted-glass panels,
no corner logo, plain and `-SFX` (sound-designed) versions.

Every file is mastered to **-14 LUFS / -1 dBTP, stereo, 48 kHz** — run
`99-toolkit/fd_master.py` over a delivery folder before it goes out.

### One service, one ad

| File | Service | Car | Length |
|---|---|---|---|
| `FD-Annual-Service-3999.mp4` | Annual package, $3,999 | Ferrari SF90 | 22.2 s |
| `GT3RS-BrakeService.mp4` | Brake service, $499 | Porsche 911 GT3 RS | 28.7 s |
| `Ferrari296-OilService.mp4` | Oil service, $1,199 | Ferrari 296 | 31.8 s |
| `Roma-Suspension.mp4` | Suspension work | Ferrari Roma | 25.7 s |
| `Urus-Diagnostics.mp4` | Diagnostics, $499 | Mansory Urus | 21.8 s |

### PPF and tuning

| File | Service | Car | Length |
|---|---|---|---|
| `Roma-FullCarPPF.mp4` | Full car PPF, ceramic included | Ferrari Roma | 25.7 s |
| `GT3RS-WindshieldPPF.mp4` | Windshield PPF $899, headlights free | GT3 RS | 28.7 s |
| `Urus-GradientPPF.mp4` | Custom gradient PPF | Mansory Urus | 21.8 s |
| `Roma-FreeTune-RYFT.mp4` | Free tune, RYFT named | Ferrari Roma | 25.7 s |
| `Aventador-FreeTune.mp4` | Free tune, offer only | Aventador S | 14.0 s |
| `SF90-Service-Pricing.mp4` | Oil / brake / diagnostics prices | Ferrari SF90 | 22.2 s |

Each has a matching `-SFX` file. **Post the SFX version** — the sound sits on
the animation's own beats and carries no music, so a licensed track drops under
it cleanly.

## The annual ad was rebuilt

`../superseded/FD-Annual-Service-3999-v1-price-in-hook.mp4` opened on
**ANNUAL SERVICE / $3,999** — a price in the first three seconds, which filters
people out before the value is made. The current cut opens on
**KEEP YOUR EXOTIC / UP TO DATE**, names the four services as *any oil service,
any brake service, any suspension work, any diagnostic*, and lands the figure on
the fifth panel at 13.5 s.

The counts moved to the ticker, because "any oil service" beside a package price
reads as unlimited when the package is two. The panels keep the shop's word and
the ticker keeps it true.

## Two ways to sell the same tune

`Aventador-FreeTune.mp4` states the offer and claims nothing about the car in
shot. `Roma-FreeTune-RYFT.mp4` names RYFT, because **that** car's fitment is
confirmed — a partner name over a car is a claim about that car. Both stay: one
is the generic statement of the offer, the other is the evidenced version.

## Pricing sits beside the package on purpose

`SF90-Service-Pricing.mp4` is the à la carte counterpart to the annual package,
and it is deliberately on the **same car**. Together they read as one menu: pay
per job, or buy the year for $3,999. The conditions carry over unchanged —
**oil included, pads not included.**

## Why the tune ad carries no panels

The Aventador plate is 14.04 s and that is the longest source there is for that
car. The panel run needs a window between the opening title and the CTA, and on
a 14-second clip that window closes before it opens — forcing it produces
panels that hold for 0.58 s, which is worse than the chips they replaced.

So the offer lives in the title plate and the ticker instead. That works here
because the offer is one service with one condition, which does not need a
service-and-inclusions breakdown. **Longer footage of that car would let it take
the panels.**

Rule of thumb from the whole set: **a panel run needs about 20 seconds of clip.**
Under that, put the offer in the title plate.

## How these actually get downloaded

Worth writing down, because it cost a round trip. **Nothing generated in a
session has a public URL.** The live Download buttons on the download page point
at the shop's *own uploaded footage*, which sits on a CDN a link can reach;
anything built here is a chat attachment and nothing more. Minting a link for it
is not possible — the Dropbox connector takes UTF-8 text only, and Google Drive
would need each file base64'd through the conversation, which for 304 MB of video
is not a real option.

**The route that works:** the files go into Dropbox once by hand, then a Dropbox
link with `?dl=1` serves them. That is better than the CDN anyway, because a
Dropbox link saves under the **true filename** where the CDN saves under a random
id.

Two gotchas:

- A shared link created through the connector is locked to audience **no one** —
  it works for the account owner while signed in, and shows a permission wall to
  everyone else. Opening it up is a one-time thing in the Dropbox UI: Share →
  *Anyone with the link · Can view*.
- A **folder** link with `?dl=1` makes Dropbox zip the folder, which is one tap
  for a whole set instead of one tap per file. The download page carries that as
  a `Download all` row above the file rows.
