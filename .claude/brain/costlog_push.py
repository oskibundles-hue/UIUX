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
Written 2026-10-06 (approved by Omarie the same day). Since 2026-10-26 it also pushes nq-check's FAIL rows
(qualityfails.jsonl, the file next to the cost log) the same way, so the review sees them from every session.
Since 2026-10-27 it also pushes the job cards (brain/jobcards/*.json, job_card.py), which used to die with the
container, so job_diff and rule_gate have past jobs to compare against. A card is written once, so it goes up
only when main lacks it; cards a session saved to the git-ignored work/jobcards/ before the brain was attached
go up too. The pins (refs.json) and the replay set (replayset.json) go up only when this session changed them
(they differ from the clone's HEAD, from main and from the copy last pushed, kept in work/pushed/), so a stale
copy never overwrites another session's pin.
job_diff_hook.py runs this in the background after each nq-check, so cards don't wait for live_card.py done.
"""
import glob
import json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from post_mortem import FAILS, LOG
from nqos_config import WORK

PATH = "brain/costlog/costlog.jsonl"
FAILS_PATH = "brain/costlog/qualityfails.jsonl"
CARDS_PATH = "brain/jobcards"
STATE = ("refs.json", "replayset.json")       # job_diff's pins and rule_gate's replay set: state, not records
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
    """Cost lines are one per session and time; a FAIL row also needs its check, reason and agent."""
    return row.get("session"), row.get("at"), row.get("key"), row.get("why"), row.get("agent")


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


def push_to(repo, branch, base, new_rows, dry, path=PATH):
    """Commit the missing lines on top of `base` and push to `branch`. Returns (status, message)."""
    code, remote_text, _ = git(repo, "show", f"{base}:{path}")
    text, added = merged(remote_text if not code else "", new_rows)
    if not added:
        return "ok", f"up to date: {branch} has all {len(new_rows)} new line(s)"
    if dry:
        return "ok", f"would push {added} line(s) to {branch}"
    what = "session line(s)" if path == PATH else "nq-check FAIL row(s)"
    status, msg = commit_push(repo, branch, base, {path: text}, f"costlog: add {added} {WHERE} {what}")
    return status, msg.replace("pushed 1 line(s)", f"pushed {added} line(s)")


def card_files(repo):
    """{repo path: local file} for this session's cards and state files. CARDS is read here, not imported,
    so NQOS_JOBCARDS (tests) works the way job_card.py reads it."""
    cards = os.environ.get("NQOS_JOBCARDS") or os.path.join(repo, CARDS_PATH)
    out = {}
    for d in (os.path.join(WORK, "jobcards"), cards):                 # the clone's copy wins a name clash
        for f in glob.glob(os.path.join(d, "*.json")):
            out[f"{CARDS_PATH}/{os.path.basename(f)}"] = f
    return out


def last_pushed(name):
    """The copy of a state file this machine last pushed (the clone's HEAD never moves, so HEAD can't tell)."""
    try:
        return open(os.path.join(WORK, "pushed", name)).read()
    except OSError:
        return None


def cards_to_push(repo, base):
    """{repo path: text} that `base` is missing: new cards, and state files this session changed."""
    code, listing, _ = git(repo, "ls-tree", "--name-only", f"{base}:{CARDS_PATH}")
    have = set(listing.split()) if not code else set()
    out = {}
    for path, local in card_files(repo).items():
        name = os.path.basename(path)
        try:
            text = open(local).read()
            json.loads(text)                                         # a half-written card stays home
        except (OSError, ValueError):
            continue
        if name in STATE:
            hc, at_head, _ = git(repo, "show", f"HEAD:{path}")
            bc, at_base, _ = git(repo, "show", f"{base}:{path}")
            if text not in ((at_head if not hc else ""), (at_base if not bc else None), last_pushed(name)):
                out[path] = text
        elif name not in have:
            out[path] = text
    return out


def push_cards(repo, dry):
    """Push the cards main lacks to main (or the fallback branch), in one commit. Returns (code, message)."""
    for branch in ("main", FALLBACK):
        for _ in (1, 2):                                       # one retry when another push got there first
            exists, err = fetch(repo, branch)
            if err:
                status, msg = "fail", "fetch failed: " + err
                break
            base = f"origin/{branch}" if exists else "origin/main"
            files = cards_to_push(repo, base)
            if not files:
                return 0, f"up to date: {branch} has every card"
            if dry:
                return 0, f"would push {len(files)} card file(s) to {branch}"
            status, msg = commit_push(repo, branch, base, files, f"jobcards: add {len(files)} {WHERE} card file(s)")
            if status == "ok":
                os.makedirs(os.path.join(WORK, "pushed"), exist_ok=True)
                for path, text in files.items():
                    if os.path.basename(path) in STATE:
                        open(os.path.join(WORK, "pushed", os.path.basename(path)), "w").write(text)
            if status != "race":
                break
        if status == "ok":
            return 0, msg.replace("line(s)", "card file(s)")
        print(f"{branch}: {msg}", file=sys.stderr)
    return 1, "card push failed (see above); the cards are still on this machine"


def commit_push(repo, branch, base, files, message):
    """One commit of {path: text} on top of `base`, pushed to `branch`. Returns (status, message)."""
    with tempfile.TemporaryDirectory() as tmp:                 # a private index, so the clone's own is untouched
        env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
        code, _, err = git(repo, "read-tree", base, env=env)
        for path, text in files.items():
            if not code:
                code, blob, err = git(repo, "hash-object", "-w", "--stdin", stdin=text)
            if not code:
                code, _, err = git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob.strip()},{path}", env=env)
        if not code:
            code, tree, err = git(repo, "write-tree", env=env)
    if not code:
        code, commit, err = git(repo, "commit-tree", tree.strip(), "-p", base,
                                "-m", f"{message}\n\nFrom .claude/brain/costlog_push.py.")
    if code:
        return "fail", "commit failed: " + err.strip()[-200:]
    code, _, err = git(repo, "push", "-q", "origin", f"{commit.strip()}:refs/heads/{branch}")
    if code:
        return ("race" if "fetch first" in err or "non-fast-forward" in err else "refused"), err.strip()[-200:]
    return "ok", f"pushed {len(files)} line(s) to {branch} ({commit.strip()[:7]})"


def push_file(repo, local, path, dry):
    """Push one log's missing lines to main (or the fallback branch). Returns (code, message)."""
    _, on_main, _ = git(repo, "show", f"origin/main:{path}")
    local_rows = rows(open(local).read())
    have = {key(r) for r in rows(on_main)}
    new = [r for r in local_rows if key(r) not in have]       # lines main already has never go to the fallback
    if not new:
        return 0, f"up to date: main has all {len(local_rows)} lines"
    for branch in ("main", FALLBACK):
        for _ in (1, 2):                                       # one retry when another push got there first
            exists, err = fetch(repo, branch)
            status, msg = ("fail", "fetch failed: " + err) if err else \
                push_to(repo, branch, f"origin/{branch}" if exists else "origin/main", new, dry, path)
            if status != "race":
                break
        if status == "ok":
            return 0, msg
        print(f"{branch}: {msg}", file=sys.stderr)
    return 1, "cost log push failed (see above); the lines are still in " + local


def main(argv):
    if os.environ.get("NQOS_COSTLOG") or not os.path.isfile(LOG):
        return 0, "skipped: no shared cost log here"
    repo = clone_of(LOG)
    if not repo:
        return 0, "skipped: the cost log isn't in a clone of nq-agent-channel"
    exists, err = fetch(repo, "main")
    if not exists:
        return 1, "can't fetch nq-agent-channel main: " + (err or "no main branch")
    code, msg = push_file(repo, LOG, PATH, "--dry-run" in argv)
    if os.path.isfile(FAILS) and os.path.dirname(os.path.abspath(FAILS)) == os.path.dirname(os.path.abspath(LOG)):
        fcode, fmsg = push_file(repo, FAILS, FAILS_PATH, "--dry-run" in argv)
        code, msg = max(code, fcode), f"{msg}; quality fails: {fmsg}"
    ccode, cmsg = push_cards(repo, "--dry-run" in argv)
    return max(code, ccode), f"{msg}; job cards: {cmsg}"


if __name__ == "__main__":
    code, msg = main(sys.argv[1:])
    print(msg, file=sys.stderr if code else sys.stdout)
    sys.exit(code)
