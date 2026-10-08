# Playbook: Formula Dynamics

The shop: builds, wheels, exhaust, suspension, tuning, PPF, detailing. Formula Dynamics is a client and
one of Omarie's employers, so work at full care in one linear build. Not for Supercar Experience rentals
or the personal channel. Read by `nq-build`, `nq-fix`, `nq-check` and `nq-story` when the brief names
this playbook. (Moved from the `fd-ads` agent on 2026-09-30.)

`<repo>` means the main checkout's root: `git rev-parse --show-toplevel`, run before you move into
any worktree.

## Where the work lives

Two places, depending on what is being made:

- **FD vlog overlays** (end card, CTA, lower thirds, Lock-On callouts, corner bug) are Remotion components
  in `creator-kit/remotion/src/brand/fd/` on the Anti Stock branch
  `claude/instagram-growth-video-editing-rswexx` (this checkout if it has `creator-kit/`, otherwise a
  worktree of it at `<repo>-antistock`, made the same way as the FD one below). Read
  `git log --format='%ad %s' --date=short -- creator-kit/remotion/src/brand/fd` first — his latest
  calls are in those messages (e.g. 2026-09-24: no grid on the vlog end card).
- **FD ads, stills, service reels and ad ratios** use the Pillow pipeline on branch
  `claude/formula-dynamics-assets-bnlnkm`. Work in a worktree so this checkout stays on its own branch:

    git -C <repo> fetch origin claude/formula-dynamics-assets-bnlnkm
    git -C <repo> worktree add <repo>-fd claude/formula-dynamics-assets-bnlnkm   # skip if it exists

Commit there. The lead pushes after review.

Read, in the worktree: `CLAUDE.md`, `formula-dynamics/README.md`, `formula-dynamics/99-toolkit/README.md`,
`formula-dynamics/01-brand-core/BRAND-SPEC.md`, `formula-dynamics/05-copy-library/voice-and-tone.md`,
`formula-dynamics/12-service-ads-footage/COPY-RULES.md`.

## Rules

- **For ads, Pillow + ffmpeg is the pipeline**, driven by `99-toolkit/build_all.py` from one constants
  file, `99-toolkit/fd_brand.py`. The FD branch's Remotion project is a cross-check only — do not make it
  the ad pipeline. (The vlog overlays above are a separate, Remotion-native set.)
- Brand values come from `fd_brand.py` and nowhere else. Red `#FE0F13`, type Bebas Neue. The accent
  stripe has **five** segments (red 36.7%, black 21.4%, white 19.4%, green 17.0%, yellow 5.5%); on black
  ground the black segment vanishes — that is correct, do not "fix" it.
- Measure before choosing: sample luminance under a graphic's own zone across the whole clip and pick
  tone from the range, not the mean.
- Keep-out zones on 9:16: top 11%, bottom 20%, right 16%, left 5%.
- **Verify a composited still before rendering.** Every anchor error in this project was caught or
  missed at that step.
- Partner logos (NV Forged, iPE, RYFT) are their property and are never generated.
- **Only put a figure on screen if it can be substantiated from a named source.** The McLaren 765LT cut
  is on hold because its counter carries invented placeholder figures. Leave a figure out rather than
  guess it.
- Copy you write (hooks, CTAs, lower thirds) goes through SlopMonster:
  `python3 <repo>/.claude/skills/slopmonster/tools/deslop.py --text "..."` — ship at 5/5.

## Hand-back extras

Which variants are approved versus held (they ship in separate zips), and every figure on screen with
its source, for the facts panel.
