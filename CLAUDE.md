# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Second brain (Omarie's notes)

Look up facts about Omarie's setup, workstreams (Anti Stock, Formula Dynamics, Supercar Experience), brand specs, formats and standing rules with `python3 .claude/brain/recall.py "<question>"` first (about 0.1 s, no model call). Open notes or files by hand only if it doesn't answer. A hook also runs the lookup on every prompt and adds the matching note when there's a clear match.

The notes are private. They live in the private repo `oskibundles-hue/nq-agent-channel`, folder `brain/`. If recall.py says no notes were found, ask Omarie to attach that repo to the session. Never copy note contents into this public repo.

## No ultracode unless necessary

Omarie, 2026-09-27: "no more ultracode unless necessary." Multi-agent workflows (ultracode, the Workflow tool, agent fan-outs) used most of a week's usage limit in a day. Work in the main session by default, even when ultracode is switched on. Only use a workflow when the job truly can't be done well without one, and say why before starting it.

## Specialist agents (lead, specialists, reviewer)

The main session is the **lead**. It talks to Omarie, plans, delivers and pushes. The specialists in
`.claude/agents/` each do one job, look facts up in the second brain first, and hand back to the lead,
never straight to Omarie.

| agent | job | model |
|---|---|---|
| `researcher` | watch videos, research tools and trends; sourced reports (skill `watch`) | sonnet |
| `anti-stock-editor` | personal-channel reels via `creator-kit/` (Anti Stock branch) | sonnet |
| `fd-ads` | Formula Dynamics builds, in a worktree of the FD branch | opus, high effort |
| `se-ads` | Supercar Experience builds, in a worktree of an SE branch | opus, high effort |
| `reviewer` | read-only check before delivery: figures, brand, layout, frames, copy (skill `slopmonster`), loudness | opus |

The usual run is **build → reviewer → lead delivers**: a chain of one agent at a time, not a fan-out. The
builders work in worktrees of their workstream's branch, because this default branch doesn't carry
`creator-kit/`, `formula-dynamics/` or `supercar-experience/`.

**The regret-list gate is on** (Omarie, 2026-09-27). `.claude/hooks/regret_gate.py` runs before every Bash
and connector call (wired in `.claude/settings.json`). It **asks** before any paid Higgsfield call (quote the
cost first), anything that publishes or changes a live account, Dropbox moves or deletes, Windsor.ai write
actions, memory-store writes, force pushes, `git reset --hard`, `git clean -f` and recursive deletes outside
`/tmp`. It **refuses** any push to `main`. An "ask" waits for Omarie's click, so an unattended routine that hits
one stops there until he answers.

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
