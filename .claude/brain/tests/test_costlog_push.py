#!/usr/bin/env python3
"""Check costlog_push.py against a throwaway nq-agent-channel (a local bare repo; no network, a few seconds).

usage: python3 .claude/brain/tests/test_costlog_push.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.realpath(tempfile.mkdtemp(prefix="costlog-push-test-"))
ORIGIN = os.path.join(TMP, "nq-agent-channel.git")
CLONE = os.path.join(TMP, "clone", "nq-agent-channel")
LOG = os.path.join(CLONE, "brain", "costlog", "costlog.jsonl")
HOME = os.path.join(TMP, "home")
ENV = {k: v for k, v in os.environ.items() if k != "NQOS_COSTLOG"}
ENV.update(NQOS_HOME=os.path.join(CLONE, "brain"), HOME=HOME, CLAUDE_CODE_REMOTE_SESSION_ID="cse_test",
           GIT_AUTHOR_NAME="costlog test", GIT_AUTHOR_EMAIL="test@example.invalid",
           GIT_COMMITTER_NAME="costlog test", GIT_COMMITTER_EMAIL="test@example.invalid",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def sh(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env or ENV)


def line(session, at, **kw):
    return json.dumps(dict(at=at, session=session, job="j", usd=1.0, **kw)) + "\n"


def push(*args, env=None):
    p = sh(sys.executable, os.path.join(HERE, "costlog_push.py"), *args, env=env)
    return p.returncode, (p.stdout + p.stderr).strip()


def on(branch):
    p = sh("git", "-C", ORIGIN, "show", f"{branch}:brain/costlog/costlog.jsonl")
    return [json.loads(x) for x in p.stdout.splitlines()] if not p.returncode else None


def append(text):
    with open(LOG, "a") as fh:
        fh.write(text)


# origin: main holds the notes index and one Mac line; the cloud clone is single-branch, like a container's
seed = os.path.join(TMP, "seed")
os.makedirs(os.path.join(seed, "brain", "memory"))
os.makedirs(os.path.join(seed, "brain", "costlog"))
open(os.path.join(seed, "brain", "memory", "MEMORY.md"), "w").write("# test\n")
open(os.path.join(seed, "brain", "costlog", "costlog.jsonl"), "w").write(line("mac1", "2026-10-05T01:00:00Z", where="mac"))
sh("git", "init", "-q", "--bare", "-b", "main", ORIGIN)
sh("git", "init", "-q", "-b", "main", seed)
sh("git", "add", "-A", cwd=seed)
sh("git", "commit", "-qm", "seed", cwd=seed)
sh("git", "push", "-q", ORIGIN, "main", cwd=seed)
sh("git", "clone", "-q", "--single-branch", "-b", "main", ORIGIN, CLONE)
head = sh("git", "-C", CLONE, "rev-parse", "HEAD").stdout

append(line("cloud1", "2026-10-06T02:00:00Z") + line("cloud2", "2026-10-06T01:00:00Z"))
CHECKS = []
code, out = push("--dry-run")
CHECKS.append(("dry run says what it would push, pushes nothing", code == 0 and "would push 2" in out and len(on("main")) == 1))
code, out = push()
main = on("main")
CHECKS += [
    ("new lines reach main", code == 0 and "pushed 2 line(s) to main" in out and len(main) == 3),
    ("Mac line kept, new lines oldest first, tagged cloud",
     [(r["session"], r["where"]) for r in main] == [("mac1", "mac"), ("cloud2", "cloud"), ("cloud1", "cloud")]),
    ("clone's HEAD and working tree untouched", sh("git", "-C", CLONE, "rev-parse", "HEAD").stdout == head
     and sh("git", "-C", CLONE, "status", "--porcelain").stdout.strip() == "M brain/costlog/costlog.jsonl"),
]
code, out = push()
CHECKS.append(("running it twice changes nothing", code == 0 and "up to date" in out and len(on("main")) == 3))

# main moves on (a Mac sync) after the container cloned it: the push lands on top, nothing lost
other = os.path.join(TMP, "other")
sh("git", "clone", "-q", ORIGIN, other)
with open(os.path.join(other, "brain", "costlog", "costlog.jsonl"), "a") as fh:
    fh.write(line("mac2", "2026-10-06T03:00:00Z", where="mac"))
sh("git", "commit", "-qam", "mac sync", cwd=other)
sh("git", "push", "-q", "origin", "main", cwd=other)
append(line("cloud3", "2026-10-06T04:00:00Z"))
code, out = push()
CHECKS.append(("stale clone: fetches first, keeps the Mac's newer line",
               code == 0 and [r["session"] for r in on("main")] == ["mac1", "cloud2", "cloud1", "mac2", "cloud3"]))

# main refuses pushes: lines go to claude/costlog-cloud, never main's lines, and main is untouched
hook = os.path.join(ORIGIN, "hooks", "pre-receive")
open(hook, "w").write('#!/bin/sh\nwhile read o n r; do [ "$r" = refs/heads/main ] && echo "GH006: protected" >&2 && exit 1; done\nexit 0\n')
os.chmod(hook, 0o755)
append(line("cloud4", "2026-10-06T05:00:00Z"))
code, out = push()
fb = on("claude/costlog-cloud")
CHECKS += [
    ("main refused: line goes to the fallback branch", code == 0 and "to claude/costlog-cloud" in out and "main: " in out
     and fb is not None and fb[-1]["session"] == "cloud4" and len(on("main")) == 5),
    ("fallback holds main's file plus only the new line", [r["session"] for r in fb] == ["mac1", "cloud2", "cloud1", "mac2", "cloud3", "cloud4"]),
]
code, out = push()
CHECKS.append(("fallback twice changes nothing", code == 0 and "up to date: claude/costlog-cloud" in out
               and len(on("claude/costlog-cloud")) == 6))
append(line("cloud5", "2026-10-06T06:00:00Z"))
code, out = push()
CHECKS.append(("next line stacks on the fallback branch", code == 0 and
               [r["session"] for r in on("claude/costlog-cloud")][-2:] == ["cloud4", "cloud5"]))
open(hook, "w").write("#!/bin/sh\nexit 1\n")
append(line("cloud6", "2026-10-06T07:00:00Z"))
code, out = push()
CHECKS.append(("both refused: exit 1, says the lines are still local", code == 1 and "still in" in out))
os.remove(hook)

# skips: tests' NQOS_COSTLOG, and a brain that isn't an nq-agent-channel clone
code, out = push(env=dict(ENV, NQOS_COSTLOG=os.path.join(TMP, "x.jsonl")))
CHECKS.append(("NQOS_COSTLOG set: skipped", code == 0 and out.startswith("skipped")))
stranger = os.path.join(TMP, "clone2", "someother")
sh("git", "clone", "-q", ORIGIN, stranger)
sh("git", "-C", stranger, "remote", "set-url", "origin", os.path.join(TMP, "someother.git"))
code, out = push(env=dict(ENV, NQOS_HOME=os.path.join(stranger, "brain")))
CHECKS.append(("log in some other repo: skipped", code == 0 and "isn't in a clone of nq-agent-channel" in out))

# live_card done pushes the session's line; --no-sync logs it without pushing
os.makedirs(os.path.join(HOME, ".claude", "projects", "x"))
rec = {"type": "assistant", "timestamp": "t", "message": {"id": "m1", "model": "claude-opus-5-5", "content": [],
       "usage": {"input_tokens": 0, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 0, "output_tokens": 10}}}
for sid in ("cardpush", "cardnosync"):
    with open(os.path.join(HOME, ".claude", "projects", "x", sid + ".jsonl"), "w") as fh:
        fh.write(json.dumps(rec) + "\n")
    os.utime(fh.name)
    flag = ["--no-sync"] if sid == "cardnosync" else []
    card = sh(sys.executable, os.path.join(HERE, "live_card.py"), "done", "shipped " + sid, *flag, cwd=TMP)
    sessions = [r["session"] for r in on("main")]
    local = [json.loads(x)["session"] for x in open(LOG)]
    CHECKS.append((f"live_card done {' '.join(flag) or '(default)'}: card printed, line logged, "
                   + ("not pushed" if flag else "pushed"),
                   card.returncode == 0 and json.loads(card.stdout)["data"]["status"] == "done" and sid in local
                   and (sid in sessions) != bool(flag) and ("cost log push:" in card.stderr) != bool(flag)))

bad = 0
for label, ok in CHECKS:
    bad += not ok
    print(("ok  " if ok else "FAIL") + "  " + label)
print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} passed")
sys.exit(1 if bad else 0)
