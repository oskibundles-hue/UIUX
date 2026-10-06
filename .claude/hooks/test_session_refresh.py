#!/usr/bin/env python3
"""Check session_refresh.py on throwaway repos: clean, dirty, diverged, up to date, offline (no network, ~2 s).

usage: python3 .claude/hooks/test_session_refresh.py
"""
import json, os, subprocess, sys, tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_refresh.py")
BRANCH = "claude/new-session-mucc2q"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "NQ_DEFAULT_BRANCH": BRANCH,
       "NQ_REFRESH_REMOTE_MATCH": "origin.git"}
ENV.pop("NQ_SKIP_REFRESH", None)


def sh(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=ENV, check=True).stdout.strip()


def commit(repo, name, text="x"):
    with open(os.path.join(repo, name), "w") as f:
        f.write(text)
    sh(repo, "add", name)
    sh(repo, "commit", "-q", "-m", name)


def setup(tmp):
    """origin (bare) <- upstream (pushes new commits); clone = the session's checkout, 2 commits behind."""
    origin, up, clone = (os.path.join(tmp, n) for n in ("origin.git", "up", "clone"))
    subprocess.run(["git", "init", "-q", "--bare", origin], check=True)
    subprocess.run(["git", "init", "-q", "-b", BRANCH, up], check=True)
    commit(up, "README")
    sh(up, "remote", "add", "origin", origin)
    sh(up, "push", "-q", "origin", BRANCH)
    # A narrow fetch refspec, like Omarie's main clone: a plain fetch would not see BRANCH.
    subprocess.run(["git", "clone", "-q", "-b", BRANCH, origin, clone], check=True, env=ENV)
    sh(clone, "config", "remote.origin.fetch", "+refs/heads/other:refs/remotes/origin/other")
    commit(up, "CLAUDE.md", "new rules")
    commit(up, "notes.txt")
    sh(up, "push", "-q", "origin", BRANCH)
    return clone


def run(cwd):
    env = {**ENV, "CLAUDE_PROJECT_DIR": cwd}
    out = subprocess.run([sys.executable, HOOK], input=json.dumps({"source": "startup"}), capture_output=True,
                         text=True, env=env, timeout=60)
    note = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"] if out.stdout.strip() else ""
    return out.returncode, note


def case_clean(clone):
    head = sh(clone, "rev-parse", "HEAD")
    rc, note = run(clone)
    assert rc == 0 and sh(clone, "rev-parse", "HEAD") != head, note
    assert sh(clone, "rev-list", "--count", f"HEAD..origin/{BRANCH}") == "0"
    assert "fast-forwarded" in note and "2 commits" in note and "CLAUDE.md" in note and "restart" in note, note
    rc, note = run(clone)  # second start: up to date, silent
    assert rc == 0 and note == "", note


def case_dirty(clone):
    head = sh(clone, "rev-parse", "HEAD")
    with open(os.path.join(clone, "README"), "w") as f:
        f.write("work in progress")
    rc, note = run(clone)
    assert rc == 0 and sh(clone, "rev-parse", "HEAD") == head, "dirty tree was moved"
    assert open(os.path.join(clone, "README")).read() == "work in progress", "edit lost"
    assert "uncommitted changes" in note and "not updated" in note, note


def case_untracked_only(clone):
    with open(os.path.join(clone, "scratch.log"), "w") as f:
        f.write("untracked")
    rc, note = run(clone)
    assert rc == 0 and "fast-forwarded" in note, note
    assert os.path.exists(os.path.join(clone, "scratch.log"))


def case_diverged(clone):
    commit(clone, "mine.txt")
    head = sh(clone, "rev-parse", "HEAD")
    rc, note = run(clone)
    assert rc == 0 and sh(clone, "rev-parse", "HEAD") == head, "diverged branch was moved"
    assert "own commits" in note, note


def case_offline(clone):
    sh(clone, "remote", "set-url", "origin", "/nonexistent/repo.git")
    head = sh(clone, "rev-parse", "HEAD")
    rc, note = run(clone)
    assert rc == 0 and note == "" and sh(clone, "rev-parse", "HEAD") == head, note


def case_other_repo(clone):
    head = sh(clone, "rev-parse", "HEAD")
    env_match = ENV["NQ_REFRESH_REMOTE_MATCH"]
    ENV["NQ_REFRESH_REMOTE_MATCH"] = "oskibundles-hue/uiux"   # the real default; origin here is a temp path
    try:
        rc, note = run(clone)
    finally:
        ENV["NQ_REFRESH_REMOTE_MATCH"] = env_match
    assert rc == 0 and note == "" and sh(clone, "rev-parse", "HEAD") == head, note


def case_not_a_repo(tmp):
    rc, note = run(tmp)
    assert rc == 0 and note == "", note


CASES = [("clean, 2 behind -> fast-forward, then silent", case_clean),
         ("tracked edit -> left alone, told why", case_dirty),
         ("untracked file only -> fast-forward", case_untracked_only),
         ("own commits -> left alone, told why", case_diverged),
         ("remote unreachable -> silent, unchanged", case_offline),
         ("origin is another repo -> silent, unchanged", case_other_repo)]

if __name__ == "__main__":
    failed = 0
    for label, fn in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                fn(setup(tmp))
                print(f"ok    {label}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL  {label}: {e}")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            case_not_a_repo(tmp)
            print("ok    not a git repo -> silent")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  not a git repo: {e}")
    print(f"{len(CASES) + 1 - failed}/{len(CASES) + 1} passed")
    sys.exit(1 if failed else 0)
