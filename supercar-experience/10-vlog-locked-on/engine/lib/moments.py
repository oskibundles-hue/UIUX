"""Moment finder: candidate lines for the editor, scored per category.

Candidates are runs of 1-6 consecutive transcript pieces of one clip (gaps <= 1.6 s, <= 16 s long).
Each category scores a candidate from
  + phrase evidence (weighted patterns; each pattern counts once; car names count per distinct make/model)
  + speaker fit (e.g. intro/offer/closing lines from the HOST, reactions from OTHER speakers)
  + where in the day (openers early, closers late)
  + clean audio (whisper confidence) and a usable length for the category
  - words that carry no evidence (a tight moment beats the same line with filler around it)
Candidates overlapping a block flag are dropped (listed in moments.md as blocked, so nothing is silently lost);
profanity/slurs are noted for a bleep. Per category, overlapping candidates are reduced to the best one.
"""
import re

CAR_NAMES = [
    r'black series', r'urus(?:es)?|uris(?:es)?|urises', r'huracan|huracán|hurricane|turcon', r'evos?', r'aventador', r'revuelto',
    r'lambo(?:rghini)?s?', r'gt3(?: rs)?s?', r'gt ?2 ?rs', r'911|nine eleven', r'porsches?', r'cayenne', r'taycan',
    r'ferraris?', r'roma', r'f8', r'sf90', r'296', r'488', r'purosangue', r'mclarens?', r'570s?', r'720s?', r'750s?', r'765',
    r'artura', r'rolls[- ]?royce|rolls', r'cullinan|coleman|colin', r'ghost', r'wraith', r'spectre', r'bentley', r'bentayga',
    r'corvettes?|c8', r'audi', r'r8', r'mercedes', r'amg', r'g[- ]?wagons?|g63', r'bmw', r'm4|m5|m8', r'nissan|gt-?r',
    r'maserati', r'aston(?: martin)?', r'cybertruck', r'tesla', r'escalade', r'range rover',
]
CAR_RE = re.compile(r'\b(?:' + '|'.join(CAR_NAMES) + r')\b')

ROADS = r'\b(?:215|two fifteen|15 north|the 15|i-?15|flamingo|las vegas (?:blvd|boulevard)|the strip|blue diamond|red rock|' \
        r'charleston|summerlin|venetian|spring mountain|canyons?|freeway|highway|interstate|exit|on-?ramp|parking structure|' \
        r'(?:ninth|9th) floor|level nine)\b'

CATS = {
    'intro': dict(speaker='HOST', where='early', ideal=(2.5, 12), pats=[
        (r"\bwhat'?s (?:going on|up|good),? (?:guys|y'?all|everybody|everyone|youtube)\b", 4),
        (r"\b(?:we'?re|we are) back\b", 2.5), (r'\bwelcome (?:back|to)\b', 2.5), (r'\bso today,? (?:we|i)\b', 2.5),
        (r"\btoday (?:we|is|it'?s|i)\b", 1.5), (r'\b(?:rally|event|drive|tour|shoot) day\b', 1.5),
        (r"\b(?:hey|yo|what'?s up),? (?:guys|everybody|everyone|y'?all)\b", 2), (r'\bback at it\b', 2),
        (r'\btoday we have\b', 2)]),
    'offer': dict(speaker='HOST', ideal=(2.5, 14), pats=[
        (r'\bbook (?:with|us)\b', 4), (r'\b(?:hit|reach|contact|call|text|dm|message|inbox) us\b', 3),
        (r'\bfollow us\b', 4), (r'\bif you (?:guys )?(?:ever )?(?:want|need|wanna)\b', 2.5),
        (r'\b(?:supercar|some car|super car) experience\b', 1.5), (r'\b(?:we|what we) offer\b|\boffer\b', 2),
        (r'\blet us know\b', 2.5), (r"\bwe'?ll make it happen\b", 2.5), (r'\b(?:instagram|tiktok|youtube|website|link in (?:the )?bio)\b', 2.5),
        (r'\b(?:the things|what) we do\b', 2), (r'\b(?:large|big|private|corporate) (?:event|group)s?\b', 2),
        (r'\bgiving them the experience\b|\bthe experience (?:that )?they want\b', 3), (r'\bwe (?:also )?help\b', 1.5),
        (r"\bwe(?:'re| are) able to\b", 1.5), (r'\bshow up,? show out\b', 1.5)]),
    'lineup': dict(speaker=None, ideal=(1.5, 14), cars=True, pats=[
        (r'\b(?:all|all the|all these|all those|all of the|all of those|a lot of) (?:cars|vehicles)\b', 3), (r'\bline ?-?up\b', 2.5), (r'\bfleet\b', 2),
        (r"\byou'?(?:ll| will)? (?:get|be in|be driving|drive) the\b", 2.5), (r'\bfavou?rite\b', 2),
        (r'\bpicking (?:out )?their (?:vehicle|car)s?\b', 2), (r'\bwhich (?:car|one)\b', 1)]),
    'arrival': dict(speaker=None, ideal=(1.2, 10), pats=[
        (r'\b(?:customers?|guests?|clients?)\b', 2), (r'\bhow (?:are )?you (?:guys )?doing\b', 3),
        (r'\bmeet(?:ing)? (?:the )?(?:customers|guests|clients|everyone|everybody)\b', 3.5),
        (r'\b(?:welcome|nice to meet you|good to see you)\b', 2), (r'\bcheck(?:ing)?[- ]in\b|\bsign(?:ing)? in\b|\bwaivers?\b', 2),
        (r'\bwhere (?:are )?you (?:guys )?from\b', 3), (r"\b(?:arriv\w*|here they come|they'?re here|showing up|pulling up)\b", 2.5),
        (r'\bgetting ready to meet\b', 2)]),
    'briefing': dict(speaker=None, ideal=(2.5, 14), roads=True, pats=[
        (r'\b(?:take|taking) a (?:left|right)\b|\b(?:turn|turning) (?:left|right)\b|\bgetting off (?:on|at)\b', 2.5),
        (r'\bfollow (?:the|that) car\b', 3), (r'\bcar in front of you\b', 3), (r'\b(?:lead|leaded|tail) car\b', 2.5),
        (r'\b(?:the )?groups? (?:that )?you(?: are|\'re) in\b|\byour group\b', 1.5),
        (r'\bstay with your group\b', 2.5), (r'\bbrief(?:ing)?\b', 2.5), (r'\bsafe(?:ly|ty)?\b', 2),
        (r'\bhow the vehicles? (?:are|is) supposed to be driven\b', 3.5), (r'\bnumber one thing\b', 2),
        (r"\bwe(?:'re| are) (?:going|gonna) (?:to )?take\b", 2), (r'\bmake sure (?:everybody|everyone)\b', 2.5),
        (r'\bhaving fun\b', 1.5), (r'\bkeep an eye on\b', 2)]),
    'convoy': dict(speaker='HOST', ideal=(2, 12), pats=[
        (r"\b(?:i'?ll|i will|i'?m) (?:be )?lead(?:ing)?\b", 3.5), (r'\bleading (?:everybody|everyone|the group|them)\b', 3.5),
        (r'\b(?:convoy|caravan)\b', 2.5), (r'\bfollow(?:ing)? (?:me|us)\b', 2),
        (r'\blost (?:so many |some |a few |a couple )?(?:people|cars|them|everybody)\b|\bgot lost\b', 3),
        (r'\bpart of (?:the,? (?:you know,? )?)?(?:being in )?a rally\b', 3), (r'\brally\b', 1.5),
        (r'\bgroup (?:one|two|1|2)\b|\bour group\b|\bgroup of people\b', 1.5), (r'\bhead and tail\b|\bguiding\b', 2.5),
        (r"\bgetting ready to (?:get out of here|go|leave|roll)\b|\bstart (?:this|the) drive\b|\blet'?s roll\b", 2.5),
        (r"\b(?:i'?m|we'?re) (?:going|gonna) (?:to )?(?:go )?(?:down )?to\b", 1.5), (r'\bheading (?:to|out)\b', 1.5),
        (r'\bin the (?:all )?(?:black )?(?:cullinan|coleman|rolls)\b', 2)]),
    'food': dict(speaker=None, ideal=(1.5, 12), pats=[
        (r'\b(?:dinner|lunch|breakfast|food|restaurant|drinks?)\b', 2.5), (r'\b(?:eat|eating|ate)\b', 2.5),
        (r'\b(?:yard house|lotus of s\w+|steakhouse|our house)\b', 2.5), (r'\bteam\b', 1),
        (r'\b(?:everybody|everyone) together\b', 2.5), (r'\bget(?:ting)? (?:dinner|food|something to eat)\b', 2),
        (r'\bnachos|tacos|pizza|burgers?|wings|steak\b', 1.5)]),
    'reaction': dict(speaker='OTHER', ideal=(0.6, 8), pats=[
        (r'\b(?:good|great|wonderful|amazing|awesome|fun|incredible|insane|best|nice) (?:time|experience|day|drive|ride)\b', 4),
        (r'\bhad (?:so much |a lot of |a )?fun\b|\bguys had fun\b', 4), (r'\b(?:wonderful|amazing|awesome|incredible|beautiful|love it|loved it)\b', 2.5),
        (r'\benjoy(?:ed|ing)?\b', 2.5), (r'\bfavou?rite\b', 1.5), (r'\b(?:so|really|pretty) (?:good|nice|cool|fun)\b', 1.5),
        (r'\b(?:do it again|come back)\b', 2), (r'\bglad to hear\b', 1.5), (r'\bhad a (?:great|good) time\b', 2),
        (r'\bmy favou?rite\b|\bi would say\b', 1.5)]),
    'closing': dict(speaker='HOST', where='late', ideal=(2, 12), pats=[
        (r'\buntil next time\b', 5), (r'\b(?:hell|heck) of a day\b', 4), (r'\b(?:long|full|eventful|great|good|crazy) day\b', 3),
        (r"\bthat'?s (?:a )?wrap\b", 4), (r'\b(?:see|catch) you (?:guys )?(?:next time|later|soon)\b', 3.5),
        (r'\bthanks for watching\b', 4), (r'\b(?:peace|signing off)\b', 1.5),
        (r'\b(?:back to|going back to|heading back|head back)\b', 1.5), (r'\bthe ending\b|\bend of the (?:day|night)\b', 2.5),
        (r"\b(?:today|it) (?:was|has been|'s been)\b", 1.5)]),
}

CATEGORY_TITLES = {
    'intro': 'Intro / opening lines', 'offer': 'What SE offers / CTA', 'lineup': 'Lineup / car naming',
    'arrival': 'Guest arrival', 'briefing': 'Briefings / route talk', 'convoy': 'Leading / convoy',
    'food': 'Food / dinner / team', 'reaction': 'Guest reactions', 'closing': 'Closing lines',
}


def _words(text):
    return len(re.findall(r"[a-z0-9']+", text.lower()))


def evidence(cat, text):
    cfg = CATS[cat]
    t = ' ' + text.lower() + ' '
    score = 0.0
    hits = []
    covered = 0
    for p, w in cfg['pats']:
        m = re.search(p, t)
        if m:
            score += w
            hits.append(m.group(0).strip())
            covered += _words(m.group(0))
    if cfg.get('cars'):
        names = {m.group(0) for m in CAR_RE.finditer(t)}
        if len(names) >= 2:
            score += min(6.0, 1.2 * len(names))
            hits.extend(sorted(names))
            covered += len(names)
        elif names:
            score += 0.8
            hits.extend(names)
    if cfg.get('roads'):
        roads = {m.group(0) for m in re.finditer(ROADS, t)}
        if roads:
            score += min(5.0, 1.6 * len(roads))
            hits.extend(sorted(roads))
            covered += len(roads)
    return score, hits, covered


def _who(labels, min_conf=0.55):
    sure = {l['speaker'] for l in labels if l['conf'] >= min_conf} or {l['speaker'] for l in labels}
    return 'HOST+OTHER' if len(sure) > 1 else sure.pop()


def candidates(pieces, max_pieces=6, max_len=16.0, max_gap=2.5):
    out = []
    n = len(pieces)
    for i in range(n):
        for j in range(i, min(n, i + max_pieces)):
            if j > i and pieces[j]['start'] - pieces[j - 1]['end'] > max_gap:
                break
            if pieces[j]['end'] - pieces[i]['start'] > max_len:
                break
            out.append((i, j))
    return out


def score_clip(cid, pieces, labels, day_pos, flags, quality_at=None):
    """All scored candidates of one clip: [(cat, score, cand dict)]."""
    from .flags import overlaps
    res = []
    for i, j in candidates(pieces):
        ps = pieces[i:j + 1]
        a, b = ps[0]['start'], ps[-1]['end']
        dur = b - a
        text = ' '.join(p['text'] for p in ps).strip()
        nw = max(1, _words(text))
        lab = labels[i:j + 1]
        host_w = sum((p['end'] - p['start']) * (l['conf'] if l['speaker'] == 'HOST' else 1 - l['conf']) for p, l in zip(ps, lab))
        host_frac = host_w / max(1e-6, sum(p['end'] - p['start'] for p in ps))
        lp = sum(p.get('avg_logprob', -0.4) for p in ps) / len(ps)
        blocked = overlaps(flags, cid, a, b, 'block')
        caution = overlaps(flags, cid, a, b, 'caution')
        for cat, cfg in CATS.items():
            ev, hits, covered = evidence(cat, text)
            if ev < 2.0:
                continue
            # evidence in the first and last piece: a moment should start and end on its line
            ev_first = evidence(cat, ps[0]['text'])[0]
            ev_last = evidence(cat, ps[-1]['text'])[0]
            s = ev
            want = cfg.get('speaker')
            if want == 'HOST':
                s += 2.0 * (host_frac - 0.5) * 2
            elif want == 'OTHER':
                other = [1 - (l['conf'] if l['speaker'] == 'HOST' else 1 - l['conf']) for l in lab]
                s += 2.0 * (max(other) - 0.5) * 2
            if cfg.get('where') == 'early':
                s += 2.5 * max(0.0, 1 - day_pos / 0.2)
            elif cfg.get('where') == 'late':
                s += 2.5 * max(0.0, (day_pos - 0.6) / 0.4)
            lo, hi = cfg['ideal']
            if dur < lo:
                s -= 1.5 * (lo - dur) / lo
            if dur > hi:
                s -= 0.25 * (dur - hi)
            s += 0.8 if lp > -0.5 else (-1.0 if lp < -1.0 else 0.0)
            filler = max(0, nw - 3 * covered - 6)
            s -= 0.08 * filler
            if j > i:
                s -= 0.6 * ((ev_first < 1.0) + (ev_last < 1.0))
            if caution:
                s -= 0.3
            q = quality_at(cid, a, b) if quality_at else None
            if q:
                s -= 0.5
            res.append((cat, round(s, 2), {
                'clip': cid, 'in': round(a, 2), 'out': round(b, 2), 'dur': round(dur, 2), 'text': text,
                'speaker': _who(lab), 'host_frac': round(host_frac, 2),
                'speakers': [(l['speaker'], l['conf']) for l in lab], 'hits': hits[:10],
                'blocked': [f"{f['category']} {f['t0']:.1f}-{f['t1']:.1f}" for f in blocked],
                'caution': [f"{f['category']} {f['t0']:.1f}-{f['t1']:.1f}" for f in caution],
                'picture': q, 'pieces': [i, j]}))
    return res


def rank(all_scored, per_cat=15):
    """Best non-overlapping candidates per category; blocked ones listed separately."""
    out = {}
    blocked = {}
    for cat in CATS:
        lst = sorted((x for x in all_scored if x[0] == cat), key=lambda x: -x[1])
        keep, bl = [], []
        for _, s, c in lst:
            dst = bl if c['blocked'] else keep
            if any(k['clip'] == c['clip'] and min(k['out'], c['out']) - max(k['in'], c['in']) > 0.3 * min(c['dur'], k['dur'])
                   for k in dst):
                continue
            c = dict(c, score=s)
            dst.append(c)
            if len(keep) >= per_cat and len(bl) >= 5:
                break
        out[cat] = keep[:per_cat]
        blocked[cat] = bl[:5]
    return out, blocked
