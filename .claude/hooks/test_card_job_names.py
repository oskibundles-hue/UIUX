#!/usr/bin/env python3
"""Check that each nq-check card gets its own job name, format and workstream (no model, about 1 s).

usage: python3 .claude/hooks/test_card_job_names.py
Session af6460ee (2026-10-28) filed two nq-check cards under an nq-facts brief and a reel re-check as the earlier
vlog, and named every card after its "Format: X / Workstream: Y" lines. This replays that shape with made-up
briefs: a vlog nq-check, then an nq-facts call, then a reel nq-check, all in one session. Temp folders only.
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "job_diff_hook.py")
TMP = tempfile.mkdtemp(prefix="card-job-names-test-")
ENV = dict(os.environ, NQOS_JOBCARDS=os.path.join(TMP, "cards"), NQOS_WORK=os.path.join(TMP, "work"),
           NQOS_COSTLOG=os.path.join(TMP, "costlog", "costlog.jsonl"),
           NQOS_FAILLOG=os.path.join(TMP, "costlog", "qualityfails.jsonl"), NQOS_LIVECARD=os.path.join(TMP, "livecard"))
CHECKS = []

VLOG_BUILD = ("Format: vlog\nWorkstream: Supercar Experience\n"
              "Cut the made-up Demo Drive vlog, part 3, from the selects. Your full brief is in /tmp/x/brief.md.")
VLOG_CHECK = "Format: vlog\nWorkstream: Supercar Experience\nCheck out/demo_part3.mp4 against Locked-On."
FACTS = ("Format: vlog\nWorkstream: Supercar Experience\nClass: facts (first voter of the facts panel)\n"
         "Trace every figure in out/demo_part3.mp4.")
REEL_BUILD = ("Format: reel\nWorkstream: Formula Dynamics\n"
              "Re-cut the made-up FD Demo Coupe reel with the new end card.")
REEL_CHECK = "Format: reel\nWorkstream: Formula Dynamics\nRe-check out/fd_demo_reel.mp4 against Reel Cut."
REPORT = "| check | verdict | evidence |\n|---|---|---|\n| Layout | PASS | fine |\nShip."


def check(name, ok, detail=""):
    CHECKS.append(ok)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def use(tid, kind, prompt):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": tid, "name": "Agent", "input": {"subagent_type": kind, "prompt": prompt}}]}}


def session(name, with_reel_build=True):
    """A lead transcript with the af6460ee shape, and a transcript + meta for each nq-check agent."""
    lead = os.path.join(TMP, name + ".jsonl")
    sub = os.path.join(TMP, name, "subagents")
    os.makedirs(sub, exist_ok=True)
    recs = [use("toolu_vb", "nq-build", VLOG_BUILD), use("toolu_vc", "nq-check", VLOG_CHECK),
            use("toolu_vf", "nq-facts", FACTS)]
    recs += [use("toolu_rb", "nq-build", REEL_BUILD)] if with_reel_build else []
    recs += [use("toolu_rc", "nq-check", REEL_CHECK)]
    with open(lead, "w") as fh:
        fh.write("".join(json.dumps(r) + "\n" for r in recs))
    for aid, tid in (("vlogchk1", "toolu_vc"), ("reelchk2", "toolu_rc")):
        open(os.path.join(sub, f"agent-{aid}.jsonl"), "w").write(json.dumps(
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": REPORT}]}}) + "\n")
        json.dump({"agentType": "nq-check", "toolUseId": tid}, open(os.path.join(sub, f"agent-{aid}.meta.json"), "w"))
    return lead, sub


def run(ev):
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(ev), capture_output=True, text=True, env=ENV)
    return p.returncode


def card(sess, aid):
    for f in os.listdir(os.path.join(TMP, "cards")):
        if f.endswith(aid[-6:] + ".json") and sess[:8] in f:
            return json.load(open(os.path.join(TMP, "cards", f)))
    return {}


def handback(sess, lead, sub, aid):
    """The handback fires inside the agent: its tool_use_id is the SubagentHandback call's, not the Agent call's."""
    return {"hook_event_name": "PostToolUse", "session_id": sess, "tool_name": "SubagentHandback",
            "tool_use_id": f"toolu_handback_{aid}", "agent_type": "nq-check", "agent_id": aid,
            "transcript_path": os.path.join(sub, f"agent-{aid}.jsonl"), "tool_input": {"message": REPORT}}


def stop(sess, lead, sub, aid):
    return {"hook_event_name": "SubagentStop", "session_id": sess, "transcript_path": lead, "agent_id": aid,
            "agent_type": "nq-check", "last_assistant_message": REPORT}


# 1. both checks report by handback after the whole session is in the transcript (the worst case: the latest
#    nq-check is the reel one, which is what the vlog card fell back to)
lead, sub = session("s-hand")
run(handback("s-hand", lead, sub, "vlogchk1"))
run(handback("s-hand", lead, sub, "reelchk2"))
v, r = card("s-hand", "vlogchk1"), card("s-hand", "reelchk2")
check("handback, vlog check: format vlog, Supercar Experience",
      (v.get("format"), v.get("workstream")) == ("vlog", "Supercar Experience"), v)
check("handback, vlog check: its own build brief, not the reel's or the facts brief",
      v.get("job", "").startswith("Cut the made-up Demo Drive vlog"), v.get("job"))
check("handback, reel check: format reel, Formula Dynamics",
      (r.get("format"), r.get("workstream")) == ("reel", "Formula Dynamics"), r)
check("handback, reel check: named after the reel build, not the nq-facts brief",
      r.get("job", "").startswith("Re-cut the made-up FD Demo Coupe reel"), r.get("job"))
check("no card's job is a Format/Workstream label", not any(
      c.get("job", "").lower().startswith(("format:", "workstream:", "class:")) for c in (v, r)), (v.get("job"), r.get("job")))

# 2. SubagentStop with no tool_use_id: the meta file pairs each card with its own call
lead, sub = session("s-stop")
run(stop("s-stop", lead, sub, "vlogchk1"))
run(stop("s-stop", lead, sub, "reelchk2"))
v, r = card("s-stop", "vlogchk1"), card("s-stop", "reelchk2")
check("SubagentStop: vlog card is vlog / Supercar Experience",
      (v.get("format"), v.get("workstream")) == ("vlog", "Supercar Experience"), v)
check("SubagentStop: reel card is reel / Formula Dynamics",
      (r.get("format"), r.get("workstream")) == ("reel", "Formula Dynamics"), r)

# 3. a re-check with no build brief in scope (the C63 case): the nq-facts brief before it is not its job,
#    its own Format/Workstream lines win, and the Working-now title names it
lead, sub = session("s-re", with_reel_build=False)
os.makedirs(ENV["NQOS_LIVECARD"], exist_ok=True)
json.dump({"title": "Made-up FD Demo Coupe re-check"}, open(os.path.join(ENV["NQOS_LIVECARD"], "s-re.json"), "w"))
run(handback("s-re", lead, sub, "reelchk2"))
r = card("s-re", "reelchk2")
check("re-check after nq-facts: reel / Formula Dynamics from its own nq-check brief",
      (r.get("format"), r.get("workstream")) == ("reel", "Formula Dynamics"), r)
check("re-check after nq-facts: job is the Working-now title", r.get("job") == "Made-up FD Demo Coupe re-check", r.get("job"))
check("re-check after nq-facts: the facts brief isn't filed as the job's brief",
      not any("facts panel" in b.get("text", "") for b in r.get("brief", [])), r.get("brief"))

# 4. job_name on its own: labelled opening lines never become the name
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "brain"))
os.environ.update(NQOS_JOBCARDS=ENV["NQOS_JOBCARDS"], NQOS_WORK=ENV["NQOS_WORK"])
import job_card
check("job_name skips Format/Workstream/Class lines",
      job_card.job_name(FACTS) == "Trace every figure in out/demo_part3.mp4.", job_card.job_name(FACTS))
check("job_name of a brief that is only labels is empty", job_card.job_name("Format: vlog\nWorkstream: SE") == "")
check("job_name keeps a plain opening line", job_card.job_name("Build the made-up poster.\nFormat: poster")
      == "Build the made-up poster.")

print(f"\n{len(CHECKS)} checks, {CHECKS.count(False)} failing")
sys.exit(1 if False in CHECKS else 0)
