#!/usr/bin/env python3
"""Check cost_meter.py and post_mortem.py on a built transcript with known answers (no model, under 1 s).

usage: python3 .claude/brain/tests/test_cost_meter.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="cost-meter-test-")
os.environ["NQOS_COSTLOG"] = os.path.join(TMP, "costlog.jsonl")
sys.path.insert(0, HERE)
import cost_meter, post_mortem  # noqa: E402


def call(mid, read, write1h, out, model="claude-opus-5-5", side=False, tools=()):
    return {"type": "assistant", "isSidechain": side, "timestamp": mid, "message": {
        "id": mid, "model": model, "content": [{"type": "tool_use", "name": n, "input": i} for n, i in tools],
        "usage": {"input_tokens": 0, "cache_read_input_tokens": read, "cache_creation_input_tokens": write1h,
                  "output_tokens": out, "cache_creation": {"ephemeral_1h_input_tokens": write1h}}}}


path = os.path.join(TMP, "sess.jsonl")
recs = [
    call("a1", 100_000, 10_000, 5),               # mid-stream record, superseded below
    call("a1", 100_000, 10_000, 500),             # last record for a1 wins
    call("a2", 400_000, 20_000, 1000, tools=[("Bash", {"command": 'until ! pgrep -f "vlog.py"; do sleep 30; done'}),
                                              ("WebFetch", {"url": "https://x/frames"})]),
    call("a3", 500_000, 0, 1000, tools=[("WebFetch", {"url": "https://x/frames"}),
                                        ("Bash", {"command": "cat > t.py <<'E'\nwhile x: sleep 99\nE"})]),
    {"type": "system", "subtype": "compact_boundary"},
]
with open(path, "w") as fh:
    fh.write("\n".join(json.dumps(r) for r in recs) + "\nnot json\n")
os.makedirs(os.path.join(TMP, "sess", "subagents"))
with open(os.path.join(TMP, "sess", "subagents", "agent-x.jsonl"), "w") as fh:
    fh.write(json.dumps(call("b1", 50_000, 50_000, 100, model="claude-sonnet-5-5")) + "\n")

r = cost_meter.meter(path)
lead = next(s for s in r["streams"] if s["name"] == "lead")
usd_lead = (1_000_000 * 0.20 + 30_000 * 8.0 + 2500 * 20.0) / 1e6
usd_agent = (50_000 * 0.20 + 50_000 * 4.0 + 100 * 10.0) / 1e6
CHECKS = [
    ("last usage record per message id", lead["calls"] == 3 and lead["tokens"]["output"] == 2500),
    ("lead dollars at Opus 5.5 rates, 1h writes", abs(lead["usd"] - round(usd_lead, 2)) < 0.006),
    ("subagent counted at Sonnet 5.5 rates", r["agents"] == 1 and abs(r["usd"] - round(usd_lead + usd_agent, 2)) < 0.011),
    ("context per call: max, median, now", (lead["ctx_max"], lead["ctx_median"], lead["ctx_now"]) == (500_000, 420_000, 500_000)),
    ("calls over 300k", lead["calls_over_300k"] == 2),
    ("compaction counted", r["compactions"] == 1),
    ("poll loop flagged, heredoc text not", sum("poll" in d for d in r["drains"]) == 1),
    ("same fetch twice flagged", any("2x WebFetch" in d for d in r["drains"])),
    ("cost share adds to ~100", 98 <= sum(r["cost_share_pct"].values()) <= 102),
    ("opus-5-5 not priced as opus-5", cost_meter.price("claude-opus-5-5")[2] == 0.20 and cost_meter.price("claude-opus-5")[2] == 0.50),
    ("card payload carries the cost line", "$" in cost_meter.card(r)["data"]["cost"]["line"]),
]
post_mortem.log_line(r, "test job", "wait loop ran long")
post_mortem.log_line(r, "test job", "logged twice")
rev = post_mortem.review(7)
CHECKS += [
    ("log keeps one line per session in the review", rev.count("test job") == 1 and "logged twice" in rev),
    ("review proposes the handoff rule", "hand off" in rev),
    ("review proposes the wait rule", "marker file" in rev),
]
WAITS = [   # (command, flagged?)
    ('until ! pgrep -f "vlog.py"; do sleep 30; done', True),                          # unbounded pgrep loop
    ('timeout 600 bash -c \'until ! pgrep -f render; do sleep 5; done\'', True),        # bounded, still pgrep
    ("sleep 120", True),                                                              # bare sleep check
    ("sleep 90 && tail -3 render.log", True),
    ("while true; do sleep 10; ls out/; done", True),                                 # no bound, no target
    ("timeout 900 bash -c 'while kill -0 4242; do sleep 10; done'", False),          # timeout + PID
    ("timeout -k 5 1800 bash -c 'until [ -f out/DONE ]; do sleep 15; done'", False),  # timeout + marker
    ("end=$((SECONDS+3600)); while [ ! -f render.done ] && [ $SECONDS -lt $end ]; do sleep 60; done", False),
    ("while kill -0 $pid 2>/dev/null && (( SECONDS < 1200 )); do sleep 20; done", False),
    ("while kill -0 $pid; do sleep 20; done", True),                                  # PID but no bound
    ("ffmpeg -i a.mp4 -t 10 b.mp4", False),                                           # not a wait at all
]
CHECKS += [(f"wait {'flagged' if want else 'allowed'}: {cmd[:60]}", cost_meter.is_poll(cmd) == want)
           for cmd, want in WAITS]
cli = subprocess.run([sys.executable, os.path.join(HERE, "cost_meter.py"), path], capture_output=True, text=True)
CHECKS.append(("CLI text runs", cli.returncode == 0 and "possible drains" in cli.stdout))

home = os.path.join(TMP, "home")                    # live_card finds the newest transcript under ~/.claude/projects
os.makedirs(os.path.join(home, ".claude", "projects", "x"))
with open(path) as src, open(os.path.join(home, ".claude", "projects", "x", "cardtest.jsonl"), "w") as dst:
    dst.write(src.read())
env = dict(os.environ, HOME=home)
lc = [sys.executable, os.path.join(HERE, "live_card.py")]
subprocess.run(lc + ["step", "midway"], capture_output=True, text=True, env=env, cwd=TMP)
done = subprocess.run(lc + ["done", "card test shipped"], capture_output=True, text=True, env=env, cwd=TMP)
logged = [json.loads(x) for x in open(os.environ["NQOS_COSTLOG"]) if '"cardtest"' in x]
CHECKS.append(("done logs the job once, step does not",
               done.returncode == 0 and len(logged) == 1 and logged[0]["job"] == "card test shipped"
               and "cost" in json.loads(done.stdout)["data"]))

bad = 0
for label, ok in CHECKS:
    bad += not ok
    print(("ok  " if ok else "FAIL") + "  " + label)
print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} passed")
sys.exit(1 if bad else 0)
