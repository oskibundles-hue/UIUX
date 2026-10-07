#!/usr/bin/env python3
"""Check prompt_brief.py against messages with known answers (no model, under 1 s).

usage: python3 .claude/hooks/test_prompt_brief.py
"""
import json, os, subprocess, sys

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt_brief.py")
LONG = ("That was actually pretty good. I like the storyboard. Um, can we work on the clarification of my voice? And I "
        "notice in some parts, it feels like my voice gets cut off at the end of the sentence a little too early. Can "
        "we also learn how to identify critical components in a vlog? I just feel like we need to change the music "
        "because that's music we used in the rally video. Make it more personable. But can we also have something "
        "that's more vlog like lifestyle? Let's make an experimental version of this.")
CASES = [
    ("long multi-ask message", LONG, True),
    ("short ask", "show me the video", False),
    ("one-liner", "its in dropbox now check it", False),
    ("link with a note", "https://www.youtube.com/@brezscales heres another vlogger reference as well", False),
    ("mid-length, three asks", "can you fix the caption at 0:40 and also make the logo bigger, and can we add the "
                               "Part 2 tease at the end before it goes out tonight please thanks", True),
    ("mid-length, one ask", "the second clip in the folder from yesterday afternoon has the better light so use that "
                            "one for the opening shot of the reel because it matches the colour of the rest", False),
    ("system text", "<task-notification> " + LONG, False),
    ("slash command", "/review " + LONG, False),
]


def run(prompt):
    out = subprocess.run([sys.executable, HOOK], input=json.dumps({"prompt": prompt}), capture_output=True, text=True,
                         timeout=10)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def main():
    bad = 0
    for name, prompt, want in CASES:
        out = run(prompt)
        got = bool(out)
        if got:
            ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
            assert ctx.startswith("[prompt tool, automatic]"), ctx
        ok = got == want
        bad += not ok
        print(("ok  " if ok else "FAIL"), name, "->", "fires" if got else "quiet")
    out =subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=10)
    print("ok   bad input -> exit", out.returncode) if out.returncode == 0 and not out.stdout else print("FAIL bad input")
    bad += out.returncode != 0 or bool(out.stdout)
    print(f"{len(CASES) + 1 - bad}/{len(CASES) + 1} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
