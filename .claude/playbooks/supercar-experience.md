# Playbook: Supercar Experience

The rental fleet: pickups, drop-offs, handovers, experience days. Supercar Experience is a client and
one of Omarie's employers, so work at full care in one linear build. Not for Formula Dynamics shop work
or the personal channel. Read by `nq-build`, `nq-fix`, `nq-check` and `nq-story` when the brief names
this playbook. (Moved from the `se-ads` agent on 2026-09-30.)

`<repo>` means the main checkout's root: `git rev-parse --show-toplevel`, run before you move into
any worktree.

## Where the work lives

Three places, depending on what is being made:

- **SE vlog overlays and captions** (including the coworker speaker tag in SE orange) are Remotion
  components in `creator-kit/remotion/src/brand/se/` on the Anti Stock branch
  `claude/instagram-growth-video-editing-rswexx` (this checkout if it has `creator-kit/`, otherwise a
  worktree of it at `<repo>-antistock`, made the same way as the ones below). Read
  `git log --format='%ad %s' --date=short -- creator-kit/remotion/src/brand/se` first for his latest calls.
- **SE campaign ads and deliverable sets** (the `build_ad.py` toolkit) are on branch
  `claude/skills-download-ai3m6a`. Work in a worktree:

    git -C <repo> fetch origin claude/skills-download-ai3m6a
    git -C <repo> worktree add <repo>-se claude/skills-download-ai3m6a   # skip if it exists

- **SE vlogs and the Locked-On ads** are on branch `claude/supercar-rental-ad-graphics-o64vo3` (draft
  PR #7), in a worktree at `<repo>-se-vlog` made the same way. The Sep 15 rally vlog v2
  (`supercar-experience/10-vlog-locked-on/2026-09-15-rally-v2/`) is the SE vlog standard: every SE vlog
  starts from it unless the job says otherwise.

Commit there. The lead pushes after review.

Read, in the worktree: `CLAUDE.md`, `supercar-experience/09-campaign-ads/README.md`,
`supercar-experience/09-campaign-ads/HOUSE-STYLE.md`, `supercar-experience/09-campaign-ads/PLATES.md`,
`supercar-experience/09-campaign-ads/_grade/WORKFLOW.md`, `supercar-experience/DELIVERY.md`.
Brand values: `supercar-experience/01-brand-core/brand-tokens.json`.

## Rules

- An ad is a `cue.json` plus variants under `variants/`, built by `09-campaign-ads/build_ad.py`.
  Deliverable sets come from `09-campaign-ads/build_deliverables.py` — the reference implementation of
  the "Delivering Video Sets" rule (renamed for a human, numbered folders, README.txt, `zip -0`,
  approved and held in separate zips).
- **Which brand a clip belongs to is decided by what is happening, not by what he wears.** The "ANTI
  STOCK SUPERCAR EXPERIENCE" shirt tells you nothing. Collecting, delivering, handovers, the fleet → SE.
  Work being done to a car in a bay → Formula Dynamics.
- **Price and offer variants carry figures.** Every price, rate or spec on screen must come from a named
  source (the client's site or Omarie). If it isn't sourced, hold the variant.
- Copy you write goes through SlopMonster:
  `python3 <repo>/.claude/skills/slopmonster/tools/deslop.py --text "..."` — ship at 5/5.
- Verify a composited still before rendering.
- **Vlogs: frame gate before the full render** (added 2026-10-06). The chain is build → contact sheets →
  `nq-check` on the sheets → full render → `nq-check` on the render. The builder makes sheets of every
  driving shot and every replacement shot, a frame about every 0.3 s at 640 px tiles (command in
  `nq-build`). Why: both of "One-way ticket" Part 2's fix rounds (a 16:9 fill bug; hands, speedo-box
  placement and lip sync) were picture problems the full render exposed, at about $4–5 a re-render.
- **Hands rule** (Omarie, 2026-10-06): one hand on the wheel while he talks is fine. A phone or camera
  in hand, or both hands off the wheel, while moving or stopped in traffic means a cutaway.

## Hand-back extras

Approved versus held variants, and every price, rate or spec on screen with its source, for the facts
panel.
