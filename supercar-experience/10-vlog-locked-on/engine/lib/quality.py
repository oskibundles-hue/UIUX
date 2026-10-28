"""Per-clip picture notes from the survey thumbnails, so nobody picks unusable B-roll.

Per keyframe (thumbs.frame_stats): mean luma, share of near-black pixels, sharpness, share of textureless
cells, and where the light is (top / bottom / left / right). Issues, reported as time ranges:
  very dark        mean luma < 22 for >= 3 keyframes in a row
  black / blocked  an isolated all-black frame (mean < 10, >= 95% black): lens covered
  covered / blur   >= 40% textureless cells and sharpness < 45% of the clip's median (finger, hand, fog)
  sideways         bright side on the left or right, not the top (sky / ceiling lights), for >= 3 keyframes
  upside down      bright side at the bottom for >= 3 keyframes (and the top is not a night sky)
Calibrated on Sep 15 (0005 / 0019 / 0020 night interiors, 0015 5:40 finger on the lens, 0011 2:00-8:00
camera on its side, 0008 camera mounted upside down). Thresholds are heuristics: a note is a warning.
"""
import numpy as np


def frame_issue(s, med_sharp):
    if s['mean'] < 10 and s['black'] >= 0.95:
        return 'black'
    if s['mean'] < 22:
        return 'dark'
    if s.get('smooth', 0) >= 0.4 and med_sharp > 120 and s['sharp'] < 0.45 * med_sharp:
        return 'covered'
    if s['mean'] >= 45:
        dv = s['top'] - s['bottom']
        dh = s['left'] - s['right']
        # the dark side must not be a night sky (lit ground under a black sky is an upright night shot)
        if abs(dh) >= 45 and abs(dh) >= 2.5 * abs(dv) and s['gx'] >= s['gy'] and min(s['left'], s['right']) >= 35:
            return 'sideways'
        if dv <= -45 and abs(dv) >= 2.5 * abs(dh) and s['top'] >= 35:
            return 'upside_down'
    return None


LABEL = {'dark': 'very dark', 'black': 'black frame (lens blocked?)', 'covered': 'lens covered / blurred',
         'sideways': 'camera sideways', 'upside_down': 'camera upside down'}
MIN_RUN = {'dark': 3, 'black': 1, 'covered': 1, 'sideways': 3, 'upside_down': 3}


def clip_notes(stats):
    """stats: [(t, frame_stats)] sorted by t -> {'issues': [{kind, t0, t1, n}], 'usable': share, 'summary': str}"""
    if not stats:
        return {'issues': [], 'usable': None, 'summary': 'no thumbnails'}
    med = float(np.median([s['sharp'] for _, s in stats]))
    kinds = [frame_issue(s, med) for _, s in stats]
    ts = [t for t, _ in stats]
    step = float(np.median(np.diff(ts))) if len(ts) > 1 else 1.0
    issues = []
    i = 0
    n = len(kinds)
    while i < n:
        k = kinds[i]
        if k is None:
            i += 1
            continue
        j = i
        while j + 1 < n and (kinds[j + 1] == k or (k == 'dark' and kinds[j + 1] == 'black')):
            j += 1
        run = j - i + 1
        if run >= MIN_RUN[k]:
            issues.append({'kind': k, 't0': round(ts[i], 1), 't1': round(ts[j] + step, 1), 'n': run})
        i = j + 1
    # join runs of one kind separated by a keyframe or two (a flicker of light in a dark car is still dark)
    merged = []
    for x in issues:
        if merged and merged[-1]['kind'] == x['kind'] and x['t0'] - merged[-1]['t1'] <= max(3 * step, 4.0):
            merged[-1]['t1'] = x['t1']
            merged[-1]['n'] += x['n']
        else:
            merged.append(dict(x))
    issues = merged
    bad = sum(1 for k in kinds if k in ('dark', 'black', 'covered', 'sideways', 'upside_down'))
    usable = 1 - bad / n
    parts = []
    dur = ts[-1] + step
    for kind in ('dark', 'sideways', 'upside_down', 'covered', 'black'):
        rs = [x for x in issues if x['kind'] == kind]
        if not rs:
            continue
        tot = sum(x['t1'] - x['t0'] for x in rs)
        if kind in ('dark', 'sideways', 'upside_down') and tot >= 0.8 * dur:
            parts.append(f'{LABEL[kind]} throughout')
        else:
            spans = ', '.join(f"{_mmss(x['t0'])}-{_mmss(x['t1'])}" for x in rs[:6]) + (' ...' if len(rs) > 6 else '')
            parts.append(f'{LABEL[kind]} {spans}')
    mean = float(np.median([s['mean'] for _, s in stats]))
    summary = '; '.join(parts) if parts else 'looks usable'
    return {'issues': issues, 'usable': round(usable, 2), 'median_luma': round(mean, 1), 'summary': summary}


def _mmss(t):
    return f'{int(t // 60)}:{int(t % 60):02d}'


def issues_between(notes, a, b):
    return [x for x in notes.get('issues', []) if x['t0'] < b and x['t1'] > a]
