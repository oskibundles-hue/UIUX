# Skill Observation Log

Observations captured during task-oriented work. Each entry identifies a
potential skill improvement or new skill opportunity.

**Status key:** OPEN = not yet actioned | ACTIONED = skill updated/created |
DECLINED = user decided not to pursue

---

## 2026-09-16 — Session: tool assessment, Task Observer install, vidIQ profile pull

### Observation 1: Channel numbers contradict the approved Fast Cut format

**Status:** OPEN
**Date:** 2026-09-16
**Session context:** First vidIQ pull of @nq.young (profile + 12 reels) after installing Task Observer.
**Skill:** CLAUDE.md "Anti Stock" section and creator-kit/fastcut/RUNBOOK.md (the Fast Cut recipe)
**Type:** internal
**Phase/Area:** Format selection, before building or re-rendering reels

**Issue:** The two reels with real reach are 14–20 s car-only shots with a question hook in the caption ("can you name this car", "guess where I'm at"): 2.2K and 1.3K plays. Every talking-head vlog cut (the format the Fast Cut recipe reproduces) sits at 50–150 plays, and every reel over 60 s is under 80 plays. Follower count is 3.7K, so even the best reel reaches well under the audience. The recipe was tuned to MR8 as the reference reel without checking MR8's own performance against the rest of the channel.

**Suggested improvement:** Add a "check the numbers first" step at the top of RUNBOOK.md: pull the channel's last 12 reels (vidiq_ig_profile_reels, 5 credits) and confirm the format being reproduced is actually the one that performs. Consider a second recipe, "Hook Cut": under 20 s, car-only, no talking, question in the caption, title card only. Do not re-render MR1–MR8 for the red fix until this is settled.

**Principle:** Validate a format rule against the channel's own performance data before scaling it. A reference reel is a taste choice until the numbers say otherwise.

**Reference file:** vidIQ output is in this session only; the 12-reel table is reproduced in the chat reply of 2026-09-16 and should be copied to Dropbox `/Anti Stock Media/00 Claude memory backup (2026-09-14)/` if it is to be acted on later.

### Observation 2: "Report Higgsfield balance before spending" has no mechanism

**Status:** ACTIONED 2026-09-25 — `.claude/hooks/regret_gate.py` now asks before every paid Higgsfield call and tells Claude to quote the per-render cost and confirm the beat against a contact sheet. The CLAUDE.md rule itself was rewritten on 17 Sept (a38270b); the gate is the mechanism behind it.
**Date:** 2026-09-16
**Session context:** Earth Zoom intros and LED-blink renders on Higgsfield across several days.
**Skill:** CLAUDE.md standing rules (Higgsfield spend)
**Type:** internal
**Phase/Area:** Pre-spend check

**Issue:** The rule requires reporting the credit balance before any paid render. The Higgsfield connector has exposed 37 of 88 tools on every reconnect this week and never a balance tool; show_plans_and_credits is a sales widget with no number. Every session flags the same impossibility, and 10 credits were still spent on a wrong-beat render.

**Suggested improvement:** Rewrite the rule to something the environment can enforce: quote the per-render cost (get_cost:true where the model supports it, otherwise the preset's listed price) and get an explicit go before each paid call; he checks the balance in the Higgsfield app himself. Also: no paid render until the target beat has been confirmed against a contact sheet, since the two wrong-beat renders came from misreading the reference, not from cost.

**Principle:** A rule needs a mechanism that exists in the environment. If the tool a rule depends on is missing, rewrite the rule rather than re-flagging the gap every session.

## 2026-09-25 — Session: video re-watch, agents and gates

### Observation 3: Subagents were briefed before the repo was read

**Status:** OPEN
**Date:** 2026-09-25
**Session context:** Four research agents were sent to rebuild four YouTube videos for "NQ OS".
**Skill:** CLAUDE.md (session start) and `.claude/agents/researcher.md`
**Type:** internal
**Phase/Area:** Briefing subagents; any recommendation about "his skills" or "his workstreams"

**Issue:** The agents were told FD was "a marketing/ads client" and SE "a services/production business", and the recommendations were written against skills like `/site-audit`, `/inbox-triage` and `/perf-report`. Those skill names were placeholder data inside the JARVIS test dashboard, not real skills, and the three workstreams are one personal channel plus two automotive clients. The root CLAUDE.md, which says all of this, was only read after "do it all" — once the recommendations had already gone to him.

**Suggested improvement:** Before briefing any subagent or recommending changes to "the OS", read root `CLAUDE.md` and `creator-kit/BRANDS.md`, and paste the workstream table into the brief (the `researcher` agent now carries it). Label sample data in any dashboard as sample, in the page itself.

**Principle:** A brief inherits every wrong assumption in it. Ground the brief in the repo's own description of itself, not in the last thing on screen.

### Observation 4: YouTube cannot be watched from this container except through Gemini

**Status:** ACTIONED 2026-09-25 — `.claude/skills/watch/` vendored with `SOURCE.md`; `researcher` agent uses it.
**Date:** 2026-09-25
**Session context:** Re-watching four videos after a bot-check page had blocked every earlier attempt.
**Skill:** `watch` (bradautomates/claude-video)
**Type:** internal
**Phase/Area:** Getting any evidence from a YouTube link

**Issue:** yt-dlp, captions, transcript endpoints, Invidious/Piped mirrors and a headless browser all fail from this IP. The Gemini engine works because the URL goes to Google. The free tier caps each model at about 20 requests a day; a 2.5-hour video needed 30-minute pieces; overloaded models return 503 and need rotating. When Gemini was down, Jina's reader (`r.jina.ai`, raw HTML) still returned each video's description, chapters and links, which led to the creators' own companion pages.

**Suggested improvement:** Done as described. Still open: the Gemini key lives in `~/.config/watch/.env`, which does not survive a container reset. It belongs in the environment's secrets setting.

**Principle:** When the direct route is blocked, find a service that fetches from its own IP — and write down the failure modes the first time, so the next session doesn't rediscover them.

### Observation 5: Gemini's video metadata is unreliable

**Status:** ACTIONED 2026-09-25 — the verification step is in `watch/SOURCE.md` and the `researcher` agent.
**Date:** 2026-09-25
**Session context:** Gemini reports for four videos.
**Skill:** `watch`
**Type:** internal
**Phase/Area:** Reporting what a video is

**Issue:** Gemini gave the wrong title and creator for two of four videos ("How I run my life with a team of AI agents" for Sharbel's Hermes video; "Simon MacDonald" for Simon Scrapes), a 15:58 length for a video whose chapters run past 35 minutes, and named "Claude 3.5 Sonnet" in a video about a model released in 2026. The content it described was mostly consistent with the creators' own pages.

**Suggested improvement:** Always confirm title and creator with YouTube's oEmbed and check coverage against the chapter list before relaying a Gemini report.

**Principle:** A model's report on media is evidence to check, not a record. Verify the cheap facts with a primary source so the expensive ones can be trusted.

### Observation 6: The account-wide CLAUDE.md did not load in this container

**Status:** OPEN — restored in this container on 2026-09-25 with `git show origin/claude/skills-download-ai3m6a:.claude/user-CLAUDE.md > ~/.claude/CLAUDE.md`; the single-backup problem remains.
**Date:** 2026-09-25
**Session context:** Looking for the standing rules while building the approval gates.
**Skill:** `.claude/user-CLAUDE.md` (exists only on branch `claude/skills-download-ai3m6a`)
**Type:** internal
**Phase/Area:** Session start

**Issue:** The SE branch's CLAUDE.md says `~/.claude` persists across sessions (verified 2026-09-11) and that `~/.claude/CLAUDE.md` carries the account-wide rules. In this container `~/.claude/CLAUDE.md` did not exist, so those rules were not loaded this session. The only backup is on the SE branch, so a session on this branch cannot restore it.

**Suggested improvement:** At session start, if `~/.claude/CLAUDE.md` is missing, restore it from the backup. Consider keeping the backup on every workstream branch, or in Dropbox beside the project memory, so any session can restore it.

**Principle:** A rule that lives in one place outside version control is a rule that silently stops applying. Check that the rules loaded, not only that they exist.
