#!/usr/bin/env python3
"""After nq-check, save the job's card; after a FAIL, show the lead where it split from a good job ("gap 2").

Two events, one script (.claude/settings.json):
  SubagentStop, matcher nq-check   logs the report's FAIL rows for the weekly review (gap 1, quality_fails.py),
                                   then saves the job card (job_card.py), so nq-check's output is read once;
                                   each part runs on its own, so one failing never stops the other. This is the only event that sees a
                                   background nq-check finish. A SubagentStop hook can't speak to the lead
                                   (its output goes to the subagent), so on a FAIL with a reference on file it
                                   leaves the note in work/jobdiff-pending/<session>.txt.
  PostToolUse, matcher SubagentHandback
                                   the same capture as SubagentStop, from the handback message. Most agents
                                   report this way, so their last text is empty and SubagentStop alone saw no
                                   report (the real run of 2026-10-27 left no card). Whichever of the two fires
                                   second finds the card saved and does nothing.
  PostToolUse, matcher Agent|Task  a foreground nq-check's result arrives here: save the card (same id, so no
                                   duplicate) and add the first divergence next to the FAIL as additionalContext.
  PostToolUse, every tool          through jobdiff_pending.sh, which starts Python only when a note is pending
                                   (about 4 ms a call instead of 30; 2026-10-27): add the pending note once.
                                   Runs with --pending-only, so it leaves Agent and Task calls to the entry above.
After saving a card it starts costlog_push.py in the background, so cards and FAIL rows reach nq-agent-channel
even when the session never runs live_card.py done.
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


def take_pending(session):
    """The pending note, claimed with a rename so two hooks firing on the same call never both show it."""
    p = pending_path(session)
    claim = f"{p}.{os.getpid()}"
    try:
        os.rename(p, claim)
    except OSError:
        return ""
    try:
        return open(claim).read()
    finally:
        os.remove(claim)


def push_later():
    """Push the new card and FAIL rows to nq-agent-channel in the background (costlog_push.py), so they outlive
    the container even if the session never reaches live_card.py done. Detached: the hook returns at once.
    Skipped in tests (NQOS_COSTLOG or NQOS_JOBCARDS set) and when NQOS_NO_PUSH is set."""
    if any(os.environ.get(k) for k in ("NQOS_COSTLOG", "NQOS_JOBCARDS", "NQOS_NO_PUSH")):
        return
    import subprocess
    try:
        subprocess.Popen([sys.executable, os.path.join(BRAIN, "costlog_push.py")], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def main(pending_only=False):
    ev = json.load(sys.stdin)
    sys.path.insert(0, BRAIN)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    event = ev.get("hook_event_name", "")
    session = ev.get("session_id", "")
    handback = event == "PostToolUse" and ev.get("tool_name") == "SubagentHandback"
    if event == "SubagentStop" or handback:
        if ev.get("agent_type") != "nq-check":
            return
        if handback:                                   # the report is the handback message, not the last text
            ev = {**ev, "hook_event_name": "SubagentStop",
                  "last_assistant_message": (ev.get("tool_input") or {}).get("message", "")}
        card = None
        try:
            import job_card
            card = job_card.from_event(ev)             # built first, so the FAIL rows get the card's job and format
        except Exception:
            pass
        if card and os.path.isfile(os.path.join(job_card.CARDS, card["id"] + ".json")):
            return                                     # the handback and SubagentStop both fire: capture once
        try:
            import quality_fails
            text = quality_fails.report(ev)
            if not text and job_card.with_paths(ev).get("agent_transcript_path"):
                text = job_card.agent_report(job_card.with_paths(ev)["agent_transcript_path"])
            if text:
                from post_mortem import log_fails
                log_fails(text, session, job=(card or {}).get("job", ""), agent=ev.get("agent_id", ""),
                          fmt=(card or {}).get("format", ""))
        except Exception:                              # the FAIL log must never stop the job card
            pass
        if not card:
            push_later()                               # a FAIL row may still be new
            return
        job_card.save(card)
        push_later()
        note = note_for(card)
        if note:
            p = pending_path(session)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write(note)
        return
    if event != "PostToolUse":
        return
    inp = ev.get("tool_input") or {}
    if pending_only and ev.get("tool_name") in ("Agent", "Task"):
        return                                         # the Agent|Task entry handles these, so a note shows once
    if ev.get("tool_name") in ("Agent", "Task") and inp.get("subagent_type") == "nq-check":
        import job_card
        card = job_card.from_event(ev)
        if card:
            job_card.save(card)
            push_later()
            note = note_for(card)
            p = pending_path(session)
            if os.path.isfile(p):
                os.remove(p)
            if note:
                say(event, note)
            return
    note = take_pending(session)
    if note.strip():
        say(event, note)


if __name__ == "__main__":
    try:
        main("--pending-only" in sys.argv)
    except Exception:                                  # a broken note must never stop the lead's work
        pass
    sys.exit(0)
