#!/usr/bin/env python3
"""tail_check.py -- fix A (Omarie, 6 Oct): every dialog out-point against the end of its last word.

For each EDL dialog piece (with config `audio.trims` applied) the last word's end is small.en's (the day index in
paths.transcripts, the captions' timing source); the next word's start is the later of small.en's and medium.en's (beam 5,
data/words_medium.json), because whisper stretches a word back over the pause before it. medium.en's own gap is listed too. The gap = out-point - last word end. The build aims for >= 350 ms (tools/make_edl.py `tail`); a gap
under 300 ms fails. It also fails a tail that cuts into a next word (the out-point inside a word of either model), and
two voices overlapping on the timeline.
    python3 tools/tail_check.py          # prints the table, exit 1 on a failure
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_GAP = 0.300


def _cfg():
    return json.load(open(os.path.join(ROOT, 'config.json')))


def words(src, med, tr_dir):
    t = json.load(open(os.path.join(tr_dir, f'{src}.json')))
    sm = [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]
    return sm, med


def inside(w, a, b):
    return min(w[1], b) - max(w[0], a) >= 0.15 or (a - 1e-6 <= w[0] < b - 0.1)


def rows():
    C = _cfg()
    edl = json.load(open(os.path.join(ROOT, C['paths']['edl'])))
    med = json.load(open(os.path.join(ROOT, 'data', 'words_medium.json')))
    trims = C['audio'].get('trims', {})
    out = []
    for i, d in enumerate(edl['dialog']):
        tr = trims.get(str(i), {})
        a, b = d['in'] + tr.get('in', 0.0), d['out'] + tr.get('out', 0.0)
        t = json.load(open(os.path.join(C['paths']['transcripts'], f"{d['src']}.json")))
        sm = [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]
        md = [[w[0], w[1], w[2].strip()] for w in med.get(f"{d['src']}:{d['in']:.2f}", [])]
        # the piece's words: inside [in, out - TAIL] (the tail itself holds no word by construction)
        lim = d.get('last_word_end', b) + 0.01
        p = [w for w in sm if inside(w, a, lim)]
        le = p[-1][1] if p else a
        pm = [w for w in md if inside(w, a, lim)]
        nxt = [n[0][0] for n in ([w for w in m if w[0] > q[-1][0] + 0.01 and not inside(w, a, lim)] for m, q in ((sm, p), (md, pm)) if q) if n]
        no = max(nxt) if nxt else 1e9           # the next word's start: the later of the two models' (whisper stretches a
        cut_word = [] if b <= no - 0.02 else ['next word starts at %.2f' % no]   # word over the pause before it)
        out.append(dict(i=i, src=d['src'], out=round(b, 3), last_word_end=round(le, 3), gap=round(b - le, 3),
                        gap_medium=round(b - pm[-1][1], 3) if pm else None,
                        t0=round(d['t'], 3), t1=round(d['t'] + b - a, 3), cut_word=cut_word, extended=bool(d.get('extended'))))
    return out


def gate_items():
    """for build.py st_gates: errors for every failure, one check line with the summary."""
    R = rows()
    g = []
    for r in R:
        if r['gap'] < MIN_GAP:
            g.append(dict(level='error', code='TAIL', what=f"dialog {r['i']} ({r['src']}) out {r['out']} is {r['gap'] * 1000:.0f} ms after its last word (< 300 ms)"))
        if r['cut_word']:
            g.append(dict(level='error', code='TAIL', what=f"dialog {r['i']} ({r['src']}) out {r['out']} cuts into {r['cut_word']}"))
    for p, q in zip(R, R[1:]):
        if q['t0'] < p['t1'] - 1e-3:
            g.append(dict(level='error', code='TAIL', what=f"dialog {p['i']} tail runs into dialog {q['i']} ({p['t1']} > {q['t0']})"))
    g.append(dict(level='check', code='TAIL', what=f"tail check: {len(R)} pieces, min gap {min(r['gap'] for r in R) * 1000:.0f} ms, "
                                                  f"{sum(r['extended'] for r in R)} extended"))
    return g


if __name__ == '__main__':
    R = rows()
    print(f"{'i':>2} {'src':4} {'out':>8} {'lastend':>8} {'gap_ms':>6}  timeline")
    for r in R:
        print(f"{r['i']:2d} {r['src']} {r['out']:8.2f} {r['last_word_end']:8.2f} {r['gap'] * 1000:6.0f}  {r['t0']:7.2f}-{r['t1']:7.2f}"
              f"{'  EXT' if r['extended'] else ''}{'  CUTS ' + str(r['cut_word']) if r['cut_word'] else ''}")
    G = [x for x in gate_items() if x['level'] == 'error']
    print(gate_items()[-1]['what'])
    for x in G:
        print('FAIL', x['what'])
    sys.exit(1 if G else 0)
