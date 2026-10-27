#!/usr/bin/env python3
"""Check rule_gate.py on a fixture replay set with known answers (no model, about 1 s).

usage: python3 .claude/brain/tests/test_rule_gate.py
The cards are in the shape gap 2's job_card.py saves (feat/failed-vs-good-diff); nothing here is client copy.
"""
import io, json, os, sys, tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="rule-gate-test-")
os.environ["NQOS_JOBCARDS"] = os.path.join(TMP, "jobcards")
os.environ["NQOS_GATE"] = os.path.join(TMP, "gate")
os.environ["NQOS_COSTLOG"] = os.path.join(TMP, "costlog.jsonl")
os.environ["NQOS_FAILLOG"] = os.path.join(TMP, "qualityfails.jsonl")
sys.path.insert(0, HERE)
import rule_gate as g  # noqa: E402


def card(cid, verdict="PASS", fmt="reel", style="Locked-On", lufs=-14.0, duration=28.0, size="1080x1920"):
    c = {"id": cid, "at": f"2026-10-2{cid[-1]}T10:00:00Z", "session": "sess", "job": f"SE reel {cid}",
         "workstream": "Supercar Experience", "format": fmt, "style": style, "playbook": "supercar-experience",
         "brief": [{"who": "nq-build", "style": style, "playbook": "supercar-experience", "text": "Build the reel."}],
         "steps": [], "outputs": [{"file": f"{cid}.mp4", "duration": duration, "size": size, "fps": 30.0, "lufs": lufs}],
         "verdict": verdict, "checks": {"Audio level": verdict}}
    os.makedirs(g.CARDS, exist_ok=True)
    json.dump(c, open(os.path.join(g.CARDS, cid + ".json"), "w"))
    return c


def caps(name, lines):
    p = os.path.join(TMP, name)
    open(p, "w").write("\n\n".join(f"{i}\n00:00:0{i},000 --> 00:00:0{i},900\n{l}" for i, l in enumerate(lines, 1)))
    return p


card("20261021-sess-aaaaa1")
card("20261022-sess-bbbbb2", duration=44.0)
card("20261023-sess-ccccc3", style="")
card("20261024-sess-ddddd4", verdict="FAIL", lufs=-9.0)
card("20261025-sess-eeeee5", fmt="carousel", size="1080x1350")

# ---- the replay set ----
assert "did not pass" in g.set_add("20261024-sess-ddddd4"), "a failed job must not join the set"
assert "added" in g.set_add("20261021", captions=caps("a.srt", ["Track day, 911 GT3", "Book the drive"]))
assert "added" in g.set_add("20261022", captions=caps("b.srt", ["The longest straight in the county, flat out"]))
assert "added" in g.set_add("20261023")                     # no captions on record
open(os.path.join(TMP, "copy.txt"), "w").write("Unleash the 812 GTS. Book now.")
assert "added" in g.set_add("20261025", copy=os.path.join(TMP, "copy.txt"))
assert [e["card"] for e in g.replay_set()["reel"]] == ["20261021-sess-aaaaa1", "20261022-sess-bbbbb2",
                                                       "20261023-sess-ccccc3"]
assert g.replay_set()["reel"][0]["captions"] == ["Track day, 911 GT3", "Book the drive"], "srt parsed to lines"
assert g.set_suggest() == [], "every passed card is in the set"
for i in range(3):
    card(f"20261026-sess-fffff{i}")
    g.set_add(f"20261026-sess-fffff{i}")
assert "already has 5" in g.set_add(card("20261027-sess-ggggg7")["id"]), "the set stops at 5 per format"
g.set_remove("20261026-sess-fffff")
assert len(g.replay_set()["reel"]) == 3

# ---- reading the rule ----
P = g.parse
assert P("captions under 32 characters")["field"] == "caption_len" and P("captions under 32 characters")["op"] == "<"
assert P("Caption lines at most 2 lines")["field"] == "caption_lines"
assert P("Reels at -14 LUFS")["value"] == -14 and P("Reels at -14 LUFS")["tol"] == 1.0
assert P("loudness at least -16 LUFS")["op"] == ">="
assert P("reels under 30 seconds")["field"] == "duration" and P("reels under 1 min")["value"] == 60
assert P("deliver 1080x1920")["value"] == "1080x1920"
assert P('never say "unleash" or "elevate" in copy')["value"] == ["unleash", "elevate"]
assert P("name the style in every reel brief")["field"] == "brief_style"
assert P("bind reminders and check-ins to a small session")["kind"] == "process"
assert P("have nq-build measure loudness on every reel render and report it with the hand-over")["kind"] == "process"
assert P("the hook must land in the first second")["kind"] == "judgement"
assert g.rule_format("captions under 32 characters on reels") == "reel" and g.rule_format("captions") is None

# ---- mechanical: the done-looks-like example ----
r = g.gate("captions under 32 characters", "reel")
st = {x["job"]: x["status"] for x in r["results"]}
assert st == {"20261021-sess-aaaaa1": "pass", "20261022-sess-bbbbb2": "fail", "20261023-sess-ccccc3": "unknown"}, st
assert "44 characters" in next(x["why"] for x in r["results"] if x["status"] == "fail")
assert r["verdict"] == "would break 1 of 3 past jobs", r["verdict"]
buf = io.StringIO()
with redirect_stdout(buf):
    code = g.main(["check", "captions under 32 characters", "--format", "reel"])
assert code == 1 and "FAIL    20261022-sess-bbbbb2" in buf.getvalue(), buf.getvalue()

assert g.gate("reels under 30 seconds")["verdict"] == "would break 1 of 3 past jobs"
assert g.gate("reels at -14 LUFS")["verdict"] == "safe to land (3 of 3 past jobs still pass)"
assert g.gate("reels louder than -12 LUFS")["verdict"] == "would break 3 of 3 past jobs"
assert g.gate("name the style in every reel brief")["verdict"] == "would break 1 of 3 past jobs"
assert g.gate("captions at most 2 lines", "reel")["verdict"].startswith("safe to land on 2 of 3")
assert g.gate('never say "unleash" on a carousel')["verdict"] == "would break 1 of 1 past jobs"
assert g.gate("deliver every carousel at 1080x1350")["verdict"].startswith("safe to land")
assert g.gate("posters under 10 seconds")["verdict"].startswith("can't tell: no replay set")
assert g.gate("hand off at 300k context")["kind"] == "process"

# ---- judgement: one bundle for the whole set, never a second run ----
r = g.gate("the hook must land in the first second", "reel")
assert r["kind"] == "judgement" and r["verdict"].startswith("needs judgement: one nq-check run over all 3 jobs")
bundles = os.listdir(g.GATE)
assert len(bundles) == 1, bundles
prompt = open(os.path.join(r["bundle"], "prompt.md")).read()
assert all(j in prompt for j in st), "the one prompt names every job"
assert g.gate("The hook must land in the first  second", "reel")["bundle"] == r["bundle"], "same rule, same bundle"
assert len(os.listdir(g.GATE)) == 1
report = ("| job | verdict | evidence |\n|---|---|---|\n"
          "| 20261021-sess-aaaaa1 | PASS | car on screen at 0.4 s |\n"
          "| `20261022-sess-bbbbb2` | **FAIL** | title card until 1.8 s |\n")
out = g.record_verdict(r["bundle"], report)
assert out["verdict"] == "would break 1 of 3 past jobs", out
assert [x["status"] for x in out["results"]] == ["pass", "fail", "unknown"]
again = g.gate("the hook must land in the first second", "reel")
assert again["verdict"].startswith("would break 1 of 3 past jobs (nq-check"), "the saved answer is reused"

# ---- the contact sheet: one image for the set (ffmpeg only) ----
if g.shutil.which("ffmpeg"):
    import subprocess
    pics = []
    for i in range(2):
        p = os.path.join(TMP, f"s{i}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=red:s={200 + i * 50}x300",
                        "-frames:v", "1", p], check=True)
        pics.append(p)
    assert g.contact_sheet(pics, os.path.join(TMP, "sheet.jpg")), "two sheets tile into one"

# ---- the weekly review carries a gate line under each proposal ----
json.dump({"at": g._now(), "session": "s1", "job": "x", "note": "", "usd": 1, "calls": 1, "agents": 0,
           "compactions": 0, "ctx_max": 400_000, "ctx_median": 350_000, "cache_read": 0, "cache_write": 0,
           "output": 0, "share": {}, "agent_ctx_max": 0, "drains": []}, open(os.environ["NQOS_COSTLOG"], "w"))
text = g.review(7)
assert "gate: safe to land (process rule" in text, text
import post_mortem  # noqa: E402
assert post_mortem.review(7) == text, "post_mortem.py review carries the gate line itself"
assert text.count("gate:") == text.count("Proposed rule:"), "one gate line per proposal, not two"
assert "gate:" not in post_mortem.review(7, gate=False)

# ---- a real gap 2 card (job_card.py) joins the set and is measured ----
sys.path.insert(0, os.path.join(HERE, "tests"))
import job_card, jobdiff_fixtures  # noqa: E402
job_card.CARDS = g.CARDS
lead, rep, tid = jobdiff_fixtures.job(TMP, "real1", lufs=-14)
real = job_card.build_card(lead, rep, tid, "sess", "creal1", TMP)
job_card.save(real)
assert "added" in g.set_add(real["id"], fmt="reel"), real
r = g.gate("reels louder than -12 LUFS")
assert next(x for x in r["results"] if x["job"] == real["id"])["status"] == "fail"
r = g.gate("name the style in every reel brief")
assert next(x for x in r["results"] if x["job"] == real["id"])["status"] == "pass"

# ---- the replay set file sits among the cards: job_card.py and job_diff.py must skip it, not crash ----
import job_diff  # noqa: E402
assert os.path.isfile(g.REPLAY)
assert all("id" in c for c in job_card.load_all()), "replayset.json read as a card"
assert job_card.load("no-such-card") is None
assert job_diff.reference(dict(real, verdict="FAIL", id="x"))[0] is not None

print("rule_gate: all checks pass")
