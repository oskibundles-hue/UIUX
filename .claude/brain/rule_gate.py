#!/usr/bin/env python3
"""Before a proposed rule lands, replay it over a small set of past passed jobs (gap 3 of the reel-harness
comparison, 2026-10-26: "nothing that used to pass may fail after an update").

usage: python3 .claude/brain/rule_gate.py check "<proposed rule>" [--format reel] [--json]
       python3 .claude/brain/rule_gate.py review [--days 7]      post_mortem's review, a gate line under each proposal
       python3 .claude/brain/rule_gate.py verdict <bundle> [--file report.md]   record the one nq-check answer
       python3 .claude/brain/rule_gate.py set suggest [--format reel]   passed job cards not yet in the set
       python3 .claude/brain/rule_gate.py set add <card> [--format reel] [--captions f.srt] [--copy f.txt] [--sheet s.jpg]
       python3 .claude/brain/rule_gate.py set remove <card>  |  set list

Nothing is rebuilt: the gate re-checks what past jobs already stored. The replay set is 3 to 5 passed jobs per
format, picked or confirmed by Omarie. Each entry points at a gap 2 job card (job_card.py: brief, steps,
outputs with duration/size/fps/loudness, verdict) and can add what a card doesn't hold: the caption lines,
the on-screen copy and a contact sheet.

A rule is one of three kinds:
  mechanical  a number or a word list the stored outputs can be measured against (caption length or lines,
              duration, loudness, size, fps, banned words, a brief that names the style or playbook).
              Checked here, no model call.
  process     how the team works (sessions, cache, agents, waits, the builder's hand-over steps). It changes no
              delivered file, so no past job can fail it.
  judgement   anything else. The gate writes ONE bundle for the whole set (rule, briefs, outputs, one contact
              sheet) for a single nq-check run. Its answer is saved with `verdict`, and the same rule is never
              bundled twice (Omarie, 2026-10-26: scripts, plus at most one nq-check per proposal).
The last line is the verdict: "safe to land", or "would break N of M past jobs". It goes in the click that puts
the proposal to Omarie.

Cards, the set and the bundles quote briefs and client copy, so they live only in the private brain
(nq-agent-channel/brain/jobcards/ and gate/) or the git-ignored .claude/brain/work/ fallback.
NQOS_JOBCARDS and NQOS_GATE override the folders (tests). Stdlib only; ffmpeg tiles the sheet when installed.
"""
import datetime, glob, hashlib, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nqos_config import HAVE_NOTES, HOME, WORK

# The same folder job_card.py writes to, so the set reuses gap 2's cards rather than keeping a second record.
CARDS = os.environ.get("NQOS_JOBCARDS") or (os.path.join(HOME, "jobcards") if HAVE_NOTES
                                            else os.path.join(WORK, "jobcards"))
GATE = os.environ.get("NQOS_GATE") or (os.path.join(HOME, "gate") if HAVE_NOTES else os.path.join(WORK, "gate"))
REPLAY = os.path.join(CARDS, "replayset.json")
PER_FORMAT = 5
FORMATS = ("carousel", "reel", "poster", "thumbnail", "ad", "promo", "story", "page", "vlog")
IMAGE = (".png", ".jpg", ".jpeg", ".webp")


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- job cards and the replay set ----------------------------------------------------------------------

def cards():
    out = {}
    for p in glob.glob(os.path.join(CARDS, "*.json")):
        if os.path.basename(p) in ("refs.json", "replayset.json"):   # job_diff's pins, the replay set
            continue
        try:
            c = json.load(open(p))
        except (ValueError, OSError):
            continue
        if c.get("id"):
            out[c["id"]] = c
    return out


def card(ref, every=None):
    every = cards() if every is None else every
    if ref in every:
        return every[ref]
    hits = [c for i, c in every.items() if i.startswith(ref)]
    return hits[0] if len(hits) == 1 else None


def replay_set():
    try:
        return json.load(open(REPLAY))
    except (OSError, ValueError):
        return {}


def _save_set(s):
    os.makedirs(CARDS, exist_ok=True)
    with open(REPLAY, "w") as fh:
        json.dump(s, fh, indent=1)


def read_captions(path):
    """Caption lines from an .srt, a .json list or a plain text file (one caption per line)."""
    text = open(path, errors="replace").read()
    if path.lower().endswith(".json"):
        return [str(x) for x in json.loads(text)]
    lines = [l.strip() for l in text.splitlines()]
    if path.lower().endswith((".srt", ".vtt")):
        lines = [l for l in lines if l and not l.isdigit() and "-->" not in l and l != "WEBVTT"]
    return [l for l in lines if l]


def set_add(ref, fmt=None, captions=None, copy=None, sheet=None):
    c = card(ref)
    if not c:
        return f"no job card {ref} in {CARDS}"
    if c.get("verdict") != "PASS":
        return f"{c['id']} did not pass nq-check ({c.get('verdict') or 'no verdict'}); only passed jobs go in the set"
    fmt = fmt or c.get("format")
    if not fmt:
        return "the card has no format; give --format"
    s = replay_set()
    jobs = [e for e in s.get(fmt, []) if e["card"] != c["id"]]
    if len(jobs) >= PER_FORMAT:
        return f"the {fmt} set already has {PER_FORMAT} jobs; remove one first (set list)"
    entry = {"card": c["id"], "added": _now()}
    if captions:
        entry["captions"] = read_captions(captions)
    if copy:
        entry["copy"] = open(copy, errors="replace").read()
    if sheet:
        entry["sheet"] = os.path.abspath(sheet)
    s[fmt] = jobs + [entry]
    _save_set(s)
    return f"{fmt} set: {len(s[fmt])} job(s), added {c['id']}"


def set_remove(ref):
    s, gone = replay_set(), 0
    for fmt in list(s):
        keep = [e for e in s[fmt] if not e["card"].startswith(ref)]
        gone += len(s[fmt]) - len(keep)
        s[fmt] = keep
    _save_set(s)
    return f"removed {gone} job(s)"


def set_suggest(fmt=None):
    """Passed cards not in the set yet, newest first, so the lead can put a pick to Omarie."""
    have = {e["card"] for jobs in replay_set().values() for e in jobs}
    good = sorted((c for c in cards().values() if c.get("verdict") == "PASS" and c["id"] not in have
                   and (not fmt or c.get("format") == fmt)), key=lambda c: c.get("at", ""), reverse=True)
    return [f"{c['id']}  {c.get('format') or '-':9} {c.get('workstream', '')[:20]:20} {c.get('job', '')[:50]}"
            for c in good[:10]]


def replay_jobs(fmt=None):
    """[(entry, card)] for the format, or for every format when none is given."""
    every, out = cards(), []
    for f, jobs in replay_set().items():
        if fmt and f != fmt:
            continue
        for e in jobs:
            out.append((dict(e, format=f), every.get(e["card"])))
    return out


# ---- reading the rule ----------------------------------------------------------------------------------

LESS = r"(?:under|below|less than|shorter than|fewer than|<)"
MOST = r"(?:at most|max(?:imum)?|no more than|no longer than|up to|<=|≤)"
MORE = r"(?:over|above|more than|longer than|>)"
LEAST = r"(?:at least|min(?:imum)?|no less than|no shorter than|>=|≥)"
BOUND = rf"({LESS}|{MOST}|{MORE}|{LEAST})"


def _op(word):
    for pat, op in ((LESS, "<"), (MOST, "<="), (MORE, ">"), (LEAST, ">=")):
        if re.fullmatch(pat, word.strip()):
            return op
    return "=="


def _cmp(v, op, x, tol=0.0):
    return {"<": v < x, "<=": v <= x + tol, ">": v > x, ">=": v >= x - tol, "==": abs(v - x) <= tol}[op]


PROCESS = re.compile(r"\b(session|context|cache|compaction|hand ?off|handoff|reminder|check-in|poll|wait loop|"
                     r"wait on|subagent|agent past|one agent|token|worktree|nq-build|builder|hand-over|hands over|"
                     r"pre-flight|preflight|before nq-check|through nq-facts|slopmonster|pid|scratchpad)\b", re.I)


def parse(rule):
    """The rule as a check: {"kind": "mechanical", "field", "op", "value", "tol", "text"},
    {"kind": "process"} or {"kind": "judgement"}. "text" says in plain words what will be measured."""
    r = rule.lower().replace("’", "'")
    m = re.search(rf"captions?\b[^.]*?{BOUND}\s*(\d+)\s*(?:char|characters|chars|letters)\b", r)
    if m:
        return {"kind": "mechanical", "field": "caption_len", "op": _op(m[1]), "value": int(m[2]), "tol": 0,
                "text": f"every caption line {_op(m[1])} {m[2]} characters"}
    m = re.search(rf"captions?\b[^.]*?{BOUND}\s*(\d+)\s*lines?\b", r)
    if m:
        return {"kind": "mechanical", "field": "caption_lines", "op": _op(m[1]), "value": int(m[2]), "tol": 0,
                "text": f"every caption {_op(m[1])} {m[2]} lines"}
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*lufs", r)
    if m:
        target = float(m[1])
        target = -abs(target)                                   # "14 LUFS" means -14
        tol = re.search(r"(?:±|\+/-|\+-|within)\s*(\d+(?:\.\d+)?)", r)
        b = re.search(rf"{BOUND}\s*-?\d+(?:\.\d+)?\s*lufs", r)
        if re.search(r"louder than|quieter than|no louder|no quieter", r):
            op = "<=" if re.search(r"no louder|quieter than", r) else ">="
            if re.search(r"(?<!no )louder than", r):
                op = ">"
        elif b:
            op = _op(b[1])
        else:
            op = "=="
        t = float(tol[1]) if tol else (1.0 if op == "==" else 0.0)
        return {"kind": "mechanical", "field": "lufs", "op": op, "value": target, "tol": t,
                "text": f"integrated loudness {op} {target:g} LUFS" + (f" (±{t:g})" if t else "")}
    m = re.search(rf"{BOUND}\s*(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds|min|mins|minutes)\b", r)
    if m:
        secs = float(m[2]) * (60 if m[3].startswith("m") else 1)
        return {"kind": "mechanical", "field": "duration", "op": _op(m[1]), "value": secs, "tol": 0,
                "text": f"duration {_op(m[1])} {secs:g} s"}
    m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", r)
    if m:
        return {"kind": "mechanical", "field": "size", "op": "==", "value": f"{m[1]}x{m[2]}", "tol": 0,
                "text": f"size {m[1]}x{m[2]}"}
    m = re.search(r"(\d+(?:\.\d+)?)\s*fps\b", r)
    if m:
        return {"kind": "mechanical", "field": "fps", "op": "==", "value": float(m[1]), "tol": 0.05,
                "text": f"{float(m[1]):g} fps"}
    if re.search(r"\b(never (?:say|use|write)|ban(?:ned)?|don't (?:say|use)|no (?:use of )?)\b", r):
        words = re.findall(r"[\"“']([^\"”']{2,40})[\"”']", rule)
        if words:
            return {"kind": "mechanical", "field": "banned", "op": "none", "value": words, "tol": 0,
                    "text": "no caption or copy uses " + ", ".join(f'"{w}"' for w in words)}
    m = re.search(r"briefs?\b[^.]*\bnames? (?:a|the) (style|playbook)|name the (style|playbook)\b[^.]*\bbriefs?", r)
    if m:
        f = m[1] or m[2]
        return {"kind": "mechanical", "field": f"brief_{f}", "op": "set", "value": "", "tol": 0,
                "text": f"every brief names a {f}"}
    if PROCESS.search(r):
        return {"kind": "process"}
    return {"kind": "judgement"}


def rule_format(rule):
    hits = [f for f in FORMATS if re.search(rf"(?<![a-z]){f}s?(?![a-z])", rule, re.I)]
    return hits[0] if len(hits) == 1 else None


# ---- the mechanical replay -----------------------------------------------------------------------------

def values(field, entry, c):
    """What the job stored for the field, or None when it didn't record it."""
    c = c or {}
    caps = entry.get("captions") or c.get("captions")
    if field in ("caption_len", "caption_lines"):
        if not caps:
            return None
        if field == "caption_len":
            return [l for cap in caps for l in str(cap).split("\n")]
        return caps
    if field in ("duration", "lufs", "fps", "size"):
        got = [(o.get("file") or "output", o[field]) for o in c.get("outputs") or [] if o.get(field) not in (None, "")]
        return got or None
    if field == "banned":
        text = "\n".join([*(caps or []), entry.get("copy") or c.get("copy") or ""])
        return text if text.strip() else None
    if field.startswith("brief_"):
        briefs = [b for b in c.get("brief") or [] if b.get("who") not in ("nq-check",)] or c.get("brief") or []
        return briefs or None
    raise ValueError(field)


def judge(spec, entry, c):
    """("pass" | "fail" | "unknown", reason)."""
    if c is None:
        return "unknown", f"job card {entry['card']} is missing"
    got = values(spec["field"], entry, c)
    f, op, x, tol = spec["field"], spec["op"], spec["value"], spec["tol"]
    if got is None:
        what = {"caption_len": "captions", "caption_lines": "captions", "banned": "captions or copy"}.get(
            f, "a brief" if f.startswith("brief_") else f)
        return "unknown", f"no {what} on record"
    if f == "caption_len":
        bad = [l for l in got if not _cmp(len(l), op, x)]
        return ("fail", f'caption "{bad[0][:50]}" is {len(bad[0])} characters'
                + (f" (+{len(bad) - 1} more)" if len(bad) > 1 else "")) if bad else ("pass", f"{len(got)} lines ok")
    if f == "caption_lines":
        bad = [cap for cap in got if not _cmp(len(str(cap).split("\n")), op, x)]
        return ("fail", f'a caption has {len(str(bad[0]).split(chr(10)))} lines') if bad else ("pass", "ok")
    if f in ("duration", "lufs", "fps"):
        bad = [(n, v) for n, v in got if not _cmp(float(v), op, x, tol)]
        unit = {"duration": " s", "lufs": " LUFS", "fps": " fps"}[f]
        return ("fail", f"{bad[0][0]} is {bad[0][1]:g}{unit}") if bad else ("pass", f"{got[0][1]:g}{unit}")
    if f == "size":
        bad = [(n, v) for n, v in got if v != x]
        return ("fail", f"{bad[0][0]} is {bad[0][1]}") if bad else ("pass", x)
    if f == "banned":
        hit = [w for w in x if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", got, re.I)]
        return ("fail", "uses " + ", ".join(f'"{w}"' for w in hit)) if hit else ("pass", "none used")
    key = f.split("_", 1)[1]
    bad = [b.get("who", "?") for b in got if not b.get(key)]
    return ("fail", f"the {bad[0]} brief names no {key}") if bad else ("pass", f"{len(got)} brief(s) name one")


def verdict_line(results):
    m = len(results)
    if not m:
        return "can't tell: no replay set for this format yet (pick 3-5 passed jobs: rule_gate.py set suggest)"
    fails = [r for r in results if r["status"] == "fail"]
    unknown = [r for r in results if r["status"] == "unknown"]
    if fails:
        return f"would break {len(fails)} of {m} past jobs"
    if len(unknown) == m:
        return f"can't tell: none of the {m} past jobs recorded what this rule measures"
    if unknown:
        return f"safe to land on {m - len(unknown)} of {m} past jobs ({len(unknown)} didn't record it)"
    return f"safe to land ({m} of {m} past jobs still pass)"


# ---- the judgement bundle ------------------------------------------------------------------------------

def bundle_id(rule, fmt):
    key = re.sub(r"\s+", " ", rule.strip().lower()) + "|" + (fmt or "")
    return hashlib.sha1(key.encode()).hexdigest()[:10]


def contact_sheet(paths, out):
    """Tile the jobs' sheets into one image (3 across), so nq-check opens one file. None without ffmpeg."""
    paths = [p for p in paths if p and os.path.isfile(p) and p.lower().endswith(IMAGE)]
    if not paths or not shutil.which("ffmpeg"):
        return None
    if len(paths) == 1:
        shutil.copy(paths[0], out)
        return out
    cols = min(3, len(paths))
    rows = -(-len(paths) // cols)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p in paths:
        cmd += ["-i", p]
    chain = "".join(f"[{i}:v]scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2:color=gray[t{i}];"
                    for i in range(len(paths)))
    layout = "|".join(f"{(i % cols) * 480}_{(i // cols) * 480}" for i in range(len(paths)))
    chain += "".join(f"[t{i}]" for i in range(len(paths))) + f"xstack=inputs={len(paths)}:layout={layout}:fill=gray"
    try:
        subprocess.run(cmd + ["-filter_complex", chain, "-frames:v", "1", out], check=True, capture_output=True, timeout=60)
    except (subprocess.SubprocessError, OSError):
        return None
    return out if os.path.isfile(out) else None


def make_bundle(rule, fmt, jobs):
    """One folder for one nq-check run over the whole set: prompt.md, jobs.md, sheet.jpg. Reused when the
    same rule comes back, so a proposal never costs a second run."""
    d = os.path.join(GATE, bundle_id(rule, fmt))
    if os.path.isfile(os.path.join(d, "verdict.json")):
        return d, json.load(open(os.path.join(d, "verdict.json")))
    os.makedirs(d, exist_ok=True)
    lines = [f"# Replay set for: {rule}", ""]
    ids = []
    for e, c in jobs:
        c = c or {}
        ids.append(e["card"])
        lines += [f"## {e['card']}  ({e['format']}, {c.get('workstream', '')}, style {c.get('style') or '-'})",
                  f"job: {c.get('job', '')}"]
        for b in c.get("brief") or []:
            lines.append(f"brief ({b.get('who')}): {b.get('text', '')[:400]}")
        for o in c.get("outputs") or []:
            lines.append("output: " + ", ".join(f"{k} {v}" for k, v in o.items()))
        if e.get("captions"):
            lines.append("captions: " + " / ".join(e["captions"][:20]))
        if e.get("copy"):
            lines.append("copy: " + e["copy"][:600])
        lines.append(f"sheet: {e.get('sheet') or '-'}")
        lines.append("")
    open(os.path.join(d, "jobs.md"), "w").write("\n".join(lines))
    sheet = contact_sheet([e.get("sheet") for e, _ in jobs], os.path.join(d, "sheet.jpg"))
    prompt = (f"Gate check, one run for the whole set. Proposed rule: \"{rule}\".\n"
              f"These {len(jobs)} past jobs all passed nq-check before. Judge each one ONLY against the proposed "
              "rule, from what is on file: the briefs, outputs and captions in jobs.md"
              + (", and the one contact sheet sheet.jpg (a tile per job, in the order of jobs.md)" if sheet else "")
              + f". Files: {d}. Don't rebuild or re-render anything.\n"
              "Answer with a table: job id | PASS/FAIL | evidence (one line). Job ids: " + ", ".join(ids) + ".\n"
              "PASS means the job would still pass with the rule in place.")
    open(os.path.join(d, "prompt.md"), "w").write(prompt)
    json.dump({"rule": rule, "format": fmt, "jobs": ids, "at": _now()}, open(os.path.join(d, "bundle.json"), "w"), indent=1)
    return d, None


VERDICT_CELL = re.compile(r"^[^\w]*\**\s*(PASS|FAIL)\b", re.I)


def record_verdict(d, report):
    """Read nq-check's table for the bundle and save it; the gate reuses it from then on."""
    meta = json.load(open(os.path.join(d, "bundle.json")))
    results = []
    for line in report.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [re.sub(r"[*`]", "", c).strip() for c in line.strip().strip("|").split("|")]
        job = next((j for j in meta["jobs"] if cells and (cells[0] == j or cells[0].startswith(j[:12]))), None)
        i = next((i for i, c in enumerate(cells) if i and VERDICT_CELL.match(c)), None)
        if job and i and job not in {r["job"] for r in results}:
            why = next((c for c in cells[i + 1:] if c), "")
            results.append({"job": job, "status": VERDICT_CELL.match(cells[i])[1].lower(), "why": why[:120]})
    for j in meta["jobs"]:
        if j not in {r["job"] for r in results}:
            results.append({"job": j, "status": "unknown", "why": "not in nq-check's table"})
    out = {"at": _now(), "results": results, "verdict": verdict_line(results)}
    json.dump(out, open(os.path.join(d, "verdict.json"), "w"), indent=1)
    return out


# ---- the gate ------------------------------------------------------------------------------------------

def gate(rule, fmt=None):
    fmt = fmt or rule_format(rule)
    spec = parse(rule)
    jobs = replay_jobs(fmt)
    res = {"rule": rule, "format": fmt or "all", "kind": spec["kind"], "jobs": len(jobs)}
    if spec["kind"] == "process":
        res["verdict"] = "safe to land (process rule: it changes how the team works, not a delivered file)"
        return res
    if spec["kind"] == "mechanical":
        res["measures"] = spec["text"]
        res["results"] = [dict(zip(("status", "why"), judge(spec, e, c)), job=e["card"]) for e, c in jobs]
        res["verdict"] = verdict_line(res["results"])
        return res
    if not jobs:
        res["verdict"] = verdict_line([])
        return res
    d, done = make_bundle(rule, fmt, jobs)
    res["bundle"] = d
    if done:
        res["results"], res["verdict"] = done["results"], done["verdict"] + f" (nq-check, {done['at'][:10]})"
    else:
        res["verdict"] = (f"needs judgement: one nq-check run over all {len(jobs)} jobs, brief in {d}/prompt.md, "
                          f"then rule_gate.py verdict {d} < report")
    return res


def show(res):
    out = [f"rule: {res['rule']}", f"kind: {res['kind']}" + (f" ({res['measures']})" if res.get("measures") else ""),
           f"replay set: {res['jobs']} past job(s), format {res['format']}"]
    for r in res.get("results", []):
        out.append(f"  {r['status'].upper():7} {r['job']}  {r['why']}")
    out.append(f"verdict: {res['verdict']}")
    return "\n".join(out)


def review(days=7):
    """post_mortem's weekly review, which now carries the gate's verdict under each proposal itself."""
    import post_mortem
    return post_mortem.review(days)


def main(a):
    opt = lambda n: a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else None
    if a[:1] == ["check"] and len(a) > 1:
        res = gate(a[1], opt("--format"))
        print(json.dumps(res, indent=1) if "--json" in a else show(res))
        return 1 if res["verdict"].startswith("would break") else 0
    if a[:1] == ["review"]:
        print(review(int(opt("--days") or 7)))
        return 0
    if a[:1] == ["verdict"] and len(a) > 1:
        report = open(opt("--file")).read() if opt("--file") else sys.stdin.read()
        out = record_verdict(a[1], report)
        for r in out["results"]:
            print(f"  {r['status'].upper():7} {r['job']}  {r['why']}")
        print(f"verdict: {out['verdict']}")
        return 0
    if a[:1] == ["set"] and len(a) > 1:
        if a[1] == "add" and len(a) > 2:
            print(set_add(a[2], opt("--format"), opt("--captions"), opt("--copy"), opt("--sheet")))
        elif a[1] == "remove" and len(a) > 2:
            print(set_remove(a[2]))
        elif a[1] == "suggest":
            print("\n".join(set_suggest(opt("--format"))) or "no passed job cards to add yet")
        elif a[1] == "list":
            for fmt, jobs in replay_set().items():
                print(f"{fmt}: " + (", ".join(e["card"] for e in jobs) or "-"))
        else:
            sys.exit(__doc__)
        return 0
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
