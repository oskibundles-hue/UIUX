#!/usr/bin/env bash
# Stop hook: sums token usage for the turns since the last human message and for the whole session.
HOOK_JSON="$(cat)" python3 - <<'PY'
import json, sys, os
try: h = json.loads(os.environ.get('HOOK_JSON') or '{}')
except Exception: h = {}
path = h.get('transcript_path')
if not path or not os.path.exists(path): sys.exit(0)
tot = {}; last = {}; seen = set(); n_all = n_last = 0
def add(d, u):
    for k in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'): d[k] = d.get(k, 0) + (u.get(k) or 0)
for line in open(path):
    try: e = json.loads(line)
    except Exception: continue
    m = e.get('message') or {}
    if e.get('type') == 'user' and isinstance(m, dict):
        c = m.get('content')
        if isinstance(c, str) or (isinstance(c, list) and c and c[0].get('type') == 'text'): last = {}; n_last = 0
    u = m.get('usage') if isinstance(m, dict) else None
    if not u or m.get('id') in seen: continue
    seen.add(m.get('id')); add(tot, u); add(last, u); n_all += 1; n_last += 1
f = lambda d, k: f"{d.get(k,0):,}"
print(f"Token report | this task: {n_last} turns, output {f(last,'output_tokens')}, new context {f(last,'cache_creation_input_tokens')}, cached re-read {f(last,'cache_read_input_tokens')} | session: {n_all} turns, output {f(tot,'output_tokens')}, new context {f(tot,'cache_creation_input_tokens')}, cached re-read {f(tot,'cache_read_input_tokens')}")
PY
