#!/usr/bin/env python3
"""SessionStart hook (every session): bring this checkout up to the default branch.

Why (Omarie, 2026-10-06): the "One-way ticket" Part 2 session started 10 commits behind
origin/claude/new-session-mucc2q, so the 300k auto-compact setting and the nq-* agents never loaded and its
agents ran as general-purpose ones.

What it does: fetches the default branch (by explicit refspec, because some clones only track a few branches),
and if HEAD is behind it, is an ancestor of it (a fast-forward is possible) and has no tracked changes, runs
`git merge --ff-only`. Untracked files don't count as dirty; git itself refuses the merge if one would be
overwritten. Anything else (dirty, diverged, detached, offline, not a repo) leaves the checkout alone and, where
it matters, tells the session why.

Settings, hooks and CLAUDE.md are read before this hook runs, so when the fast-forward touched them the
session is told to restart to pick them up.

It also keeps the user-level copy of the system current (2026-10-27): the cloud installer stamps
/home/user/.nqos-system with the commit it came from, and when that is behind the default branch (or has no
stamp) this re-runs the installer. A session opened outside the repo loads only that copy, and one copy
predated the learning loop's hooks, so a real nq-check left no card and no FAIL rows.

Only acts when `origin` is oskibundles-hue/UIUX (the cloud installer runs it in every repo).
Never blocks a session: any error -> exit 0. Skip with NQ_SKIP_REFRESH=1.
Test: python3 .claude/hooks/test_session_refresh.py
"""
import json, os, subprocess, sys

DEFAULT_BRANCH = os.environ.get("NQ_DEFAULT_BRANCH", "claude/new-session-mucc2q")
REMOTE = "origin"
# The cloud installer runs this hook in every repo; only act on UIUX clones.
REPO_MATCH = os.environ.get("NQ_REFRESH_REMOTE_MATCH", "oskibundles-hue/uiux").lower()
SYSTEM = os.environ.get("NQOS_SYSTEM_DIR", "/home/user/.nqos-system")
UIUX_DIR = os.environ.get("NQ_UIUX_DIR", "/home/user/UIUX")
LOADED_AT_START = (".claude/settings.json", ".claude/hooks/", ".claude/agents/", "CLAUDE.md")


def git(cwd, *args, timeout=10):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip()


def refresh(cwd):
    """Return a note for the session, or None when there is nothing worth saying."""
    rc, _ = git(cwd, "rev-parse", "--is-inside-work-tree")
    if rc:
        return None
    rc, url = git(cwd, "remote", "get-url", REMOTE)
    if rc or REPO_MATCH not in url.lower():
        return None  # another repo: not ours to move
    rc, branch = git(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
    if rc:
        return None  # detached HEAD: leave it
    target = f"{REMOTE}/{DEFAULT_BRANCH}"
    rc, _ = git(cwd, "fetch", "-q", REMOTE, f"+refs/heads/{DEFAULT_BRANCH}:refs/remotes/{target}", timeout=20)
    if rc:
        return None  # offline or no such remote: say nothing, change nothing
    _, behind = git(cwd, "rev-list", "--count", f"HEAD..{target}")
    if behind in ("", "0"):
        return None
    rc, _ = git(cwd, "merge-base", "--is-ancestor", "HEAD", target)
    if rc:
        return (f"Checkout refresh: `{branch}` has its own commits and is {behind} behind {target}; not "
                f"fast-forwarded. Merge {target} in if this job needs the latest rules, agents or settings.")
    _, dirty = git(cwd, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        return (f"Checkout refresh: `{branch}` is {behind} commits behind {target} but has uncommitted changes, "
                f"so it was not updated. Commit or set them aside, then `git merge --ff-only {target}`.")
    _, old = git(cwd, "rev-parse", "HEAD")
    rc, _ = git(cwd, "merge", "--ff-only", "-q", target, timeout=30)
    if rc:
        return (f"Checkout refresh: `{branch}` is {behind} commits behind {target}; the fast-forward failed "
                f"(probably an untracked file in the way). Run `git merge --ff-only {target}` to see why.")
    _, changed = git(cwd, "diff", "--name-only", old, "HEAD")
    loaded = [f for f in changed.splitlines() if f.startswith(LOADED_AT_START)]
    note = f"Checkout refresh: fast-forwarded `{branch}` {behind} commits to {target}."
    if loaded:
        note += (" These were loaded before the update, so restart the session to use the new versions: "
                 + ", ".join(loaded[:8]) + (" …" if len(loaded) > 8 else "") + ".")
    return note


def system_note():
    """Re-run the installer when the user-level copy is behind the default branch; a note, or None."""
    if not os.path.isdir(SYSTEM):
        return None  # the installer isn't used on this machine
    try:
        stamp = json.load(open(os.path.join(SYSTEM, ".claude", "cloud", "installed.json")))
    except Exception:
        stamp = {}
    src = stamp.get("src") or UIUX_DIR
    if not os.path.isfile(os.path.join(src, ".claude", "cloud", "install.py")):
        return None
    rc, url = git(src, "remote", "get-url", REMOTE)
    if rc or REPO_MATCH not in url.lower():
        return None
    target = f"{REMOTE}/{DEFAULT_BRANCH}"
    rc, _ = git(src, "fetch", "-q", REMOTE, f"+refs/heads/{DEFAULT_BRANCH}:refs/remotes/{target}", timeout=20)
    rc2, sha = git(src, "rev-parse", target)
    if rc or rc2 or sha == stamp.get("sha"):
        return None  # offline, or already current
    r = subprocess.run([sys.executable, os.path.join(src, ".claude", "cloud", "install.py")],
                       capture_output=True, text=True, timeout=180, env={**os.environ, "NQOS_SYSTEM_DIR": SYSTEM})
    old = (stamp.get("sha") or "no stamp")[:7]
    if r.returncode:
        return (f"NQ OS system: the user-level copy ({old}) is behind {target} ({sha[:7]}) and the reinstall failed. "
                f"Run `python3 {src}/.claude/cloud/install.py` to see why.")
    return (f"NQ OS system: the user-level copy ({old}) was behind {target} ({sha[:7]}), so it was reinstalled. "
            "Hooks, agents and CLAUDE.md load at session start: restart the session to use the new versions.")


def main():
    if os.environ.get("NQ_SKIP_REFRESH") == "1":
        return
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    note = " ".join(n for n in (refresh(cwd), system_note()) if n)
    if note:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
