#!/usr/bin/env python3
"""After nq-check, save the job's card; after a FAIL, show the lead where it split from a good job ("gap 2").

Two events, one script (.claude/settings.json):
  SubagentStop, matcher nq-check   saves the job card (job_card.py). This is the only event that sees a
                                   background nq-check finish. A SubagentStop hook can't speak to the lead
                                   (its output goes to the subagent), so on a FAIL with a reference on file it
                                   leaves the note in work/jobdiff-pending/<session>.txt.
  PostToolUse, every tool          a foreground nq-check's result arrives here: save the card (same id, so no
                                   duplicate) and add the first divergence next to the FAIL as additionalContext.
                                   Any other tool call: if a note is pending for this session, add it once.
No FAIL, no reference yet, or anything going wrong: silent, exit 0. Never blocks. Stdlib only.
Test: python3 .claude/hooks/test_job_diff_hook.py
"""
import json, os, sys

BRAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brain")


def pending_path(session):
    from nqos_config import WORK
    return os.path.join(WORK, "jobdiff-pending", (session or "nosession").replace("/", "_") + ".txt")


def note_for(card):
    import job_diff
    if not card or card.get("verdict") != "FAIL":
        return None
    text, _ = job_diff.first_divergence(card)
    if not text:
        return None
    return ("[job diff, gap 2] nq-check FAILed. Lined up against a good job of the same kind:\n" + text +
            f"\nFull diff: python3 .claude/brain/job_diff.py {card['id']}")


def say(event, text):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


def main():
    ev = json.load(sys.stdin)
    sys.path.insert(0, BRAIN)
    event = ev.get("hook_event_name", "")
    session = ev.get("session_id", "")
    if event == "SubagentStop":
        if ev.get("agent_type") != "nq-check":
            return
        import job_card
        card = job_card.from_event(ev)
        if not card:
            return
        job_card.save(card)
        note = note_for(card)
        if note:
            p = pending_path(session)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write(note)
        return
    if event != "PostToolUse":
        return
    inp = ev.get("tool_input") or {}
    if ev.get("tool_name") in ("Agent", "Task") and inp.get("subagent_type") == "nq-check":
        import job_card
        card = job_card.from_event(ev)
        if card:
            job_card.save(card)
            note = note_for(card)
            p = pending_path(session)
            if os.path.isfile(p):
                os.remove(p)
            if note:
                say(event, note)
            return
    p = pending_path(session)
    if os.path.isfile(p):
        note = open(p).read()
        os.remove(p)
        if note.strip():
            say(event, note)


if __name__ == "__main__":
    try:
        main()
    except Exception:                                  # a broken note must never stop the lead's work
        pass
    sys.exit(0)
