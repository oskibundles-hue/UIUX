# Approved work — the one ledger (DRAFT, not committed)

Drafted 21 Nov 2026 by the artifacts routine, extended 22 Nov 2026 (four new rows). **Nothing here is pushed or published.**
It exists because approved work is currently remembered in three incomplete places:

1. `CLAUDE.md` (installed in every session) — names the styles, carries the quotes, but is a rules file.
2. `supercar-experience/09-campaign-ads/HOUSE-STYLE.md` — the file every agent is told to read first.
   Its feedback log **stops at 3 Oct 2026**, and it lives on the Supercar Experience branch in
   **draft PR #7, open since 27 Sep**, so a session on the default branch cannot read it at all.
3. `design-systems/*/README.md` + the artifact pages (NQ Edit Styles, Locked-On Standard) — each
   records its own approval date and quote, but only for itself.

The rows below are every approval I can trace to a source. Rows marked **MISSING** are approved work
that is in none of the three HOUSE-STYLE sections and would need adding to its feedback log.

## Approved styles and formats

| Date | Thing | Omarie's words | Where it lives now | In HOUSE-STYLE? |
|---|---|---|---|---|
| 2026-09-08 | `hud` layout (FD) | "I love the very first video" | HOUSE-STYLE, Approved layouts | yes |
| 2026-09-08 | `centred` layout (FD) | "the third was very fitting" | HOUSE-STYLE, Approved layouts | yes |
| 2026-09-26 | `quick-promo` | "I approve those ads for when we need quick story ads for promotions" | HOUSE-STYLE | yes |
| 2026-09-26 | Locked-On, as THE standard | "That is amazing make that a standard" | Locked-On Standard page | yes |
| 2026-09-26 | Keep source music | "Keep music as well if the videos ever have any" | HOUSE-STYLE, rules learned the hard way | yes |
| 2026-09-27 | Locked-On vlog (Sep 15 rally v2) | "This is the standard for making vlogs" | HOUSE-STYLE | yes |
| 2026-09-27 | ROOF DOWN 4:5 + 1:1 feed cuts | "approve video" | HOUSE-STYLE, THE STANDARD | yes |
| 2026-09-28 | One Instagram-ready file per edit | "I just need Instagram ready reels for these edits I don't need 2 videos per video" | HOUSE-STYLE rule 8 | yes |
| 2026-09-28 | Ask which style first, every session | "make sure every session/branch/everything knows and implements it no matter what when creating any work but ask beforehand what style should be used" | CLAUDE.md rule 1 | yes |
| 2026-09-28 | Locked-On page as the standard for all work | "My locked on artifact is my standard for any work I work on" | CLAUDE.md, HOUSE-STYLE | yes |
| 2026-09-28 | **iPhone index layout** | "save this apple layout it looks so nice" | `design-systems/iphone-index/` (+ `qa.js`) | **MISSING** |
| 2026-10-03 | `race-weekend` Night + Day | "approve all 3 f1 ads", "save the layouts" | HOUSE-STYLE | yes |
| 2026-10-04 | Layout engine for variations | (process change) | HOUSE-STYLE header | yes |
| 2026-10-10 | **Post mockup page** | "this is a great model and way to show what it would look like save this" | `design-systems/post-mockup/` (+ `qa.js`) | **MISSING** |
| 2026-10-13 | **Studio carousel generator** | "this carousel generator why isnt it on my os" | `design-systems/studio-carousel/` (+ `qa.py`, `LAYOUT.md`) | **MISSING** |
| 2026-10-13 | **Light grey studio look as default** | "it should offer different variations as well but this is one of my new favorites ones so this can be default" | `design-systems/studio-carousel/README.md` | **MISSING** |
| 2026-11-07 | **Auto Reel Approvals, one approval page** | (the moved page carries the banner) | artifact `35mFG1611rNbCYdfATQLUw` | **MISSING** |
| 2026-11-16 | **NQ Edit Styles as the styles index** | (per the artifacts page) | artifact `1EddiMAtT93e7tHFKxaFK5` | **MISSING** |
| 2026-11-20 | **FD carousel kit** (`formula-dynamics/17-carousel-kit/`) | "Great save the system" | PR #113, branch `claude/fd-bfcm-75-bcd576` — base is **not** the default branch | **MISSING** |
| 2026-11-20 | **FD-BFCM-75**, 75 Black Friday carousels approved | (75 approved carousels, per PR #113) | `formula-dynamics/30-bfcm-75/` on that branch + artifact `SSEtSGEYSjUbXXdZ2U9DFp` | **MISSING** |
| 2026-11-21 | **Footage-to-queue working agreement** | "The goal (agreed Nov 21, 2026). Omarie drops footage. The agents sort it by lane, plan it, push back, make a low-res preview, and after his go they check, render, QA and file it into one Ready to post queue. Posting, scheduling and spend stay his decision, piece by piece, until he says otherwise. Personal, Formula Dynamics and Supercar Experience stay separate." | artifact `7KNm3P7uk6iQyuEnwLuT8R` (NQ Studio Master Library) | **MISSING** |
| 2026-11-22 | **Sound rule for a personal reel** — awaiting your confirm | "One transition and its sound per scene change. Plain cuts inside a scene get nothing. Sound only when something moves or something real happens. The heaviest sounds once per video. Camera audio is the bed; pack sounds sit just above it, never over it." | artifact `4C5mxD4Kxddi1grn8av8nb` (Personal OS), updated 22 Nov | **MISSING — and would close the conflict below** |

## Proposed, never approved — do not build as if settled

| Thing | Status | Source |
|---|---|---|
| Now Boarding | proposed 2026-09-28, on the Locked-On page | HOUSE-STYLE feedback log |
| Paste-Up | proposed 2026-09-28, on the Locked-On page | HOUSE-STYLE feedback log |
| `panel`, `rail` layouts | built, never signed off | HOUSE-STYLE, "The other two" |
| FD `LIVERY` look | proposed in draft PR #65 | PR #65 |

## One unresolved conflict that blocks the next reel

**How many sounds on a personal reel?** Grok's Edit Types page (14 Nov) wants a transition and an SFX
on every beat. The Claude handbook says sparse by default, because when every cut has a sound nothing
lands. Both are written down as current. Master Video Index flags it. **Needs your pick.**

**Update, 22 Nov:** Personal OS (updated today) now states a third position plainly — one transition
and its sound per scene change, nothing on plain cuts inside a scene, heaviest sounds once per video,
camera audio as the bed. That is neither "every beat" nor "sparse by default". If it is your pick,
saying so closes the conflict and retires the two older statements.

Related: the standing rule "a match cut in every video, no exceptions" pointed at a dead page
(`1S4i8HtqAm9UgikUqHqCzF`) for weeks. The playbook is live again on NQ Edit Styles under
Match Cut Playbook.

## What this ledger could not cover

Item 8 of the routine asks to go through **every session**. This container holds **one** transcript
(the current run; the same was true on 21 Nov). Past sessions ran in their own containers and their transcripts are not reachable from
here, and `recall.py` reports no notes, because the private `nq-agent-channel` repo is not attached.
So every row above is traced to a file or an artifact page, not to a session transcript. To get the
session-level memory you asked for, attach `oskibundles-hue/nq-agent-channel` to a small fresh
session and point item 8 at it.
