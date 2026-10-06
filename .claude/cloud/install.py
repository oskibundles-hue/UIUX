#!/usr/bin/env python3
"""Put the NQ OS system in effect for every Claude Code session on this machine, whatever folder it opens in.

Omarie, 2026-10-06: "it should work in every session thats the point" and "yes build the installer so it
works every session". A repo's .claude/settings.json (the hooks, auto-compact at 300k, the agent limits) and
its agents only load when a session opens inside that repo, and a cloud session can open one folder up or on
an old checkout. So this installs the latest system at the user level, which Claude Code loads in every
session:

  1. Copies .claude/ and CLAUDE.md from the default branch (fetched fresh; falls back to this checkout) to
     /home/user/.nqos-system, next to nq-agent-channel, so the hooks find the notes.
  2. Merges into ~/.claude/settings.json the repo's env, deny rules and hooks. Each hook goes through
     run_hook.py, which skips a hook the session's own project settings already run, so nothing fires twice.
  3. Copies the NQ agents to ~/.claude/agents/.
  4. Adds an import of the system's CLAUDE.md to ~/.claude/CLAUDE.md.

Run it from the environment's setup script (the line is in .claude/cloud/README.md). Re-running is safe: it
replaces only what it installed before and leaves the rest of the user's settings alone.
Test without touching the real settings: HOME=<tmp> NQOS_SYSTEM_DIR=<tmp>/sys python3 install.py
"""
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile

BRANCH = os.environ.get("NQOS_BRANCH", "claude/new-session-mucc2q")
SRC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.environ.get("NQOS_SYSTEM_DIR", "/home/user/.nqos-system")
CLAUDE = os.path.join(os.path.expanduser("~"), ".claude")
RUNNER = os.path.join(DEST, ".claude", "cloud", "run_hook.py")
BEGIN, END = "<!-- nqos-system: begin -->", "<!-- nqos-system: end -->"


def log(msg):
    print(f"nqos install: {msg}", flush=True)


def fetch_tree():
    """The default branch's .claude/ and CLAUDE.md as a tar archive, or None to copy this checkout."""
    try:
        subprocess.run(["git", "-C", SRC, "fetch", "-q", "--depth", "1", "origin", BRANCH],
                       check=True, timeout=120, capture_output=True)
        out = subprocess.run(["git", "-C", SRC, "archive", "FETCH_HEAD", ".claude", "CLAUDE.md"],
                             check=True, timeout=60, capture_output=True).stdout
        sha = subprocess.run(["git", "-C", SRC, "rev-parse", "--short", "FETCH_HEAD"],
                             capture_output=True, text=True).stdout.strip()
        return out, f"{BRANCH} @ {sha}"
    except Exception as e:  # offline, no origin, not a git checkout
        log(f"fetch of {BRANCH} failed ({type(e).__name__}); installing from {SRC}")
        return None, SRC


def install_tree():
    data, where = fetch_tree()
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=".nqos-new-", dir=os.path.dirname(DEST))
    if data:
        tarfile.open(fileobj=io.BytesIO(data)).extractall(tmp, filter="data")
    else:
        shutil.copytree(os.path.join(SRC, ".claude"), os.path.join(tmp, ".claude"),
                        ignore=shutil.ignore_patterns("work", "__pycache__", "settings.local.json"))
        shutil.copy2(os.path.join(SRC, "CLAUDE.md"), tmp)
    if not os.path.isfile(os.path.join(tmp, ".claude", "cloud", "run_hook.py")):
        # The fetched branch predates this installer: run_hook.py must still be there for the hooks.
        os.makedirs(os.path.join(tmp, ".claude", "cloud"), exist_ok=True)
        shutil.copy2(os.path.join(SRC, ".claude", "cloud", "run_hook.py"), os.path.join(tmp, ".claude", "cloud"))
    keep = os.path.join(DEST, ".claude", "brain", "work")   # the note hook's prompt log survives a re-run
    if os.path.isdir(keep):
        shutil.copytree(keep, os.path.join(tmp, ".claude", "brain", "work"), dirs_exist_ok=True)
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.rename(tmp, DEST)
    log(f"system copied from {where} to {DEST}")


def strip_ours(hooks):
    """Drop the hook entries a previous install added (their command runs RUNNER)."""
    out = {}
    for event, groups in (hooks or {}).items():
        kept = []
        for g in groups:
            hs = [h for h in g.get("hooks", []) if RUNNER not in h.get("command", "")]
            if hs:
                kept.append({**g, "hooks": hs})
        if kept:
            out[event] = kept
    return out


def install_settings():
    repo = json.load(open(os.path.join(DEST, ".claude", "settings.json")))
    path = os.path.join(CLAUDE, "settings.json")
    user = json.load(open(path)) if os.path.isfile(path) else {}
    user.setdefault("env", {}).update(repo.get("env", {}))
    deny = user.setdefault("permissions", {}).setdefault("deny", [])
    deny += [d for d in repo.get("permissions", {}).get("deny", []) if d not in deny]
    hooks, n = strip_ours(user.get("hooks")), 0
    for event, groups in repo.get("hooks", {}).items():
        for g in groups:
            new = []
            for h in g.get("hooks", []):
                cmd = h.get("command", "")
                if '"$CLAUDE_PROJECT_DIR/' not in cmd:
                    continue
                rel = cmd.split('"$CLAUDE_PROJECT_DIR/', 1)[1].split('"', 1)[0]
                new.append({**h, "command": f'python3 "{RUNNER}" "{rel}"'})
            if new:
                hooks.setdefault(event, []).append({**g, "hooks": new})
                n += len(new)
    user["hooks"] = hooks
    os.makedirs(CLAUDE, exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(user, f, indent=2)
    os.replace(path + ".tmp", path)
    log(f"{path}: env {sorted(repo.get('env', {}))}, {n} hooks")


def install_agents():
    src, dst = os.path.join(DEST, ".claude", "agents"), os.path.join(CLAUDE, "agents")
    os.makedirs(dst, exist_ok=True)
    names = sorted(f for f in os.listdir(src) if f.endswith(".md"))
    for f in names:
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    log(f"{len(names)} agents in {dst}")


def install_claude_md():
    path = os.path.join(CLAUDE, "CLAUDE.md")
    text = open(path).read() if os.path.isfile(path) else ""
    if BEGIN in text and END in text:
        text = text[:text.index(BEGIN)] + text[text.index(END) + len(END):]
    block = (f"{BEGIN}\nOmarie's NQ OS rules, installed for every session by .claude/cloud/install.py "
             f"(the uiux repo's CLAUDE.md, branch {BRANCH}).\n@{DEST}/CLAUDE.md\n{END}\n")
    with open(path, "w") as f:
        f.write(text.rstrip() + ("\n\n" if text.strip() else "") + block)
    log(f"{path}: imports {DEST}/CLAUDE.md")


if __name__ == "__main__":
    install_tree()
    install_settings()
    install_agents()
    install_claude_md()
    log("done; sessions that start from now on load it")
