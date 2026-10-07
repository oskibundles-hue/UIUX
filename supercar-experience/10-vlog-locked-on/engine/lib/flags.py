"""Exclusion flags: spans of a clip that must never be used (block) or need care (caution).

Matching runs on the transcript's words (whisper segments), so every flag has word-accurate times.
A category has strong patterns (a hit creates a flag) and weak ones (a hit only extends a flag of the same
category within `reach` seconds, e.g. "is it cleared?" after gun talk). Hits of one category closer than
`merge` seconds join into one span. `back`/`fwd` pad the span; a cut request reaches back over what it
asks to remove (20 s, or the "17 second segment" it names).

Categories (block unless noted): password/code, cut request, speed, weapons, unsafe driving, fleet fault,
police, profanity/slur (caution: flag the words so they can be bleeped; the moment stays usable).
"""
import re

D = r'(?:zero|oh|one|two|three|four|five|six|seven|eight|nine|\d)'

RULES = [
    dict(cat='password', sev='block', back=2, fwd=8, merge=20, reach=20, strong=[
        r'\bpass ?(?:word|code)\b', r'\bcapital [a-z]\b', r'\blower ?case\b', r'\bupper ?case\b',
        r'\b(?:pin|code|combo|combination) (?:is|number)\b', r'\b(?:log ?in|login|sign ?in|user ?name)\b.{0,12}\b(?:is|it\'?s)\b',
        r'\bwi-?fi\b.{0,20}\b(?:is|password)\b', D + r'(?:[\s,.-]+' + D + r'){3,}\b'],
        weak=[r'\b[a-z]\b(?: [a-z]\b){2,}', r'\b(?:log ?in|login|account|click on)\b']),
    dict(cat='cut_request', sev='block', back=20, fwd=2, merge=25, reach=10, strong=[
        r'\b(?:take|cut|edit|leave) (?:that|this|it|that whole|this whole|that piece|this piece|that part|this part)\b[^.?!]{0,40}\bout\b',
        r'\btake that out\b', r'\b(?:don\'?t|do not|never) (?:post|put|use|show|upload|air) (?:that|this|it)\b',
        r'\boff the record\b', r'\b(?:delete|remove|scrap) (?:that|this)\b', r'\b(?:don\'?t|do not) record\b',
        r'\b(?:won\'?t|will not|ain\'?t gonna|not gonna) (?:post|show|put|let (?:him|her|them) know)\b'],
        weak=[r'\bclaude\b', r'\bsegment\b']),
    dict(cat='speed', sev='block', back=2, fwd=6, merge=20, reach=15, strong=[
        r'\b(?:\d{2,3}|a hundred|one hundred|hundred)\s*(?:mph|miles an hour|miles per hour|kilometers? (?:per|an) hour|km/?h|kph)\b',
        r'\b(?:hit|hitting|doing|going|did|went|clocked|topped out at|reached|touched|pushing)\s+(?:like\s+|about\s+|over\s+|almost\s+|a\s+|around\s+)?(?:1\d\d|[6-9]\d|a hundred|one hundred|hundred|two hundred)\b',
        r'\btop speed\b', r'\bspeeding\b', r'\b(?:over|above|past) the (?:speed )?limit\b', r'\bhow fast (?:were|was|did) (?:we|you|he|she|they)\b'],
        weak=[r'\bkilometers? per hour\b', r'\bmiles per hour\b', r'\bmph\b', r'\bfast\b', r'\bspeed\b', r'\b1\d\d\b']),
    dict(cat='weapons', sev='block', back=2, fwd=5, merge=25, reach=30, strong=[
        r'\b(?:gun|guns|pistol|firearms?|glock|rifle|shotgun|ammo|ammunition|bullets?|holster|revolver|handgun|ar-?15|nine millimeter|9 ?mm)\b',
        r'\bf-?n ?-?509\b', r'\bconceal(?:ed)? carry\b', r'\bstrapped\b'],
        weak=[r'\bcarry\b', r'\bcleared\b', r'\bloaded\b', r'\bmag(?:azine)?\b', r'\bsafety\b', r'\bchamber(?:ed)?\b', r'\bclaimed it\b']),
    dict(cat='unsafe_driving', sev='block', back=2, fwd=5, merge=20, reach=15, strong=[
        r'\bdouble yellow\b', r'\b(?:run|ran|running|blow|blew|blowing) (?:a |the |through (?:a |the )?)?(?:red|reds|red light|stop sign)\b',
        r'\b(?:go|going|drive|driving) a little (?:bit )?faster\b', r'\bstreet rac\w*', r'\b(?:drag rac\w*|race each other|racing each other)\b',
        r'\bno seat ?belts?\b', r'\b(?:drunk|buzzed|tipsy) (?:driv\w*|behind)\b', r'\bwrong way\b',
        r'\bpass(?:ing|ed)? on (?:a |the )?(?:double|shoulder|right)\b', r'\bweav(?:e|ing) (?:through|in and out)\b',
        r'\bbrake[- ]check\w*', r'\btailgat\w*', r'\blane[- ]split\w*', r'\bburnouts? (?:on|in) the (?:street|road)\b'],
        weak=[r'\bfaster\b', r'\bwild,? wild west\b', r'\bsafe enough\b', r'\bspeeds? up\b', r'\bkeep up\b']),
    dict(cat='fleet_fault', sev='block', back=2, fwd=5, merge=20, reach=15, strong=[
        r'\bdoor handle\b[^.?!]{0,25}\b(?:broke|broken|snapped|came off)\b', r'\b(?:broke|broken|snapped)\b[^.?!]{0,25}\bdoor handle\b',
        r'\bmisfir\w*', r'\bknocking\b', r'\bcheck engine\b', r'\bengine light\b', r'\bwarning light\b',
        r'\bflat (?:tire|tyre)\b', r'\bblew (?:a|the) (?:tire|tyre)\b', r'\bblowout\b', r'\boverheat\w*', r'\bleak(?:ing|s)?\b',
        r'\bwon\'?t start\b', r'\b(?:dead battery|battery (?:is |was )?dead)\b', r'\bbroke(?:n)? down\b', r'\blimp mode\b',
        r'\bcurb(?:ed)? (?:the |a )?(?:rim|wheel)\b', r'\bfender bender\b', r'\b(?:crash|crashed|wrecked)\b', r'\baccident\b',
        r'\b(?:transmission|clutch|brakes?) (?:is |are |was )?(?:slipping|going out|failing|grinding|gone)\b'],
        weak=[r'\bdoor handle\b', r'\bbroke\b', r'\bbroken\b', r'\bsounds? (?:weird|bad|off|funny)\b', r'\bmechanic\b', r'\bshop\b']),
    dict(cat='police', sev='block', back=2, fwd=5, merge=20, reach=10, strong=[
        r'\b(?:police|cops?|cop car|officers?|troopers?|sheriffs?|highway patrol|popo)\b',
        r'\bpulled (?:me|us|him|her|them|you) over\b', r'\bgot pulled over\b', r'\b(?:speeding|traffic) ticket\b',
        r'\bwr(?:ite|ote) (?:me|us|him|her|them) (?:a|up)\b'],
        weak=[r'\bticket\b', r'\blights behind\b']),
    dict(cat='profanity', sev='caution', back=0.15, fwd=0.15, merge=0, reach=0, word_level=True, strong=[
        r'\b\w*fuck\w*\b', r'\b\w*shit\w*\b', r'\bbitch\w*\b', r'\bgod ?damn\w*\b', r'\bass ?hole\w*\b', r'\bdick\w*\b',
        r'\bpuss(?:y|ies)\b', r'\bbastards?\b', r'\bcunt\w*\b'], weak=[]),
    dict(cat='slur', sev='caution', back=0.15, fwd=0.15, merge=0, reach=0, word_level=True, strong=[
        r'\bnigg\w*\b', r'\bfagg?\w*\b', r'\bretard\w*\b', r'\bspic\b', r'\bchink\w*\b', r'\btrann\w*\b'], weak=[]),
]

NUMWORDS = {'seventeen': 17, 'fifteen': 15, 'twenty': 20, 'thirty': 30, 'ten': 10, 'five': 5, 'sixty': 60}


def _text_and_map(seg):
    """Lower-case text of a segment's words and a char -> word index map."""
    ws = seg.get('words') or []
    if not ws:
        t = ' ' + seg['text'].lower()
        return t, None
    parts, owner = [], []
    for i, w in enumerate(ws):
        s = w[2].lower()
        if not s.startswith(' '):
            s = ' ' + s
        parts.append(s)
        owner.extend([i] * len(s))
    return ''.join(parts), owner


def _span(seg, owner, a, b):
    ws = seg.get('words') or []
    if owner is None or not ws:
        return seg['start'], seg['end']
    i = owner[min(max(a, 0), len(owner) - 1)]
    j = owner[min(max(b - 1, 0), len(owner) - 1)]
    return ws[i][0], ws[j][1]


def find_hits(segments):
    """[(cat, sev, strong, t0, t1, matched_text, seg_index)]"""
    hits = []
    for si, seg in enumerate(segments):
        txt, owner = _text_and_map(seg)
        for r in RULES:
            for kind, pats in (('strong', r['strong']), ('weak', r['weak'])):
                for p in pats:
                    for m in re.finditer(p, txt):
                        t0, t1 = _span(seg, owner, m.start(), m.end())
                        hits.append((r['cat'], r['sev'], kind == 'strong', t0, t1, m.group(0).strip(), si))
    return hits


def flags_for_clip(cid, segments, clip_dur=None):
    rules = {r['cat']: r for r in RULES}
    hits = find_hits(segments)
    out = []
    for cat, r in rules.items():
        strong = sorted((h for h in hits if h[0] == cat and h[2]), key=lambda h: h[3])
        weak = sorted((h for h in hits if h[0] == cat and not h[2]), key=lambda h: h[3])
        if not strong:
            continue
        if r.get('word_level'):
            for h in strong:
                out.append(_flag(cid, r, h[3] - r['back'], h[4] + r['fwd'], [h], segments))
            continue
        groups = []
        for h in strong:
            if groups and h[3] - groups[-1]['t1'] <= r['merge']:
                groups[-1]['hits'].append(h)
                groups[-1]['t1'] = max(groups[-1]['t1'], h[4])
            else:
                groups.append({'t0': h[3], 't1': h[4], 'hits': [h]})
        for g in groups:
            # weak hits within reach extend the span (repeatedly, so a chain of them can)
            changed = True
            while changed:
                changed = False
                for h in weak:
                    if h in g['hits']:
                        continue
                    if g['t0'] - r['reach'] <= h[4] and h[3] <= g['t1'] + r['reach']:
                        g['hits'].append(h)
                        g['t0'] = min(g['t0'], h[3])
                        g['t1'] = max(g['t1'], h[4])
                        changed = True
            back = r['back']
            if cat == 'cut_request':
                for h in g['hits']:
                    seg = segments[h[6]]['text'].lower()
                    m = re.search(r'\b(\d+|' + '|'.join(NUMWORDS) + r')[ -]second', seg)
                    if m:
                        n = int(m.group(1)) if m.group(1).isdigit() else NUMWORDS[m.group(1)]
                        back = max(back, n + 2 - (g['t1'] - g['t0']))
            # padding applies to the strong hits; the span also covers the whole segments its hits sit in
            st = [h for h in g['hits'] if h[2]]
            s0 = min(h[3] for h in st) - back
            s1 = max(h[4] for h in st) + r['fwd']
            first = min(g['hits'], key=lambda h: h[3])
            last = max(g['hits'], key=lambda h: h[4])
            seg0 = max(segments[first[6]]['start'], first[3] - 12)
            seg1 = min(segments[last[6]]['end'], last[4] + 12)
            out.append(_flag(cid, r, min(s0, seg0), max(s1, seg1), g['hits'], segments))
            out[-1]['_first'] = min(h[3] for h in st)
    # a cut request right after other flagged talk ("I hit 114 ... we'll take that out the clip") refers to that
    # talk: reach back only to where it starts, not the full 20 s
    for f in out:
        if f['category'] != 'cut_request':
            continue
        first = f.get('_first', f['t0'])
        prior = [g for g in out if g is not f and g['severity'] == 'block' and g['category'] != 'cut_request'
                 and first - 20 <= g['t0'] <= first + 2]
        if prior:
            f['t0'] = max(f['t0'], min(g['t0'] for g in prior))
            f['refers_to'] = sorted({g['category'] for g in prior})
    for f in out:
        f.pop('_first', None)
        f['t0'] = round(max(0.0, f['t0']), 2)
        if clip_dur:
            f['t1'] = round(min(clip_dur, f['t1']), 2)
    out.sort(key=lambda f: (f['t0'], f['category']))
    return out


def _flag(cid, r, t0, t1, hits, segments):
    segs = sorted({h[6] for h in hits})
    text = ' '.join(segments[i]['text'] for i in segs)
    return {'clip': cid, 't0': round(t0, 2), 't1': round(t1, 2), 'category': r['cat'], 'severity': r['sev'],
            'terms': sorted({h[5] for h in hits})[:12], 'text': text[:400]}


def overlaps(flags, cid, a, b, severity=None):
    return [f for f in flags if f['clip'] == cid and f['t0'] < b and f['t1'] > a and (severity is None or f['severity'] == severity)]
