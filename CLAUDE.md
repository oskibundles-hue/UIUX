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

## Working Style

Standing instructions from the shop, not preferences.

**Take a list one item at a time** when asked to. Deliver the first item, show
it, wait. A batch of six changes lands as six things to argue with at once.

**Fact-check before building, and measure rather than remember.** Frame
timestamps, text widths against the Instagram action rail, panel hold times off
the dry run, brightness before choosing a logo tone. A number read off the file
beats a number recalled from an earlier session every time.

**Say when the ask and the facts disagree.** "Any oil service" next to a package
price reads as unlimited when the package is two. Flag it, propose wording that
keeps the shop's voice and stays true, and keep building — do not silently
"correct" their language or silently ship the overreach.

**Give an opinion.** Which cut is stronger, which line is weaker, what you would
drop. Say it plainly with the reason, then do what they decide.

**Cross-reference before starting.** The copy rules, the approved settings, the
partner file, prior sessions' artifacts. A new ad starts from an approved ad's
settings, never from scratch.

**Improve the prompt when it helps.** If a request would come out better stated
a different way, say so and use the better version — do not just execute a
looser reading in silence.

## Ad Copy Order

**Benefit first, price late, never in the opening.** A price in the hook filters
people out before the value is made. Lead with what the service does for the car
— keeps it dependable, reliable, up to date — then name the work, then the ask.
For a high-ticket package, a DM-for-pricing CTA converts better than a figure on
screen: it lets the shop sell instead of letting the number decide.

**One service, one ad.** Each service earns its own cut with its own reason to
care — brake service is about stopping, suspension about how it rides. A bundle
ad and a single-service ad are different jobs, and both exist.

## Artifact Conventions

Keep the "fast cut" look: dark ground, Bebas Neue display, Barlow body, IBM Plex
Mono for figures, brand red as the only accent.

Any artifact covering video gets a cue timeline — a time ruler, one labelled lane
per element, bars placed by `left: start/duration`. Take the numbers from
`build_edit.py --dry-run`, never by hand. Never let a bar's label clip mid-word.

One page per job: update an existing artifact rather than publishing a second one
that covers the same ground.

## Video Edits

Whenever a video is cut, ask whether they also want the **SFX motion pack
version** — `build_edit.py --motion` (which implies `--sfx`). It is a separate
deliverable, not a replacement, so the plain cut still gets made.

Sound density adapts per clip rather than being fixed: `fd_sfx.py` derives a
hit from every cue and drops the secondary layers if the result runs busier
than its cap. Each video is different — judge it, don't hold a number.

## Delivering Downloads

When asked for files to download, always build a **download-page artifact** in
the fast-cut look: categorised sections, one row per file with its runtime,
size and a one-tap Download button that saves under the real filename. Never a
wall of raw URLs in chat.

Verify the links before publishing — count the buttons, check every id against
a set read off disk. A download page with one wrong link is worse than none.

Files with no public URL get a row too, marked as delivered in chat rather than
a dead button, and carry the folder path to save them into.
