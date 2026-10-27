#!/usr/bin/env python3
"""Check job_diff_hook.py against hook events with known answers (no model, about 2 s).

usage: python3 .claude/hooks/test_job_diff_hook.py
Throwaway jobs from .claude/brain/tests/jobdiff_fixtures.py; cards and pending notes go to the temp folder.
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "job_diff_hook.py")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "brain", "tests"))
from jobdiff_fixtures import job, post_tool_use, subagent_stop

TMP = tempfile.mkdtemp(prefix="job-diff-hook-test-")
FAILLOG = os.path.join(TMP, "costlog", "qualityfails.jsonl")
ENV = dict(os.environ, NQOS_JOBCARDS=os.path.join(TMP, "cards"), NQOS_WORK=os.path.join(TMP, "work"),
           NQOS_COSTLOG=os.path.join(TMP, "costlog", "costlog.jsonl"), NQOS_FAILLOG=FAILLOG)
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def run(ev):
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(ev), capture_output=True, text=True, env=ENV)
    if p.returncode:
        return "crash: " + p.stderr[-200:]
    out = p.stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def fails():
    return [json.loads(l) for l in open(FAILLOG)] if os.path.isfile(FAILLOG) else []


def cards():
    d = os.path.join(TMP, "cards")
    return sorted(f for f in os.listdir(d) if f != "refs.json") if os.path.isdir(d) else []


pending = os.path.join(TMP, "work", "jobdiff-pending", "sess.txt")

# 1. a FAIL with no good job on file yet: card saved, nothing said
lead, rep, tid = job(TMP, "first", fail_audio=True)
check("FAIL with no reference: silent", run(subagent_stop(TMP, "first", lead, rep)) == "" and not os.path.exists(pending))
check("FAIL with no reference: card still saved", len(cards()) == 1, cards())

check("FAIL: SubagentStop also logs the FAIL row for the weekly review (gap 1)",
      len(fails()) == 1 and fails()[0].get("session") == "sess", fails())

# 2. a PASS becomes the reference; nothing said
lead, rep, tid = job(TMP, "good")
check("PASS: silent", run(subagent_stop(TMP, "good", lead, rep)) == "" and run(post_tool_use("good", lead, rep, tid)) == "")
check("PASS: SubagentStop and PostToolUse share one card", len(cards()) == 2, cards())
check("PASS: no FAIL row logged", len(fails()) == 1, fails())

# 3. foreground nq-check FAIL: SubagentStop leaves a note, PostToolUse on the Agent call shows it and clears it
lead, rep, tid = job(TMP, "loud", fail_audio=True)
check("SubagentStop says nothing itself", run(subagent_stop(TMP, "loud", lead, rep)) == "")
check("SubagentStop leaves the note pending", os.path.isfile(pending))
note = run(post_tool_use("loud", lead, rep, tid))
check("PostToolUse shows the first divergence next to the FAIL",
      "First divergence (steps)" in note and "loudnorm=I=-9" in note and "job_diff.py" in note, note)
check("note shown once", not os.path.exists(pending) and run({"hook_event_name": "PostToolUse", "session_id": "sess",
                                                              "tool_name": "Bash", "tool_input": {}}) == "")

# 4. background nq-check: the launch says nothing; the note rides on the lead's next tool call
lead, rep, tid = job(TMP, "nostyle", style="", fail_style=True)
check("background launch: silent, no card", run(post_tool_use("nostyle", lead, rep, tid, async_launch=True)) == ""
      and len(cards()) == 3, cards())
run(subagent_stop(TMP, "nostyle", lead, rep))
note = run({"hook_event_name": "PostToolUse", "session_id": "sess", "tool_name": "Read", "tool_input": {}})
check("background FAIL: the next tool call carries the note", "named no style" in note, note)
other = run({"hook_event_name": "PostToolUse", "session_id": "other", "tool_name": "Read", "tool_input": {}})
check("another session's call doesn't get it", other == "")

# 5. one part failing never stops the other
lead, rep, tid = job(TMP, "split", fail_audio=True)
bad = dict(ENV, NQOS_FAILLOG=TMP)                      # a folder, so the FAIL log can't be written
p = subprocess.run([sys.executable, HOOK], input=json.dumps(subagent_stop(TMP, "split", lead, rep, session="s2")),
                   capture_output=True, text=True, env=bad)
check("FAIL log broken: card still saved, exit 0, silent",
      p.returncode == 0 and not p.stdout.strip() and len(cards()) == 5,
      (p.returncode, p.stdout, cards()))
lead, rep, tid = job(TMP, "split2", fail_audio=True)
blocker = os.path.join(TMP, "notadir")
open(blocker, "w").write("x")
bad = dict(ENV, NQOS_JOBCARDS=blocker)                 # a file, so no card can be saved
n = len(fails())
p = subprocess.run([sys.executable, HOOK], input=json.dumps(subagent_stop(TMP, "split2", lead, rep, session="s3")),
                   capture_output=True, text=True, env=bad)
check("job card broken: FAIL row still logged, exit 0, silent",
      p.returncode == 0 and not p.stdout.strip() and len(fails()) == n + 1, (p.returncode, p.stdout, p.stderr[-200:]))

# 6. other agents and junk never break anything
check("other agent: silent", run(dict(subagent_stop(TMP, "good", lead, rep), agent_type="nq-build")) == "")
p = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, env=ENV)
check("bad input: exit 0, silent", p.returncode == 0 and not p.stdout.strip(), p.stderr[-200:])

print(f"\n{len(CHECKS)} checks, {CHECKS.count(False)} failing")
sys.exit(1 if False in CHECKS else 0)
