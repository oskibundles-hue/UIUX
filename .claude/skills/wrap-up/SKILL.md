---
name: wrap-up
description: Closes out a finished job so the next one starts smarter — captures Omarie's corrections, confirmed style choices and trusted sources into the observation log and agent memory, proposes CLAUDE.md changes for approval, and reports token usage. Use when a deliverable has been handed over, or when he says "wrap up", "save what you learned", "end of job" or "end of day". Not for mid-task checkpoints, and never a way to write to the Vertiso memory store.
---

# Wrap-up

The job is done when the work is delivered *and* what he taught you this round is written down.
"You are not running a team, you are training one."

## 1. Collect, from this session only

- **Corrections** he made — quote him. A correction that says *why* is worth more than one that says
  what.
- **Choices he confirmed**: format, length, style, colour, caption treatment, which variant he picked.
- **Sources** he trusted or rejected (a reference edit, a creator, a data source).
- **What went wrong** in the process: a wrong assumption, a tool that failed, a rule that had no way
  to be enforced.

If there is nothing in a category, leave it out. Do not invent learnings to fill the page.

## 2. Write it where it will load next time

| what | where | approval |
|---|---|---|
| A correction or pattern that should change how a skill, agent or runbook works | `skill-observations/log.md`, in the task-observer entry format, tagged to the file it should change | none — the log is for this |
| Something a specialist agent should remember next run | that agent's project memory (`.claude/agent-memory/<agent>/MEMORY.md`), one dated line each | none |
| A durable decision (format settled, a rule changed, a client preference) | `CLAUDE.md` — **propose the exact edit, list it, and apply only after he approves** | required |

A one-off correction is not a rule. Log it only if it would apply to the next job of this kind.

Never write to the Vertiso memory store from here. It is full until 1 October, and memory writes happen
at end of day, listed first and approved by him. `CLAUDE.md` is the memory until then.

## 3. Report

End with, in plain words:

1. What was delivered, with links.
2. What was logged, and where.
3. Any `CLAUDE.md` edits waiting for his yes.
4. Token usage (standing rule):

       echo "{\"transcript_path\":\"$(ls -t ~/.claude/projects/*/*.jsonl | head -1)\"}" | bash .claude/token-report.sh

Then commit the log and memory files to the workstream's own branch.
