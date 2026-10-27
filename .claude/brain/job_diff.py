#!/usr/bin/env python3
"""Line a failed job up against a good one of the same kind and name the first place they split.

usage: python3 .claude/brain/job_diff.py <failed card id | path> [--ref <card id | path | format>] [--json]
       python3 .claude/brain/job_diff.py latest [--ref ...]          the newest FAIL card
       python3 .claude/brain/job_diff.py pin <card id> [--format reel]  make a card the reference for its format
       python3 .claude/brain/job_diff.py unpin <format>

This is "gap 2" of the reel-harness comparison (its "Precise error signals" box: a failed run beside a
reference run, and the first step where they differ). nq-check says *what* failed; this says *where the job
went wrong*: a brief that left out the style, a different ffmpeg flag, an output at the wrong loudness.

The reference: the card pinned for the format (`pin`; Omarie's pick wins), else the latest PASS of the same
format, preferring the same workstream. --ref overrides with a card or a format.

The comparison runs in the order a job runs, and the first difference found is the first divergence:
  1. setup    workstream, style, playbook
  2. briefs   which agents were briefed, and the style and playbook each brief named
  3. steps    the working steps, aligned by program (difflib), then flag by flag where they match
  4. outputs  duration, size, fps, loudness (with tolerances)
  5. checks   nq-check rows that passed on the good job and failed here
Timestamps, session ids, paths and media file names never count (they always differ).
Cards come from job_card.py. Stdlib only, no model call, about 0.05 s.
"""
import difflib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import job_card

REFS = os.path.join(job_card.CARDS, "refs.json")
# Steps that only keep house: they don't shape the output, so they don't count as a divergence.
HOUSEKEEPING = re.compile(r"^(mkdir|rm|touch|chmod|ln|cp|mv|git (add|commit|push|checkout|switch|merge|pull|stash|worktree|clone)|"
                          r"python -c|python [\w-]*(live_card|cost_meter|recall|job_card|job_diff|costlog_push)\.py|"
                          r"brief nq-check|brief claude-code-guide|brief Explore|curl|pip|npm|apt(-get)?)\b")
MEDIA_NAME = re.compile(job_card.MEDIA + "$", re.I)
TOL = {"duration": 0.5, "fps": 0.05, "lufs": 1.0}


def refs():
    try:
        return json.load(open(REFS))
    except (OSError, ValueError):
        return {}


def pin(card_id, fmt=None):
    card = job_card.load(card_id)
    if not card:
        sys.exit(f"no card {card_id}")
    fmt = fmt or card.get("format")
    if not fmt:
        sys.exit("the card has no format; give --format")
    r = refs()
    r[fmt] = card["id"]
    os.makedirs(job_card.CARDS, exist_ok=True)
    json.dump(r, open(REFS, "w"), indent=1)
    return f"reference for {fmt}: {card['id']}"


def reference(failed, ref=None):
    """(card, why) for the good job to compare against, or (None, why not)."""
    if ref and not re.fullmatch(r"[a-z]+", ref):
        c = job_card.load(ref)
        return (c, "picked with --ref") if c else (None, f"no card {ref}")
    fmt = ref or failed.get("format")
    if not fmt:
        return None, "the failed job has no format, so there is no reference; pass --ref <card>"
    pinned = refs().get(fmt)
    if pinned and pinned != failed.get("id"):
        c = job_card.load(pinned)
        if c:
            return c, f"pinned reference for {fmt}"
    good = [c for c in job_card.load_all() if c.get("format") == fmt and c.get("verdict") == "PASS"
            and c.get("id") != failed.get("id")]
    if not good:
        return None, f"no passed {fmt} job on file yet"
    same = [c for c in good if c.get("workstream") and c.get("workstream") == failed.get("workstream")]
    return (same or good)[0], f"latest PASS for {fmt}" + (f" ({same[0]['workstream']})" if same else "")


# ---- comparison ----------------------------------------------------------------------------------------

def _show(v):
    return v if v not in ("", None) else "(none)"


def setup_diffs(f, r):
    out = []
    for key in ("workstream", "style", "playbook"):
        if (f.get(key) or "") != (r.get(key) or ""):
            out.append(("setup", key, f"{key}: {_show(f.get(key))}  ·  good job: {_show(r.get(key))}"))
    return out


def brief_diffs(f, r):
    out = []
    fw = [b.get("who") for b in f.get("brief") or []]
    rw = [b.get("who") for b in r.get("brief") or []]
    for who in [w for w in rw if w not in fw]:
        out.append(("briefs", who, f"the good job briefed {who}; this job didn't"))
    for who in [w for w in fw if w not in rw]:
        out.append(("briefs", who, f"this job briefed {who}; the good job didn't"))
    for fb in f.get("brief") or []:
        rb = next((b for b in r.get("brief") or [] if b.get("who") == fb.get("who")), None)
        if not rb:
            continue
        for key in ("style", "playbook"):
            if (fb.get(key) or "") != (rb.get(key) or ""):
                gap = "named no " + key if not fb.get(key) else f"named {key} {fb.get(key)}"
                out.append(("briefs", f"{fb.get('who')} {key}",
                            f"the {fb.get('who')} brief {gap}  ·  good job: {_show(rb.get(key))}"))
    return out


def _flags(step):
    d = {}
    for k, v in step.get("flags") or []:
        v = "<media>" if MEDIA_NAME.match(v or "") else v
        d[k] = f"{d[k]} {v}".strip() if k in d else v
    return d


def _parts(v):
    return set(p for p in re.split(r"[,;\[\]]", v or "") if p)


def _flag_change(k, a, b):
    if a is None:
        return f"{k} only on the good job ({b})" if b else f"{k} only on the good job"
    if b is None:
        return f"{k} only on this job ({a})" if a else f"{k} only on this job"
    pa, pb = _parts(a), _parts(b)
    if len(pa) > 1 or len(pb) > 1:                     # a filter graph: show just the pieces that differ
        a, b = ",".join(sorted(pa - pb)) or "-", ",".join(sorted(pb - pa)) or "-"
    return f"{k} {a}  ·  good job: {b}"


def work_steps(card):
    return [s for s in card.get("steps") or [] if not HOUSEKEEPING.match(s.get("prog", ""))]


def step_diffs(f, r):
    fs, rs = work_steps(f), work_steps(r)
    keys = lambda steps: [s.get("prog", "") for s in steps]
    out = []
    sm = difflib.SequenceMatcher(None, keys(fs), keys(rs), autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for a, b in zip(fs[i1:i2], rs[j1:j2]):
                fa, fb = _flags(a), _flags(b)
                changed = [k for k in list(fb) + [k for k in fa if k not in fb] if fa.get(k) != fb.get(k)]
                if changed:
                    n = fs.index(a) + 1
                    lines = [_flag_change(k, fa.get(k), fb.get(k)) for k in changed[:4]]
                    out.append(("steps", f"step {n} {a['prog']}",
                                f"step {n}, {a['prog']} ({a.get('who')}): " + "; ".join(lines)))
            continue
        for k in range(max(i2 - i1, j2 - j1)):
            a = fs[i1 + k] if i1 + k < i2 else None
            b = rs[j1 + k] if j1 + k < j2 else None
            n = (i1 + k + 1) if a else i1 + 1
            if a and b:
                text = f"step {n}: this job ran `{a['cmd'][:90]}` ({a.get('who')}); the good job ran `{b['cmd'][:90]}` ({b.get('who')})"
            elif b:
                text = f"step {n}: missing here; the good job ran `{b['cmd'][:90]}` ({b.get('who')})"
            else:
                text = f"step {n}: extra here, `{a['cmd'][:90]}` ({a.get('who')}); the good job had no such step"
            out.append(("steps", f"step {n} {(a or b)['prog']}", text))
    return out


def output_diffs(f, r):
    out = []
    fo, ro = f.get("outputs") or [], r.get("outputs") or []
    for i, (a, b) in enumerate(zip(fo, ro)):
        label = a.get("file") or b.get("file") or f"output {i + 1}"
        for key in ("duration", "size", "fps", "lufs"):
            va, vb = a.get(key), b.get(key)
            if va is None or vb is None:
                continue
            if key in TOL:
                if abs(float(va) - float(vb)) <= max(TOL[key], 0.02 * abs(float(vb)) if key == "duration" else 0):
                    continue
            elif va == vb:
                continue
            unit = {"duration": " s", "lufs": " LUFS"}.get(key, "")
            out.append(("outputs", f"{label} {key}", f"{label}: {key} {va}{unit}  ·  good job: {vb}{unit}"))
    if len(fo) != len(ro) and fo and ro:
        out.append(("outputs", "count", f"{len(fo)} output file(s)  ·  good job: {len(ro)}"))
    return out


def check_diffs(f, r):
    rc = r.get("checks") or {}
    return [("checks", name, f"{name}: FAIL  ·  good job: {rc.get(name, 'not checked')}")
            for name, v in (f.get("checks") or {}).items() if v == "FAIL"]


def diff(failed, ref):
    return (setup_diffs(failed, ref) + brief_diffs(failed, ref) + step_diffs(failed, ref)
            + output_diffs(failed, ref) + check_diffs(failed, ref))


def _line(card):
    fails = [k for k, v in (card.get("checks") or {}).items() if v == "FAIL"]
    bits = [card.get("format") or "?", card.get("workstream") or "?", card.get("style") or "no style",
            card.get("verdict") or "?"]
    return f"{card.get('id')}  " + " · ".join(bits) + (f" ({', '.join(fails[:3])})" if fails else "")


def report(failed, ref, why, limit=6):
    diffs = diff(failed, ref)
    out = [f"Failed job: {_line(failed)}", f"Good job:   {_line(ref)}  [{why}]", ""]
    if not diffs:
        return "\n".join(out + ["No difference found between the two jobs' records."])
    stage, _, text = diffs[0]
    out.append(f"First divergence ({stage}): {text}")
    rest = diffs[1:]
    if rest:
        out.append("Then:")
        out += [f"  - ({s}) {t}" for s, _, t in rest[:limit]]
        if len(rest) > limit:
            out.append(f"  ... {len(rest) - limit} more (job_diff.py {failed.get('id')} --json)")
    return "\n".join(out)


def first_divergence(failed, ref=None):
    """The one-paragraph note for the hook, or None when there is no reference yet."""
    good, why = reference(failed, ref)
    if not good:
        return None, why
    return report(failed, good, why, limit=4), why


def main(a):
    if not a:
        sys.exit(__doc__)
    if a[0] == "pin" and len(a) > 1:
        return print(pin(a[1], a[a.index("--format") + 1] if "--format" in a else None))
    if a[0] == "unpin" and len(a) > 1:
        r = refs()
        r.pop(a[1], None)
        os.makedirs(job_card.CARDS, exist_ok=True)
        json.dump(r, open(REFS, "w"), indent=1)
        return print(f"no pinned reference for {a[1]}; the latest PASS is used")
    ref = a[a.index("--ref") + 1] if "--ref" in a else None
    if a[0] == "latest":
        failed = next((c for c in job_card.load_all() if c.get("verdict") == "FAIL"), None)
    else:
        failed = job_card.load(a[0])
    if not failed:
        sys.exit(f"no card {a[0]} (job_card.py list shows the saved ones)")
    good, why = reference(failed, ref)
    if not good:
        sys.exit(f"No reference: {why}.")
    if "--json" in a:
        return print(json.dumps({"failed": failed.get("id"), "ref": good.get("id"), "why": why,
                                 "diffs": [{"stage": s, "where": w, "text": t} for s, w, t in diff(failed, good)]}, indent=1))
    print(report(failed, good, why))


if __name__ == "__main__":
    main(sys.argv[1:])
