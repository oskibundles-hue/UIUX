#!/usr/bin/env python3
"""UserPromptSubmit + PreToolUse hook: inject a domain's standing rule when the prompt names the domain or Claude is
about to write a file in it. Idea taken from Basemode (github.com/ChristopherKahler/base, 2026-10-27): rules attach to
a domain and fire on match, and file-path rules fire before the tool runs, which recall_hook.py (prompt words only)
can't do. Rules live in .claude/domains.json. Each domain fires at most once per session, so it costs a line, not a
line per edit. Never blocks: any error -> prints nothing, exits 0.
Test: python3 .claude/hooks/test_domain_rules.py
"""
import fnmatch, json, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAINS = os.path.join(os.path.dirname(HERE), "domains.json")
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
STATE_DIR = os.environ.get("NQOS_DOMAIN_STATE", os.path.join(tempfile.gettempdir(), "nqos-domain-rules"))


def load():
    with open(DOMAINS, encoding="utf-8") as f:
        return json.load(f)["domains"]


def by_prompt(prompt, domains):
    low = prompt.lower()
    return [name for name, d in domains.items()
            if any(re.search(r"\b" + re.escape(k.lower()) + r"\b", low) for k in d.get("keywords", []))]


def by_path(path, domains, root):
    rel = os.path.relpath(os.path.abspath(path), root) if os.path.isabs(path) else path
    rel = rel.replace(os.sep, "/")
    return [name for name, d in domains.items()
            if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, g.rstrip("*").rstrip("/") + "/*")
                   for g in d.get("paths", []))]


def unseen(session, names):
    """Keep only domains not yet injected this session, and mark them seen."""
    if not names:
        return []
    os.makedirs(STATE_DIR, exist_ok=True)
    state = os.path.join(STATE_DIR, re.sub(r"[^A-Za-z0-9_-]", "_", session or "nosession") + ".json")
    try:
        seen = set(json.load(open(state)))
    except Exception:
        seen = set()
    new = [n for n in names if n not in seen]
    if new:
        json.dump(sorted(seen | set(new)), open(state, "w"))
    return new


def main():
    try:
        data = json.load(sys.stdin)
        event = data.get("hook_event_name", "")
        domains = load()
        root = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        if event == "UserPromptSubmit" or ("prompt" in data and not event):
            event, names = "UserPromptSubmit", by_prompt(data.get("prompt", "") or "", domains)
        elif data.get("tool_name") in WRITE_TOOLS:
            event = "PreToolUse"
            inp = data.get("tool_input") or {}
            names = by_path(inp.get("file_path") or inp.get("notebook_path") or "", domains, root)
        else:
            return
        names = unseen(data.get("session_id"), names)
        if not names:
            return
        text = "[domain rules, automatic] " + " ".join(f"{n}: {domains[n]['rule']}" for n in names)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))
    except Exception:
        pass


if __name__ == "__main__":
    main()
