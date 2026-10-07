# Playbook: Anti Stock

Omarie's own channel, @nq.young: reels built with the creator-kit pipeline (Fast Cut and Kinetic Cut).
Not for videos made for Formula Dynamics or Supercar Experience, including their branded vlog overlays in
`creator-kit/remotion/src/brand` — those use the `formula-dynamics` or `supercar-experience` playbook.
Read by `nq-build`, `nq-fix`, `nq-check`, `nq-label` and `nq-story` when the brief names this playbook.
(Moved from the `anti-stock-editor` agent on 2026-09-30.)

`<repo>` means the main checkout's root: `git rev-parse --show-toplevel`, run before you move into
any worktree.

## Where the work lives

Branch `claude/instagram-growth-video-editing-rswexx`. If this checkout has no `creator-kit/` folder,
it's on another branch, so work in a worktree of the Anti Stock branch instead:

    git -C <repo> fetch origin claude/instagram-growth-video-editing-rswexx
    git -C <repo> worktree add <repo>-antistock claude/instagram-growth-video-editing-rswexx   # skip if it exists

Read first: `creator-kit/WORKFLOW.md`, `creator-kit/DELIVERY.md`, and for a Fast Cut reel
`creator-kit/fastcut/RUNBOOK.md` (build: `creator-kit/fastcut/build_reel.sh`). For a Kinetic Cut piece:
`creator-kit/experiments/kinetic/` — `build_kinetic.py` is spec-driven, so a new piece is a new JSON spec,
not new code. "Make this, but with my footage" is `match_reference.py`.

Then check `skill-observations/log.md` for OPEN observations on these files and apply them.

## Rules that are easy to break

- **Format is not settled.** Observation 1 in the log: his two reels with reach are 14–20 s car-only
  shots with a question hook, while talking-head Fast Cuts sit at 50–150 plays. If asked to build
  "another one like MR8", say so first.
- **Red is `#FE0F13`.** MR1–MR8 are old work (2026-09-26) — not re-rendered, not a reference to match.
- **Only his voice is captioned**, matched through `creator-kit/voice/omarie_profile.json`. Do not loosen
  the voice threshold to raise caption coverage — it captions other people as him.
- **Never "improve" his words.** Captions are what he said. SlopMonster is for copy you write (hooks,
  titles, post captions), never for his speech.
- ffmpeg `drawbox` has no timestamp variable (`t` is thickness). Draw moving bars per frame in Pillow.
- Measure flashes per frame, not per shot — shot averages hide single-frame flashes.

## Hand-back extras

The spec or command that reproduces the reel, and a contact sheet or stills checked before the full
render.
