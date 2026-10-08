#!/usr/bin/env python3
"""Cost log and the weekly review that proposes rule changes.

After each job the lead logs the session's numbers and one line on what went wrong:
    python3 .claude/brain/cost_meter.py --log --job "SE vlog Part 1" --note "wait loop ran 28 min"
Once a week (or whenever asked):
    python3 .claude/brain/post_mortem.py review [--days 7]
prints the week's cost list, the drains that repeated, and proposed rule changes. The proposals are
only proposals: each one goes to Omarie as a click (AskUserQuestion) before any rule or CLAUDE.md
line changes. Claude can't be retrained; this loop changes the rules, briefs and routing instead.

The log is costlog/costlog.jsonl in the private brain (nq-agent-channel/brain) when it is attached,
so the Mac and the cloud share one history; otherwise .claude/brain/work/ (git-ignored, local only).
No model call, stdlib only.
"""
import datetime, json, os, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nqos_config import HAVE_NOTES, HOME, WORK

LOG = os.environ.get("NQOS_COSTLOG") or (os.path.join(HOME, "costlog", "costlog.jsonl") if HAVE_NOTES
                                         else os.path.join(WORK, "costlog.jsonl"))


def log_line(r, job=None, note=None):
    t = r["tokens"]
    line = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session": r["session"], "job": job or "", "note": note or "", "usd": r["usd"],
            "calls": r["calls"], "agents": r["agents"], "compactions": r["compactions"],
            "ctx_max": r["ctx_max"], "ctx_median": r["ctx_median"],
            "cache_read": t.get("cache_read", 0), "cache_write": t.get("cache_write", 0),
            "output": t.get("output", 0), "share": r["cost_share_pct"],
            "agent_ctx_max": max([s["ctx_max"] for s in r["streams"] if s["name"] != "lead"], default=0),
            "drains": r["drains"][:10]}
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(json.dumps(line) + "\n")
    return LOG


def read_log(days):
    cut = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H")
    rows = {}
    if os.path.isfile(LOG):
        for raw in open(LOG):
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            if row.get("at", "") >= cut:
                rows[row["session"]] = row          # a session logged twice keeps its latest numbers
    return list(rows.values())


def proposals(rows):
    """Rule changes the numbers argue for. Thresholds come from the Oct 5-6 case and usage-drains."""
    out = []
    big = [r for r in rows if r["ctx_median"] > 300_000]
    if big:
        out.append(f"{len(big)} session(s) ran at a median context over 300k. Proposed rule: hand off to a fresh "
                   "session from a short handoff once the guard's 300k warning fires, and always after a compaction.")
    churn = [r for r in rows if r["share"].get("cache_write", 0) >= 35]
    if churn:
        out.append(f"{len(churn)} session(s) spent 35%+ on cache writes, which means the cache keeps going cold "
                   "(idle gaps past the TTL, or wakes on a big session). Proposed rule: bind reminders and check-ins "
                   "to a small session, and finish or hand off before stepping away.")
    polls = sum(any("poll" in d for d in r["drains"]) for r in rows)
    if polls:
        out.append(f"{polls} session(s) ran wait/poll loops. Proposed rule: wait on a marker file or the PID "
                   "(`wait $pid`, or `pgrep -f '[v]log.py'` so it can't match itself), with a hard timeout.")
    dups = sum(any("x " in d and "poll" not in d for d in r["drains"]) for r in rows)
    if dups:
        out.append(f"{dups} session(s) fetched or read the same thing twice. Proposed rule: save fetched frames "
                   "and transcripts to the scratchpad once and point agents at the file.")
    heavy = [r for r in rows if r["agent_ctx_max"] > 250_000]
    if heavy:
        out.append(f"{len(heavy)} session(s) had an agent past 250k context. Proposed rule: one agent, one job; "
                   "split the brief or start a fresh agent from a summary.")
    return out


def review(days=7):
    rows = sorted(read_log(days), key=lambda r: -r["usd"])
    total = sum(r["usd"] for r in rows) or 0
    out = [f"Cost review, last {days} days: {len(rows)} sessions, ${total:.2f} API-equivalent", ""]
    for r in rows[:12]:
        out.append(f"  ${r['usd']:>8.2f}  {r['session'][:8]}  {r['calls']:>4} calls  ctx med {r['ctx_median'] // 1000}k"
                   f"  {r['agents']} agents  {r['job'][:40]}" + (f"  | {r['note'][:60]}" if r["note"] else ""))
    drains = Counter(d.split(": ", 1)[-1][:50] for r in rows for d in r["drains"])
    if drains:
        out += ["", "repeated drains:"] + [f"  {n}x {d}" for d, n in drains.most_common(5)]
    props = proposals(rows)
    out += ["", "proposed rule changes (each goes to Omarie as a click before it lands):"]
    out += [f"  {i}. {p}" for i, p in enumerate(props, 1)] or ["  none this week"]
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] != "review":
        sys.exit(__doc__)
    print(review(int(a[a.index("--days") + 1]) if "--days" in a else 7))
