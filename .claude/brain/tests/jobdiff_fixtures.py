"""Throwaway jobs for the gap 2 tests: a lead transcript, an nq-build transcript and an nq-check report.

job(dir, name, ...) writes <dir>/<name>.jsonl (the lead), <dir>/<name>/subagents/agent-*.jsonl (+ meta.json)
and returns (lead transcript path, nq-check report, nq-check tool_use id). Nothing here is real client copy.
"""
import json, os

GOOD_STEPS = [
    "cd /home/user/UIUX-se && python3 tools/cut.py --spec spec.json --out /home/user/UIUX-se/out/{name}.mp4",
    "ffmpeg -y -i /tmp/claude-0/abc/scratch/clip_{name}.mov -vf scale=1080:1920,fps=30 -c:v libx264 -crf 18 "
    "-af loudnorm=I={lufs}:TP=-1.5:LRA=11 /home/user/UIUX-se/out/{name}.mp4",
    "ls -la /home/user/UIUX-se/out",
    "python3 tools/captions.py --style {cap} --in out/{name}.mp4",
]


def _rec(kind, content, ts="2026-10-26T06:00:00Z"):
    return {"type": kind, "timestamp": ts, "message": {"role": kind, "content": content}}


def _use(tid, name, inp):
    return _rec("assistant", [{"type": "tool_use", "id": tid, "name": name, "input": inp}])


def report(name, lufs, fail_audio=False, fail_style=False):
    return (f"Checked /home/user/UIUX-se/out/{name}.mp4 (Supercar Experience reel).\n"
            "| check | verdict | evidence |\n|---|---|---|\n"
            f"| Style | {'**FAIL**' if fail_style else 'PASS'} | {'brief names no style' if fail_style else 'Locked-On'} |\n"
            f"| Audio level | {'❌ FAIL' if fail_audio else 'PASS'} | {lufs} LUFS integrated |\n"
            "| Caption rules | PASS | 2 lines max |\n"
            + ("Must change: audio level." if fail_audio else "Ship."))


def job(d, name, style="Locked-On", lufs=-14, cap="locked", fail_audio=False, fail_style=False,
        session="sess", extra_lead=()):
    lead = os.path.join(d, name + ".jsonl")
    sub = os.path.join(d, name, "subagents")
    os.makedirs(sub, exist_ok=True)
    brief = (f"Build the Supercar Experience reel for the 911 drive. Playbook: .claude/playbooks/supercar-experience.md. "
             + (f"Style: {style}. " if style else "") + "Deliver 9:16 at 30 fps.")
    rep = report(name, -9 if fail_audio else lufs, fail_audio, fail_style)
    recs = [_use(f"toolu_{name}_x", "Bash", {"command": "python3 .claude/brain/recall.py 'reel rules'"}),
            *extra_lead,
            _use(f"toolu_{name}_b", "Agent", {"subagent_type": "nq-build", "description": "build reel", "prompt": brief}),
            _use(f"toolu_{name}_c", "Agent", {"subagent_type": "nq-check", "description": "check reel",
                                              "prompt": f"Check out/{name}.mp4 against Locked-On."})]
    with open(lead, "w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    with open(os.path.join(sub, f"agent-b{name}.jsonl"), "w") as fh:
        for i, c in enumerate(GOOD_STEPS):
            fh.write(json.dumps(_use(f"toolu_{name}_s{i}", "Bash",
                                     {"command": c.format(name=name, lufs=-9 if fail_audio else lufs, cap=cap)})) + "\n")
        fh.write(json.dumps(_use(f"toolu_{name}_r", "Read", {"file_path": "/x/spec.json"})) + "\n")
    json.dump({"agentType": "nq-build", "toolUseId": f"toolu_{name}_b"}, open(os.path.join(sub, f"agent-b{name}.meta.json"), "w"))
    with open(os.path.join(sub, f"agent-c{name}.jsonl"), "w") as fh:
        fh.write(json.dumps(_rec("assistant", [{"type": "text", "text": rep}])) + "\n")
    json.dump({"agentType": "nq-check", "toolUseId": f"toolu_{name}_c"}, open(os.path.join(sub, f"agent-c{name}.meta.json"), "w"))
    return lead, rep, f"toolu_{name}_c"


def subagent_stop(d, name, lead, rep, session="sess"):
    return {"hook_event_name": "SubagentStop", "session_id": session, "transcript_path": lead,
            "agent_id": f"c{name}", "agent_type": "nq-check", "last_assistant_message": rep,
            "agent_transcript_path": os.path.join(d, name, "subagents", f"agent-c{name}.jsonl"), "cwd": d}


def post_tool_use(name, lead, rep, tid, session="sess", async_launch=False):
    resp = ({"status": "async_launched", "agentId": f"c{name}", "outputFile": "/tmp/x"} if async_launch else
            {"status": "completed", "agentId": f"c{name}", "content": [{"type": "text", "text": rep}]})
    return {"hook_event_name": "PostToolUse", "session_id": session, "transcript_path": lead, "tool_name": "Agent",
            "tool_use_id": tid, "tool_input": {"subagent_type": "nq-check", "prompt": "check"}, "tool_response": resp}
