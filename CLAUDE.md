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

   To show Omarie a post before it goes out (a carousel, a feed post, a reel set), present it on the **post mockup**
   page: the post in an Instagram phone frame beside its posting kit (versions, posting order with Save buttons,
   caption, the 9:16 cut, notes). He approved it on 2026-10-10 ("this is a great model and way to show what it would
   look like save this"). It lives in `design-systems/post-mockup/`, with `qa.js` to run before publishing. The
   style question above is still asked for the post itself.
2. **Then build that style all the way**: its techniques, process and quality bar, in the workstream's own brand. The
   page's gold on black is Supercar Experience's; Formula Dynamics keeps FD red and Bebas Neue, Anti Stock keeps its
   own look, and two brands never share a video.
3. **Agents never ask Omarie themselves.** The lead asks, then names the style in the brief. An agent
   whose brief names no style stops and asks the lead.

The rules and the feedback log are in `supercar-experience/09-campaign-ads/HOUSE-STYLE.md` on the SE branch
(`claude/supercar-rental-ad-graphics-o64vo3`).

## Delivering finished videos: Dropbox, through Video Drop when needed

Omarie, 2026-09-28. Finished videos go into his Dropbox (the notes' `deliver-to-dropbox` has the folders and
naming). When a session can't put the file there itself (the connector can't upload video; chat attachments stop
at 30 MiB), deliver through the one **Video Drop** page, https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP, and
never make a second one. Clear older cards only once they're confirmed in Dropbox, and ask him first. The
split/upload/SHA-256/confirm steps are in `.claude/playbooks/lead.md` (Video Drop steps).

## The NQ OS team (the main team in every session)

Omarie, 2026-09-30. The agents in `.claude/agents/` are the NQ OS agentmesh classes; each job goes to a
class, and the class decides the model and effort. Policy and reasons: `.claude/agentmesh/MESH.md`
(cloud v1.3); background, briefing and enforcement detail: `.claude/playbooks/lead.md`.

The main session is the **lead**. It talks to Omarie, plans, briefs one agent at a time, delivers and
pushes. Every agent looks facts up in the second brain first and hands back to the lead, never
straight to Omarie.

| agent | class | model/effort | job |
|---|---|---|---|
| `nq-run` | run | sonnet/low | run a script or read a file; report the lines word for word |
| `nq-label` | label | sonnet/low | tags, captions, sorting, contact-sheet calls; never a verdict |
| `nq-build` | build | opus/medium | build the piece or write the step and run it, including sourced research reports |
| `nq-fix` | fix | sonnet/medium | debug a failing chain and patch the source |
| `nq-check` | check | opus/medium | read-only quality pass before delivery: style, brand, layout, frames, copy, loudness |
| `nq-story` | story | opus/high | the big creative call: options with a recommendation, for the lead to put to Omarie |
| `nq-facts` | facts (floor) | opus/high | every figure and claim in the delivered file traced to a named source |
| `nq-second` | second (floor) | sonnet/high | independent voter on a different model; may only add a block |

The `plate` class is switched off, so it has no agent.

- **Brief with the class, the playbook** (`.claude/playbooks/`; `vlog-lifestyle.md` for spotting and tagging the
  moments that carry a personal, YouTube-style vlog in any workstream) **and the style.** Builders work in
  worktrees of their workstream's branch, because this default branch doesn't carry the workstream folders.
- **The usual chain** is `nq-build` → `nq-check` → lead delivers. Figures, specs, prices, names or
  "we did X" claims go through `nq-facts`, then `nq-second`, independently; either can block.
- **A failed step goes sideways, not up.** `run`, `build` and `fix` retry once, then report; the lead
  sends a failure to `nq-fix`, because a bigger model fails at a broken flag the same way.
- **Fewer agents is the saving.** An agent costs about 55k tokens of start-up context, so a job the lead
  can do in a few commands stays with the lead. Settings cap subagents at one at a time, depth 1.
- **The regret gate** (`.claude/hooks/regret_gate.py`, 2026-09-27) **refuses** any push to `main`,
  `master` or the default branch `claude/new-session-mucc2q` (also via `git -C`, `sudo`, `env`, `bash -c`)
  and GitHub-connector file writes to them, because those change only through a PR. It **asks** before
  paid Higgsfield calls, publishing, Dropbox moves/deletes, force pushes, `reset --hard`, `clean -f` and
  recursive deletes outside `/tmp`; full list in `.claude/playbooks/lead.md`. Test:
  `python3 .claude/hooks/test_regret_gate.py`.

## Token cost rules (Omarie, 2026-10-06)

- **Hand off after each job:** write a short handoff and start the next job in a fresh session, and also when
  the cost guard warns at 300k or after any compaction, because every call re-reads the whole conversation.
- **Sessions start on the latest default branch** (added 2026-10-06): a SessionStart hook
  (`.claude/hooks/session_refresh.py`) fast-forwards a clean checkout to `origin/claude/new-session-mucc2q` when
  it's behind, and tells the session when it can't (uncommitted changes or its own commits). If it says settings,
  hooks, agents or this file changed, restart the session. Why: the "One-way ticket" Part 2 session started 10
  commits behind, so the 300k auto-compact and the `nq-*` agents never loaded. Test:
  `python3 .claude/hooks/test_session_refresh.py`.
- **Auto-compact is set at 300k** (`CLAUDE_CODE_AUTO_COMPACT_WINDOW` in `.claude/settings.json`).
- **Change effort, not the model, mid-session,** because a model switch re-writes the whole cache.
- **Start a fresh agent from a summary rather than resuming one** past about 150k or idle more than 5 minutes,
  because its cache has gone cold.
- **Keep frames out of the lead:** send them to `nq-check` or `nq-label` as one contact sheet. The cost guard
  denies a second Read of the same image in the lead.
- **Wait on a PID, a marker file or `run_in_background`, with a hard timeout,** never a `pgrep -f` loop,
  because that loop matches itself and never ends.
- **Read a page by file only:** before republishing an artifact, read it once with `path: "index.html"`, never
  a plain read plus a path read, because each returns the whole page ("One-way ticket" Part 2: the double read
  kept the lead over 300k for 9 calls). Asset read-backs for the SHA-256 test take one `path` per call.
- **Filter render, ffmpeg and ingest logs through `tail` or `grep`** before they reach the context.
- **Lean agents:** run, label, facts and second skip CLAUDE.md (`omitClaudeMd`); build and fix have `maxTurns` caps.
- **The meter:** `python3 .claude/brain/cost_meter.py` meters a session; `live_card.py done` logs the job's cost
  line; `python3 .claude/brain/post_mortem.py review` is the weekly review, and its proposals go to Omarie as a
  click or a PR before any rule changes.
- **Finish or hand off before going idle, and point reminders and check-ins at a small session** (added
  2026-10-06; Monday's review checks it). The cache goes cold after an idle gap, so each wake of a big session
  pays to write its whole context again.
- **The cost guard** (`.claude/hooks/cost_guard.py`) warns, and only blocks repeat frame reads.
- **In every session, not just this repo's** (Omarie, 2026-10-06: "it should work in every session thats the
  point"): the cloud environment's setup script runs `.claude/cloud/install.py`, which installs these hooks, the
  300k auto-compact, the agents and this file at the user level from the default branch. The setup line and the
  check are in `.claude/cloud/README.md`.

## Show what you're working on (the Working-now card)

Omarie, 2026-09-30. On any job past a couple of minutes the lead (never an agent) keeps a card on the
control room's **Working now** block (https://claude.ai/artifact/JdMaXgCuUu7XHQ3yRhEYFy) with
`python3 .claude/brain/live_card.py start|step|done|blocked|waiting`, updating at least every 15 minutes
and never stopping on `working`, because a stale card shows as quiet. Steps: `.claude/playbooks/lead.md`.

## Organize long messages first (the prompt tool)

Omarie, 2026-10-06: "we should create a prompt tool that makes my prompts sound much better and organized once i send
one". He picked auto-organize. When his message is long or carries several asks, open the reply with it as a short
brief, in his words where you can: what he wants (numbered, most important first), what he has already decided, and
the open questions. Then ask one click ("Is this brief right?", plus up to three open questions, recommendation first)
and start once he answers. `.claude/hooks/prompt_brief.py` spots these messages and adds the reminder; test it with
`python3 .claude/hooks/test_prompt_brief.py`. Use the same brief as the prompt when a job goes to a new session.

## Prompting Claude 5 models

Brief agents with the whole job, the why, and what done looks like; write rules as "do Y, because Z"; ask
`nq-check` for a second look rather than asking an agent to double-check itself. Sourced guidance
(Ben AI, 2026-09-28), not Omarie's own rule; the full six points are in `.claude/playbooks/lead.md`.

## This repo's code (Antigravity Kit)

A searchable UI/UX design database (`python3 src/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain>`).
Source of truth is `src/ui-ux-pro-max/`; copy into `cli/assets/` before publishing. Architecture, domains,
stacks and sync rules: `.claude/playbooks/antigravity-kit.md`.

## Git Workflow

Never push directly to `main` or the default branch (`claude/new-session-mucc2q`); the regret gate refuses both. Always:

1. Create a new branch: `git checkout -b feat/...` or `fix/...`
2. Commit changes
3. Push branch: `git push -u origin <branch>`
4. Create PR: `gh pr create`
