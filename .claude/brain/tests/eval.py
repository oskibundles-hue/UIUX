#!/usr/bin/env python3
"""Check recall.py against questions with known answers (no model, about 0.1 s per question).

usage: NQOS_HOME=/path/to/brain python3 .claude/brain/tests/eval.py [questions.json]
A question passes when recall.py's top note is one of its "key" files.
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
RECALL = os.path.join(os.path.dirname(HERE), "recall.py")
qs = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "questions.json")))
ok, t0 = 0, time.time()
for item in qs:
    out = subprocess.run([sys.executable, RECALL, item["q"], "--json"], capture_output=True, text=True)
    top = (json.loads(out.stdout or "{}").get("top") or {}).get("file")
    hit = top in item["key"]
    ok += hit
    print(f"{'PASS' if hit else 'MISS'}  {item['q']!r} -> {top} (want {', '.join(item['key'])})")
print(f"\n{ok}/{len(qs)} right, {time.time() - t0:.1f} s total")
sys.exit(0 if ok == len(qs) else 1)
