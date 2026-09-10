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

This repo is also the working home for Omarie Young's short-form video editing. That work has nothing to do with the Antigravity Kit above; it lives in `creator-kit/`. If the session is about footage, reels, grading, captions or delivery, this section applies and the toolkit sections do not.

**Read these before starting:**

- `creator-kit/WORKFLOW.md` — the pipeline, looks, caption styles, voice matching, and hard-won gotchas.
- `creator-kit/DELIVERY.md` — every hosted file with its link, grouped by series.
- Dropbox, `/Anti Stock Media/00 PROJECT MEMORY (backup until Oct 1).md` — the full standing brief: the approved recipe in detail, connector policy, Dropbox layout, open items. Claude's memory store is full until 1 October, so that file is the source of truth in the meantime.

**The approved reel format is the "Fast Cut" recipe.** Under 60 seconds, 4K vertical 2160x3840 at 29.97 fps, hook line plus auto-fitting title, first shot 3.0 s then 4.5 s or less, vlog grade at 85% match, captions uniform at 70.5% frame height in Archivo 800 with no gold pill and no oversized key word, Formula Dynamics red `#DE1A22` with gold `#FBD101`, only Omarie's voice captioned via `creator-kit/voice/omarie_profile.json`, card outro, no call to action, -14 LUFS with a 0.84 limiter. The older "pop" caption style is superseded; do not use it.

**Standing rules:**

- Never push to `main`. Work on `claude/instagram-growth-video-editing-rswexx`.
- Ask before any Dropbox change that moves, renames or deletes.
- Report token usage after each task.
- New concepts get a NEW artifact page. Never overwrite an old one; he keeps them to compare.
- Deliver files through the Downloads page, not raw links: https://claude.ai/code/artifact/fb14668e-2db5-4cf4-9e6c-ae9df97b0d82 (rebuilt by `motion2/make_hub.py` from DELIVERY.md).
- Write to memory only at end of day, listed first and approved by him.

**Known limitation:** the Dropbox connector writes text files but not video, and this environment cannot reach Dropbox's upload page. Video is handed over as links.
