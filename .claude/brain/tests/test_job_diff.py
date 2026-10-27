#!/usr/bin/env python3
"""Check job_card.py and job_diff.py against throwaway jobs with known answers (no model, under 1 s).

usage: python3 .claude/brain/tests/test_job_diff.py
A good reel (Locked-On, loudnorm I=-14, PASS) is the reference. One failed reel differs only at the loudness
flag, one only by a brief with no style; each must name that place as the first divergence.
"""
import json, os, sys, tempfile

TMP = tempfile.mkdtemp(prefix="job-diff-test-")
os.environ["NQOS_JOBCARDS"] = os.path.join(TMP, "cards")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import job_card, job_diff
from jobdiff_fixtures import job, subagent_stop

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def card(name, **kw):
    lead, rep, tid = job(TMP, name, **kw)
    c = job_card.from_event(subagent_stop(TMP, name, lead, rep))
    job_card.save(c)
    return c


good = card("good")
check("card: format, workstream, style, playbook detected",
      (good["format"], good["workstream"], good["style"], good["playbook"]) ==
      ("reel", "Supercar Experience", "Locked-On", "supercar-experience"), good)
check("card: PASS with every check row", good["verdict"] == "PASS" and len(good["checks"]) == 3, good["checks"])
progs = [s["prog"] for s in good["steps"]]
check("card: steps keep the work, drop looking around", progs == ["python recall.py", "brief nq-build", "python cut.py",
      "ffmpeg", "python captions.py"], progs)
ff = dict(next(s for s in good["steps"] if s["prog"] == "ffmpeg")["flags"])
check("card: ffmpeg flags parsed, paths cut to names", ff.get("-af") == "loudnorm=I=-14:TP=-1.5:LRA=11"
      and ff.get("-i") == "clip_good.mov", ff)
check("card: loudness from the report", good["outputs"][0].get("lufs") == -14.0, good["outputs"])
check("card: saved outside the repo", good and os.path.isfile(os.path.join(TMP, "cards", good["id"] + ".json")))

loud = card("loud", fail_audio=True)
check("loud: FAIL, emoji verdict cell read", loud["verdict"] == "FAIL" and loud["checks"]["Audio level"] == "FAIL",
      loud["checks"])
ref, why = job_diff.reference(loud)
check("reference: latest PASS of the same format", ref and ref["id"] == good["id"], (ref or {}).get("id"))
d = job_diff.diff(loud, ref)
check("loud: first divergence is the loudness step", d and d[0][0] == "steps" and "ffmpeg" in d[0][1]
      and "loudnorm=I=-9" in d[0][2] and "loudnorm=I=-14" in d[0][2], d[:1])
check("loud: later list has the output loudness and the failed check",
      any(s == "outputs" and "lufs" in w for s, w, _ in d) and any(s == "checks" and w == "Audio level" for s, w, _ in d), d)
check("loud: clip names and paths are not differences", not any("clip_" in t or "UIUX-se" in t for _, _, t in d), d)

nostyle = card("nostyle", style="", fail_style=True)
d2 = job_diff.diff(nostyle, job_diff.reference(nostyle)[0])
# the lead told nq-check the style but not the builder: the builder's brief is where it went wrong
check("nostyle: first divergence is the builder brief with no style", d2 and d2[0][0] == "briefs"
      and "nq-build brief named no style" in d2[0][2] and "Locked-On" in d2[0][2], d2[:1])
text = job_diff.report(nostyle, good, why)
check("report: first divergence printed first", text.splitlines()[3].startswith("First divergence (briefs): the nq-build brief named no style"), text)

same = card("same")
check("same job again: no difference found", job_diff.diff(same, good) == [], job_diff.diff(same, good))

# extra harmless steps (a live card update, a git commit) don't shift the alignment
busy = card("busy", fail_audio=True, extra_lead=[
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_busy_l", "name": "Bash",
     "input": {"command": "python3 .claude/brain/live_card.py step 'x' && git add -A && git commit -m wip"}}]}}])
d3 = job_diff.diff(busy, good)
check("housekeeping steps ignored", d3 and d3[0][0] == "steps" and "ffmpeg" in d3[0][1], d3[:1])

# a different program in the chain is a divergence of its own
stray = card("stray", fail_audio=True, cap="fast")
stray["steps"][-1] = dict(stray["steps"][-1], prog="python subs.py", cmd="python3 subs.py --in x.mp4")
d4 = job_diff.diff(stray, good)
check("swapped step named", any("subs.py" in t and "captions.py" in t for _, _, t in d4), d4)

# a pin beats the latest PASS
later = card("later")
check("latest PASS moves to the newer job", job_diff.reference(loud)[0]["id"] in (later["id"], same["id"]),
      job_diff.reference(loud))
job_diff.pin(good["id"])
r, why = job_diff.reference(loud)
check("pinned reference wins", r["id"] == good["id"] and why.startswith("pinned"), (r["id"], why))
check("--ref with a card id", job_diff.reference(loud, later["id"])[0]["id"] == later["id"])
check("no reference for an unknown format", job_diff.reference(dict(loud, format="poster"))[0] is None)

note, _ = job_diff.first_divergence(loud)
check("hook note names the step", note and "First divergence (steps)" in note and "loudnorm" in note, note)

# a report with no table: gap 1's bullet reader still finds the FAIL
v, rows = job_card.parse_report("Checked out/x.mp4.\n- Audio level: FAIL - 9 LUFS too loud\n- Captions: PASS")
check("bullet report: FAIL read through post_mortem.parse_fails", v == "FAIL" and rows == {"Audio level": "FAIL"}, (v, rows))

# a background launch is not a finished check
check("async launch gives no card", job_card.from_event({"tool_input": {"subagent_type": "nq-check"},
      "tool_response": {"status": "async_launched", "agentId": "x"}}) is None)
check("other agents give no card", job_card.from_event({"agent_type": "nq-build", "last_assistant_message": "x"}) is None)
check("noise: ids and times replaced", job_card.denoise("session_01ABC at 2026-10-26T06:00:00Z") == "<id> at <time>",
      job_card.denoise("session_01ABC at 2026-10-26T06:00:00Z"))

print(f"\n{len(CHECKS)} checks, {CHECKS.count(False)} failing")
sys.exit(1 if False in CHECKS else 0)
