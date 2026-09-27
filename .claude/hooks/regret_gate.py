#!/usr/bin/env python3
"""PreToolUse gate for the regret list: spend, publish, destroy, push to main.

Reads the hook payload on stdin. Prints a permission decision for gated calls and
nothing for everything else. Fails closed: if the payload can't be read, it asks.
"""
import json
import re
import shlex
import sys

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


def decide(kind, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": kind,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def check_mcp(tool, args):
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


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1.*?\n.*?\n\s*\2\b", re.S)


def split_commands(cmd):
    cmd = HEREDOC.sub(" ", cmd)
    return [c for c in re.split(r"&&|\|\||;|\n|\|", cmd) if c.strip()]


def check_bash(cmd):
    for part in split_commands(cmd):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        while words and re.match(r"^\w+=", words[0]):
            words = words[1:]
        if not words:
            continue
        if words[0] == "git" and len(words) > 1:
            sub = words[1]
            rest = words[2:]
            if sub == "push":
                refs = [w for w in rest if not w.startswith("-")]
                targets = [r.split(":")[-1].lstrip("+") for r in refs[1:]]
                if any(t in ("main", "master", "refs/heads/main", "refs/heads/master") for t in targets):
                    decide("deny", "Never push to main. Push the workstream's own branch.")
                if any(f in ("-f", "--force", "--force-with-lease") or f.startswith("--force") for f in rest) \
                        or any(r.startswith("+") for r in refs[1:]):
                    decide("ask", "Force push rewrites shared history. Confirm this one.")
            if sub == "reset" and "--hard" in rest:
                decide("ask", "git reset --hard discards work. Stash first, or confirm.")
            if sub == "clean" and any(re.match(r"^-\w*f", w) for w in rest):
                decide("ask", "git clean -f deletes untracked files. Archive, never delete.")
            if sub in ("checkout", "restore") and "." in rest:
                decide("ask", f"git {sub} . discards uncommitted changes. Stash first, or confirm.")
        if words[0] == "rm":
            flags = [w for w in words[1:] if w.startswith("-")]
            paths = [w for w in words[1:] if not w.startswith("-")]
            recursive = any(("r" in f.lstrip("-").lower() and not f.startswith("--")) or f == "--recursive"
                            for f in flags)
            outside_tmp = [p for p in paths if not re.match(r"^(/tmp/|\$TMPDIR|/var/tmp/)", p)]
            if recursive and outside_tmp:
                decide("ask", "Recursive delete outside /tmp. Standing rule: archive, never delete.")


def main():
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name", "")
        args = payload.get("tool_input") or {}
    except Exception as e:  # noqa: BLE001
        decide("ask", f"regret_gate could not read the hook payload ({e}); asking instead of guessing.")
    if tool == "Bash":
        check_bash(args.get("command", ""))
    elif tool.startswith("mcp__"):
        check_mcp(tool, args)


if __name__ == "__main__":
    main()
