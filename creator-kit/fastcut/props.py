#!/usr/bin/env python3
"""Overlay props for one Fast Cut reel.

Title comes from the hook, chapters and lower thirds from what each clip shows,
follow cards land in speech gaps, card outro at the end.

    WORK=/path/to/work python3 props.py MR1 "the shop before" "THE SHOP, BEFORE ANYTHING"

Clip labels: put a labels.json next to the work dir mapping clip number to a plain
description, e.g. {"01": "Garage walkthrough", "02": "Product to camera"}. Without it
the label falls back to the words in the cut's own filename, which is usually fine
because cuts are named "NN a few words.mp4".

Brand: override BRAND ("Formula Dynamics"), IG_NAME, IG_HANDLE, IG_FOLLOWERS,
YT_NAME, YT_HANDLE and ENDCARD through the environment.
"""
import json, os, re, sys

r, slug, hook = sys.argv[1], sys.argv[2], sys.argv[3]
WORK = os.environ.get('WORK', 'work')
BRAND = os.environ.get('BRAND', 'Formula Dynamics')
ENDCARD = os.environ.get('ENDCARD', 'fd/end-cards/endcard_9x16_dark.png')

labels_path = os.path.join(WORK, 'labels.json')
LABEL = json.load(open(labels_path)) if os.path.exists(labels_path) else {}

def label_for(num, clip_path):
    if num in LABEL:
        return LABEL[num]
    stem = os.path.splitext(os.path.basename(clip_path))[0]
    words = re.sub(r'^\d+\s*', '', stem).strip()
    return words[:1].upper() + words[1:] if words else num

p = json.load(open(os.path.join(WORK, f'{r}.props.json')))
d = p['durationSeconds']
cuts = p.get('cuts', [])

# "THE SHOP, BEFORE ANYTHING" -> two lines, split on the first comma or period
m = re.match(r'^(.*?[,.])\s*(.+)$', hook)
if m:
    line1, line2 = m.group(1).rstrip(',.'), m.group(2).rstrip('.')
else:
    parts = hook.split(' ', 1)
    line1, line2 = parts[0], (parts[1] if len(parts) > 1 else '')

chapters, lts, last = [], [], None
for c in cuts:
    m2 = re.search(r'(?:^|/)(\d\d)[ _]', c.get('clip', ''))
    n = m2.group(1) if m2 else None
    if n and n != last:
        text = label_for(n, c.get('clip', ''))
        chapters.append({'at': round(c['at'], 2), 'label': text})
        lts.append({'at': round(c['at'] + (3.0 if not lts else 0.4), 2), 'hold': 3.6,
                    'title': text, 'sub': f'{BRAND} · {slug}'})
        last = n

w = p['words']
gaps = [(a['end'], b['start']) for a, b in zip(w, w[1:]) if b['start'] - a['end'] > 3.0]

def slot(after, hold):
    """First speech gap starting at or after `after` that is long enough to hold a card."""
    for g in gaps:
        if g[0] >= after and g[1] - g[0] >= hold + 0.8:
            return round(g[0] + 0.3, 2)
    return None

ig = 8.0
yt = slot(ig + 12, 4.0) or min(d - 12.0, 32.0)

o = {
    "src": f"{r}.master.mp4", "words": w, "cuts": cuts, "durationSeconds": d,
    "overlayOnly": True, "keyWord": False, "wipes": True, "hook": hook,
    "title": {"eyebrow": f"{BRAND.upper()} · {slug.upper()}",
              "line1": line1.upper(), "line2": line2.upper(), "until": 2.6},
    "chapters": chapters, "lowerThirds": lts,
    "callouts": [],   # only populated for a genuinely red car, via scripts/redspot.py
    "follows": [
        {"at": ig, "hold": 4.0, "platform": "instagram",
         "name": os.environ.get('IG_NAME', 'Omarie Young'),
         "handle": os.environ.get('IG_HANDLE', '@nq.young'),
         "followers": os.environ.get('IG_FOLLOWERS', '3,697 followers'),
         "avatarSrc": "avatars/ig.png"},
        {"at": yt, "hold": 4.0, "platform": "youtube",
         "name": os.environ.get('YT_NAME', "Omari'e Young"),
         "handle": os.environ.get('YT_HANDLE', '@Youngomarie'),
         "followers": "YouTube", "avatarSrc": "avatars/yt.png"},
    ],
    "outro": {"at": round(d - 3.0, 2), "endCardSrc": ENDCARD},
}

json.dump(o, open(os.path.join(WORK, f'{r}.overlay.json'), 'w'))
json.dump({}, open(os.path.join(WORK, f'{r}.final.json'), 'w'))
print(r, 'duration', d, 'words', len(w), 'chapters', len(chapters), 'ig', ig, 'yt', yt)
