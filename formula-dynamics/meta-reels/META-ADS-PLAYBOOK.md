# Running these on Meta — connectors and setup

## Connectors

### Already connected, already on in this chat

| Connector | What it does for this project |
|-----------|-------------------------------|
| **Higgsfield** | `virality_predictor` scores hook strength and retention risk *before* you spend. It caps at 16s and these reels are 15.0s, so each one fits in a single pass. `reframe` turns one reel into 1:1 and 16:9 for Feed and in-stream placements. The `ad-multiplier` workflow produces several independently edited variants of one clip — that is exactly what you want for A/B testing creative. Costs credits; ask before large runs. |
| **vidIQ** | `vidiq_instagram_tiktok_outlier_search` and `vidiq_ig_profile_reels` for competitor research — what hooks are actually working for other exotic/performance shops right now. `vidiq_generate_music` for licence-safe music beds, which matters because Instagram's consumer music library is **not** cleared for paid ads. |
| **Dropbox** | Raws in, deliverables out. Already the working store. |
| **Vertiso Memory** | Carries the brand decisions between sessions — that's how this session picked up the FD red, the Anton spec and the stripe device without re-deriving them. |

### Connected but switched off in this chat — worth turning on

Both of these read Meta Ads performance data back into Claude. **Neither one
publishes or creates ads** — they are reporting connectors. Turning one on
closes the loop so we can see which hook is actually winning and cut the next
batch against real numbers instead of guesses.

| Connector | Note |
|-----------|------|
| **Supermetrics Marketing Analytics** | Facebook Ads, Instagram, TikTok + 200 sources. |
| **Windsor.ai** | Meta Ads, Google Ads, TikTok Ads + 320 sources. |

They do substantially the same job here — **pick one, not both**. You enable
them in the chat's connector settings on claude.ai; I can't toggle connectors
myself.

**OpusClip** is also installed but off. It turns long video into short clips —
useful later if you want to mine long-form shop footage for hooks, not needed
for these five.

### What no connector can do

There is no connector in your directory that uploads to Meta Ads Manager or
launches campaigns. Publishing is manual: download the MP4s and upload them in
Ads Manager. I'd keep it that way regardless — ad spend should have a human
hand on it.

---

## Campaign structure

A sensible starting shape for a shop this size:

**Prospecting (cold)**
- Creative: **R5 (20 Years)** — it's the only one that explains who Formula
  Dynamics is before it asks for anything.
- Targeting: interest-based (Maserati, Ferrari, McLaren, exotic/performance
  aftermarket) plus a broad lookalike if you have a customer list.
- Objective: traffic or engagement first, to build the retargeting pool.

**Retargeting (warm)**
- Creative: **R1–R4**, one per ad set so each service gets its own audience
  signal.
- Targeting: video viewers (75%+ of R5), site visitors, IG engagers.
- Objective: leads or conversions.

**Testing**
- Run all five in one ad set against a broad audience for the first few days
  and let Meta find the winner, then split the winner into its own campaign.
- The hook is the variable that moves performance most. If a reel
  underperforms, change the first 2 seconds before you change anything else.

## Placement and spec notes

- These are cut for **Reels and Stories** (9:16, full bleed). For Feed, run
  `reframe` to get a 1:1 version rather than letting Meta letterbox them.
- 15s is inside the Reels ad limit and long enough to land hook → proof → CTA.
- **Add music before you run them.** They're silent by design so you can drop
  a bed on without re-cutting — but a silent ad reads as broken to some
  viewers even on muted autoplay, and Meta's own data favours ads with audio.
  Use a licensed track or `vidiq_generate_music`; do **not** use the
  Instagram consumer music library on a paid ad.
- Set the primary text and headline in Ads Manager to carry the offer — the
  reels carry the message, the ad copy carries the specifics (pricing,
  availability, "book now").

## Before you spend

Read `README.md` § *Copy that needs your sign-off*. Two items need a
factual check from Formula Dynamics — the service process descriptions, and
whether you want real dyno figures in R2 (it currently makes no numeric
power claim at all).
