#!/usr/bin/env python3
"""Rebuild props.words from word-level transcripts, mapped through the plan's segments.
usage: rewords.py plan.json props.json txdir [drop.json]
drop.json: {"17": [[start,end],...], "18": [...]} clip-time ranges whose words are left out (other voices)."""
import json, sys, os, re
plan, props, txdir = sys.argv[1:4]; drop = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
p = json.load(open(plan)); pr = json.load(open(props))
def clipno(path): return re.search(r'/(\d\d) ', path).group(1)
tx = {}
def words_for(n):
    if n not in tx:
        d = json.load(open(os.path.join(txdir, f'a{n}.json'))); out = []
        for seg in d:
            for w in seg.get('words', []):
                t = (w.get('text') or w.get('word') or w.get('w') or '').strip()
                if t: out.append({'text': t, 'start': float(w.get('start', w.get('s'))), 'end': float(w.get('end', w.get('e')))})
        tx[n] = out
    return tx[n]
at = 0.0; words = []
for s in p['segments']:
    n = clipno(s['clip']); a, b = s['in'], s['out']
    for w in words_for(n):
        if w['start'] >= a and w['end'] <= b + 0.05 and not any(lo <= w['start'] < hi for lo, hi in drop.get(n, [])):
            words.append({'text': w['text'], 'start': round(w['start'] - a + at, 3), 'end': round(min(w['end'], b) - a + at, 3)})
    at += b - a
pr['words'] = words; json.dump(pr, open(props, 'w'))
print(f'{len(words)} words over {at:.1f}s')
