#!/usr/bin/env python3
"""Check regression.py (gap 3) against throwaway jobs with known answers (no model, under 1 s).

usage: python3 .claude/brain/tests/test_regression.py
Two passed SE reels are on file: "good" (Locked-On, loudness measured, pinned) and "plain" (newer, its
builder brief named no style). A loudness rule must leave both passing; a style rule must name "plain";
a rule scoped to another brand must say there is nothing to re-check. Then review() must carry the line.
"""
import os, sys, tempfile, time

TMP = tempfile.mkdtemp(prefix="regression-test-")
os.environ.update(NQOS_JOBCARDS=os.path.join(TMP, "cards"), NQOS_COSTLOG=os.path.join(TMP, "costlog.jsonl"),
                  NQOS_FAILLOG=os.path.join(TMP, "qualityfails.jsonl"), NQOS_WORK=os.path.join(TMP, "work"))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import job_card, job_diff, post_mortem, regression
from jobdiff_fixtures import job, report, subagent_stop

CHECKS = []
SE, REEL = ["supercar experience"], ["reel"]


def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def card(name, **kw):
    lead, rep, tid = job(TMP, name, **kw)
    c = job_card.from_event(subagent_stop(TMP, name, lead, rep))
    job_card.save(c)
    return c


check("no cards yet: says so, doesn't claim a pass",
      regression.summary(regression.recheck("audio level", "Audio level", SE, REEL)).startswith("Not re-checked: no past"))

good = card("good")
loud = card("loud", fail_audio=True)
time.sleep(1.1)                                         # the card id and order go by the second
plain = card("plain", style="")
check("fixture: plain passed with no style in the builder brief",
      plain["verdict"] == "PASS" and not plain["brief"][0]["style"], (plain["verdict"], plain["brief"][0]))
job_diff.pin(good["id"])

rs = regression.regression_set(SE, REEL)
ids = [c["id"] for c, _ in rs]
check("set: the pin first, then the latest PASS", ids == [good["id"], plain["id"]], [(c["id"], w) for c, w in rs])
check("set: a FAIL job is never in it", loud["id"] not in ids)
check("set: pin labelled as such", rs[0][1] == "pinned reference for reel", rs[0][1])

t0 = time.time()
res = regression.recheck("audio level", "Audio level", SE, REEL)
fast = time.time() - t0
check("loudness rule: both past jobs still pass", res["failed"] == [] and len(res["jobs"]) == 2, res["jobs"])
check("loudness rule: the line for Omarie", regression.summary(res) == "Re-checked against 2 past jobs: all still pass.",
      regression.summary(res))
check("re-check is fast (no model, no rebuild)", fast < 0.5, fast)

res = regression.recheck("style", "Style", SE, REEL)
check("style rule: the job with no style would now fail, and only that one",
      [r["id"] for r in res["failed"]] == [plain["id"]], res["jobs"])
line = regression.summary(res)
check("style rule: the line names the job and why", "1 would now fail" in line and plain["id"] in line
      and "nq-build brief named no style" in line, line)

check("caption rule: the caption step counts", regression.recheck("caption", "Caption rules", SE, REEL)["failed"] == [])
facts = regression.recheck("figure", "Figures", SE, REEL)
check("facts rule: jobs with no nq-facts brief are named", len(facts["failed"]) == 2, facts["jobs"])
check("frame rule: no contact sheet named", regression.recheck("framing", "Framing", SE, REEL)["failed"] != [])

fd = regression.recheck("audio level", "Audio level", ["formula dynamics"], REEL)
check("rule for another brand: nothing to re-check", fd["jobs"] == [] and "no past passed job" in regression.summary(fd),
      regression.summary(fd))
check("unscoped rule: tried on every format on file", len(regression.recheck("style", "Style")["jobs"]) == 2)

# a rule that only reaches driving shots leaves a studio job alone
studio = dict(good, id="studio", brief=[dict(good["brief"][0], text="Studio carousel for the RYFT parts.")])
v, why = regression.test_card(studio, "hands on wheel", "Hands on wheel")
check("hands rule: n/a when the brief has no driving", v == "n/a", (v, why))
res = regression.recheck("hands on wheel", "Hands on wheel", cards=[dict(studio, at="9")])
check("rule reaching no job: says so", regression.summary(res).startswith("Not re-checked: the rule doesn't reach"),
      regression.summary(res))

# a job whose own row for the check was FAIL fails any rule on it, even a pre-flight one
mixed = dict(good, id="mixed", checks={"Colour grade": "FAIL"})
check("own FAIL row fails the rule", regression.test_card(mixed, "colour grade", "Colour grade")[0] == "fail")
v, why = regression.test_card(good, "colour grade", "Colour grade")
check("pre-flight rule with nothing to test: pass, and says why", v == "pass" and "not checked" in why, (v, why))

# a few at most: one per format, capped
many = [dict(good, id=f"c{i}", format=f"fmt{i}", at=f"2026-10-2{i}") for i in range(8)]
check("set is capped", len(regression.regression_set(cards=many)) == regression.MAX)

plan = regression.rebuild_plan(regression.recheck("style", "Style", SE, REEL))
check("rebuild plan: briefs, the rule and the token cost, no model call",
      "Full re-build test" in plan and "220k tokens" in plan and "Build the Supercar Experience reel" in plan
      and plan.count("+ new rule under test") == 2, plan)

# review(): two SE reels failed Style this week, so the proposal carries the re-check line
for n, s in (("a", "s1"), ("b", "s2")):
    post_mortem.log_fails(report(f"x{n}", -14, fail_style=True), s, job=f"SE reel {n}")
text = post_mortem.review(7)
prop = next((l for l in text.splitlines() if "Proposed rule" in l), "")
check("review: proposal re-checked, the breaking job named", "Re-checked against 2 past jobs: 1 would now fail" in prop
      and plain["id"] in prop, text)
check("review: gap 1's wording kept", "2 jobs failed Style this week. Proposed rule: name the style in every" in prop, prop)
check("quality_proposals(recheck=False) leaves the line off",
      "Re-checked" not in post_mortem.quality_proposals(post_mortem.repeated_fails(post_mortem._read(post_mortem.FAILS, 7)),
                                                        recheck=False)[0])

print(f"\n{len(CHECKS)} checks, {CHECKS.count(False)} failing")
sys.exit(1 if False in CHECKS else 0)
