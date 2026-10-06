#!/usr/bin/env python3
"""PreToolUse cost guard: warns, never blocks. The token-side partner of regret_gate.py.

Warns (to Omarie as a system message, and to Claude as added context) when:
  - the conversation passes 300k tokens of context (again at 500k: hand off now);
  - a compaction has happened (a compacted session keeps re-reading a big summary: hand off);
  - a Bash call is a wait/poll loop, and harder when it is `pgrep -f` in a loop, which matches its
    own command line and never ends (the Oct 5 vlog.py loop ran 28 min after the job finished);
  - a fourth agent is about to start in one session, or any Workflow (ultracode) call.
Context and compaction warnings fire once per session and level; loop and agent warnings every time.
It never prints a permission decision, so the regret gate's ask/deny stays in charge.
Reads the tail of the transcript only; about 20 ms. Fails open: any error means no warning.
Thresholds: NQOS_GUARD_CTX (300000), NQOS_GUARD_HANDOFF (500000), NQOS_GUARD_AGENTS (3).
Tests: python3 .claude/hooks/test_cost_guard.py
"""
import json, mmap, os, re, sys, tempfile

CTX = int(os.environ.get("NQOS_GUARD_CTX", 300_000))
HANDOFF = int(os.environ.get("NQOS_GUARD_HANDOFF", 500_000))
AGENTS = int(os.environ.get("NQOS_GUARD_AGENTS", 3))
STATE = os.environ.get("NQOS_GUARD_STATE") or os.path.join(tempfile.gettempdir(), "nqos-cost-guard")

LOOP = re.compile(r"\b(while|until)\b.*\b(sleep|pgrep|pidof|ps\b)", re.S)
LONG_SLEEP = re.compile(r"\bsleep\s+(\d+)")
WATCH = re.compile(r"\bwatch\s+(-n|--interval)")
PGREP_SELF = re.compile(r"pgrep\s+-\w*f\w*\s+['\"]?(?![\['\"])")   # pgrep -f "x" without the [x] trick
HANDOFF_HOW = ("Hand off: write a short handoff (goal, state, next step, file paths) and continue in a fresh "
               "session. Every call here re-reads the whole conversation.")


def last_context(path):
    """Context of the newest assistant call: input + cache-read + cache-write tokens."""
    with open(path, "rb") as fh:
        fh.seek(max(0, os.path.getsize(path) - 600_000))
        tail = fh.read().decode("utf-8", "replace").splitlines()
    for line in reversed(tail):
        if '"usage"' not in line:
            continue
        try:
            u = json.loads(line)["message"]["usage"]
        except (ValueError, KeyError, TypeError):
            continue
        return sum(u.get(k, 0) or 0 for k in ("input_tokens", "cache_read_input_tokens",
                                              "cache_creation_input_tokens"))
    return 0


def count(path, needle):
    if not os.path.getsize(path):
        return 0
    with open(path, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        n, i = 0, mm.find(needle)
        while i != -1:
            n, i = n + 1, mm.find(needle, i + 1)
        return n


def once(session, key):
    """True the first time this session hits key."""
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, re.sub(r"[^\w.-]", "_", session or "none") + ".json")
    try:
        seen = set(json.load(open(path)))
    except (OSError, ValueError):
        seen = set()
    if key in seen:
        return False
    seen.add(key)
    json.dump(sorted(seen), open(path, "w"))
    return True


def poll_warning(cmd):
    if PGREP_SELF.search(cmd) and LOOP.search(cmd):
        return ("This wait loop uses `pgrep -f`, which also matches the loop's own command line, so it may never "
                "end. Wait on the PID (`wait $pid`), a marker file the job writes when done, or use the "
                "`pgrep -f '[v]log.py'` bracket trick, and give it a hard timeout.")
    sleeps = [int(s) for s in LONG_SLEEP.findall(cmd)]
    if LOOP.search(cmd) or WATCH.search(cmd) or any(s >= 60 for s in sleeps):
        return ("This is a wait/poll loop. Every wake re-reads the conversation. Prefer a background job that "
                "re-invokes you when it exits (run_in_background), a marker file, or a hard timeout.")
    return None


def warnings(hook):
    tool, inp = hook.get("tool_name", ""), hook.get("tool_input") or {}
    session, path = hook.get("session_id", ""), hook.get("transcript_path", "")
    out = []
    if tool == "Bash":
        w = poll_warning(inp.get("command", ""))
        if w:
            out.append(w)
    if tool == "Workflow":
        out.append("A Workflow fans out many agents (the ultracode drain). Standing rule: only when the job "
                   "can't be done well without one, and say why first.")
    if hook.get("agent_id") or not path or not os.path.isfile(path):
        return out                     # inside an agent the transcript is the lead's; skip lead-only checks
    if tool in ("Agent", "Task"):
        n = count(path, b'"name":"Agent"') + count(path, b'"name":"Task"')
        if n >= AGENTS:
            out.append(f"This would be agent number {n + 1} in this session. Each costs about 55k tokens to "
                       "start. Could the lead do this in a few commands, or one agent take it as a list?")
    ctx = last_context(path)
    if ctx >= HANDOFF:
        if once(session, "ctx-handoff"):
            once(session, "ctx")           # the 300k notice is moot once this one has fired
            out.append(f"Context is {ctx // 1000}k tokens. {HANDOFF_HOW}")
    elif ctx >= CTX and once(session, "ctx"):
        out.append(f"Context passed {CTX // 1000}k ({ctx // 1000}k now). Finish this step, then plan a "
                   "handoff to a fresh session.")
    if count(path, b'"compact_boundary"') and once(session, "compacted"):
        out.append(f"This session has been compacted. {HANDOFF_HOW}")
    return out


def main():
    try:
        hook = json.load(sys.stdin)
        found = warnings(hook)
    except Exception:
        return
    if found:
        msg = "Cost guard: " + " | ".join(found)
        print(json.dumps({"systemMessage": msg,
                          "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    main()
