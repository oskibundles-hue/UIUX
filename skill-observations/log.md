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

**Status:** OPEN
**Date:** 2026-09-16
**Session context:** Earth Zoom intros and LED-blink renders on Higgsfield across several days.
**Skill:** CLAUDE.md standing rules (Higgsfield spend)
**Type:** internal
**Phase/Area:** Pre-spend check

**Issue:** The rule requires reporting the credit balance before any paid render. The Higgsfield connector has exposed 37 of 88 tools on every reconnect this week and never a balance tool; show_plans_and_credits is a sales widget with no number. Every session flags the same impossibility, and 10 credits were still spent on a wrong-beat render.

**Suggested improvement:** Rewrite the rule to something the environment can enforce: quote the per-render cost (get_cost:true where the model supports it, otherwise the preset's listed price) and get an explicit go before each paid call; he checks the balance in the Higgsfield app himself. Also: no paid render until the target beat has been confirmed against a contact sheet, since the two wrong-beat renders came from misreading the reference, not from cost.

**Principle:** A rule needs a mechanism that exists in the environment. If the tool a rule depends on is missing, rewrite the rule rather than re-flagging the gap every session.
