#!/usr/bin/env python3
"""UserPromptSubmit hook (every session): the prompt tool.

Omarie, 2026-10-06: "we should create a prompt tool that makes my prompts sound much better and organized once i send
one". He picked "auto-organize each message": when a message is long or carries several asks, the session first turns it
into a clean numbered brief and confirms it with him (one click) before starting.

This hook only spots those messages and hands Claude the instruction as extra context; no model call, a few ms.
Never blocks a prompt: any error -> prints nothing, exits 0.
Test: python3 .claude/hooks/test_prompt_brief.py
"""
import json, re, sys

MIN_WORDS_LONG = 80          # this long -> always brief
MIN_WORDS_ASKS, MIN_ASKS = 25, 3   # or this long with this many asks
SKIP_PREFIXES = ("<", "This session is being continued", "/")
ASK = re.compile(r"\b(can (?:we|you|u)|could (?:we|you)|let'?s|i (?:want|need|would like|'d like)|we (?:need|should)|"
                 r"make|add|change|fix|create|build|show|send|look up|find|run|give|also|instead)\b", re.I)


def measure(prompt):
    words = len(prompt.split())
    asks = len(ASK.findall(prompt)) + prompt.count("?")
    return words, asks


def fires(prompt):
    if prompt.lstrip().startswith(SKIP_PREFIXES):
        return False
    words, asks = measure(prompt)
    return words >= MIN_WORDS_LONG or (words >= MIN_WORDS_ASKS and asks >= MIN_ASKS)


def context(prompt):
    words, asks = measure(prompt)
    return (f"[prompt tool, automatic] Omarie's message is long ({words} words, about {asks} asks). Before other work, "
            "open your reply with it organized as a short brief, in his words where you can: "
            "(1) What you want: numbered, one line each, most important first. "
            "(2) Already decided: anything he settled, so it isn't asked again. "
            "(3) Open questions. Then ask one AskUserQuestion: first question 'Is this brief right?' with "
            "'Yes, go (Recommended)' / 'Change something', plus up to three open questions, recommendation first. "
            "Start the work once he answers. Skip the click only if nothing is open and he said to just go.")


def main():
    try:
        prompt = json.load(sys.stdin).get("prompt", "") or ""
        if fires(prompt):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                     "additionalContext": context(prompt)}}))
    except Exception:
        pass


if __name__ == "__main__":
    main()
