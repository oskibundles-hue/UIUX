#!/usr/bin/env python3
"""Print the ArtifactData payload for this session's card on the NQ OS page (the work/* collection).

usage: python3 .claude/brain/live_card.py start "<job title>" "<first step>"   [--pct N] [--session "<name>"]
       python3 .claude/brain/live_card.py step "<what you're on now>"          [--pct N]
       python3 .claude/brain/live_card.py done|blocked|waiting "<one line>"

Every payload carries data.cost, this session's token bill from cost_meter.py (--no-cost leaves it off).
`done` also appends the session's line to the cost log (post_mortem.py; the log gate approved 2026-10-06),
with --job "<job>" --note "<what went wrong>" if given; --no-log skips it. The log path goes to stderr.
Then it pushes the line to nq-agent-channel (costlog_push.py, result on stderr), so the weekly review sees
cloud sessions before the container ends; --no-sync skips that, and so does NQOS_COSTLOG (tests).
Prints one JSON object: url, collection, doc_id, action and data. Pass those to the ArtifactData tool.
`start` is a `set` (no if_version on a new card). Every later call is an `update`: add
if_version = the version the last write returned. No model call; about 0.05 s.
"""
import datetime, json, os, socket, sys

URL = "https://claude.ai/artifact/JdMaXgCuUu7XHQ3yRhEYFy"   # the NQ OS control room
STATUS = {"start": "working", "step": "working", "done": "done", "blocked": "blocked", "waiting": "waiting"}


def session():
    """(doc_id, link, where, name) for this session, from the environment Claude Code sets."""
    remote = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID", "")      # cse_01ABC... in cloud sessions
    if remote:
        sid = remote.split("_", 1)[-1]
        return "s_" + sid, "https://claude.ai/code/session_" + sid, "cloud", "cloud session"
    local = os.environ.get("CLAUDE_CODE_SESSION_ID", "")               # a uuid on the Mac
    return "s_" + (local[:8] or "local"), "", "mac", "Mac session on " + socket.gethostname().split(".")[0]


def push_log():
    """Run costlog_push.py now, while the container is still up. Never raises: the card goes out either way."""
    import subprocess
    try:
        p = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "costlog_push.py")],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90)
        return (p.stdout + p.stderr).strip() or f"exit {p.returncode}"
    except Exception as e:
        return f"didn't run ({e.__class__.__name__})"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = {a.lstrip("-"): argv[i + 1] for i, a in enumerate(argv) if a.startswith("--") and i + 1 < len(argv)}
    if not args or args[0] not in STATUS or len(args) < 2:
        sys.exit(__doc__)
    verb, text = args[0], args[1:]
    doc_id, link, where, name = session()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {"status": STATUS[verb], "updated": now}
    if verb == "start":
        data.update(title=text[0], detail=text[1] if len(text) > 1 else "", where=where,
                    session=opts.get("session", name), link=link, started=now)
    else:
        data["detail"] = text[0]
    if "pct" in opts:
        data["pct"] = int(opts["pct"])
    want_log = verb == "done" and "--no-log" not in argv
    if "--no-cost" not in argv or want_log:           # the session's own token bill, from cost_meter.py
        try:
            from cost_meter import card, find_transcript, meter
            r = meter(find_transcript())
            if "--no-cost" not in argv:
                data["cost"] = card(r)["data"]["cost"]
            if want_log:                              # every finished job leaves its line in the cost log
                from post_mortem import log_line
                print("cost log:", log_line(r, opts.get("job", text[0]), opts.get("note")), file=sys.stderr)
                if "--no-sync" not in argv and not os.environ.get("NQOS_COSTLOG"):   # approved 2026-10-06
                    print("cost log push:", push_log(), file=sys.stderr)
        except Exception:                             # no transcript yet (or on an old Mac copy): card without it
            pass
    print(json.dumps({"url": URL, "collection": "work", "doc_id": doc_id,
                      "action": "set" if verb == "start" else "update", "data": data}, indent=1))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1:])
