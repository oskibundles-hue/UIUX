#!/usr/bin/env python3
"""Run install.py against a scratch home folder and check what it leaves; never touches the real settings.

python3 .claude/cloud/test_install.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


with tempfile.TemporaryDirectory() as tmp:
    home, sysdir = os.path.join(tmp, "home"), os.path.join(tmp, "user", ".nqos-system")
    os.makedirs(os.path.join(home, ".claude"))
    # The user already has a setting and a hook of their own: both must survive.
    json.dump({"model": "keep-me", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo mine"}]}]}},
              open(os.path.join(home, ".claude", "settings.json"), "w"))
    env = {**os.environ, "HOME": home, "NQOS_SYSTEM_DIR": sysdir, "NQOS_BRANCH": "no-such-branch-offline-test"}
    for run in (1, 2):                                   # twice: re-running must not duplicate anything
        r = subprocess.run([sys.executable, os.path.join(HERE, "install.py")], env=env, capture_output=True, text=True)
        check(f"run {run} exits 0", r.returncode == 0)
    s = json.load(open(os.path.join(home, ".claude", "settings.json")))
    repo = json.load(open(os.path.join(REPO, ".claude", "settings.json")))
    check("user's own setting kept", s.get("model") == "keep-me")
    check("user's own hook kept", any(h["command"] == "echo mine" for g in s["hooks"]["Stop"] for h in g["hooks"]))
    check("repo env installed", all(s["env"].get(k) == v for k, v in repo["env"].items()))
    check("deny rules installed", all(d in s["permissions"]["deny"] for d in repo["permissions"]["deny"]))
    want = sum(1 for gs in repo["hooks"].values() for g in gs for h in g["hooks"])
    got = [h["command"] for gs in s["hooks"].values() for g in gs for h in g["hooks"] if "run_hook.py" in h["command"]]
    check(f"every repo hook installed once ({want})", len(got) == want)
    check("no hook left on $CLAUDE_PROJECT_DIR", not any("CLAUDE_PROJECT_DIR" in c for c in got))
    check("installed hook files exist",
          all(os.path.isfile(os.path.join(sysdir, c.rsplit('"', 2)[-2])) for c in got))
    agents = os.listdir(os.path.join(home, ".claude", "agents"))
    check("agents installed", sorted(agents) == sorted(os.listdir(os.path.join(REPO, ".claude", "agents"))))
    md = open(os.path.join(home, ".claude", "CLAUDE.md")).read()
    check("CLAUDE.md imports the system once", md.count(f"@{sysdir}/CLAUDE.md") == 1)

    # run_hook.py: outside the repo it runs the hook; inside the repo it steps aside for the project's copy.
    runner = os.path.join(sysdir, ".claude", "cloud", "run_hook.py")
    probe = os.path.join(sysdir, ".claude", "hooks", "probe_hook.py")
    open(probe, "w").write("import sys; d=sys.stdin.read(); print('ran:' + d)\n")
    out = subprocess.run([sys.executable, runner, ".claude/hooks/probe_hook.py"], input="x", capture_output=True,
                         text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": tmp}).stdout
    check("runner runs the hook outside the repo, stdin passed", out.strip() == "ran:x")
    proj = os.path.join(tmp, "proj")
    os.makedirs(os.path.join(proj, ".claude", "hooks"))
    open(os.path.join(proj, ".claude", "settings.json"), "w").write("{}")
    open(os.path.join(proj, ".claude", "hooks", "probe_hook.py"), "w").write("")
    r = subprocess.run([sys.executable, runner, ".claude/hooks/probe_hook.py"], input="x", capture_output=True,
                       text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": proj})
    check("runner skips when the project runs the same hook", r.returncode == 0 and r.stdout == "")

print(f"{'FAILED' if fails else 'passed'}: {len(fails)} failing")
sys.exit(1 if fails else 0)
