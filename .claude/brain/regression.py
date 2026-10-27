#!/usr/bin/env python3
"""Re-check a proposed rule against a few past PASSED jobs before it reaches Omarie.

usage: python3 .claude/brain/regression.py set [--workstream "..."] [--format reel]   the regression set
       python3 .claude/brain/regression.py check "<check>" [--workstream ...] [--format ...] [--json]
       python3 .claude/brain/regression.py rebuild "<check>" [--workstream ...] [--format ...]

Gap 3 of the reel-harness comparison (its "Gate 2: performance" row): a rule from post_mortem.py review
must not fail work that used to pass. review calls recheck() for each quality proposal and adds one line
to it: "re-checked against N past jobs: all still pass", or the jobs that would now fail and why.

The regression set, per rule: the pinned reference for each format in the rule's scope (job_diff.py pin,
Omarie's picks), plus the latest PASS card of each such format, preferring the rule's workstream; at most
MAX jobs. A rule scoped to "supercar experience reel" is only tried on SE reels; an unscoped one on all.

The default re-check is a card test, no rebuild: each rule asks the builder to do something it can be
seen doing on a job card (job_card.py), so the test looks for that on the stored card. A loudness rule
looks for a loudness measurement step or a LUFS figure; a style rule for a style in every builder brief;
a fact rule for an nq-facts brief. The parts of a rule that only change the next brief (add X to the brief)
are not tested, because no past brief carried them. Any rule also fails a job whose own nq-check row for
that check was FAIL. About 0.05 s, stdlib only, no model call (Omarie's pick, 2026-10-27).

rebuild is the opt-in full test: it prints, for each job in the set, the original briefs with the rule
added, for the lead to send through nq-build then nq-check. It calls no model itself; each job costs about
two agent start-ups (~110k tokens), so it is for a rule that would change how every job is built.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import job_card
from post_mortem import check_key, fix_for, rule_text

MAX = 5
AGENT_TOKENS = 55_000          # start-up context of one agent (CLAUDE.md, "Fewer agents is the saving")


# ---- the regression set ---------------------------------------------------------------------------------

def _in_scope(card, ws=(), fm=()):
    return ((not ws or (card.get("workstream") or "").lower() in {w.lower() for w in ws})
            and (not fm or card.get("format") in fm))


def regression_set(ws=(), fm=(), cards=None):
    """[(card, why it is in the set)]: pins first, then the latest PASS per format, newest first."""
    cards = job_card.load_all() if cards is None else cards
    passed = [c for c in cards if c.get("verdict") == "PASS" and _in_scope(c, ws, fm)]
    by_id = {c["id"]: c for c in passed}
    try:
        pins = json.load(open(os.path.join(job_card.CARDS, "refs.json")))
    except (OSError, ValueError):
        pins = {}
    out, seen = [], set()
    for fmt, cid in sorted(pins.items()):
        if cid in by_id and cid not in seen:
            out.append((by_id[cid], f"pinned reference for {fmt}"))
            seen.add(cid)
    for fmt in sorted({c.get("format") or "" for c in passed}):
        mine = [c for c in passed if (c.get("format") or "") == fmt]
        same = [c for c in mine if ws and (c.get("workstream") or "").lower() in {w.lower() for w in ws}]
        c = (same or mine)[0]
        if c["id"] not in seen:
            out.append((c, f"latest PASS for {fmt or 'no format'}"))
            seen.add(c["id"])
    return out[:MAX]


# ---- what each rule asks of a job ----------------------------------------------------------------------

def _text(card):
    return " ".join(f"{s.get('prog', '')} {s.get('cmd', '')}" for s in card.get("steps") or []).lower()


def _builder_briefs(card):
    return [b for b in card.get("brief") or [] if b.get("who") != job_card.CHECK_AGENT]


def _has(card, *words):
    t = _text(card)
    return any(w in t for w in words)


def _caption(c):
    return _has(c, "caption", "subs"), "no caption step (lint or caption tool) before the hand-over"


def _hand(c):
    if not re.search(r"\bdriv", " ".join(b.get("text", "") for b in c.get("brief") or []), re.I):
        return None, "no driving shots in the brief"
    return _has(c, "gate"), "driving shots went out without the pre-render frame gate"


def _audio(c):
    measured = _has(c, "loudnorm", "ebur128", "lufs") or any(o.get("lufs") is not None for o in c.get("outputs") or [])
    return measured, "no loudness measurement (loudnorm/ebur128 step or LUFS figure) on the card"


def _style(c):
    briefs = _builder_briefs(c) or c.get("brief") or []
    missing = [b.get("who") or "?" for b in briefs if not b.get("style")]
    return not missing, f"the {', '.join(missing)} brief named no style"


def _brand(c):
    text = " ".join(b.get("text", "") for b in c.get("brief") or [])
    named = [name for name, pat in job_card.WORKSTREAMS if re.search(pat, text, re.I)]
    return len(named) <= 1, f"the brief names two brands ({', '.join(named)})"


def _copy(c):
    return _has(c, "slopmonster"), "no /slopmonster pass on the script or caption"


def _facts(c):
    briefs = [b.get("who") for b in c.get("brief") or []]
    return "nq-facts" in briefs or _has(c, "brief nq-facts"), "figures not sent through nq-facts"


def _frame(c):
    return _has(c, "contact", "tile="), "no framing contact sheet in the hand-over"


# keyed by the rule id post_mortem.fix_for() returns (the first keyword of its FIX_FOR entry)
TESTS = {"caption": _caption, "hand": _hand, "audio": _audio, "style": _style, "brand": _brand,
         "ai": _copy, "figure": _facts, "frame": _frame}


def test_card(card, key, check=""):
    """(verdict, why): "pass", "fail" or "n/a" for one past job against the rule for this check key."""
    rows = {check_key(name): v for name, v in (card.get("checks") or {}).items()}
    if rows.get(key) == "FAIL":
        return "fail", f"its own nq-check row for {check or key} was FAIL"
    test = TESTS.get(fix_for(key)[0])
    if not test:
        if key in rows:
            return "pass", f"nq-check row {rows[key]}"
        return "pass", "not checked on that job (pre-flight rule, nothing to test on the card)"
    ok, why = test(card)
    if ok is None:
        return "n/a", why
    return ("pass", "") if ok else ("fail", why)


# ---- the re-check ---------------------------------------------------------------------------------------

def recheck(key, check="", ws=(), fm=(), cards=None):
    """{rule, set: [{id, why, verdict, reason}], passed, failed, na} for the proposal on this check key."""
    key = key or check_key(check)
    rows = []
    for card, why in regression_set(ws, fm, cards):
        verdict, reason = test_card(card, key, check)
        rows.append({"id": card["id"], "format": card.get("format", ""), "workstream": card.get("workstream", ""),
                     "in_set": why, "verdict": verdict, "reason": reason})
    return {"key": key, "check": check or key, "rule": rule_text(key, check or key, ws, fm), "jobs": rows,
            "failed": [r for r in rows if r["verdict"] == "fail"], "na": [r for r in rows if r["verdict"] == "n/a"]}


def summary(res):
    """The one line that goes on the proposal Omarie decides on."""
    jobs, failed = res["jobs"], res["failed"]
    tried = [r for r in jobs if r["verdict"] != "n/a"]
    if not jobs:
        return "Not re-checked: no past passed job of this kind on file yet."
    if not tried:
        return f"Not re-checked: the rule doesn't reach the {len(jobs)} past job(s) on file ({jobs[0]['reason']})."
    n = f"{len(tried)} past job" + ("s" if len(tried) != 1 else "")
    if not failed:
        return f"Re-checked against {n}: all still pass."
    names = "; ".join(f"{r['id']} ({r['reason']})" for r in failed[:3])
    return (f"Re-checked against {n}: {len(failed)} would now fail: {names}. "
            "Narrow the rule or fix those jobs' setup before it lands.")


def rebuild_plan(res, cards=None):
    """The opt-in full test: re-run each job's briefs with the rule added. Text for the lead; no model call."""
    by_id = {c["id"]: c for c in (job_card.load_all() if cards is None else cards)}
    jobs = [r for r in res["jobs"] if r["verdict"] != "n/a"]
    out = [f"Full re-build test for: {res['rule']}",
           f"{len(jobs)} job(s), about {len(jobs) * 2 * AGENT_TOKENS // 1000}k tokens "
           "(one nq-build and one nq-check each). The lead runs them one at a time; a job that comes back FAIL "
           "means the rule breaks it.", ""]
    for i, r in enumerate(jobs, 1):
        card = by_id.get(r["id"], {})
        out.append(f"{i}. {r['id']}  {r['format'] or '?'} · {r['workstream'] or '?'}  [{r['in_set']}]")
        for b in _builder_briefs(card) or card.get("brief") or []:
            out.append(f"   brief {b.get('who')}: {b.get('text', '')[:400]}")
        out.append(f"   + new rule under test: {res['rule']}")
        out.append(f"   then nq-check against the checks it passed: {', '.join(card.get('checks') or {}) or 'its usual list'}")
    return "\n".join(out)


def main(a):
    opt = lambda name: [a[i + 1] for i, x in enumerate(a[:-1]) if x == name]
    ws, fm = opt("--workstream"), opt("--format")
    if not a:
        sys.exit(__doc__)
    if a[0] == "set":
        rows = regression_set(ws, fm)
        for c, why in rows:
            print(f"{c['id']}  {c.get('format') or '-':9} {(c.get('workstream') or '')[:20]:20} {why}")
        return print(f"{len(rows)} job(s) in the regression set" if rows else "no passed job cards on file yet")
    if a[0] in ("check", "rebuild") and len(a) > 1:
        res = recheck(check_key(a[1]), a[1], ws, fm)
        if a[0] == "rebuild":
            return print(rebuild_plan(res))
        if "--json" in a:
            return print(json.dumps(res, indent=1))
        print(f"Proposed rule: {res['rule']}.")
        for r in res["jobs"]:
            print(f"  {r['verdict']:4}  {r['id']}  {r['format'] or '-'} · {r['workstream'] or '-'}  [{r['in_set']}]"
                  + (f"  {r['reason']}" if r["reason"] else ""))
        return print(summary(res))
    sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
