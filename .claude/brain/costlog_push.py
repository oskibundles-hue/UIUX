#!/usr/bin/env python3
"""Push this cloud session's cost log lines to nq-agent-channel main, so the weekly review sees them.

usage: python3 .claude/brain/costlog_push.py            push the lines main doesn't have yet
       python3 .claude/brain/costlog_push.py --dry-run  say what would be pushed, change nothing

`live_card.py done` runs it after logging the line (--no-sync skips it). post_mortem.py appends to the
attached brain clone (nq-agent-channel/brain/costlog/costlog.jsonl), which dies with the container
unless it is pushed. A line counts as there when its session and `at` match a line on main (same key
as the Mac's costlog_sync.py); new lines go on the end, tagged "where": "cloud". The commit is built
with git plumbing on top of origin/main, so the clone's working tree and other changes are never
touched. If main refuses the push, the lines go to branch claude/costlog-cloud instead, and the Mac's
costlog_sync.py merges that branch into main. Skipped when NQOS_COSTLOG is set (tests), or when the
log isn't brain/costlog/costlog.jsonl in a clone of nq-agent-channel. Running it twice changes nothing.
Written 2026-10-06 (approved by Omarie the same day).
"""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from post_mortem import LOG

PATH = "brain/costlog/costlog.jsonl"
FALLBACK = "claude/costlog-cloud"
WHERE = "cloud" if os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID") else "mac"


def git(repo, *args, stdin=None, env=None):
    r = subprocess.run(["git", "-C", repo, *args], input=stdin, capture_output=True, text=True,
                       env=dict(os.environ, **(env or {})), timeout=60)
    return r.returncode, r.stdout, r.stderr


def rows(text):
    out = []
    for raw in text.splitlines():
        try:
            out.append(json.loads(raw))
        except ValueError:
            pass
    return out


def key(row):
    return row.get("session"), row.get("at")


def clone_of(log):
    """The nq-agent-channel clone holding the log at brain/costlog/costlog.jsonl, or None."""
    code, top, _ = git(os.path.dirname(os.path.abspath(log)), "rev-parse", "--show-toplevel")
    if code:
        return None
    top = os.path.realpath(top.strip())
    _, url, _ = git(top, "remote", "get-url", "origin")
    if os.path.relpath(os.path.realpath(log), top) != PATH or "nq-agent-channel" not in url:
        return None
    return top


def fetch(repo, branch):
    """Refresh origin/<branch>, even in a single-branch clone. Returns (branch exists, error)."""
    code, _, err = git(repo, "fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}")
    if code and "couldn't find remote ref" in err:
        return False, ""
    return not code, err.strip()[-200:] if code else ""


def merged(remote_text, new_rows):
    """The remote file with the missing lines added, and how many were added."""
    have = {key(r) for r in rows(remote_text)}
    new = sorted((r for r in new_rows if key(r) not in have), key=lambda r: r.get("at", ""))
    if not new:
        return remote_text, 0
    text = remote_text if not remote_text or remote_text.endswith("\n") else remote_text + "\n"
    return text + "".join(json.dumps(dict(r, where=r.get("where", WHERE))) + "\n" for r in new), len(new)


def push_to(repo, branch, base, new_rows, dry):
    """Commit the missing lines on top of `base` and push to `branch`. Returns (status, message)."""
    code, remote_text, _ = git(repo, "show", f"{base}:{PATH}")
    text, added = merged(remote_text if not code else "", new_rows)
    if not added:
        return "ok", f"up to date: {branch} has all {len(new_rows)} new line(s)"
    if dry:
        return "ok", f"would push {added} line(s) to {branch}"
    with tempfile.TemporaryDirectory() as tmp:                 # a private index, so the clone's own is untouched
        env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
        code, blob, err = git(repo, "hash-object", "-w", "--stdin", stdin=text)
        if not code:
            code, _, err = git(repo, "read-tree", base, env=env)
        if not code:
            code, _, err = git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob.strip()},{PATH}", env=env)
        if not code:
            code, tree, err = git(repo, "write-tree", env=env)
    if not code:
        code, commit, err = git(repo, "commit-tree", tree.strip(), "-p", base,
                                "-m", f"costlog: add {added} {WHERE} session line(s)\n\nFrom .claude/brain/costlog_push.py.")
    if code:
        return "fail", "commit failed: " + err.strip()[-200:]
    code, _, err = git(repo, "push", "-q", "origin", f"{commit.strip()}:refs/heads/{branch}")
    if code:
        return ("race" if "fetch first" in err or "non-fast-forward" in err else "refused"), err.strip()[-200:]
    return "ok", f"pushed {added} line(s) to {branch} ({commit.strip()[:7]})"


def main(argv):
    if os.environ.get("NQOS_COSTLOG") or not os.path.isfile(LOG):
        return 0, "skipped: no shared cost log here"
    repo = clone_of(LOG)
    if not repo:
        return 0, "skipped: the cost log isn't in a clone of nq-agent-channel"
    exists, err = fetch(repo, "main")
    if not exists:
        return 1, "can't fetch nq-agent-channel main: " + (err or "no main branch")
    _, on_main, _ = git(repo, "show", f"origin/main:{PATH}")
    local_rows = rows(open(LOG).read())
    have = {key(r) for r in rows(on_main)}
    new = [r for r in local_rows if key(r) not in have]       # lines main already has never go to the fallback
    if not new:
        return 0, f"up to date: main has all {len(local_rows)} lines"
    dry = "--dry-run" in argv
    for branch in ("main", FALLBACK):
        for _ in (1, 2):                                       # one retry when another push got there first
            exists, err = fetch(repo, branch)
            status, msg = ("fail", "fetch failed: " + err) if err else \
                push_to(repo, branch, f"origin/{branch}" if exists else "origin/main", new, dry)
            if status != "race":
                break
        if status == "ok":
            return 0, msg
        print(f"{branch}: {msg}", file=sys.stderr)
    return 1, "cost log push failed (see above); the lines are still in " + LOG


if __name__ == "__main__":
    code, msg = main(sys.argv[1:])
    print(msg, file=sys.stderr if code else sys.stdout)
    sys.exit(code)
