#!/usr/bin/env python3
"""Check the learning loop on jobs shaped like real ones (2026-10-27): non-video formats, FAIL rows with a job and a
format, the "unknown" fallback, and the narrowed PostToolUse matcher that still shows the FAIL line.

usage: python3 .claude/hooks/test_loop_real_jobs.py
Made-up jobs only; cards, FAIL rows and notes go to a temp folder. No network, about 2 s.
"""
import json, os, re, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK = os.path.join(HERE, "job_diff_hook.py")
FAST = os.path.join(HERE, "jobdiff_pending.sh")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "brain", "tests"))
from jobdiff_fixtures import _rec, _use

TMP = tempfile.mkdtemp(prefix="loop-real-jobs-test-")
WORK = os.path.join(TMP, "work")
FAILLOG = os.path.join(TMP, "costlog", "qualityfails.jsonl")
ENV = dict(os.environ, NQOS_JOBCARDS=os.path.join(TMP, "cards"), NQOS_WORK=WORK,
           NQOS_COSTLOG=os.path.join(TMP, "costlog", "costlog.jsonl"), NQOS_FAILLOG=FAILLOG)
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def lead_job(name, brief, report, session="sess"):
    """A lead transcript: one nq-build brief, then nq-check. Returns the SubagentStop and PostToolUse events."""
    lead = os.path.join(TMP, name + ".jsonl")
    sub = os.path.join(TMP, name, "subagents")
    os.makedirs(sub, exist_ok=True)
    with open(lead, "w") as fh:
        for r in (_use(f"toolu_{name}_b", "Agent", {"subagent_type": "nq-build", "description": "build", "prompt": brief}),
                  _use(f"toolu_{name}_c", "Agent", {"subagent_type": "nq-check", "description": "check",
                                                    "prompt": "Check the delivered file."})):
            fh.write(json.dumps(r) + "\n")
    with open(os.path.join(sub, f"agent-c{name}.jsonl"), "w") as fh:
        fh.write(json.dumps(_rec("assistant", [{"type": "text", "text": report}])) + "\n")
    json.dump({"agentType": "nq-check", "toolUseId": f"toolu_{name}_c"}, open(os.path.join(sub, f"agent-c{name}.meta.json"), "w"))
    stop = {"hook_event_name": "SubagentStop", "session_id": session, "transcript_path": lead, "agent_id": f"c{name}",
            "agent_type": "nq-check", "last_assistant_message": report, "cwd": TMP,
            "agent_transcript_path": os.path.join(sub, f"agent-c{name}.jsonl")}
    post = {"hook_event_name": "PostToolUse", "session_id": session, "transcript_path": lead, "tool_name": "Agent",
            "tool_use_id": f"toolu_{name}_c", "tool_input": {"subagent_type": "nq-check", "prompt": "check"},
            "tool_response": {"status": "completed", "agentId": f"c{name}", "content": [{"type": "text", "text": report}]}}
    return stop, post


def run(ev, cmd=None):
    p = subprocess.run(cmd or [sys.executable, HOOK], input=json.dumps(ev), capture_output=True, text=True, env=ENV)
    if p.returncode:
        return "crash: " + p.stderr[-200:]
    out = p.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def fails(session):
    return [r for r in (json.loads(l) for l in open(FAILLOG))] if os.path.isfile(FAILLOG) else []


def cards():
    d = os.path.join(TMP, "cards")
    out = [json.load(open(os.path.join(d, f))) for f in os.listdir(d) if f not in ("refs.json", "replayset.json")] \
        if os.path.isdir(d) else []
    return {c["session"]: c for c in out}


TABLE = "| check | verdict | evidence |\n|---|---|---|\n| Layout | {v} | {e} |\n| Copy | PASS | plain |\n"

# 1. a page job whose report never says "page": the row takes the card's format and job from the brief
stop, _ = lead_job("pg", "Build a one-screen index page in the iPhone index layout for the made-up Demo Co links.",
                   "Checked index.html.\n" + TABLE.format(v="FAIL", e="tab bar overlaps the list"), session="s-page")
run(stop)
rows = [r for r in fails("") if r["session"] == "s-page"]
check("non-video job: the FAIL row has a format", rows and rows[0]["format"] in ("page", "index"), rows)
check("non-video job: the FAIL row has the job from the brief", rows and rows[0]["job"].startswith("Build a one-screen"), rows)
check("non-video job: the card has the same format", cards().get("s-page", {}).get("format") == rows[0]["format"] if rows else False)

# 2. an HTML artifact job: the alias makes it a page
stop, _ = lead_job("art", "Make the made-up Demo Co sign-up artifact as HTML.",
                   "Checked it.\n" + TABLE.format(v="FAIL", e="button off screen"), session="s-art")
run(stop)
rows = [r for r in fails("") if r["session"] == "s-art"]
check("artifact / HTML job: format page", rows and rows[0]["format"] == "page", rows)

# 3. nothing names a format or job: the live_card title, and "unknown", never ""
os.makedirs(os.path.join(WORK, "livecard"), exist_ok=True)
json.dump({"title": "Made-up title from the Working-now card", "at": "2026-10-27T00:00:00Z"},
          open(os.path.join(WORK, "livecard", "s-none.json"), "w"))
stop, _ = lead_job("none", "", "Looked at it.\n" + TABLE.format(v="FAIL", e="x"), session="s-none")
run(stop)
rows = [r for r in fails("") if r["session"] == "s-none"]
check("nothing detected: format is 'unknown', not empty", rows and rows[0]["format"] == "unknown", rows)
check("nothing detected: the brief is empty, so the job is the Working-now title",
      rows and rows[0]["job"] == "Made-up title from the Working-now card", rows)
c = cards().get("s-none", {})
check("nothing detected: the card says unknown too, never an empty string", c.get("format") == "unknown" and c.get("job"), c)
stop, _ = lead_job("none2", "", "Looked at it.\n" + TABLE.format(v="FAIL", e="y"), session="s-none2")
run(stop)
rows = [r for r in fails("") if r["session"] == "s-none2"]
check("no title either: job is 'unknown'", rows and rows[0]["job"] == "unknown" and rows[0]["format"] == "unknown", rows)

# a re-check with no build brief in scope: the Working-now title, not nq-check's own instructions
json.dump({"title": "Made-up re-check job"}, open(os.path.join(WORK, "livecard", "s-re.json"), "w"))
stop, _ = lead_job("re", "", "Checked.\n" + TABLE.format(v="FAIL", e="x"), session="s-re")
run(stop)
check("re-check with no build brief: the job is the Working-now title", cards().get("s-re", {}).get("job") == "Made-up re-check job",
      cards().get("s-re"))

# 4. "unknown" is never a format to compare against or group by
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "brain"))
os.environ.update(NQOS_JOBCARDS=ENV["NQOS_JOBCARDS"], NQOS_WORK=WORK, NQOS_COSTLOG=ENV["NQOS_COSTLOG"], NQOS_FAILLOG=FAILLOG)
import job_diff, post_mortem
ref, why = job_diff.reference({"id": "x", "format": "unknown"})
check("job_diff: an unknown format finds no reference and says why", ref is None and "no format" in why, why)
groups = post_mortem.repeated_fails([{"key": "layout", "check": "Layout", "job": "unknown", "session": s, "format": "unknown"}
                                     for s in ("a", "b")])
check("review: 'unknown' jobs in different sessions still count as different jobs", groups and groups[0][1] == 2
      and groups[0][4] == [], groups)
check("review: an unknown format falls back to the job's words", "page" in post_mortem.by_format(
      [{"format": "unknown", "job": "made-up landing page", "usd": 1, "verdict": "FAIL"}]))

# 5. the matcher: Python on Agent|Task only, a shell fast path on every other call
s = json.load(open(os.path.join(ROOT, ".claude", "settings.json")))
post = {g["matcher"]: [h["command"] for h in g["hooks"]] for g in s["hooks"]["PostToolUse"]}
check("settings: job_diff_hook.py runs on Agent|Task, not on every tool",
      any("job_diff_hook.py" in c for c in post.get("Agent|Task", [])) and
      not any("job_diff_hook.py" in c for c in post.get("*", [])), post)
check("settings: the every-tool entry is the shell fast path", any("jobdiff_pending.sh" in c for c in post.get("*", [])), post)
check("matcher Agent|Task matches the Agent and Task tools only",
      all(re.fullmatch("Agent|Task", t) for t in ("Agent", "Task")) and not re.fullmatch("Agent|Task", "Bash"))

# a foreground nq-check FAIL with a passed job of the same format on file: the FAIL line shows on the Agent call
good, _ = lead_job("good", "Build a one-screen index page for the made-up Demo Co.",
                   "Checked index.html.\n" + TABLE.format(v="PASS", e="fine"), session="s-good")
run(good)
stop, post_ev = lead_job("bad", "Build a one-screen index page for the made-up Demo Co. Playbook: research.",
                         "Checked index.html.\n" + TABLE.format(v="FAIL", e="overlap"), session="s-bad")
run(stop)
note = run(post_ev)
check("foreground FAIL: the Agent|Task entry shows the FAIL line", "nq-check FAILed" in note and "job_diff.py" in note, note)

# a background FAIL leaves a note; the fast path shows it on the next ordinary call, once
SH = ["sh", FAST]
stop, _ = lead_job("bg", "Build a one-screen index page for the made-up Demo Co. Playbook: research.",
                   "Checked index.html.\n" + TABLE.format(v="FAIL", e="overlap"), session="s-bg")
run(stop)
pend = os.path.join(WORK, "jobdiff-pending", "s-bg.txt")
check("background FAIL: note pending", os.path.isfile(pend))
agent_call = {"hook_event_name": "PostToolUse", "session_id": "s-bg", "tool_name": "Agent",
              "tool_input": {"subagent_type": "nq-fix"}}
check("fast path leaves Agent calls to the Agent|Task entry (no double note)", run(agent_call, SH) == "" and os.path.isfile(pend))
note = run({"hook_event_name": "PostToolUse", "session_id": "s-bg", "tool_name": "Read", "tool_input": {}}, SH)
check("fast path: the next Read shows the FAIL line", "nq-check FAILed" in note, note)
check("fast path: shown once", not os.path.exists(pend) and
      run({"hook_event_name": "PostToolUse", "session_id": "s-bg", "tool_name": "Bash", "tool_input": {}}, SH) == "")

# a handback agent (the real shape, 2026-10-27): no final text, the report is the SubagentHandback message
def handback_job(name, brief, report, session):
    stop, _ = lead_job(name, brief, "", session=session)
    sub = os.path.dirname(stop["agent_transcript_path"])
    with open(stop["agent_transcript_path"], "w") as fh:
        fh.write(json.dumps(_rec("assistant", [{"type": "tool_use", "id": f"toolu_{name}_h", "name": "SubagentHandback",
                                                "input": {"message": report}}])) + "\n")
    hb = {"hook_event_name": "PostToolUse", "session_id": session, "tool_name": "SubagentHandback",
          "transcript_path": stop["agent_transcript_path"], "agent_id": stop["agent_id"], "agent_type": "nq-check",
          "tool_input": {"message": report}, "tool_response": {}}
    stop.pop("agent_transcript_path")             # the real SubagentStop may not name it; the hook works it out
    return hb, {**stop, "last_assistant_message": ""}

hb, stop = handback_job("hb", "Build a one-screen index page for the made-up Demo Co tools.",
                        "Checked index.html.\n" + TABLE.format(v="FAIL", e="one tab sits left"), "s-hb")
run(hb)
rows = [r for r in fails("") if r["session"] == "s-hb"]
c = cards().get("s-hb", {})
check("handback: the card is saved from the handback message", c.get("verdict") == "FAIL" and c.get("format") in ("page", "index"), c)
check("handback: the FAIL row has the brief's job and the card's format",
      rows and rows[0]["job"].startswith("Build a one-screen") and rows[0]["format"] == c.get("format"), rows)
n = len(fails(""))
run(stop)
check("handback then SubagentStop with no final text: captured once", len(fails("")) == n
      and len([x for x in cards().values() if x["session"] == "s-hb"]) == 1)
hb2, stop2 = handback_job("hb2", "Build a one-screen index page for the made-up Demo Co docs.",
                          "Checked.\n" + TABLE.format(v="FAIL", e="z"), "s-hb2")
run(stop2)
check("SubagentStop alone finds the handback report in the agent transcript", cards().get("s-hb2", {}).get("verdict") == "FAIL")
check("settings: SubagentHandback goes to job_diff_hook.py", any("job_diff_hook.py" in c for c in post.get("SubagentHandback", [])), post)
env = {k: v for k, v in os.environ.items() if k not in ("NQOS_WORK", "NQOS_LIVECARD")}
out = subprocess.run([sys.executable, "-c", "import nqos_config; print(nqos_config.LIVECARD)"], capture_output=True,
                     text=True, env=env, cwd=os.path.join(os.path.dirname(HERE), "brain")).stdout.strip()
check("Working-now titles sit in one folder whichever copy runs (not under the copy's work/)", out == "/tmp/nqos-livecard", out)

# cost: with nothing pending, the fast path never starts Python
ev = json.dumps({"hook_event_name": "PostToolUse", "session_id": "s-bg", "tool_name": "Bash", "tool_input": {}})
def ms(cmd):
    xs = []
    for _ in range(15):
        t = time.perf_counter()
        subprocess.run(cmd, input=ev, capture_output=True, text=True, env=ENV)
        xs.append((time.perf_counter() - t) * 1000)
    return sorted(xs)[len(xs) // 2]
fast, slow = ms(SH), ms([sys.executable, HOOK])
print(f"     per ordinary call: fast path {fast:.1f} ms, Python hook {slow:.1f} ms")
check("fast path is cheaper than starting Python", fast < slow, (fast, slow))

print(f"\n{len(CHECKS)} checks, {CHECKS.count(False)} failing")
sys.exit(1 if False in CHECKS else 0)
