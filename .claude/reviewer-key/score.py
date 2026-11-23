#!/usr/bin/env python3
"""Score the reviewer against the frozen answer key.

    python3 score.py answers.json [--misses misses.json]

answers.json: a list of {"id", "verdict": "PASS"|"FAIL", "failed": [check ids],
"rows": [{"check", "result", "evidence", "tag": "Seen"|"Inferred"|"Unknown"}]}.
A case is right when the verdict matches and, for a FAIL, every must_catch group
has at least one of its check ids in "failed". A PASS case must list nothing failed.
The key is frozen: if cases.json no longer matches KEY_SHA, scoring refuses.
"""
import hashlib, json, sys
from pathlib import Path

KEY_SHA = "95d60440336f3e90c50ba2723ea64a1980fe5d7db8d503ac09e8aafcb0208dec"
TAGS = {"Seen", "Inferred", "Unknown"}
here = Path(__file__).resolve().parent
raw = (here / "cases.json").read_bytes()
if hashlib.sha256(raw).hexdigest() != KEY_SHA:
    sys.exit("answer key changed since it was frozen; scoring refused (needs Omarie's yes and a new KEY_SHA)")
cases = {c["id"]: c for c in json.loads(raw)["cases"]}

args = sys.argv[1:]
if not args:
    sys.exit(__doc__)
answers = {a["id"]: a for a in json.loads(Path(args[0]).read_text())}
misses, right = [], 0
rows = tagged = 0
for cid, c in cases.items():
    a = answers.get(cid)
    why = []
    if a is None:
        why.append("no answer")
    else:
        failed = set(a.get("failed", []))
        if a.get("verdict") != c["expect"]:
            why.append(f"verdict {a.get('verdict')} but key says {c['expect']}")
        for group in c["must_catch"]:
            if not failed & set(group):
                why.append(f"missed {'/'.join(group)}")
        if c["expect"] == "PASS" and failed:
            why.append(f"flagged {sorted(failed)} on a clean case")
        for r in a.get("rows", []):
            rows += 1
            tagged += r.get("tag") in TAGS
    if why:
        misses.append({"id": cid, "why": why, "sheet": c["sheet"]})
    else:
        right += 1
print(f"answer key: {right} of {len(cases)} right")
print(f"tags: {tagged} of {rows} evidence rows carry Seen/Inferred/Unknown")
for m in misses:
    print(f"  {m['id']}: {'; '.join(m['why'])}")
if "--misses" in args:
    Path(args[args.index("--misses") + 1]).write_text(json.dumps(misses, indent=1))
