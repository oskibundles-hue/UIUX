# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Second brain (Omarie's notes)

Look up facts about Omarie's setup, workstreams (Anti Stock, Formula Dynamics, Supercar Experience), brand specs, formats and standing rules with `python3 .claude/brain/recall.py "<question>"` first (about 0.1 s, no model call). Open notes or files by hand only if it doesn't answer. A hook also runs the lookup on every prompt and adds the matching note when there's a clear match.

The notes are private. They live in the private repo `oskibundles-hue/nq-agent-channel`, folder `brain/`. If recall.py says no notes were found, ask Omarie to attach that repo to the session. Never copy note contents into this public repo.

## No ultracode unless necessary

Omarie, 2026-09-27: "no more ultracode unless necessary." Multi-agent workflows (ultracode, the Workflow tool, agent fan-outs) used most of a week's usage limit in a day. Work in the main session by default, even when ultracode is switched on. Only use a workflow when the job truly can't be done well without one, and say why before starting it.

## The standard for every job, and which style to use (every session, every branch)

Omarie, 2026-09-28: "My locked on artifact is my standard for any work I work on", and "make sure every
session/branch/everything knows and implements it no matter what when creating any work but ask beforehand what
style should be used."

1. **Ask which style first.** Before building any new piece of work (an ad, a vlog, a reel, a poster, a page), ask
   Omarie which style to use, as a click (AskUserQuestion) with your recommendation first. Offer the approved styles:
   **Locked-On**, the standard (https://claude.ai/artifact/WCe1qHhTrMDw7bkDaskeQm); **Quick-Promo** when a promo has to go out in under
   about 30 minutes; and the workstream's own approved formats where they fit (Fast Cut and Reel Cut for Anti Stock,
   the Sep 15 rally v2 build for Supercar Experience vlogs). Also offer the proposed looks on the same page
   (**Now Boarding**, **Paste-Up**), marked as proposed. For a page people use to find things (an index, a
   directory, a deliverables list, a to-do board), offer the **iPhone index layout** first: Apple's system font, iOS
   colours, a tab bar and one search across everything. Omarie picked it on 2026-09-28 ("save this apple layout it
   looks so nice"). It lives in `design-systems/iphone-index/`, with `qa.js` to run before publishing. Skip the
   question only when he has already named the style for this piece.
2. **Then build that style all the way**: its techniques, process and quality bar, in the workstream's own brand. The
   page's gold on black is Supercar Experience's; Formula Dynamics keeps FD red and Bebas Neue, Anti Stock keeps its
   own look, and two brands never share a video.
3. **Specialist agents never ask Omarie themselves.** The lead asks, then names the style in the brief. An agent
   whose brief names no style stops and asks the lead.

The rules and the feedback log are in `supercar-experience/09-campaign-ads/HOUSE-STYLE.md` on the SE branch
(`claude/supercar-rental-ad-graphics-o64vo3`).

## Delivering finished videos: Dropbox, through Video Drop when needed

Omarie, 2026-09-28: "keep that as a rule for the future for when we come into this problem and keep it all in that
artifact." Finished videos go into his Dropbox (the notes' `deliver-to-dropbox` has the folders and naming). The
Dropbox connector can't upload a video, and chat attachments stop at 30 MiB. So when a session can't put the file
in Dropbox itself, deliver it through the **Video Drop** page: https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP

- Each video is a card. Omarie taps **Save video**; the page rejoins the parts and opens his phone's share sheet,
  and he picks **Dropbox** and the folder named on the card.
- Use this one page for every delivery. Never make a second one.
- The steps are in the notes:
  1. Split the master into 19 MiB parts.
  2. Upload them as the page's assets in one call.
  3. Add a card and republish.
  4. Test that the rejoined file's SHA-256 matches the master.
  5. Once he has saved it, confirm the file in Dropbox at the exact size.
- The page holds 1 GiB. Clear older cards only once they're confirmed in Dropbox, and ask him first.

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

**Claude Code enforces the chain** (Omarie, 2026-09-28). `.claude/settings.json` sets
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to 1: one subagent runs at a time,
and subagents can't start their own. Claude 5 models delegate more readily, and every agent costs a full conversation's
worth of tokens. A second spawn while one is running comes back as `Concurrent subagent limit reached`: wait for the
first to finish. Sessions with ultracode on are never refused.

**The regret-list gate is on** (Omarie, 2026-09-27). `.claude/hooks/regret_gate.py` runs before every Bash
and connector call (wired in `.claude/settings.json`). It **asks** before any paid Higgsfield call (quote the
cost first), anything that publishes or changes a live account, Dropbox moves or deletes, Windsor.ai write
actions, memory-store writes, force pushes, `git reset --hard`, `git clean -f`, and recursive deletes (`rm -r`,
`find -delete`) outside `/tmp`. It **refuses** any push to `main`, `master` or this repo's default branch
`claude/new-session-mucc2q`, because those only change through a PR. That covers a bare `git push` from one of them,
`git -C`, and commands wrapped in `sudo`, `env` or `bash -c`. Its GitHub connector rules (refuse file writes to
those branches, ask before merging a PR) take effect once `github` is added to the hook's matcher in
`.claude/settings.json`. An "ask" waits for Omarie's click, so an unattended routine that hits one stops there until
he answers. Test it with `python3 .claude/hooks/test_regret_gate.py`.

## Prompting Claude 5 models (sourced, not Omarie's own rule)

From research, 2026-09-28 — Ben AI, "Anthropic Just Revealed 7 New Rules for Prompting Claude 5
Models" (full notes on the `claude/deep-research-report-5oh5nm-gemini-notes` branch, under
`research/agent-videos-2026-09-28/gemini-notes.md`, video 1). Applies to how the lead briefs
specialist agents and how any agent prompts a Claude 5 model directly. This is adopted guidance,
not a standing instruction from Omarie — update or drop it if it doesn't hold up.

1. **Give the whole job, not steps.** State the task, guardrails and exit criteria up front rather
   than spelling out step 1/2/3 for anything past a trivial task.
2. **Say why, not just what.** A brief that names who the output is for and why it matters gets
   better judgment calls on the details it doesn't spell out.
3. **Define what done looks like.** State the exit criteria and output shape explicitly — Claude 5
   models tend to over-run rather than under-run without one.
4. **Reasons beat hard rules.** "Never do X" lands worse than "do Y, because Z." Prefer the second
   form when writing standing rules, including in this file.
5. **Don't ask it to double-check itself.** Skip "verify your work," "think step by step," or a
   built-in review pass — Claude 5 models already self-correct on their own. Ask a human or the
   `reviewer` agent for a second look instead, not the same model again.
6. **Fix tone once, not every time.** If a specialist's output keeps needing the same tone or
   format correction, put it in that agent's `.md` file once instead of repeating it in every brief.

Left out: the source's "Interview Me" skill (Anthropic uses one internally to ask clarifying
questions before a big task) — worth building only if we make a matching step for large briefs.

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

Never push directly to `main` or the default branch (`claude/new-session-mucc2q`); the regret gate refuses both. Always:

1. Create a new branch: `git checkout -b feat/...` or `fix/...`
2. Commit changes
3. Push branch: `git push -u origin <branch>`
4. Create PR: `gh pr create`
