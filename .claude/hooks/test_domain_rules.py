#!/usr/bin/env python3
"""Check domain_rules.py against inputs with known answers (no model, under 1 s).

usage: python3 .claude/hooks/test_domain_rules.py
"""
import json, os, subprocess, sys, tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domain_rules.py")
ROOT = "/repo"


def prompt(text, sid):
    return {"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": text, "cwd": ROOT}


def tool(name, path, sid):
    return {"hook_event_name": "PreToolUse", "session_id": sid, "tool_name": name,
            "tool_input": {"file_path": path}, "cwd": ROOT}


# (label, input, domains expected in the output; [] means silent)
CASES = [
    ("prompt names the kit", prompt("add a new palette to ui-ux-pro-max", "a"), ["antigravity-kit"]),
    ("same domain again, same session", prompt("and run search.py on it", "a"), []),
    ("edit in kit source, other session", tool("Edit", "/repo/src/ui-ux-pro-max/data/colors.csv", "b"), ["antigravity-kit"]),
    ("relative path into hooks", tool("Write", ".claude/hooks/new_hook.py", "c"), ["nqos-hooks"]),
    ("settings.json", tool("Edit", "/repo/.claude/settings.json", "d"), ["nqos-hooks"]),
    ("read-only tool is ignored", tool("Read", "/repo/src/ui-ux-pro-max/x.py", "e"), []),
    ("unrelated file", tool("Edit", "/repo/README.md", "f"), []),
    ("brand keyword", prompt("make a Formula Dynamics carousel for the RYFT exhaust", "g"), ["formula-dynamics"]),
    ("no keyword", prompt("show me the video", "h"), []),
    ("word boundary: 'hooked' is not 'hook'", prompt("I'm hooked on this reel", "i"), []),
    ("two domains at once", prompt("does the regret gate block antigravity publishes", "j"), ["antigravity-kit", "nqos-hooks"]),
]


def run(payload, env):
    out = subprocess.run([sys.executable, HOOK], input=json.dumps(payload), capture_output=True, text=True,
                         timeout=10, env=env).stdout.strip()
    if not out:
        return []
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    import re
    return sorted(set(re.findall(r"([a-z-]+): ", ctx.replace("[domain rules, automatic] ", ""))) &
                  {"antigravity-kit", "nqos-hooks", "nqos-agents", "formula-dynamics", "supercar-experience", "anti-stock"})


def main():
    env = dict(os.environ, NQOS_DOMAIN_STATE=tempfile.mkdtemp(prefix="domtest-"))
    fails = 0
    for label, payload, want in CASES:
        got = run(payload, env)
        ok = got == sorted(want)
        fails += not ok
        print(("PASS" if ok else "FAIL"), label, "" if ok else f"(want {want}, got {got})")
    bad = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=10, env=env)
    ok = bad.returncode == 0 and not bad.stdout.strip()
    fails += not ok
    print(("PASS" if ok else "FAIL"), "bad input stays silent")
    print(f"{len(CASES) + 1 - fails}/{len(CASES) + 1} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
