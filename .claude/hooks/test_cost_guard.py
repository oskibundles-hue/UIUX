#!/usr/bin/env python3
"""Check cost_guard.py against calls with known answers (no model, under 2 s).

usage: python3 .claude/hooks/test_cost_guard.py
Builds throwaway transcripts in the temp folder: small, past 150k, past 300k, past 500k, compacted, three agents.
"""
import json, os, subprocess, sys, tempfile

GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cost_guard.py")
TMP = tempfile.mkdtemp(prefix="cost-guard-test-")
ENV = dict(os.environ, NQOS_GUARD_STATE=os.path.join(TMP, "state"))


def transcript(name, ctx, extra=()):
    path = os.path.join(TMP, name + ".jsonl")
    with open(path, "w") as fh:
        for rec in extra:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
        fh.write(json.dumps({"type": "assistant", "message": {"id": "m1", "usage": {
            "input_tokens": 2, "cache_read_input_tokens": ctx - 1002, "cache_creation_input_tokens": 1000,
            "output_tokens": 50}}}, separators=(",", ":")) + "\n")
    return path


def agent_use(tid=None):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid or os.urandom(4).hex(),
                                                          "name": "Agent", "input": {}}]}}


SMALL = transcript("small", 40_000)
MID = transcript("mid", 180_000)
BIG = transcript("big", 320_000)
HUGE = transcript("huge", 640_000)
COMPACTED = transcript("compacted", 90_000, [{"type": "system", "subtype": "compact_boundary"}])
def read_use(fp, tid="toolu_old", at=None, name="Read", **inp):
    rec = {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid, "name": name,
                                                         "input": dict({"file_path": fp} if fp else {}, **inp)}]}}
    return dict(rec, timestamp=at) if at else rec


W = os.path.join(TMP, "w")
os.makedirs(os.path.join(W, "look"))
for name in ("look/96.jpg", "look/99.jpg", "look/100.jpg", "story.html", "notes.md", "edited.py", "old.md"):
    open(os.path.join(W, name), "w").write("x")
    os.utime(os.path.join(W, name), (1767225600, 1767225600))         # 2026-01-01, before every read below
os.utime(os.path.join(W, "edited.py"))                                  # changed now, after its read
READ_AT = "2026-06-01T00:00:00Z"
FRAMES = transcript("frames", 50_000, [read_use(f"{W}/look/96.jpg"), read_use(f"{W}/look/99.jpg", "toolu_now")])
READS = transcript("reads", 50_000, [
    read_use(f"{W}/old.md", "t0", READ_AT), {"type": "system", "subtype": "compact_boundary"},
    read_use(f"{W}/notes.md", "t1", READ_AT), read_use(f"{W}/edited.py", "t2", READ_AT),
    read_use(f"{W}/story.html", "t3", READ_AT, offset=10, limit=20),
    read_use(None, "t4", READ_AT, "WebFetch", url="https://example.com/a", prompt="list the prices")])
AGENTS3 = transcript("agents3", 50_000, [agent_use(), agent_use(), agent_use()])
LISTED = transcript("listed", 50_000, [{"type": "attachment", "tools": [{"name": "Agent"}] * 4},
                                       agent_use("same"), agent_use("same")])   # tool list + a re-written record


def run(tool, inp, path=SMALL, session="s1", **extra):
    hook = dict({"tool_name": tool, "tool_input": inp, "transcript_path": path, "session_id": session}, **extra)
    p = subprocess.run([sys.executable, GUARD], capture_output=True, text=True, input=json.dumps(hook), env=ENV)
    if p.returncode:
        return "crash: " + p.stderr.strip()[-200:]
    if not p.stdout.strip():
        return ""
    out = json.loads(p.stdout)
    if out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny":
        return "DENY " + out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "permissionDecision" not in out.get("hookSpecificOutput", {}), "the guard only ever denies"
    assert out["systemMessage"] == out["hookSpecificOutput"]["additionalContext"]
    return out["systemMessage"]


CASES = [
    # (label, call, words the warning must contain; "" means no warning)
    ("plain command, small context", lambda: run("Bash", {"command": "ls -la"}), ""),
    ("short sleep", lambda: run("Bash", {"command": "sleep 5 && ls"}), ""),
    ("Oct 5 self-matching pgrep loop",
     lambda: run("Bash", {"command": 'until ! pgrep -f "vlog.py ingest"; do sleep 30; done'}), "DENY Cost guard: blocked. This wait loop uses `pgrep -f`"),
    ("Oct 5 loop is blocked in the background too (it never ends)",
     lambda: run("Bash", {"command": 'until ! pgrep -f "vlog.py"; do sleep 30; done', "run_in_background": True}),
     "DENY Cost guard: blocked. This wait loop uses `pgrep -f`"),
    ("bracket-trick pgrep loop with no bound is blocked as unbounded, not self-matching",
     lambda: run("Bash", {"command": "while pgrep -f '[v]log.py'; do sleep 20; done"}), "DENY Cost guard: blocked. This wait loop has no hard bound"),
    ("bracket-trick pgrep loop with a timeout only warns",
     lambda: run("Bash", {"command": "timeout 600 bash -c \"while pgrep -f '[v]log.py'; do sleep 20; done\""}), "wait/poll loop"),
    ("unbounded loop sent to the background only warns",
     lambda: run("Bash", {"command": "while kill -0 $pid; do sleep 20; done", "run_in_background": True}), "wait/poll loop"),
    ("bounded loop on no PID or marker only warns",
     lambda: run("Bash", {"command": "timeout 300 bash -c 'while true; do sleep 5; done'"}), "wait/poll loop"),
    ("long sleep", lambda: run("Bash", {"command": "sleep 600"}), "wait/poll loop"),
    ("watch -n", lambda: run("Bash", {"command": "watch -n 10 ls"}), "wait/poll loop"),
    ("loop text inside a heredoc is file content, not a wait",
     lambda: run("Bash", {"command": "cat > t.py <<'E'\nwhile True: sleep(5)\nuntil pgrep -f x; do sleep 9; done\nE\npython3 t.py"}), ""),
    ("a real loop after a heredoc still warns",
     lambda: run("Bash", {"command": "cat > t <<E\nhi\nE\nwhile true; do sleep 30; done"}), "DENY"),
    ("loop without sleep is fine", lambda: run("Bash", {"command": "for f in *.mp4; do echo $f; done"}), ""),
    ("send_later past 150k warns", lambda: run("mcp__claude-code-remote__send_later",
                                               {"delay_minutes": 50, "message": "x"}, MID), "wakes this session at 180k"),
    ("send_later past 150k warns every time", lambda: run("mcp__claude-code-remote__send_later",
                                                          {"delay_minutes": 50, "message": "x"}, MID), "wakes this session"),
    ("send_later in a small session is fine", lambda: run("mcp__claude-code-remote__send_later",
                                                          {"delay_minutes": 50, "message": "x"}), ""),
    ("ScheduleWakeup past 150k warns", lambda: run("ScheduleWakeup", {"delaySeconds": 1200, "prompt": "x"}, MID),
     "wakes this session"),
    ("stopping a wakeup loop is fine", lambda: run("ScheduleWakeup", {"stop": True}, MID), ""),
    ("create_trigger into this session warns", lambda: run("mcp__claude-code-remote__create_trigger",
                                                           {"name": "n", "prompt": "p"}, MID), "wakes this session"),
    ("create_trigger with a fresh session is fine", lambda: run("mcp__claude-code-remote__create_trigger",
     {"name": "n", "prompt": "p", "create_new_session_on_fire": True}, MID), ""),
    ("create_trigger into another session is fine", lambda: run("mcp__claude-code-remote__create_trigger",
     {"name": "n", "prompt": "p", "persistent_session_id": "session_small"}, MID), ""),
    ("a check-in set inside an agent is skipped", lambda: run("mcp__claude-code-remote__send_later",
     {"delay_minutes": 5, "message": "x"}, MID, agent_id="a1"), ""),
    ("past 300k warns", lambda: run("Read", {"file_path": "x"}, BIG, "s-big"), "passed 300k"),
    ("past 300k warns once", lambda: run("Read", {"file_path": "x"}, BIG, "s-big"), ""),
    ("past 500k says hand off", lambda: run("Read", {"file_path": "x"}, HUGE, "s-huge"), "Hand off"),
    ("past 500k once", lambda: run("Read", {"file_path": "x"}, HUGE, "s-huge"), ""),
    ("compacted session", lambda: run("Grep", {"pattern": "x"}, COMPACTED, "s-c"), "compacted"),
    ("first agents are fine", lambda: run("Agent", {"prompt": "x"}), ""),
    ("tool lists and repeated records aren't agents", lambda: run("Agent", {"prompt": "x"}, LISTED, "s-l"), ""),
    ("fourth agent warns", lambda: run("Agent", {"prompt": "x"}, AGENTS3, "s-a"), "agent number 4"),
    ("workflow always warns", lambda: run("Workflow", {"script": "x"}), "ultracode"),
    ("inside an agent: no lead context check", lambda: run("Read", {}, HUGE, "s-sub", agent_id="a1"), ""),
    ("inside an agent: an unbounded loop is still blocked",
     lambda: run("Bash", {"command": "while true; do sleep 5; done"}, HUGE, "s-sub", agent_id="a1"), "DENY"),
    ("inside an agent: a long sleep still warns",
     lambda: run("Bash", {"command": "sleep 300"}, HUGE, "s-sub", agent_id="a1"), "wait/poll"),
    ("second read of the same frame is denied", lambda: run("Read", {"file_path": f"{W}/look/96.jpg"}, FRAMES, "s-f",
                                                              tool_use_id="toolu_new"), "DENY"),
    ("the current call's own record doesn't count", lambda: run("Read", {"file_path": f"{W}/look/99.jpg"}, FRAMES, "s-f",
                                                                tool_use_id="toolu_now"), ""),
    ("first read of a new frame is fine", lambda: run("Read", {"file_path": f"{W}/look/100.jpg"}, FRAMES, "s-f"), ""),
    ("first read of a source file is fine", lambda: run("Read", {"file_path": f"{W}/story.html"}, FRAMES, "s-f"), ""),
    ("agents may re-read frames", lambda: run("Read", {"file_path": f"{W}/look/96.jpg"}, FRAMES, "s-f", agent_id="a1"), ""),
    ("second read of an unchanged file is denied", lambda: run("Read", {"file_path": f"{W}/notes.md"}, READS, "s-r"),
     "DENY Cost guard: blocked. This file was already read"),
    ("the reads fixture is compacted, so it warns once first", lambda: run("Grep", {"pattern": "x"}, READS, "s-r"),
     "compacted"),
    ("a file edited since its last read may be read again",
     lambda: run("Read", {"file_path": f"{W}/edited.py"}, READS, "s-r"), ""),
    ("a read from before the compaction doesn't count", lambda: run("Read", {"file_path": f"{W}/old.md"}, READS, "s-r"), ""),
    ("the same range again is denied",
     lambda: run("Read", {"file_path": f"{W}/story.html", "offset": 10, "limit": 20}, READS, "s-r"), "DENY"),
    ("a different range of the same file is fine",
     lambda: run("Read", {"file_path": f"{W}/story.html", "offset": 30, "limit": 20}, READS, "s-r"), ""),
    ("a file that doesn't exist isn't blocked (the Read fails on its own)",
     lambda: run("Read", {"file_path": f"{W}/gone.md"}, READS, "s-r"), ""),
    ("agents may re-read files", lambda: run("Read", {"file_path": f"{W}/notes.md"}, READS, "s-r", agent_id="a1"), ""),
    ("the same fetch twice is denied",
     lambda: run("WebFetch", {"url": "https://example.com/a", "prompt": "list the prices"}, READS, "s-r"),
     "DENY Cost guard: blocked. This URL was already fetched"),
    ("the same URL with a new prompt is fine",
     lambda: run("WebFetch", {"url": "https://example.com/a", "prompt": "who wrote it"}, READS, "s-r"), ""),
    ("missing transcript fails open", lambda: run("Read", {}, "/nonexistent.jsonl"), ""),
]

TIMED = [   # the approved waits: no warning
    ("timed wait on a PID", "timeout 900 bash -c 'while kill -0 4242; do sleep 10; done'"),
    ("timed wait on a marker file", "timeout -k 5 1800 bash -c 'until [ -f out/DONE ]; do sleep 15; done'"),
    ("SECONDS-bounded wait on a marker", "end=$((SECONDS+3600)); while [ ! -f render.done ] && [ $SECONDS -lt $end ]; do sleep 60; done"),
    ("SECONDS-bounded wait on a PID", "while kill -0 $pid 2>/dev/null && (( SECONDS < 1200 )); do sleep 20; done"),
]
STILL = [   # still flagged: blocked (DENY) or warned
    ("PID wait with no bound", "while kill -0 $pid; do sleep 20; done", "DENY Cost guard: blocked. This wait loop has no hard bound"),
    ("pgrep -f loop even with a timeout", "timeout 600 bash -c 'until ! pgrep -f render; do sleep 5; done'",
     "DENY Cost guard: blocked. This wait loop uses `pgrep -f`"),
    ("bare long sleep check", "sleep 120 && tail -3 render.log", "wait/poll loop"),
]
CASES += [(label, (lambda c=cmd: run("Bash", {"command": c})), "") for label, cmd in TIMED]
CASES += [(label, (lambda c=cmd: run("Bash", {"command": c})), want) for label, cmd, want in STILL]


def agrees_with_meter():
    """The guard and the meter use one rule: the guard is quiet exactly where the meter doesn't flag a wait."""
    brain = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brain")
    if not os.path.isfile(os.path.join(brain, "cost_meter.py")):
        return True                       # installed copy without the meter beside it: nothing to compare
    sys.path[:0] = [brain, os.path.dirname(GUARD)]
    import cost_meter, cost_guard
    cmds = [c for _, c in TIMED] + [c for _, c, _ in STILL] + ['until ! pgrep -f "vlog.py"; do sleep 30; done']
    return all((cost_guard.poll_warning(c) is None) == (not cost_meter.is_poll(c)) for c in cmds)


def main():
    bad = 0
    for label, call, want in CASES:
        got = call()
        ok = (got == "") if want == "" else (want in got and not got.startswith("crash"))
        bad += not ok
        print(("ok  " if ok else "FAIL") + f"  {label}" + ("" if ok else f"\n      want {want!r}\n      got  {got!r}"))
    p = subprocess.run([sys.executable, GUARD], input="not json", capture_output=True, text=True)
    ok = p.returncode == 0 and not p.stdout.strip()
    bad += not ok
    print(("ok  " if ok else "FAIL") + "  bad payload fails open")
    ok = agrees_with_meter()
    bad += not ok
    print(("ok  " if ok else "FAIL") + "  guard and meter agree on which waits are fine")
    print(f"\n{len(CASES) + 2 - bad}/{len(CASES) + 2} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
