# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Antigravity Kit is an AI-powered design intelligence toolkit providing searchable databases of UI styles, color palettes, font pairings, chart types, and UX guidelines. It works as a skill/workflow for AI coding assistants (Claude Code, Windsurf, Cursor, etc.).

## Search Command

```bash
python3 src/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain> [-n <max_results>]
```

**Domain search:**
- `product` - Product type recommendations (SaaS, e-commerce, portfolio)
- `style` - UI styles (glassmorphism, minimalism, brutalism) + AI prompts and CSS keywords
- `typography` - Font pairings with Google Fonts imports
- `color` - Color palettes by product type
- `landing` - Page structure and CTA strategies
- `chart` - Chart types and library recommendations
- `ux` - Best practices and anti-patterns

**Stack search:**
```bash
python3 src/ui-ux-pro-max/scripts/search.py "<query>" --stack <stack>
```
Available stacks: `html-tailwind` (default), `react`, `nextjs`, `astro`, `vue`, `nuxtjs`, `nuxt-ui`, `svelte`, `swiftui`, `react-native`, `flutter`, `shadcn`, `jetpack-compose`

## Architecture

```
src/ui-ux-pro-max/                # Source of Truth
├── data/                         # Canonical CSV databases
│   ├── products.csv, styles.csv, colors.csv, typography.csv, ...
│   └── stacks/                   # Stack-specific guidelines
├── scripts/
│   ├── search.py                 # CLI entry point
│   ├── core.py                   # BM25 + regex hybrid search engine
│   └── design_system.py          # Design system generation
└── templates/
    ├── base/                     # Base templates (skill-content.md, quick-reference.md)
    └── platforms/                # Platform configs (claude.json, cursor.json, ...)

cli/                              # CLI installer (uipro-cli on npm)
├── src/
│   ├── commands/init.ts          # Install command with template generation
│   └── utils/template.ts         # Template rendering engine
└── assets/                       # Bundled assets (~564KB)
    ├── data/                     # Copy of src/ui-ux-pro-max/data/
    ├── scripts/                  # Copy of src/ui-ux-pro-max/scripts/
    └── templates/                # Copy of src/ui-ux-pro-max/templates/

.claude/skills/ui-ux-pro-max/     # Claude Code skill (symlinks to src/)
.factory/skills/ui-ux-pro-max/   # Droid (Factory) skill (symlinks to src/)
.shared/ui-ux-pro-max/            # Symlink to src/ui-ux-pro-max/
.claude-plugin/                   # Claude Marketplace publishing
```

The search engine uses BM25 ranking combined with regex matching. Domain auto-detection is available when `--domain` is omitted.

## Sync Rules

**Source of Truth:** `src/ui-ux-pro-max/`

When modifying files:

1. **Data & Scripts** - Edit in `src/ui-ux-pro-max/`:
   - `data/*.csv` and `data/stacks/*.csv`
   - `scripts/*.py`
   - Changes automatically available via symlinks in `.claude/`, `.factory/`, `.shared/`

2. **Templates** - Edit in `src/ui-ux-pro-max/templates/`:
   - `base/skill-content.md` - Common SKILL.md content
   - `base/quick-reference.md` - Quick reference section (Claude only)
   - `platforms/*.json` - Platform-specific configs

3. **CLI Assets** - Run sync before publishing:
   ```bash
   cp -r src/ui-ux-pro-max/data/* cli/assets/data/
   cp -r src/ui-ux-pro-max/scripts/* cli/assets/scripts/
   cp -r src/ui-ux-pro-max/templates/* cli/assets/templates/
   ```

4. **Reference Folders** - No manual sync needed. The CLI generates these from templates during `uipro init`.

## Prerequisites

Python 3.x (no external dependencies required)

## Git Workflow

Never push directly to `main`. Always:

1. Create a new branch: `git checkout -b feat/...` or `fix/...`
2. Commit changes
3. Push branch: `git push -u origin <branch>`
4. Create PR: `gh pr create`

---

# Omarie's video work (read this first)

This repo is the working home for Omarie Young's video work. It is unrelated to the Antigravity Kit above. If the session is about footage, reels, ads, grading, captions or delivery, this section applies and the toolkit sections do not.

There are **three separate workstreams**. Establish which one you are in before touching anything, because they use different pipelines, different branches and different brand rules.

| workstream | who for | lives in | branch |
|---|---|---|---|
| Anti Stock | Omarie's own channel, @nq.young | `creator-kit/` | `claude/instagram-growth-video-editing-rswexx` |
| Formula Dynamics | client, luxury car shop | `formula-dynamics/` | `claude/formula-dynamics-assets-bnlnkm` |
| Supercar Experience | client, fleet rentals | see its own index | `claude/skills-download-ai3m6a` |

**One index for everything delivered:** https://claude.ai/code/artifact/c2501ca3-40ac-4b1d-833e-1b7c98f9abad — 79 files across Anti Stock and Formula Dynamics, with save paths. Supercar Experience is deliberately indexed separately at https://claude.ai/code/artifact/9bca62e7-2acb-437d-af68-da260daf2fdb so the two clients cannot drift. Do not start a third index.

## Anti Stock — the personal channel

Pipeline is `creator-kit/`: cut and grade with `cut_clip.sh`, transcribe, match his voice, plan shots, render overlays in Remotion, compose with ffmpeg. Read `creator-kit/WORKFLOW.md` and `creator-kit/DELIVERY.md` first.

**To build a reel, follow `creator-kit/fastcut/RUNBOOK.md`.** It reproduces MR8, the reference reel, from raw footage: cut and grade, transcribe, match his voice, then one command per reel. The build script is `creator-kit/fastcut/build_reel.sh` and takes no hardcoded paths.

**The approved format is the Fast Cut recipe.** Under 60 s, 4K vertical 2160x3840 at 29.97 fps, hook line plus auto-fitting title, first shot 3.0 s then 4.5 s or less, vlog grade at 85% match, captions uniform at 70.5% frame height in Archivo 800 with no gold pill and no oversized key word, only Omarie's voice captioned via `creator-kit/voice/omarie_profile.json`, card outro, no call to action, -14 LUFS with a 0.84 limiter. The older "pop" caption style is superseded.

**Colour is fixed in the pipeline, wrong in the delivered files.** `RED` in `creator-kit/remotion/src/Motion.tsx` is now `#FE0F13`, the real brand red measured off Omarie's own overlay pack and confirmed by the FD brand kit. Reels MR1-MR8 were built before that fix (2026-09-12) and still carry the old `#DE1A22`, so anything you build now will not colour-match them. Re-render the series when he asks; do not quietly mix the two.

**A second look exists: the Kinetic Cut** (`creator-kit/experiments/kinetic/`). Monochrome, letterboxed, strobing, with staircase type that lands one word at a time. It is NOT a replacement for Fast Cut — it is a separate format for a different kind of post, and it has its own builder. `build_kinetic.py` is spec-driven: shot list, band keyframes, grade and audio placement all live in one JSON, so a new piece is a new spec rather than new code. Two are built: K1 (his own words, from the take about working with Alex and Nate) and K2 (a reference edit he sent, rebuilt frame for frame on his footage).

`match_reference.py` is the general tool behind K2: measure any reference edit's shots, band, flashes and word timings, then fill every slot with the moment from his own clips that best matches its light and movement. That is how to answer "make this, but with my footage".

**Two traps found building it.** ffmpeg's `drawbox` has no timestamp variable — its `t` is box thickness — so an animated letterbox written as a drawbox expression silently fills the frame black. Draw moving bars per frame in Pillow instead. And shot-level averaging hides single-frame flashes: the reference put 40 one-frame white flashes on its cuts, which is most of why its strobe reads as an assault, and measuring per shot found one.

**The channel's own numbers question the Fast Cut format (reported 2026-09-16).** A vidIQ pull of
@nq.young's last 12 reels, run by another session, found the only two with real reach are 14-20 s
car-only shots with a question hook in the caption ("can you name this car"), at 2.2K and 1.3K plays.
Every talking-head vlog cut — the format the Fast Cut recipe reproduces — sits at 50-150 plays, and
every reel over 60 s is under 80. Followers are 3.7K, so even the best reel is reaching well under
the audience. **This contradicts the standing rule that Fast Cut is the approved format**, which was
set from MR8 as a taste reference without checking MR8's own performance. It also points the same way
as the external outlier search below: away from long talking-head cuts.

Nothing has been changed on the strength of this. It is one pull by one session and has not been
re-verified. **Do not re-render MR1-MR8 for the red fix until Omarie has settled the format question**,
because that is a day of compute spent on a format the numbers do not currently support.

**Caption coverage, measured 2026-09-13.** The flagged reels are MR4 at 18% of speech, MR3 at 51%, MR6 at 53%. Counting his words in the source shows most of this is the footage, not the edit: MR4's two takes hold 55 of his words in 86 s and the reel already captions 48 of them, so it cannot be rebuilt above roughly 20%. MR3 sits at 155 of 221 against a ceiling of 161 — not worth a rebuild. Only MR6 has real headroom, 128 of 200 against 143, which `plan_reel.py --weight 0.7` now reaches by giving the talky take more of the 56 s. Do not loosen the voice threshold to raise the number; it captions other people as him.

## Formula Dynamics — client ads

Completely different pipeline. **Pillow plus ffmpeg, not Remotion**, driven by `99-toolkit/build_all.py` from one constants file, `fd_brand.py`. Overlays render as full-frame PNGs and burn onto cue windows. A Remotion project exists only as a cross-check; do not make it the pipeline.

- Brand red `#FE0F13`. The accent stripe has **five** segments: red 36.7%, black 21.4%, white 19.4%, green 17.0%, yellow 5.5%.
- Measure before choosing. Sample luminance under a graphic's own zone across the whole clip and pick tone from the range, not the mean.
- Verify a composited still before rendering. Every anchor error in that project was caught or missed at that step.
- Keep-out zones on 9:16: top 11%, bottom 20%, right 16%, left 5%.
- Partner logos (NV Forged, iPE, RYFT) are their property and are deliberately not generated.
- Only put a performance figure on screen if it can be substantiated. The McLaren 765LT cut is **on hold** because its counter carries invented placeholder figures.

Full engineering record, fault log and cue timelines: https://claude.ai/code/artifact/ac280c47-c977-4500-a946-d8d22e8eb58c

## Standing rules, all workstreams

- Never push to `main`. Use the workstream's own branch.
- Ask before any Dropbox change that moves, renames or deletes.
- Report token usage after each task.
- Paid renders: there is no Higgsfield balance tool (the connector has exposed 37 of 88 tools on every reconnect this week, and `show_plans_and_credits` is a sales widget with no number). So quote the per-render cost instead — `get_cost:true` where the model supports it, otherwise the preset's listed price — and get an explicit go before each paid call. He checks the balance in the Higgsfield app himself. Confirm the target against a contact sheet before spending: the wrong-beat renders cost credits through misreading the reference, not through price.
- New concepts get a NEW artifact page; never overwrite one he keeps for comparison. But do not create a second index of the same thing.
- Archive, never delete. Superseded cuts stay reachable with a note saying what replaced them.
- Write to memory only at end of day, listed first and approved by him.
- Claude's memory store is full until 1 October. Until then the standing brief is this file plus Dropbox, `/Anti Stock Media/00 PROJECT MEMORY (backup until Oct 1).md`.
- At the start of any task-oriented session — any interaction where you will use tools and produce deliverables — invoke the `task-observer` skill (`.claude/skills/task-observer/`) before beginning work, so corrections and repeated patterns get logged to `skill-observations/log.md`. When loading any skill, check that log for OPEN observations tagged to it and apply them even if the skill file hasn't been updated yet.

## Memory, and why it lives here

The Vertiso Memory store is at its write limit (20/20) and refuses every write until **1 October 2026**.
Do not keep asking him to approve saves that cannot happen. **This file is the memory** in the meantime:
it loads automatically in every session in this repo, which the memory store does not. When something
durable is decided, write it into this file and commit it.

Queued for 1 October, already assessed with him and needing no further approval:

| memory | action on 1 Oct |
|---|---|
| 34453 "pop captions" | rewrite — Fast Cut replaced pop |
| 34455 pipeline as of 7 Sept | rewrite — vlog look right, captions wrong |
| 34407 priority connectors | rewrite — superseded by keep-5/pause-7 (34456) |
| 34394 "the companies he works for" | rewrite — they are three separate workstreams, see the table above |
| 34430 /watch needs a Whisper key | archive — never used |
| 34395 token spend analysis | archive — one-off |
| 34342 Ruflo resolver lesson | archive — different project |
| 34454 Vlog Cut links V1/VR1-VR8 | archive with a pointer to the MR series; links still resolve |
| 34456, 34452, 34408, 34341, 34340, 34339 | keep as is |

New items to write on 1 October: the Fast Cut build is reproducible from the runbook; three workstreams
not one; the red correction and which files carry which value; the caption-coverage defect; the index
hierarchy (one master, one per client); and that this file is the channel that actually loads. Add from
15 Sept: the Kinetic Cut as a second format with its own builder; the outlier finding that music-only
dominates his niche while every reel he has is voice-only; and what Higgsfield is and is not worth.

**Tools assessed 16 Sept 2026 (from three TikToks he sent).** Installed: `task-observer` (Eoghan Henn, CC BY 4.0 — a SKILL.md only, no code, no hooks). Rejected after sandbox install and code read: **OmniRoute** ("Omni") — routes the Claude Code login through a local proxy and mirrors other providers' models under `claude/` names; account risk, solves a cost problem we don't have. **claude-mem / Grok Mem** — needs bun, calls the Anthropic API itself, PostHog telemetry, paid-tier funnel; redundant with this file. The Instagram-analysis workflow from the third video is already available through the vidIQ connector (`vidiq_ig_profile_reels`, outlier search); no download needed. Full notes: Dropbox `/Anti Stock Media/00 Claude memory backup (2026-09-14)/task-observer.INSTALL.md`.

**What is actually working in his niche (vidIQ outlier search, 15 Sept).** Ten reels that beat their own creator's median by 16x to 312x, in car-shop and detailing content. Three patterns worth building to:

- **Music carries it.** Six of ten were music-only, two voice-plus-music, none voice-only. Every reel he has is voice-only with no bed. This is the biggest structural gap between his work and what wins.
- **Transformation beats process.** The two largest (8.2M and 2.1M views) were both dirty-to-clean restoration montages. He has the strongest possible version of this and has not used it: `01 garage walkthrough` is the empty shop and the later clips are finished bays. Right now that arc is buried inside chronological edits.
- **Six of ten loop.** His all end on a card outro.

Follower count is not the gate: one of these did 131K views on 5.5K followers.

**What Higgsfield is worth here (assessed 15 Sept).** Most of it is built for someone making footage that does not exist, which is the opposite of his problem. Generated car footage would also cost him the one thing his channel has, which is that it is visibly real. Three parts earn their place: **hosting** (the presigned upload plus CloudFront link is how every finished reel actually reaches him, since the Dropbox connector cannot take video), the **Virality Predictor**, and **TikTok trending music and publishing**. Skip video/image generation, Soul avatars, 3D, the website builder, and especially voice cloning, which would break the his-voice-only rule. It cannot generate music at all — its audio tool is speech-only.

**Known limitation:** the Dropbox connector writes text but not video, and this environment cannot reach Dropbox's upload page. Video is handed over as links or attached in chat.
