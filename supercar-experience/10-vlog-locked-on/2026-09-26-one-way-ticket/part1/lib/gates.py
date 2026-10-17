"""gates.py: automatic QA gates for the rally-v2 build, run BEFORE the full render (build.py prep / --draft) and again in QA.

  lock_gate      every lock-on (convoy hop segments, single locks) is checked frame by frame against its tracked box:
                 a car that leaves the frame (less than MIN_VIS of its box on screen) or whose track is lost (tracker
                 confidence under MIN_CONF for LOST_N frames) while its lock is shown is released automatically: a convoy
                 hop into the next car becomes a LOCK LOST re-lock that snaps once the next car is in frame; a single
                 lock (or the last car of a convoy) exits as its car leaves. Every change is reported.
  shot_scan      every rendered shot (.work/shots/NN.mov), sampled at 10 fps at 1/8 size: black, near-constant and
                 lens-blocked frames (a frame whose detail collapses against its own shot's median while a large area
                 goes flat and smooth: a hand, an arm or a pocket over the lens). Cached per shot signature.
  caption_gate   caption pieces whose words sit more than 0.2 s off the speech (build.py caption_sync).
  loud_gate      the mix (mix.json) and the delivered files: -14 LUFS +-0.5, true peak <= -1.5 dBTP.
  quote_gate     every quote card: its label and source clip, for a human to confirm who is speaking (no speaker
                 labels exist in the transcripts; a card labelled GUEST is flagged louder).
"""
import json, math, os, subprocess
import numpy as np

W, H = 1080, 1920
MIN_VIS = 0.4          # fraction of the tracked box that must be on screen while its lock is shown
MIN_CONF, LOST_N = 0.15, 8
GRACE = 2              # frames released before the first failing frame


def _box(tr, f):
    fr = tr['frames']
    i = f - tr['f0']
    if i < 0 or i >= len(fr):
        return None
    return fr[i]


def visible(b):
    if b is None:
        return 0.0
    x0, y0, x1, y1 = max(0, b['x']), max(0, b['y']), min(W, b['x'] + b['w']), min(H, b['y'] + b['h'])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0) / max(1.0, b['w'] * b['h'])


def _first_fail(tr, fa, fb):
    """first frame in [fa, fb) where the target is off screen or its track lost; None if it holds."""
    low = 0
    for f in range(fa, fb):
        b = _box(tr, f)
        if b is None or visible(b) < MIN_VIS:
            return f
        low = low + 1 if b.get('conf', 1) < MIN_CONF else 0
        if low >= LOST_N:
            return f - LOST_N + 1
    return None


def _first_ok(tr, fa, fb):
    for f in range(fa, fb):
        b = _box(tr, f)
        if b is not None and visible(b) >= MIN_VIS and b.get('conf', 1) >= MIN_CONF:
            return f
    return None


def lock_gate(comps, tracks, fps):
    rep = []
    fr = lambda t: int(round(t * fps))
    for c in comps:
        p = c.get('p', {})
        if c['type'] == 'convoyHop':
            S = p['segs']
            for i, s in enumerate(S):
                tr = tracks.get(s['track'])
                if tr is None:
                    rep.append(dict(code=c['code'], level='error', what=f"{s['make']}: no track {s['track']}"))
                    continue
                snap = s['t'] + (s.get('lost', 0.36) if s.get('mode') == 'relock' else 0)
                end = S[i + 1]['t'] if i + 1 < len(S) else p['exit']
                # the new car must be on screen when the brackets snap onto it
                f_ok = _first_ok(tr, fr(snap), fr(end))
                if f_ok is None:
                    rep.append(dict(code=c['code'], level='error', what=f"{s['make']}: never in frame while its lock is shown ({snap:.2f}-{end:.2f} s)"))
                    continue
                if f_ok > fr(snap) + 1 and i > 0:
                    new_snap = f_ok / fps
                    if s.get('mode') == 'relock':
                        s['lost'] = round(new_snap - s['t'], 3)
                    else:
                        s['mode'], s['lost'] = 'relock', round(new_snap - s['t'], 3)
                    rep.append(dict(code=c['code'], level='auto', what=f"{s['make']}: not in frame at {snap:.2f} s -> LOCK LOST, snaps at {new_snap:.2f} s"))
                    snap = new_snap
                ff = _first_fail(tr, fr(snap) + 1, fr(end))
                if ff is None:
                    continue
                t_rel = max(snap + 0.3, (ff - GRACE) / fps)
                if i + 1 < len(S):
                    nx = S[i + 1]
                    nsnap = nx['t'] + (nx.get('lost', 0.36) if nx.get('mode') == 'relock' else 0)
                    ntr = tracks.get(nx['track'])
                    f_n = _first_ok(ntr, fr(max(nsnap, t_rel)), fr(S[i + 2]['t'] if i + 2 < len(S) else p['exit'])) if ntr else None
                    nsnap = f_n / fps if f_n is not None else nsnap
                    old = f"{nx.get('mode', 'hop')} at {nx['t']:.2f}"
                    nx['mode'], nx['t'], nx['lost'] = 'relock', round(t_rel, 3), round(max(0.2, nsnap - t_rel), 3)
                    rep.append(dict(code=c['code'], level='auto', what=f"{s['make']} leaves the frame at {ff / fps:.2f} s: {old} -> LOCK LOST at {nx['t']:.2f}, "
                                                                        f"{nx['make']} locks at {nx['t'] + nx['lost']:.2f}"))
                else:
                    old = p['exit']; p['exit'] = round(t_rel, 3); c['t1'] = min(c['t1'], p['exit'] + 0.4)
                    rep.append(dict(code=c['code'], level='auto', what=f"{s['make']} leaves the frame at {ff / fps:.2f} s: exit {old:.2f} -> {p['exit']:.2f}"))
        elif c['type'] in ('v2lock', 'leadLock', 'personLock'):
            tr = tracks.get(p.get('track'))
            if tr is None:
                rep.append(dict(code=c['code'], level='error', what=f"no track {p.get('track')}")); continue
            a, ex = p.get('acquire', c['t0']), p.get('exit', c['t1'] - 0.3)
            ff = _first_fail(tr, fr(a), fr(ex))
            if ff is not None:
                t_rel = max(a + 0.5, (ff - GRACE) / fps)
                rep.append(dict(code=c['code'], level='auto', what=f"{p.get('name', c['code'])} leaves the frame / loses track at {ff / fps:.2f} s: exit {ex:.2f} -> {t_rel:.2f}"))
                p['exit'] = round(t_rel, 3); c['t1'] = min(c['t1'], p['exit'] + 0.4)
    return comps, rep


# ------------------------------------------------------------------------------ shots
def _frames(ff, path, n, fps_s=10):
    w, h = 135, 240
    raw = subprocess.run([ff, '-v', 'error', '-i', path, '-vf', f'fps={fps_s},scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32) / 255


def frame_stats(g):
    """per frame: mean luma, std, detail (mean abs Laplacian), flat fraction (8x8 blocks with std < 0.012)."""
    lap = np.abs(4 * g[:, 1:-1, 1:-1] - g[:, :-2, 1:-1] - g[:, 2:, 1:-1] - g[:, 1:-1, :-2] - g[:, 1:-1, 2:])
    det = lap.mean((1, 2))
    n, h, w = g.shape
    blk = g[:, :h // 8 * 8, :w // 8 * 8].reshape(n, h // 8, 8, w // 8, 8).std((2, 4))
    flat = (blk < 0.012).mean((1, 2))
    return g.mean((1, 2)), g.std((1, 2)), det, flat


def shot_scan(ff, shots_dir, fr_table, shots, sigs, cache_path):
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    out = []
    fps = 30000 / 1001
    from concurrent.futures import ThreadPoolExecutor
    need = [(k, f0, f1) for k, f0, f1 in fr_table if shots[k]['src'] != 'card' and os.path.exists(os.path.join(shots_dir, f'{k:02d}.mov'))
            and f'{k}:{sigs.get(k, "")}' not in cache]
    def one(item):
        k, f0, f1 = item
        m, s, d, fl = frame_stats(_frames(ff, os.path.join(shots_dir, f'{k:02d}.mov'), f1 - f0))
        return f'{k}:{sigs.get(k, "")}', dict(mean=[round(float(v), 4) for v in m], std=[round(float(v), 4) for v in s],
                                              det=[round(float(v), 5) for v in d], flat=[round(float(v), 3) for v in fl])
    with ThreadPoolExecutor(4) as ex:
        for key, st in ex.map(one, need):
            cache[key] = st
    for k, f0, f1 in fr_table:
        key = f'{k}:{sigs.get(k, "")}'
        if shots[k]['src'] == 'card' or key not in cache:
            continue
        st = cache[key]
        m, s, d, fl = (np.array(st[x]) for x in ('mean', 'std', 'det', 'flat'))
        med_d, med_f = float(np.median(d)), float(np.median(fl))
        bad = []
        for j in range(len(m)):
            why = []
            if m[j] < 0.025:
                why.append('black')
            elif s[j] < 0.02:
                why.append('near-constant')
            if d[j] < 0.4 * med_d and fl[j] > max(0.45, med_f + 0.15) and m[j] >= 0.025:
                why.append('lens blocked?')
            if why:
                bad.append((j, why))
        # runs of >= 3 samples (0.3 s) only
        runs, cur = [], []
        for j, why in bad:
            if cur and j == cur[-1][0] + 1:
                cur.append((j, why))
            else:
                if len(cur) >= 3:
                    runs.append(cur)
                cur = [(j, why)]
        if len(cur) >= 3:
            runs.append(cur)
        for r in runs:
            t0 = f0 / fps + r[0][0] / 10
            t1 = f0 / fps + (r[-1][0] + 1) / 10
            kinds = sorted({w for _, ws in r for w in ws})
            out.append(dict(shot=k, src=shots[k]['src'], t0=round(t0, 2), t1=round(min(t1, f1 / fps), 2), what=', '.join(kinds), level='warn'))
    json.dump(cache, open(cache_path, 'w'))
    return out


# ------------------------------------------------------------------------------ others
def caption_gate(cs, limit_ms=200):
    out = []
    for p in cs.get('pieces', []):
        lag = p.get('lag_ms', p.get('lag'))
        if lag is not None and abs(lag) > limit_ms:
            out.append(dict(level='warn', what=f"captions {p.get('t', '?')} s ({p.get('src', '')}): {lag:+.0f} ms off the speech"))
    return out


def loud_gate(name, I, TP, target=-14.0, tol=0.5, tp_max=-1.5):
    out = []
    if I is None or abs(I - target) > tol:
        out.append(dict(level='error', what=f'{name}: {I} LUFS (target {target} +-{tol})'))
    if TP is None or TP > tp_max:
        out.append(dict(level='error', what=f'{name}: true peak {TP} dBTP (max {tp_max})'))
    return out


def quote_gate(comps, caps):
    out = []
    for c in comps:
        if c['type'] != 'quoteCard':
            continue
        p = c.get('p', {})
        words = p.get('words', [])
        t0 = words[0]['t'] if words else c['t0']
        src = next((pc['src'] for pc in caps if any(abs(w[0] - t0) < 0.01 for w in pc['words'])), '?')
        lab = p.get('label', '')
        lvl = 'warn' if 'GUEST' in lab.upper() else 'check'
        out.append(dict(code=c['code'], level=lvl, what=f"quote card {c['code']} {c['t0']:.2f}-{c['t1']:.2f} s, label \"{lab}\", words from clip {src}: "
                                                      f"confirm who is speaking (no speaker labels in the transcripts)"
                                                      + (' - a GUEST label on a line the host may say cost a re-render before' if lvl == 'warn' else '')))
    return out
