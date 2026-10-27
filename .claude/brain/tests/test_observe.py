#!/usr/bin/env python3
"""Check "Observe": each cost line carries the job's nq-check outcome, and the review reports cost and pass
rate per format (no model, about 1 s).

usage: python3 .claude/brain/tests/test_observe.py
Real job cards are made by the real SubagentStop hook (job_diff_hook.py) from throwaway jobs, then the cost
lines are logged and reviewed. Writes only to a throwaway folder, never the real logs or cards.
"""
import datetime, json, os, subprocess, sys, tempfile

TMP = tempfile.mkdtemp(prefix="observe-test-")
os.environ.update(NQOS_JOBCARDS=os.path.join(TMP, "cards"), NQOS_COSTLOG=os.path.join(TMP, "costlog.jsonl"),
                  NQOS_FAILLOG=os.path.join(TMP, "qualityfails.jsonl"), NQOS_WORK=os.path.join(TMP, "work"))
HERE = os.path.dirname(os.path.abspath(__file__))
BRAIN = os.path.dirname(HERE)
HOOK = os.path.join(os.path.dirname(BRAIN), "hooks", "job_diff_hook.py")
sys.path.insert(0, BRAIN)
sys.path.insert(0, HERE)
import job_card, post_mortem as pm  # noqa: E402
from jobdiff_fixtures import job, subagent_stop  # noqa: E402

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def nq_check(name, session, **kw):
    """One nq-check run through the real hook, as Claude Code fires it."""
    lead, rep, _ = job(TMP, name, session=session, **kw)
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(subagent_stop(TMP, name, lead, rep, session=session)),
                       capture_output=True, text=True, env=os.environ, timeout=30)
    return p.returncode


def meter(session, usd):
    """The parts of a cost_meter.meter() result that log_line reads."""
    return {"session": session, "usd": usd, "calls": 10, "agents": 1, "compactions": 0, "ctx_max": 1, "ctx_median": 1,
            "tokens": {}, "cost_share_pct": {}, "streams": [], "drains": []}


def logged(session):
    return [json.loads(x) for x in open(pm.LOG) if json.loads(x)["session"] == session][-1]


# reel 1: failed on audio, fixed, passed on the second nq-check -> PASS, two rounds, both cards linked
check("hook exits 0", nq_check("r1a", "sessR1", fail_audio=True) == 0 and nq_check("r1b", "sessR1") == 0)
pm.log_line(meter("sessR1", 4.0), "SE 911 reel")
r1 = logged("sessR1")
ids = [c["id"] for c in reversed(job_card.load_all()) if c["session"] == "sessR1"]
check("fixed then passed: verdict PASS, 2 rounds, no fails", (r1["verdict"], r1["rounds"], r1["fails"]) == ("PASS", 2, []), r1)
check("cost line links both job card ids", r1["cards"] == ids and len(ids) == 2, (r1["cards"], ids))
check("format and workstream from the card", (r1["format"], r1["workstream"]) == ("reel", "supercar experience"), r1)

# reel 2: failed and shipped no fix -> FAIL with the failing check named
nq_check("r2", "sessR2", fail_audio=True)
pm.log_line(meter("sessR2", 2.0), "SE drive reel")
r2 = logged("sessR2")
check("failed job: verdict FAIL with the failing check", (r2["verdict"], r2["fails"]) == ("FAIL", ["Audio level"]), r2)
check("the card id resolves to the saved card", job_card.load(r2["cards"][0])["verdict"] == "FAIL")
pm.log_line(meter("sessR2", 2.5), "SE drive reel")
check("logged twice: the latest line keeps the verdict", logged("sessR2")["verdict"] == "FAIL" and logged("sessR2")["usd"] == 2.5)

# reel 3: lead-only, nq-check never ran -> unchecked, format from the job name
pm.log_line(meter("sessR3", 1.0), "SE reel caption tweak")
r3 = logged("sessR3")
check("lead-only job: unchecked, no cards", (r3["verdict"], r3["cards"], r3["format"]) == ("unchecked", [], "reel"), r3)

# carousel: a handback-only report left FAIL-log rows but no card -> FAIL from gap 1's log
pm.log_fails("- Caption rules: FAIL - three lines\n- Brand: FAIL - wrong red\nFD carousel", "sessC", agent="h1")
pm.log_line(meter("sessC", 3.0), "FD carousel")
rc = logged("sessC")
check("no card: the FAIL log decides", (rc["verdict"], rc["fails"], rc["format"]) == ("FAIL", ["Caption rules", "Brand"], "carousel"), rc)

# an old line from before this change has no verdict: it counts as unchecked
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
old = {k: v for k, v in logged("sessR3").items() if k not in ("verdict", "fails", "cards", "rounds", "format", "workstream")}
with open(pm.LOG, "a") as fh:
    fh.write(json.dumps(dict(old, at=now, session="sessOld", job="old poster", usd=1.5)) + "\n")

g = pm.by_format(pm.read_log(7))
check("per format: reels 3 jobs, 2 checked, 1 passed, 1 unchecked",
      (g["reel"]["jobs"], g["reel"]["checked"], g["reel"]["passed"], g["reel"]["unchecked"]) == (3, 2, 1, 1), g["reel"])
check("old line without a verdict counts as unchecked", g["poster"]["unchecked"] == 1 and g["poster"]["checked"] == 0)
text = pm.review(7)
block = text.split("cost and pass rate by format")[1].split("\n\n")[0]
check("review: reel pass rate leaves the unchecked job out", "1/2 passed (50%)" in block and "1 unchecked" in block, block)
check("review: cost per passed reel is checked spend over passes ($4.00 + $2.50) / 1",
      "$6.50 per passed reel" in block, block)
check("review: a format with no pass says so", "0/1 passed (0%)  no passes yet" in block, block)
check("review: each session line shows its verdict and fails",
      "FAIL" in text and "[fails: Audio level]" in text and "unchecked" in text.split("cost and pass")[0])

# the cost line still goes out if the cards can't be read
real = job_card.load_all
job_card.load_all = lambda: (_ for _ in ()).throw(OSError("cards folder gone"))
pm.log_line(meter("sessX", 1.0), "SE reel")
job_card.load_all = real
check("unreadable cards: line logged, unchecked", logged("sessX")["verdict"] == "unchecked")
check("everything stayed in the throwaway folder",
      all(os.path.dirname(f).startswith(TMP) for f in (pm.LOG, pm.FAILS, job_card.CARDS)))

print(f"\n{sum(CHECKS)}/{len(CHECKS)} passed")
sys.exit(0 if all(CHECKS) else 1)
