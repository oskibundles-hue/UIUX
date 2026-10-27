#!/usr/bin/env python3
"""Cost log and the weekly review that proposes rule changes.

After each job the lead logs the session's numbers and one line on what went wrong:
    python3 .claude/brain/cost_meter.py --log --job "SE vlog Part 1" --note "wait loop ran 28 min"
Once a week (or whenever asked):
    python3 .claude/brain/post_mortem.py review [--days 7] [--no-gate]
prints the week's cost list, the drains that repeated, and proposed rule changes. The proposals are
only proposals: each one goes to Omarie as a click (AskUserQuestion) before any rule or CLAUDE.md
line changes. Claude can't be retrained; this loop changes the rules, briefs and routing instead.
A finding whose rule CLAUDE.md or lead.md already has is listed apart, as a rule broken anyway, with the hook
that could enforce it, so the review never proposes the same rule twice (2026-10-27).

The log is costlog/costlog.jsonl in the private brain (nq-agent-channel/brain) when it is attached,
so the Mac and the cloud share one history; otherwise .claude/brain/work/ (git-ignored, local only).
nq-check's FAIL rows go to costlog/qualityfails.jsonl next to it (gap 1 of the reel-harness comparison,
2026-10-26): the SubagentStop hook .claude/hooks/quality_fails.py records each one as it happens, and
    python3 .claude/brain/post_mortem.py fail [--job "..."] [--file report.md]    (or the report on stdin)
does the same by hand. review groups the checks that failed in two or more jobs and turns them into
proposals; one-offs are left out. FAIL evidence can quote client copy, so it only ever goes to that
private file (or the git-ignored work/ fallback), never into this repo.
Each proposal carries a "gate:" line (gap 3): rule_gate.py replays the rule over the replay set of past passed
jobs and says "safe to land" or "would break N of M past jobs". --no-gate leaves it out.
Each cost line also carries the job's quality outcome ("Observe", 2026-10-27): verdict PASS / FAIL from the
nq-check job cards this session saved (job_card.py; a session is one job, as in read_log), the failing checks, the card
ids, and the format. A job with no card falls back to its FAIL-log rows, and a job nq-check never saw is
"unchecked": review shows it, but leaves it out of the pass rate (Omarie's call, 2026-10-27). review then
prints cost and pass rate per format, with the cost per passed job (spend on checked jobs over the passes).
No model call, stdlib only.
"""
import datetime, json, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nqos_config import HAVE_NOTES, HOME, WORK

LOG = os.environ.get("NQOS_COSTLOG") or (os.path.join(HOME, "costlog", "costlog.jsonl") if HAVE_NOTES
                                         else os.path.join(WORK, "costlog.jsonl"))
FAILS = os.environ.get("NQOS_FAILLOG") or os.path.join(os.path.dirname(LOG), "qualityfails.jsonl")


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
    try:
        line.update(quality(r["session"], job))
    except Exception:                             # the cost line goes out even if the cards can't be read
        line.update(verdict="unchecked", fails=[], cards=[], rounds=0)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(json.dumps(line) + "\n")
    return LOG


def quality(session, job=None):
    """The job's nq-check outcome for its cost line: verdict (PASS, FAIL or unchecked), the failing checks,
    the job card ids, how many nq-check rounds ran, and the format. A session is one job, as in read_log.
    The last card decides the verdict, so a job that failed, was fixed and then passed counts as passed,
    with rounds showing the retry."""
    import job_card                               # imported here: job_card imports this module
    cards = [c for c in reversed(job_card.load_all()) if c.get("session") == session]   # oldest first, ties by file time
    out = {"verdict": "unchecked", "fails": [], "cards": [c["id"] for c in cards], "rounds": len(cards),
           "format": tags(job or "")[1], "workstream": tags(job or "")[0]}
    if cards:
        last = cards[-1]
        out.update(verdict=last.get("verdict") or "unchecked",
                   fails=[k for k, v in (last.get("checks") or {}).items() if v == "FAIL"],
                   format=known(last.get("format")) or out["format"] or last.get("format") or "",
                   workstream=(last.get("workstream") or "").lower() or out["workstream"])
        return out
    fails = [f for f in _read(FAILS, None) if f.get("session") == session]
    if fails:                                     # no card (a handback-only report): the FAIL log still knows
        out.update(verdict="FAIL", rounds=1, fails=list(dict.fromkeys(f["check"] for f in fails)),
                   format=out["format"] or next((f["format"] for f in fails if known(f.get("format"))), ""))
    return out


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


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cut(days):
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H")


_VERDICT = re.compile(r"^[\W_]*(fail|failed|pass|passed|n/?a)[\W_]*$", re.I)
_BULLET = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s*(?P<check>[^:|\u2014]{2,60}?)\s*[:\u2014-]+\s*\W*FAIL\W*\s*"
                     r"(?:[:\u2014-]+\s*)?(?P<why>.*)$", re.I)
WORKSTREAMS = (("anti stock", r"anti[ -]?stock|antistock|-antistock\b"),
               ("formula dynamics", r"formula dynamics|\bFD\b|-fd\b"),
               ("supercar experience", r"supercar experience|\bSE\b|-se(?:-vlog)?\b"))
FORMATS = ("carousel", "reel", "poster", "thumbnail", "ad", "promo", "story", "page", "vlog",   # a reel cut from a vlog is a reel
           "sheet", "index", "deck", "dashboard")
# Other words for a format, so a non-video job gets one too (2026-10-27: real FAIL rows from a page job came in
# with no format). Checked after FORMATS, so "a poster page" is still a poster.
FORMAT_ALIASES = (("page", r"artifact|web ?page|landing page|website|html"), ("sheet", r"spreadsheet|contact sheet|tracker"),
                  ("index", r"directory|deliverables list|to-?do board"), ("deck", r"slides|slide deck|presentation"))
UNKNOWN = "unknown"   # what a row or card says when nothing names its format or job: never an empty string


def known(value):
    """The value, or "" when it is empty or the UNKNOWN placeholder (so "unknown" never groups or matches)."""
    return "" if not value or value == UNKNOWN else value


def live_job(session=""):
    """The job title live_card.py start gave this session's Working-now card, or ""."""
    sid = session or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    try:
        from nqos_config import LIVECARD
        return json.load(open(os.path.join(LIVECARD, sid.replace("/", "_") + ".json"))).get("title", "")
    except (OSError, ValueError, AttributeError):
        return ""


def _clean(cell):
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", cell)).strip()


def parse_fails(text):
    """FAIL rows of an nq-check report: [(check, short reason)]. Reads the check · verdict · evidence table,
    and "- check: FAIL - why" bullets as a fallback. Rows that pass, or say N/A, are skipped."""
    out = []
    for line in (text or "").splitlines():
        if line.count("|") >= 2:
            cells = [_clean(c) for c in line.strip().strip("|").split("|")]
            verdicts = [i for i, c in enumerate(cells) if _VERDICT.match(c)]
            if verdicts and verdicts[0] > 0 and _VERDICT.match(cells[verdicts[0]])[1].lower().startswith("fail"):
                i = verdicts[0]
                check = cells[0]
                why = next((c for c in cells[i + 1:] if c), "")
                if check and not set(check) <= set("-: "):
                    out.append((check[:60], why[:120]))
            continue
        m = _BULLET.match(_clean(line))
        if m:
            out.append((m["check"].strip()[:60], m["why"].strip()[:120]))
    return out


def check_key(check):
    """One name per check, so "Caption rules" and "caption rule" group together."""
    words = re.findall(r"[a-z0-9]+", check.lower())
    words = [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words]
    return " ".join(w for w in words if w not in {"the", "a", "an", "and", "of", "check", "rule"}) or check.lower()


def tags(text):
    """(workstream, format) the report names, or "" when it names none or several. A "Workstream: X" or
    "Format: X" line wins over the words around it (2026-10-27: a vlog brief that cited 09-campaign-ads/ was
    filed as an ad, and a check that said "no FD overlay" lost its workstream)."""
    ws = [name for name, pat in WORKSTREAMS if re.search(rf"\bworkstream:\s*(?:{pat})", text or "", re.I)]
    ws = ws or [name for name, pat in WORKSTREAMS if re.search(pat, text or "", re.I)]
    fm = [f for f in FORMATS if re.search(rf"\bformat:\s*\**{f}s?(?![a-z])", text or "", re.I)]
    fm = fm or [f for f in FORMATS if re.search(rf"(?<![a-z]){f}s?(?![a-z])", text or "", re.I)]   # part2_reel.mp4 counts
    fm = fm or [f for f, pat in FORMAT_ALIASES if re.search(rf"(?<![a-z])(?:{pat})s?(?![a-z])", text or "", re.I)]
    return (ws[0] if len(ws) == 1 else ""), (fm[0] if fm else "")


def log_fails(text, session, job="", agent="", source="hook", fmt="", ws=""):
    """Append one row per FAIL in an nq-check report to FAILS. Returns the rows written. A report seen twice
    (SubagentStop and a handback both firing) writes nothing the second time. fmt is the format the job card
    found in the briefs (ws its workstream); else the report's own words decide. Where nothing names them, the job is the session's
    Working-now title and the format is UNKNOWN, never an empty string."""
    found = parse_fails(text)
    if not found:
        return []
    found_ws, fm = tags(text)
    ws = (known(ws) or found_ws).lower()
    fm = known(fmt) or fm or UNKNOWN
    job = known(job) or live_job(session) or UNKNOWN
    seen = {(r.get("session"), r.get("agent"), r.get("key"), r.get("why")) for r in _read(FAILS, None)}
    rows, at = [], _now()
    for check, why in found:
        row = {"at": at, "session": session or "", "agent": agent or "", "job": job or "", "check": check,
               "key": check_key(check), "why": why, "workstream": ws, "format": fm, "source": source}
        if (row["session"], row["agent"], row["key"], why) not in seen:
            rows.append(row)
            seen.add((row["session"], row["agent"], row["key"], why))
    if rows:
        os.makedirs(os.path.dirname(FAILS), exist_ok=True)
        with open(FAILS, "a") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in rows)
    return rows


def _read(path, days):
    out, cut = [], _cut(days) if days else ""
    if os.path.isfile(path):
        for raw in open(path):
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            if row.get("at", "") >= cut:
                out.append(row)
    return out


def repeated_fails(fails, rows=()):
    """Checks that failed in two or more jobs: [(key, jobs, example row, workstreams, formats)], most first.
    A job is the row's job name, else the cost log's job for that session, else the session itself."""
    jobs_by_session = {r["session"]: r.get("job", "") for r in rows}
    groups = defaultdict(dict)
    for f in fails:
        job = known(f.get("job")) or jobs_by_session.get(f.get("session"), "") or f.get("session", "")
        groups[f.get("key") or check_key(f.get("check", ""))].setdefault(job, f)
    out = []
    for key, by_job in groups.items():
        if len(by_job) >= 2:
            seen = list(by_job.values())
            out.append((key, len(by_job), seen[-1], sorted({f["workstream"] for f in seen if f.get("workstream")}),
                        sorted({f["format"] for f in seen if known(f.get("format"))})))
    return sorted(out, key=lambda g: (-g[1], g[0]))


# What to propose when a check keeps failing: the first keyword that matches the check's name wins.
FIX_FOR = (("caption", "add the caption rules to nq-build's brief for {where} and have the builder run the caption "
                       "lint before it hands over"),
           ("hand", "send every {where} driving shot through the pre-render frame gate, and brief the builder to cover "
                    "hands-off shots with a cutaway before the gate"),
           (("audio", "loud", "lufs", "level"), "have nq-build measure loudness (ffmpeg loudnorm) on every {where} "
                                                "render and report it with the hand-over"),
           (("style", "locked"), "name the style in every {where} brief and have the builder check the style guide's "
                                 "pre-flight list before it hands over"),
           ("brand", "put the brand sheet in every {where} brief, and fail the build if two brands share the piece"),
           (("ai", "copy", "slop"), "run /slopmonster on every {where} script and caption before nq-check"),
           (("figure", "source", "claim", "spec", "price"), "send {where} figures through nq-facts before nq-check, "
                                                            "not after"),
           (("frame", "fill", "bar", "framing"), "add a framing contact sheet to nq-build's hand-over for {where}"))


def quality_proposals(groups, days=7):
    when = "this week" if days == 7 else f"in the last {days} days"
    out = []
    for key, n, ex, ws, fm in groups:
        where = " ".join(filter(None, [" / ".join(ws), " / ".join(fm)])) or "every"
        fix = next((f for k, f in FIX_FOR if any(w in key.split() or key.startswith(w)
                                                 for w in ((k,) if isinstance(k, str) else k))),
                   "add \"{check}\" to nq-build's pre-flight for {where}, so the builder checks it before it hands over")
        out.append(f"{n} jobs failed {ex['check']} {when}. Proposed rule: " + fix.format(where=where, check=ex["check"]) + ".")
    return out


def by_format(rows):
    """Cost and pass rate per format: {format: {jobs, usd, checked, passed, unchecked, checked_usd}}.
    Lines from before the verdict was logged count as unchecked."""
    out = defaultdict(Counter)
    for r in rows:
        fm = known(r.get("format")) or tags(r.get("job", ""))[1] or r.get("format") or "other"
        v = r.get("verdict") or "unchecked"
        g = out[fm]
        g["jobs"] += 1
        g["usd"] += r.get("usd", 0)
        if v == "unchecked":
            g["unchecked"] += 1
        else:
            g["checked"] += 1
            g["checked_usd"] += r.get("usd", 0)
            g["passed"] += v == "PASS"
    return out


def format_lines(rows):
    """The review's cost-and-quality block: cost per passed job is the spend on checked jobs over the passes."""
    out = []
    for fm, g in sorted(by_format(rows).items(), key=lambda kv: -kv[1]["usd"]):
        line = f"  {fm:<10}{g['jobs']:>3} jobs  ${g['usd']:>7.2f}"
        if g["checked"]:
            line += f"  {g['passed']}/{g['checked']} passed ({100 * g['passed'] // g['checked']}%)"
            line += (f"  ${g['checked_usd'] / g['passed']:.2f} per passed {fm}" if g["passed"]
                     else "  no passes yet")
        if g["unchecked"]:
            line += f"  {g['unchecked']} unchecked"
        out.append(line)
    return out


# A proposal whose rule is already written down isn't a new rule: the sessions broke it, so the fix is a hook
# that enforces it. The marker is a phrase from the rule's line in CLAUDE.md or lead.md.
RULE_FILES = os.environ.get("NQOS_RULEFILES", "").split(os.pathsep) if os.environ.get("NQOS_RULEFILES") else \
    [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "CLAUDE.md"),
     os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "playbooks", "lead.md")]


def written_rule(marker):
    """The file that already holds the rule, or ""."""
    for f in RULE_FILES:
        try:
            if marker in open(f).read():
                return os.path.basename(f)
        except OSError:
            pass
    return ""


def proposals(rows, broken=None):
    """Rule changes the numbers argue for. Thresholds come from the Oct 5-6 case and usage-drains.
    A rule that is already written goes to `broken` (a list) instead, with how a hook could enforce it."""
    out, seen = [], []
    def add(finding, rule, marker, enforce):
        where = written_rule(marker)
        if where and broken is not None:
            broken.append(f"{finding}. Already a rule ({where}: \"{marker}\"); enforce it: {enforce}.")
        else:
            out.append(f"{finding}. Proposed rule: {rule}.")
    big = [r for r in rows if r["ctx_median"] > 300_000]
    if big:
        add(f"{len(big)} session(s) ran at a median context over 300k",
            "hand off to a fresh session from a short handoff once the guard's 300k warning fires, and always after "
            "a compaction", "Hand off after each job",
            "have the cost guard ask for a handoff at 300k instead of only warning")
    churn = [r for r in rows if r["share"].get("cache_write", 0) >= 35]
    if churn:
        add(f"{len(churn)} session(s) spent 35%+ on cache writes, which means the cache keeps going cold "
            "(idle gaps past the TTL, or wakes on a big session)",
            "bind reminders and check-ins to a small session, and finish or hand off before stepping away",
            "Finish or hand off before going idle",
            "the cost guard warns when a check-in is set from a session past 150k since 2026-10-27; check this count falls")
    polls = sum(any("poll" in d for d in r["drains"]) for r in rows)
    if polls:
        add(f"{polls} session(s) ran wait/poll loops",
            "wait on a marker file or the PID (`wait $pid`, or `pgrep -f '[v]log.py'` so it can't match itself), "
            "with a hard timeout", "never a `pgrep -f` loop",
            "the cost guard blocks unbounded loops since 2026-10-27; check this count falls")
    dups = sum(any("x " in d and "poll" not in d for d in r["drains"]) for r in rows)
    if dups:
        add(f"{dups} session(s) fetched or read the same thing twice",
            "save fetched frames and transcripts to the scratchpad once and point agents at the file",
            "Keep frames out of the lead",
            "the cost guard blocks repeat reads and fetches since 2026-10-27; check this count falls")
    heavy = [r for r in rows if r["agent_ctx_max"] > 250_000]
    if heavy:
        add(f"{len(heavy)} session(s) had an agent past 250k context",
            "one agent, one job; split the brief or start a fresh agent from a summary",
            "Start a fresh agent from a summary",
            "have the SubagentStop hook flag an agent that ended past 250k, so the next brief is split")
    return out


def review(days=7, gate=True):
    rows = sorted(read_log(days), key=lambda r: -r["usd"])
    groups = repeated_fails(_read(FAILS, days), rows)
    total = sum(r["usd"] for r in rows) or 0
    out = [f"Cost review, last {days} days: {len(rows)} sessions, ${total:.2f} API-equivalent", ""]
    for r in rows[:12]:
        out.append(f"  ${r['usd']:>8.2f}  {r['session'][:8]}  {r['calls']:>4} calls  ctx med {r['ctx_median'] // 1000}k"
                   f"  {r['agents']} agents  {r.get('verdict') or 'unchecked':9}  {r['job'][:40]}"
                   + (f"  [fails: {', '.join(r['fails'][:3])}]" if r.get("fails") else "") + (f"  | {r['note'][:60]}" if r["note"] else ""))
    fmts = format_lines(rows)
    if fmts:
        out += ["", "cost and pass rate by format (nq-check; unchecked jobs are left out of the rate):"] + fmts
    drains = Counter(d.split(": ", 1)[-1][:50] for r in rows for d in r["drains"])
    if drains:
        out += ["", "repeated drains:"] + [f"  {n}x {d}" for d, n in drains.most_common(5)]
    if groups:
        out += ["", "repeated quality fails (nq-check, 2+ jobs):"]
        out += [f"  {n}x {ex['check']}" + (f"  [{', '.join(ws + fm)}]" if ws or fm else "")
                + (f"  e.g. {ex['why'][:70]}" if ex.get("why") else "") for _, n, ex, ws, fm in groups[:5]]
    broken = []
    props = proposals(rows, broken) + quality_proposals(groups, days)
    out += ["", "proposed rule changes (each goes to Omarie as a click before it lands):"]
    for i, p in enumerate(props, 1):
        out.append(f"  {i}. {p}")
        if gate:
            out.append(f"     gate: {gate_line(p)}")
    if not props:
        out.append("  none this week")
    if broken:
        out += ["", "already rules, broken anyway (the fix is enforcing them in a hook, not adding them again; "
                    "each still goes to Omarie as a click):"]
        out += [f"  {i}. {b}" for i, b in enumerate(broken, 1)]
    return "\n".join(out)


def gate_line(proposal):
    """Gap 3: the proposed rule replayed over past passed jobs (rule_gate.py), so it goes to Omarie with the
    evidence: "safe to land" or "would break N of M past jobs"."""
    import rule_gate                    # here, not at the top: rule_gate imports this file too
    rule = proposal.split("Proposed rule: ", 1)[-1].rstrip(".")
    try:
        return rule_gate.gate(rule)["verdict"]
    except Exception as e:              # a broken replay set must not take the weekly review down with it
        return f"not checked ({type(e).__name__}: {e})"


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda name, default="": a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default
    if a and a[0] == "fail":
        text = open(opt("--file")).read() if opt("--file") else sys.stdin.read()
        sid = opt("--session") or os.environ.get("CLAUDE_CODE_SESSION_ID", "") \
            or os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID", "")
        got = log_fails(text, sid, opt("--job"), source="manual")
        print(f"logged {len(got)} FAIL row(s) to {FAILS}" if got else "no new FAIL rows found", file=sys.stderr)
    elif a and a[0] == "review":
        print(review(int(opt("--days", "7")), gate="--no-gate" not in a))
    else:
        sys.exit(__doc__)
