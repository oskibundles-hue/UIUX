#!/usr/bin/env python3
"""Token meter for one Claude Code session: what it cost, where the context went, what looked like a drain.

usage: python3 .claude/brain/cost_meter.py [TRANSCRIPT.jsonl | SESSION_ID] [--json] [--card] [--log --job "..." --note "..."]

With no argument it meters the newest transcript for this folder under ~/.claude/projects/ (the same
place on the Mac and in the cloud). Subagent transcripts in <session>/subagents/*.jsonl are counted
as agents, and so are sidechain records inside the main file (older Claude Code versions).

Counting: transcripts write a usage record mid-stream and again at the end, so only the LAST record
per message id counts. Context per call = input + cache-write + cache-read tokens of that call.
Dollar figures are API-equivalent list prices, for comparing sessions, not what a plan is billed.

  --json   one JSON object (everything below)
  --card   ArtifactData `update` payload for this session's Working-now card (live_card.py's doc id)
  --log    append this session's line to the cost log (costlog.jsonl, see post_mortem.py),
           with --job "<what the job was>" and --note "<what went wrong>"
No model call, stdlib only, about 0.1 s per 10 MB of transcript.
"""
import glob, json, os, re, statistics, sys
from collections import Counter, defaultdict

# $ per million tokens: input, output, cache read, cache write 5 min, cache write 1 h.
# Source: claude-api skill model table and prompt-caching economics, cached 2026-09-25.
PRICES = {
    "claude-fable-5":   (10.0, 50.0, 0.25, 12.5, 20.0),
    "claude-mythos-5":  (10.0, 50.0, 0.25, 12.5, 20.0),
    "claude-opus-5-5":  (4.0, 20.0, 0.20, 5.0, 8.0),
    "claude-opus-5":    (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-opus-4":    (5.0, 25.0, 0.50, 6.25, 10.0),
    "claude-sonnet-5":  (2.0, 10.0, 0.20, 2.5, 4.0),
    "claude-sonnet-4":  (3.0, 15.0, 0.30, 3.75, 6.0),
    "claude-haiku-4":   (1.0, 5.0, 0.10, 1.25, 2.0),
}
DEFAULT_PRICE = PRICES["claude-opus-5-5"]
BIG_CONTEXT = 300_000          # the live guard warns past this
POLL_RE = re.compile(r"\b(while|until)\b[^\n]*\b(sleep|pgrep)\b|\bsleep\s+([6-9]\d|\d{3,})\b|\bwatch\s+-n")


def price(model):
    m = (model or "").lower()
    for key in sorted(PRICES, key=len, reverse=True):     # longest prefix first: opus-5-5 before opus-5
        if m.startswith(key):
            return PRICES[key]
    return DEFAULT_PRICE


def project_dir(cwd=None):
    slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd or os.getcwd()))
    return os.path.join(os.path.expanduser("~/.claude/projects"), slug)


def find_transcript(arg=None):
    if arg and os.path.isfile(arg):
        return arg
    pats = [os.path.join(project_dir(), "*.jsonl")]
    if arg:                                                   # a session id, full or the first few characters
        pats = [os.path.expanduser(f"~/.claude/projects/*/{arg}*.jsonl")]
    files = [f for p in pats for f in glob.glob(p)]
    if not files and not arg:
        files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
    return max(files, key=os.path.getmtime) if files else None


class Stream:
    """One conversation: the lead or one agent."""

    def __init__(self, name):
        self.name, self.msgs, self.tools = name, {}, []

    def add(self, rec):
        msg = rec.get("message") or {}
        u, mid = msg.get("usage"), msg.get("id")
        if rec.get("type") == "assistant" and u and mid:
            self.msgs[mid] = (msg.get("model", ""), u, rec.get("timestamp", ""))   # last record wins
        if rec.get("type") == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    self.tools.append((block.get("name", ""), block.get("input") or {}))

    def summary(self):
        tok = Counter()
        cost = 0.0
        ctx, models = [], Counter()
        for model, u, _ in sorted(self.msgs.values(), key=lambda m: m[2]):
            p = price(model)
            cc = u.get("cache_creation") or {}
            w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
            w5m = (u.get("cache_creation_input_tokens", 0) or 0) - w1h
            i, o, r = (u.get(k, 0) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens"))
            tok.update(input=i, output=o, cache_read=r, cache_write=w1h + w5m, cache_write_1h=w1h)
            cost += (i * p[0] + o * p[1] + r * p[2] + w5m * p[3] + w1h * p[4]) / 1e6
            ctx.append(i + r + w1h + w5m)
            models[model] += 1
        return {
            "name": self.name, "calls": len(self.msgs), "tokens": dict(tok), "usd": round(cost, 2),
            "ctx_max": max(ctx, default=0), "ctx_median": int(statistics.median(ctx)) if ctx else 0,
            "ctx_now": ctx[-1] if ctx else 0, "calls_over_300k": sum(c > BIG_CONTEXT for c in ctx),
            "models": dict(models),
        }


def cost_parts(streams):
    """Dollar split by token kind across all streams."""
    parts = Counter()
    for s in streams:
        for model, u, _ in s.msgs.values():
            p = price(model)
            w1h = (u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens", 0) or 0
            w5m = (u.get("cache_creation_input_tokens", 0) or 0) - w1h
            parts["cache_read"] += (u.get("cache_read_input_tokens", 0) or 0) * p[2] / 1e6
            parts["cache_write"] += (w5m * p[3] + w1h * p[4]) / 1e6
            parts["output"] += (u.get("output_tokens", 0) or 0) * p[1] / 1e6
            parts["input"] += (u.get("input_tokens", 0) or 0) * p[0] / 1e6
    total = sum(parts.values()) or 1
    return {k: round(100 * v / total) for k, v in parts.items()}


def drains(streams):
    """Things worth a look: poll loops, the same fetch or read twice, calls at huge context."""
    found = []
    for s in streams:
        seen = Counter()
        for name, inp in s.tools:
            if name == "Bash" and POLL_RE.search(inp.get("command", "")):
                found.append(f"{s.name}: wait/poll loop: {inp.get('command', '')[:90]!r}")
            key = inp.get("file_path") or inp.get("url") or inp.get("video_id") or inp.get("id")
            if key and (name in ("Read", "WebFetch") or "video_transcript" in name or "frames" in name):
                seen[(name.split("__")[-1], str(key))] += 1
        found += [f"{s.name}: {n}x {tool} {key[:80]}" for (tool, key), n in seen.items() if n > 1]
    return found


def meter(path):
    streams = {"lead": Stream("lead")}
    compactions = 0
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") == "system" and rec.get("subtype") == "compact_boundary":
                compactions += 1
            key = "lead"
            if rec.get("isSidechain"):
                key = "agent-" + str(rec.get("agentId") or "sidechain")
            streams.setdefault(key, Stream(key)).add(rec)
    sub = os.path.join(os.path.splitext(path)[0], "subagents")
    for f in sorted(glob.glob(os.path.join(sub, "*.jsonl"))):
        s = streams.setdefault(os.path.basename(f)[:-6], Stream(os.path.basename(f)[:-6]))
        with open(f, errors="replace") as fh:
            for line in fh:
                try:
                    s.add(json.loads(line))
                except ValueError:
                    pass
    live = [s for s in streams.values() if s.msgs]
    rows = [s.summary() for s in live]
    total = Counter()
    for r in rows:
        total.update(r["tokens"])
    lead = next((r for r in rows if r["name"] == "lead"), rows[0] if rows else {})
    return {
        "transcript": path, "session": os.path.basename(path)[:-6],
        "usd": round(sum(r["usd"] for r in rows), 2), "calls": sum(r["calls"] for r in rows),
        "agents": len(rows) - (1 if any(r["name"] == "lead" for r in rows) else 0),
        "tokens": dict(total), "cost_share_pct": cost_parts(live), "compactions": compactions,
        "ctx_max": lead.get("ctx_max", 0), "ctx_median": lead.get("ctx_median", 0),
        "ctx_now": lead.get("ctx_now", 0), "streams": rows, "drains": drains(live),
    }


def m(n):
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.0f}k"


def text(r):
    t = r["tokens"]
    out = [f"session {r['session'][:8]}  ${r['usd']:.2f} API-equivalent  {r['calls']} calls  "
           f"{r['agents']} agents  {r['compactions']} compactions",
           f"tokens  cache-read {m(t.get('cache_read', 0))}  cache-write {m(t.get('cache_write', 0))}  "
           f"output {m(t.get('output', 0))}  input {m(t.get('input', 0))}",
           "cost share  " + "  ".join(f"{k} {v}%" for k, v in sorted(r["cost_share_pct"].items(), key=lambda x: -x[1])),
           f"lead context  max {m(r['ctx_max'])}  median {m(r['ctx_median'])}  now {m(r['ctx_now'])}", ""]
    out.append(f"{'stream':<26}{'calls':>6}{'usd':>9}{'ctx max':>9}{'median':>9}{'>300k':>7}")
    for s in sorted(r["streams"], key=lambda s: -s["usd"]):
        out.append(f"{s['name'][:25]:<26}{s['calls']:>6}{s['usd']:>9.2f}{m(s['ctx_max']):>9}"
                   f"{m(s['ctx_median']):>9}{s['calls_over_300k']:>7}")
    if r["drains"]:
        out += ["", "possible drains:"] + ["  " + d for d in r["drains"][:15]]
    return "\n".join(out)


def card(r):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from live_card import URL, session
    t = r["tokens"]
    cost = {"usd": r["usd"], "calls": r["calls"], "agents": r["agents"], "ctx_now": r["ctx_now"],
            "ctx_max": r["ctx_max"], "ctx_median": r["ctx_median"], "cache_read": t.get("cache_read", 0),
            "cache_write": t.get("cache_write", 0), "output": t.get("output", 0),
            "line": f"${r['usd']:.2f} · {r['calls']} calls · ctx {m(r['ctx_now'])} (max {m(r['ctx_max'])})"
                    f" · {r['agents']} agents"}
    return {"url": URL, "collection": "work", "doc_id": session()[0], "action": "update", "data": {"cost": cost}}


def main(argv):
    opts = {a[2:]: argv[i + 1] for i, a in enumerate(argv) if a in ("--job", "--note") and i + 1 < len(argv)}
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--job", "--note"))]
    path = find_transcript(args[0] if args else None)
    if not path:
        sys.exit("no transcript found under ~/.claude/projects/")
    r = meter(path)
    if "--log" in argv:
        from post_mortem import log_line
        print("logged to", log_line(r, opts.get("job"), opts.get("note")))
    if "--card" in argv:
        print(json.dumps(card(r), indent=1))
    elif "--json" in argv:
        print(json.dumps(r, indent=1))
    elif "--log" not in argv:
        print(text(r))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1:])
