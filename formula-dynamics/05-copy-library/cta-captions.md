# CTA Captions

On-screen calls to action, brand-locked: Bebas Neue, brand red `#FE0F13`,
white, black. Ready-made graphics live in `../03-overlays/cta-captions/`.

---

## The two styles

Every caption comes in both. Pick by what's behind it.

| Style | Looks like | Use when |
|---|---|---|
| **`bar`** | Solid red pill, white type | Default. Dark, neutral or light footage. Maximum punch. |
| **`panel`** | Black panel, white type with the key word in red, accent stripe under | **The footage is red.** Also for busy or bright backgrounds. |

**This matters more than it sounds.** A red CTA bar over a red Ferrari
disappears. A lot of your content is red cars. When in doubt, use `panel` —
it reads on anything.

Filename: `cta_{canvas}_{group}_{name}_{style}.png` — available in `9x16`
and `16x9`.

---

## The captions, by what the viewer is ready to do

### Ready to book — highest intent
Use on payoff content: finished reveals, dyno numbers, the hero shot.

- **BOOK NOW**
- **SCHEDULE AN APPOINTMENT**
- **BOOK YOUR BUILD**
- **NOW BOOKING**
- **RESERVE YOUR SPOT**

### Still deciding — a low-commitment first step
For someone who likes the work but hasn't pictured it on *their* car. This is
the highest-value group you have, and the one most shops skip.

- **SEE WHAT FITS YOUR CAR**
- **FIND YOUR FITMENT**
- **BUILT FOR YOUR CAR**

### Wants a number
Opens a direct conversation. DMs convert well because they're private — people
ask about price in a DM who'd never comment it.

- **GET A QUOTE**
- **DM US YOUR MODEL**
- **DM FOR PRICING**

### Engagement — drives comments, which drives reach
Not a sales CTA. Use it to widen the audience your sales CTAs land on.

- **WHAT WOULD YOU FIT NEXT?**
- **DROP YOUR MODEL BELOW**

### Soft — top of funnel
- **LINK IN BIO**
- **FOLLOW FOR MORE BUILDS**

### Trust
Pairs with service and maintenance content.

- **WE SERVICE WHAT WE BUILD**

---

## Rules that actually move the number

**1. One CTA per video. Never two.**
Two asks is zero asks. If the end card is on screen, that *is* the CTA — don't
stack a caption on top of it.

**2. Put it where the payoff is, not at the very end.**
Most viewers leave before the last second. Bring the CTA up as the best shot
lands — the finished car, the dyno figure, the sound — while they're still
impressed. Hold **2–3 seconds**. Long enough to read twice.

**3. Match the ask to the content.**
A reveal earns *BOOK NOW*. A general shop-culture clip does not — it earns
*FOLLOW FOR MORE BUILDS*. Asking for a booking on content that hasn't earned
it is what makes a CTA feel like an ad.

**4. Alternate reach and conversion.**
Roughly every third or fourth post, use an engagement CTA instead of a sales
one. Comments push the video to more people, which makes the *next* booking CTA
land on a bigger audience. All-sales-all-the-time shrinks your reach.

**5. Never bury it in the keep-out zone.**
Already handled — these sit above the bottom band automatically. But if you
retype a CTA by hand in CapCut, check it against
`../04-templates/safe-zone-guides/safe-zones_9x16.png`.

**6. Make the destination match the words.**
*LINK IN BIO* has to reach a page where booking is the first thing visible.
*DM US YOUR MODEL* means someone answers DMs the same day. The caption is a
promise; the follow-through is the conversion.

---

## Which CTA for which video format

Pairs with the seven formats in `../06-video-system/SHOT-LISTS.md`.

| Video | CTA | Why |
|---|---|---|
| The Reveal (body kits) | `book-your-build` | Peak desire — ask for the build |
| Sound Check (exhaust) | `dm-for-pricing` | They want to know what it costs |
| Fitment (wheels) | `see-what-fits` | Fitment is the exact worry |
| Dyno / Tune | `book-now` | Hard proof earns a hard ask |
| Before & After | `what-would-you-fit` | Comment bait — high reach |
| Install Day | `now-booking` | Shows capacity is real |
| Service | `we-service-what-we-build` | Trust, not sale |

---

## Writing your own

If you add captions, keep them to the house voice
(`voice-and-tone.md`): specific beats loud.

- **Short.** Two to four words reads in a glance. Five is the ceiling.
- **A verb first.** Book, get, see, find, drop, reserve.
- **No exclamation marks.** The red does the shouting.
- **Never promise what you can't guarantee** — "free", "same day", "instant"
  only if it's genuinely true every time. A CTA that overpromises costs more in
  trust than it wins in bookings.

To add one permanently: add a row to `CTA_CAPTIONS` in
`../99-toolkit/fd_brand.py` and run `build_all.py`. You get both styles in both
canvases automatically.
