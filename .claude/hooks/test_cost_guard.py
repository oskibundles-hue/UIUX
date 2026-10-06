#!/usr/bin/env python3
"""Check cost_guard.py against calls with known answers (no model, under 2 s).

usage: python3 .claude/hooks/test_cost_guard.py
Builds throwaway transcripts in the temp folder: small, past 300k, past 500k, compacted, three agents.
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
BIG = transcript("big", 320_000)
HUGE = transcript("huge", 640_000)
COMPACTED = transcript("compacted", 90_000, [{"type": "system", "subtype": "compact_boundary"}])
def read_use(fp, tid="toolu_old"):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid, "name": "Read",
                                                          "input": {"file_path": fp}}]}}


FRAMES = transcript("frames", 50_000, [read_use("/w/look/96.jpg"), read_use("/w/look/99.jpg", "toolu_now")])
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
    assert "permissionDecision" not in out.get("hookSpecificOutput", {}), "guard decides only on repeat frames"
    assert out["systemMessage"] == out["hookSpecificOutput"]["additionalContext"]
    return out["systemMessage"]


CASES = [
    # (label, call, words the warning must contain; "" means no warning)
    ("plain command, small context", lambda: run("Bash", {"command": "ls -la"}), ""),
    ("short sleep", lambda: run("Bash", {"command": "sleep 5 && ls"}), ""),
    ("Oct 5 self-matching pgrep loop",
     lambda: run("Bash", {"command": 'until ! pgrep -f "vlog.py ingest"; do sleep 30; done'}), "matches the loop's own"),
    ("pgrep loop with bracket trick is still a poll loop, not self-matching",
     lambda: run("Bash", {"command": "while pgrep -f '[v]log.py'; do sleep 20; done"}), "wait/poll loop"),
    ("long sleep", lambda: run("Bash", {"command": "sleep 600"}), "wait/poll loop"),
    ("watch -n", lambda: run("Bash", {"command": "watch -n 10 ls"}), "wait/poll loop"),
    ("loop text inside a heredoc is file content, not a wait",
     lambda: run("Bash", {"command": "cat > t.py <<'E'\nwhile True: sleep(5)\nuntil pgrep -f x; do sleep 9; done\nE\npython3 t.py"}), ""),
    ("a real loop after a heredoc still warns",
     lambda: run("Bash", {"command": "cat > t <<E\nhi\nE\nwhile true; do sleep 30; done"}), "wait/poll loop"),
    ("loop without sleep is fine", lambda: run("Bash", {"command": "for f in *.mp4; do echo $f; done"}), ""),
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
    ("inside an agent: poll still warns",
     lambda: run("Bash", {"command": "while true; do sleep 5; done"}, HUGE, "s-sub", agent_id="a1"), "wait/poll"),
    ("second read of the same frame is denied", lambda: run("Read", {"file_path": "/w/look/96.jpg"}, FRAMES, "s-f",
                                                              tool_use_id="toolu_new"), "DENY"),
    ("the current call's own record doesn't count", lambda: run("Read", {"file_path": "/w/look/99.jpg"}, FRAMES, "s-f",
                                                                tool_use_id="toolu_now"), ""),
    ("first read of a new frame is fine", lambda: run("Read", {"file_path": "/w/look/100.jpg"}, FRAMES, "s-f"), ""),
    ("re-reading a source file is fine", lambda: run("Read", {"file_path": "/w/story.html"}, FRAMES, "s-f"), ""),
    ("agents may re-read frames", lambda: run("Read", {"file_path": "/w/look/96.jpg"}, FRAMES, "s-f", agent_id="a1"), ""),
    ("missing transcript fails open", lambda: run("Read", {}, "/nonexistent.jsonl"), ""),
]


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
    print(f"\n{len(CASES) + 1 - bad}/{len(CASES) + 1} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
