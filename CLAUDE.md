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

**Open defect:** caption coverage is low on three reels — MR4 at 18% of speech, MR3 at 51%, MR6 at 53%. On muted autoplay that is most of the dialogue lost. The cause is the his-voice filter dropping other speakers; the fix is more of his own speech in the window, not looser voice matching.

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
- New concepts get a NEW artifact page; never overwrite one he keeps for comparison. But do not create a second index of the same thing.
- Archive, never delete. Superseded cuts stay reachable with a note saying what replaced them.
- Write to memory only at end of day, listed first and approved by him.
- Claude's memory store is full until 1 October. Until then the standing brief is this file plus Dropbox, `/Anti Stock Media/00 PROJECT MEMORY (backup until Oct 1).md`.

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
hierarchy (one master, one per client); and that this file is the channel that actually loads.

**Known limitation:** the Dropbox connector writes text but not video, and this environment cannot reach Dropbox's upload page. Video is handed over as links or attached in chat.
