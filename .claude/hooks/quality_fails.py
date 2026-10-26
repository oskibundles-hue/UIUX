#!/usr/bin/env python3
"""SubagentStop hook: log each nq-check FAIL row to the quality-fail log, so the weekly review sees it.

Gap 1 of the reel-harness comparison (2026-10-26): post_mortem.py review grouped repeated cost drains but
never saw nq-check's verdicts, so a quality problem that kept coming back (the same caption issue four
times in a week) went unseen. Registered in .claude/settings.json on SubagentStop with matcher nq-check;
the docs say last_assistant_message holds the subagent's final text, and unlike PostToolUse on Agent it
also fires for background agents. A subagent that reports through SubagentHandback puts the report in
that tool's tool_input.message instead, so PostToolUse on SubagentHandback runs this too.

The rows go to costlog/qualityfails.jsonl next to the cost log (private brain, or the git-ignored work/
fallback); see post_mortem.py. Never blocks or prints: a hook failure must not keep nq-check running.
Stdlib only, no model call. Test: python3 .claude/hooks/test_quality_fails.py
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brain"))


def report(event):
    """The nq-check report in this hook input, or "" when the input isn't one."""
    if event.get("agent_type") != "nq-check":
        return ""
    if event.get("hook_event_name") == "PostToolUse":
        return (event.get("tool_input") or {}).get("message", "") if event.get("tool_name") == "SubagentHandback" else ""
    return event.get("last_assistant_message") or ""


def main():
    try:
        event = json.loads(sys.stdin.read() or "{}")
        text = report(event)
        if text:
            from post_mortem import log_fails
            log_fails(text, event.get("session_id", ""), agent=event.get("agent_id", ""))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
