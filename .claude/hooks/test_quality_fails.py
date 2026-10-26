#!/usr/bin/env python3
"""Check the nq-check FAIL capture end to end: parser, hook, grouping and the review block (no model, about 1 s).

usage: python3 .claude/hooks/test_quality_fails.py
Writes only to a throwaway folder (NQOS_COSTLOG / NQOS_FAILLOG), never the real cost log.
"""
import datetime, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BRAIN = os.path.join(os.path.dirname(HERE), "brain")
HOOK = os.path.join(HERE, "quality_fails.py")
TMP = tempfile.mkdtemp(prefix="quality-fails-test-")
COSTLOG, FAILLOG = os.path.join(TMP, "costlog.jsonl"), os.path.join(TMP, "qualityfails.jsonl")
os.environ.update(NQOS_COSTLOG=COSTLOG, NQOS_FAILLOG=FAILLOG, NQOS_WORK=os.path.join(TMP, "work"))
sys.path.insert(0, BRAIN)
import post_mortem as pm  # noqa: E402  (reads the env above)

# What nq-check hands back: the check · verdict · evidence table, then the ship line
REPORT = """Checked `/home/user/UIUX-se-vlog/out/part2_reel.mp4` against the Locked-On guide (Supercar Experience).

| check | verdict | evidence |
|---|---|---|
| Style named in brief | PASS | Locked-On, as briefed |
| Caption rules | **FAIL** | 0:14 caption runs 3 lines; rule is 2 max |
| Hands | ❌ FAIL | gate/sheet_03.jpg 00:41.2 phone in hand while moving |
| Audio level | PASS | -14.1 LUFS |
| Figures | N/A | no figures on screen |

Must change: caption at 0:14, cover 00:41 with a cutaway. Figures: none, so no facts panel needed.
"""
BULLETS = """Overall: FAIL
- Caption rule: FAIL - 0:09 caption covers the badge
- Brand: PASS
"""
CHECKS = []


def check(label, ok):
    CHECKS.append((label, bool(ok)))


def hook(event):
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True, timeout=10,
                       env=os.environ)
    return p.returncode, p.stdout + p.stderr


def fails():
    return [json.loads(x) for x in open(FAILLOG)] if os.path.isfile(FAILLOG) else []


# parser
got = pm.parse_fails(REPORT)
check("table: only the FAIL rows, in order", [c for c, _ in got] == ["Caption rules", "Hands"])
check("table: reason is the evidence cell", got[0][1] == "0:14 caption runs 3 lines; rule is 2 max")
check("bullets: fallback reads '- check: FAIL - why'", pm.parse_fails(BULLETS) == [("Caption rule", "0:09 caption covers the badge")])
check("all PASS: nothing", pm.parse_fails("| a | PASS | x |\n| b | N/A | y |") == [])
check("header and separator rows ignored", pm.parse_fails("| check | verdict | evidence |\n|---|---|---|") == [])
check("caption rule and Caption rules group together", pm.check_key("Caption rules") == pm.check_key("caption rule"))
check("workstream and format from the report", pm.tags(REPORT) == ("supercar experience", "reel"))

# hook: nq-check SubagentStop logs, anything else is ignored, bad input never fails
stop = {"hook_event_name": "SubagentStop", "session_id": "sessA", "agent_id": "ag1", "agent_type": "nq-check",
        "last_assistant_message": REPORT}
code, out = hook(stop)
check("hook: exit 0, silent", code == 0 and out == "")
check("hook: two FAIL rows logged with session and tags",
      [(r["check"], r["session"], r["workstream"], r["format"]) for r in fails()]
      == [("Caption rules", "sessA", "supercar experience", "reel"), ("Hands", "sessA", "supercar experience", "reel")])
hook(stop)
check("hook: the same report twice writes nothing new", len(fails()) == 2)
hook(dict(stop, agent_type="nq-build", agent_id="ag2"))
check("hook: other agents ignored", len(fails()) == 2)
code, _ = hook({"garbage": True})
check("hook: odd input exits 0", code == 0 and subprocess.run([sys.executable, HOOK], input="not json", text=True,
                                                              capture_output=True).returncode == 0)
hook({"hook_event_name": "PostToolUse", "tool_name": "SubagentHandback", "agent_type": "nq-check",
      "agent_id": "ag3", "session_id": "sessB", "tool_input": {"message": BULLETS}})
check("hook: a SubagentHandback report is read too", [r["session"] for r in fails()][-1] == "sessB")

# review: the cost log names the jobs; caption fails in 2 jobs group, Hands (one job) is a one-off
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
row = dict(at=now, note="", usd=3.0, calls=10, agents=1, compactions=0, ctx_max=1, ctx_median=1, cache_read=0,
           cache_write=0, output=0, share={}, agent_ctx_max=0, drains=[])
with open(COSTLOG, "w") as fh:
    fh.write(json.dumps(dict(row, session="sessA", job="SE Part 2 reel")) + "\n")
    fh.write(json.dumps(dict(row, session="sessB", job="SE Part 3 reel")) + "\n")
groups = pm.repeated_fails(pm._read(FAILLOG, 7), pm.read_log(7))
check("grouping: caption repeats across 2 jobs, Hands is left out",
      [(k, n) for k, n, *_ in groups] == [(pm.check_key("caption rule"), 2)])
text = pm.review(7)
check("review: 'repeated quality fails' block with the count",
      "repeated quality fails" in text and "2x Caption rule" in text and "Hands" not in text.split("proposed")[0].split("quality fails")[1])
check("review: proposal worded like the cost ones",
      "2 jobs failed Caption rule this week. Proposed rule: add the caption rules to nq-build's brief" in text)
check("review: a 14-day window says so", "in the last 14 days" in pm.review(14))
# a re-check in the same job doesn't count twice
pm.log_fails(BULLETS, "sessB", agent="ag4")
check("grouping: two fails in one job still count once",
      [n for _, n, *_ in pm.repeated_fails(pm._read(FAILLOG, 7), pm.read_log(7))] == [2])

# manual fallback
p = subprocess.run([sys.executable, os.path.join(BRAIN, "post_mortem.py"), "fail", "--job", "FD carousel",
                    "--session", "sessC"], input=REPORT, capture_output=True, text=True, env=os.environ)
check("manual: 'post_mortem.py fail' logs from stdin with the job", p.returncode == 0 and "logged 2" in p.stderr
      and fails()[-1]["job"] == "FD carousel" and fails()[-1]["source"] == "manual")
check("evidence stays in the private log path given", all(os.path.dirname(f) == TMP for f in (pm.FAILS, pm.LOG)))

bad = 0
for label, ok in CHECKS:
    bad += not ok
    print(("ok  " if ok else "FAIL") + "  " + label)
print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} passed")
sys.exit(1 if bad else 0)
