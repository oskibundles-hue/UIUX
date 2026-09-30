#!/usr/bin/env python3
"""PreToolUse gate for the regret list: spend, publish, destroy, push to a default branch.

Reads the hook payload on stdin. Prints a permission decision for gated calls and
nothing for everything else. Fails closed: if the payload can't be read, it asks.
Tests: python3 .claude/hooks/test_regret_gate.py
"""
import json
import os
import re
import shlex
import subprocess
import sys

# Branches that only change through a PR. UIUX's default branch is claude/new-session-mucc2q (it has
# no main); nq-agent-channel's is main. The clone's own origin/HEAD is added when git knows it.
PROTECTED = {"main", "master", "claude/new-session-mucc2q"}

HIGGSFIELD_PAID = re.compile(
    r"^(generate_\w+|execute_preset|upscale_\w+|outpaint_image|reframe|remove_background|"
    r"motion_control|voice_change|dubbing|create_voice|shorts_studio_create|"
    r"virality_predictor|tiktok_music_tune|cancel_trial_auto_renewal)$"
)
PUBLISH = {
    "Higgsfield": {"tiktok_prepare_publish", "publish_website", "deploy_website"},
    "vidIQ": {"vidiq_update_video_thumbnail"},
    "Windsor_ai": {"execute_action"},
}
DROPBOX_DESTRUCTIVE = {"move", "delete"}
MEMORY_WRITE = re.compile(r"^(remember|update_memory|archive_memory|approve_constraint|forget\w*|delete\w*)$")
GITHUB_BRANCH_WRITE = {"push_files", "create_or_update_file", "delete_file"}
GITHUB_MERGE = {"merge_pull_request", "enable_pr_auto_merge"}

# Commands that run the command after them (sudo rm ..., env X=1 git push ..., xargs rm ...), each with
# its own options that take a value, so the value isn't read as the command. Per wrapper, because a
# flag that takes a value for one (env -u) takes none for another (env -i), and treating it as if it
# did would swallow the real command.
WRAPPER_ARGS = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U"}, "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S"}, "nice": {"-n"}, "timeout": {"-s", "-k"}, "stdbuf": {"-i", "-o", "-e"},
    "xargs": {"-a", "-d", "-E", "-I", "-L", "-n", "-P", "-s"},
    "nohup": set(), "time": set(), "command": set(), "exec": set(), "builtin": set(),
}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
PUSH_OPTS_WITH_VALUE = {"-o", "--push-option", "--receive-pack", "--exec", "--repo"}


def decide(kind, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": kind,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def git_out(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        return ""


def protected(cwd):
    head = git_out(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return PROTECTED | ({head.split("/", 1)[1]} if "/" in head else set())


def current_branches(cwd):
    """The branch a bare `git push` would update: the checked-out branch and its upstream."""
    out = {git_out(cwd, "symbolic-ref", "--short", "HEAD")}
    up = git_out(cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if "/" in up:
        out.add(up.split("/", 1)[1])
    return out - {""}


def check_mcp(tool, args, cwd):
    _, server, name = tool.split("__", 2)
    if server == "Higgsfield" and HIGGSFIELD_PAID.match(name):
        decide("ask", f"Regret list: paid Higgsfield call ({name}). Quote the per-render cost "
                      "(get_cost where the model supports it, else the preset price) and confirm the "
                      "target beat against a contact sheet before approving. Balance is checked in the app.")
    if name in PUBLISH.get(server, set()):
        decide("ask", f"Regret list: {server}.{name} publishes or changes a live account. "
                      "Authority to publish is not approval of this item; confirm per action.")
    if server == "Dropbox" and name in DROPBOX_DESTRUCTIVE:
        decide("ask", f"Regret list: Dropbox {name}. Standing rule: ask before any move, rename or delete.")
    if server == "Vertiso_Memory" and MEMORY_WRITE.match(name):
        decide("ask", "Memory writes happen at end of day, listed first and approved. "
                      "Until 1 October the store is full; CLAUDE.md is the memory.")
    if server == "github":
        if name in GITHUB_BRANCH_WRITE:
            # With no branch, GitHub writes to the repo's default branch.
            branch = re.sub(r"^refs/heads/", "", str(args.get("branch") or ""))
            if not branch or branch in protected(cwd):
                decide("deny", f"{branch or 'The default branch'} only changes through a PR. "
                               "Write to a work branch and open one.")
        if name in GITHUB_MERGE:
            decide("ask", f"Merging lands the PR on its base branch ({name}). Confirm this one.")


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1.*?\n.*?\n\s*\2\b", re.S)


def split_commands(cmd):
    cmd = HEREDOC.sub(" ", cmd)
    return [c for c in re.split(r"&&|\|\||;|\n|\||\$\(|`", cmd) if c.strip()]


def resolve(path, cwd):
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))


def in_tmp(path, cwd):
    if re.match(r"^\$\{?TMPDIR\}?(/|$)", path):
        return True
    return re.match(r"^/(private/)?(var/)?tmp/.", resolve(path, cwd)) is not None


def unwrap(words):
    """Drop env assignments and wrappers (sudo, env, xargs, timeout ...) in front of the real command."""
    via_xargs = False
    while words:
        if re.match(r"^\w+=", words[0]):
            words = words[1:]
            continue
        if words[0] not in WRAPPER_ARGS:
            break
        via_xargs |= words[0] == "xargs"
        wrapper, words = words[0], words[1:]
        while words and words[0].startswith("-"):
            flag, words = words[0], words[1:]
            if flag in WRAPPER_ARGS[wrapper] and words:
                words = words[1:]
        if wrapper in ("timeout", "nice") and words and re.match(r"^-?[\d.]+[smhd]?$", words[0]):
            words = words[1:]
    return words, via_xargs


def check_push(rest, gdir):
    if any(f in ("--all", "--mirror", "--branches") for f in rest):
        decide("ask", "git push --all or --mirror can push the default branch too. Confirm this one.")
    pos, i, repo_flag = [], 0, False
    while i < len(rest):
        w = rest[i]
        if w in PUSH_OPTS_WITH_VALUE:
            repo_flag |= w == "--repo"
            i += 2
            continue
        repo_flag |= w.startswith("--repo=")
        if not w.startswith("-"):
            pos.append(w)
        i += 1
    specs = pos if repo_flag else pos[1:]
    targets = set()
    for spec in specs:
        dst = re.sub(r"^refs/heads/", "", spec.lstrip("+").split(":")[-1])
        targets |= current_branches(gdir) if dst in ("HEAD", "@") else {dst}
    if not specs and "--tags" not in rest:
        targets |= current_branches(gdir)
    hit = sorted(targets & protected(gdir))
    if hit:
        decide("deny", f"Never push to {hit[0]} directly: it only changes through a PR. "
                       "Push a work branch and open one.")
    if any(f in ("-f", "--force") or f.startswith("--force") for f in rest) or any(s.startswith("+") for s in specs):
        decide("ask", "Force push rewrites shared history. Confirm this one.")


def check_git(words, cwd):
    i, gdir = 1, cwd
    while i < len(words) and words[i].startswith("-"):
        if words[i] == "-C" and i + 1 < len(words):
            gdir = resolve(words[i + 1], gdir)
        i += 2 if words[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(words):
        return
    sub, rest = words[i], words[i + 1:]
    if sub == "push":
        check_push(rest, gdir)
    if sub == "reset" and "--hard" in rest:
        decide("ask", "git reset --hard discards work. Stash first, or confirm.")
    if sub == "clean" and any(re.match(r"^-\w*f", w) for w in rest):
        decide("ask", "git clean -f deletes untracked files. Archive, never delete.")
    if sub in ("checkout", "restore") and "." in rest:
        decide("ask", f"git {sub} . discards uncommitted changes. Stash first, or confirm.")


def check_bash(cmd, cwd):
    for part in split_commands(cmd):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        # subshells and groups: (cd x && ...), { ...; }
        words = [w.strip("()") for w in words if w not in ("{", "}")]
        words = [w for w in words if w]
        words, via_xargs = unwrap(words)
        if not words:
            continue
        cmd0 = os.path.basename(words[0])
        if cmd0 == "cd":
            cwd = resolve(words[1] if len(words) > 1 else "~", cwd)
            continue
        if cmd0 in SHELLS:
            c = next((j for j, w in enumerate(words[1:], 1) if re.match(r"^-[a-z]*c[a-z]*$", w)), None)
            if c is not None and c + 1 < len(words):
                check_bash(words[c + 1], cwd)
            continue
        if cmd0 == "eval":
            check_bash(" ".join(words[1:]), cwd)
            continue
        if cmd0 == "git":
            check_git(words, cwd)
        if cmd0 == "rm":
            flags = [w for w in words[1:] if w.startswith("-")]
            paths = [w for w in words[1:] if not w.startswith("-")]
            recursive = any(("r" in f.lstrip("-").lower() and not f.startswith("--")) or f == "--recursive"
                            for f in flags)
            if recursive and (via_xargs or any(not in_tmp(p, cwd) for p in paths)):
                decide("ask", "Recursive delete outside /tmp. Standing rule: archive, never delete.")
        if cmd0 == "find":
            args = words[1:]
            while args and args[0] in ("-H", "-L", "-P"):
                args = args[1:]
            paths = []
            for w in args:
                if w.startswith("-") or w in ("!", "("):
                    break
                paths.append(w)
            deletes = "-delete" in args or any(
                a in ("-exec", "-execdir", "-ok", "-okdir") and j + 1 < len(args)
                and os.path.basename(args[j + 1]) == "rm" for j, a in enumerate(args))
            if deletes and any(not in_tmp(p, cwd) for p in (paths or ["."])):
                decide("ask", "find that deletes, outside /tmp. Standing rule: archive, never delete.")


def main():
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name", "")
        args = payload.get("tool_input") or {}
        cwd = payload.get("cwd") or os.getcwd()
    except Exception as e:  # noqa: BLE001
        decide("ask", f"regret_gate could not read the hook payload ({e}); asking instead of guessing.")
    if tool == "Bash":
        check_bash(args.get("command", ""), cwd)
    elif tool.startswith("mcp__"):
        check_mcp(tool, args, cwd)


if __name__ == "__main__":
    main()
