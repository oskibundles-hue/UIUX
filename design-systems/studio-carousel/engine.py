"""Carousel engine: a folder of photos and a words file in, five checked slides and one sheet out.

    python3 engine.py <photo folder> --words words.json --out out/ [--mockup]
    python3 engine.py --approve out/      # only after Omarie has looked at out/sheet.jpg

It builds the photo build of the studio carousel (LAYOUT.md). In order, it:
  1. reads the words file and refuses a missing word or one that isn't on its allowed list;
  2. picks which photo goes on which slide (the hook, the part, the four steps, the large photo);
  3. looks for plates and faces in every photo it uses (finder.py), covers the plates and crops the faces out;
  4. writes out/spec.json, builds the slides and runs qa.py's checks on them;
  5. writes out/sheet.jpg: the five slides, and under them every photo with what it covered outlined.
It stops with `STOPPED` and a plain reason when it can't do one of these. `all clear` means the checks
passed, not that the post is approved: the plates and faces are approved on the sheet, then --approve
writes the files to post. --mockup also fills the post mockup page (../post-mockup) with the slides.

Nothing is generated: photos supplied, rembg and Pillow only. README.md, "The engine", has the words file.
Needs numpy, Pillow, scipy and opencv-python-headless; rembg only when a part still has to be cut out.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finder  # noqa: E402
import qa  # noqa: E402
from photos import make_cuts, photo, redact  # noqa: E402

ROLES = ('brand', 'brand_1', 'brand_2', 'handle', 'cover_word', 'model', 'subject_name', 'category', 'job',
         'part_line', 'steps_title', 'step_1', 'step_2', 'step_3', 'step_4', 'view_line', 'cta_1', 'cta_2')
PHOTO_SLOTS = ('hero', 'view', 'step1', 'step2', 'step3', 'step4')
PART_SLOTS = ('hero_part', 'main', 'closing_part')
SLIDE_OF = {'hero': 'slide 1, the hook', 'view': 'slide 4, the large photo', 'step1': 'slide 3, step 01',
            'step2': 'slide 3, step 02', 'step3': 'slide 3, step 03', 'step4': 'slide 3, step 04',
            'part': 'slides 1, 2 and 5, the part'}
HINTS = {'hero': ('hero', 'hook', 'cover'), 'view': ('view', 'wide', 'large')}
SHAPE = {'hero': 740 / 600, 'view': 760 / 860}   # the frames these photos fill (generate.py, PHOTO_LAYOUT)
PAD = 0.12                                       # a found plate's box is grown by this much before it is covered


class Stop(Exception):
    """Something a person has to fix. The message is the whole report."""


def is_cutout(path):
    with Image.open(path) as im:
        return im.mode in ('RGBA', 'LA') and im.getchannel('A').getextrema()[0] < 250


def read_job(path):
    try:
        with open(path) as fh:
            job = json.load(fh)
    except (OSError, ValueError) as e:
        raise Stop(f'the words file {path} could not be read: {e}')
    brand = job.get('brand') or {}
    if not brand.get('colour') or not brand.get('font'):
        raise Stop('the words file needs "brand": {"colour": "#RRGGBB", "font": "a .ttf path"}')
    font = brand['font'] if os.path.isabs(brand['font']) else os.path.join(os.path.dirname(os.path.abspath(path)),
                                                                           brand['font'])
    if not os.path.exists(font):
        raise Stop(f'the font {brand["font"]} is not there (looked for {os.path.normpath(font)})')
    job['brand'] = {**brand, 'font': os.path.normpath(font)}
    words = job.get('words') or {}
    missing = [r for r in ROLES if not str(words.get(r, '')).strip()]
    if missing:
        raise Stop(f'the words file has no words for: {", ".join(missing)}. Every slide needs its words; '
                   f'the engine never writes copy')
    extra = [r for r in words if r not in ROLES]
    if extra:
        raise Stop(f'the words file has words the slides have no place for: {", ".join(extra)}')
    used = sorted({w for r in ROLES for w in qa.words_of(words[r])})
    if 'allowed_words' in job:   # an approved list was supplied: the slides may carry nothing else
        allowed = {w.upper() for w in job['allowed_words']}
        off = [f'"{w}" (in {r}: "{words[r]}")' for r in ROLES for w in qa.words_of(words[r]) if w not in allowed]
        if off:
            raise Stop('these words are not on the words file\'s allowed_words, so they can\'t go on a slide: '
                       + '; '.join(off))
    job['allowed'] = sorted(set(used) | {'01', '02', '03', '04'})
    return job


def pick(folder, job):
    """Which file fills which slot. Pins in the words file win, then names, then shape and name order."""
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')))
    if not files:
        raise Stop(f'no photos in {folder} (it reads .jpg, .png and .webp)')
    pins = job.get('pick') or {}
    for slot, f in pins.items():
        if slot not in PHOTO_SLOTS + PART_SLOTS + ('part',):
            raise Stop(f'"pick" names a place that doesn\'t exist: {slot}. The places are '
                       f'{", ".join(PHOTO_SLOTS + PART_SLOTS)} and part (a photo to cut the part out of)')
        if f not in files:
            raise Stop(f'"pick" puts {f} on {slot}, but that file isn\'t in {folder}')
    cutouts = [f for f in files if f.lower().endswith('.png') and is_cutout(os.path.join(folder, f))]
    photos = [f for f in files if f not in cutouts]
    chosen, why = dict(pins), {s: 'pinned in the words file' for s in pins}
    free = [f for f in photos if f not in pins.values()]

    def take(slot, f, reason):
        chosen[slot], why[slot] = f, reason
        free.remove(f)

    part_src = pins.get('part')
    if not part_src and not cutouts:   # no cutout supplied: a photo named as the part is cut out with rembg
        part_src = next((f for f in free if 'part' in f.lower()), None)
        if part_src:
            take('part', part_src, 'named "part"')
    for slot, hints in HINTS.items():
        f = next((f for f in free if any(h in f.lower() for h in hints)), None)
        if slot not in chosen and f:
            take(slot, f, 'by its name')
    steps = [s for s in PHOTO_SLOTS[2:] if s not in chosen]
    for f in [f for f in free if re.search(r'step\D{0,2}\d', f.lower())][:len(steps)]:
        take(steps.pop(0), f, 'by its name')
    shape = {}
    for slot in ('hero', 'view'):   # no name to go on: the photo whose shape fills that frame best
        if slot in chosen or not free:
            continue
        for f in free:
            if f not in shape:
                w, h = photo(os.path.join(folder, f)).size
                shape[f] = w / h
        # the frames leave four photos for the steps, so only the first six are in the running
        pool = free[:6 - sum(s in chosen for s in PHOTO_SLOTS)] or free
        take(slot, min(pool, key=lambda f: abs(shape[f] - SHAPE[slot])), 'its shape fits that frame best')
    for slot in [s for s in PHOTO_SLOTS[2:] if s not in chosen]:
        if free:
            take(slot, free[0], 'in name order')
    short = [s for s in PHOTO_SLOTS if s not in chosen]
    if short:
        raise Stop(f'not enough photos: {len(photos)} in {folder}, and the five slides need 6 (the hook, the large '
                   f'photo and four steps). Nothing to put on: {", ".join(SLIDE_OF[s] for s in short)}')
    if not part_src:
        left = [c for c in cutouts if c not in pins.values()]
        if 'main' not in chosen:
            if not left:
                raise Stop('no part to show: slides 1, 2 and 5 float one cut-out part. Put a cut-out .png in the '
                           'folder, or name a photo "part..." (or pin it as "part") and the engine cuts it out')
            chosen['main'], why['main'] = left.pop(0), 'the first cut-out by name'
        for slot in ('hero_part', 'closing_part'):
            if slot not in chosen:
                nxt = left.pop(0) if slot == 'hero_part' and left else chosen['main']
                chosen[slot], why[slot] = nxt, 'the next cut-out by name' if nxt != chosen['main'] else 'the same part'
    unused = [f for f in files if f not in chosen.values()]
    return chosen, why, unused


def look(folder, chosen, job):
    """Find plates and faces in every photo used. A box a person gave in the words file wins over the finder."""
    given = job.get('photos') or {}
    seen = {}
    for slot in [s for s in PHOTO_SLOTS + ('part',) if s in chosen]:
        f = chosen[slot]
        if f in seen:
            continue
        found = finder.find(os.path.join(folder, f))
        entry = {'file': f, 'redact': [], 'found': found, 'by': 'finder'}
        for p in found['plates']:
            x0, y0, x1, y1 = p['box']
            gx, gy = (x1 - x0) * PAD, (y1 - y0) * PAD
            entry['redact'].append([max(0, int(x0 - gx)), max(0, int(y0 - gy)), min(found['size'][0], int(x1 + gx)),
                                    min(found['size'][1], int(y1 + gy))])
        if found['crop']:
            entry['crop'] = found['crop']
        if f in given:   # a person looked at this one
            if not isinstance(given[f].get('redact'), list):
                raise Stop(f'the words file lists {f} under "photos" with no "redact" list. Give its plate boxes, '
                           f'or [] when you have looked and it has none')
            entry.update({k: given[f][k] for k in ('redact', 'crop', 'focus') if k in given[f]})
            entry['by'] = 'person'
            if 'crop' not in given[f]:
                entry.pop('crop', None)
        seen[f] = entry
    return seen


def status(entry):
    """One line for the sheet and the report, and whether this photo needs a close look."""
    n, found = len(entry['redact']), entry['found']
    if entry['by'] == 'person':
        return f'set by a person: {n} plate box(es)' + (', cropped' if entry.get('crop') else ''), False
    if found['status'] == 'check':
        return 'CHECK THIS ONE: ' + '; '.join(found['why']) + (f' ({n} box(es) covered)' if n else ''), True
    return (f'{n} plate(s) covered' if n else 'none found'), False


def write_spec(folder, out, job, chosen, seen):
    rel = lambda f: os.path.relpath(os.path.join(folder, f), out)  # noqa: E731
    spec = {'build': 'photo', 'brand': {**job['brand'], 'font': os.path.relpath(job['brand']['font'], out)},
            'words': job['words'], 'allowed_words': job['allowed'], 'photos': {}, 'parts': {},
            'slides': job.get('slides') or {}, 'plate_check': {'status': 'proposed'}}
    for k in ('theme', 'layout'):
        if k in job:
            spec[k] = job[k]
    for slot in PHOTO_SLOTS:
        e = seen[chosen[slot]]
        spec['photos'][slot] = {**{k: e[k] for k in ('redact', 'crop') if k in e}, 'file': rel(e['file']),
                                'found': {'by': e['by'], 'status': e['found']['status'], 'why': e['found']['why'],
                                          'plates': e['found']['plates'], 'faces': e['found']['faces']}}
    clean = job.get('clean') or {}
    if 'part' in chosen:   # cut the part out of its photo, with its plates covered and faces cropped first
        e = seen[chosen['part']]
        os.makedirs(os.path.join(out, 'cut'), exist_ok=True)
        im = photo(os.path.join(folder, e['file']))
        for box in e['redact']:
            im = redact(im, box)
        if e.get('crop'):
            im = im.crop(tuple(e['crop']))
        im.save(os.path.join(out, 'cut', 'part_source.png'))
        try:
            make_cuts({'part': {'file': 'cut/part_source.png', 'out': 'cut/part.png'}}, out)
        except ImportError:
            raise Stop(f'{e["file"]} has to be cut out and rembg isn\'t installed. Run the engine again with '
                       f'`--with rembg` added to the uv command')
        part = {'file': 'cut/part.png', **({'clean': clean[e['file']]} if e['file'] in clean else {})}
        spec['parts'] = {s: part for s in PART_SLOTS}
    else:
        for slot in PART_SLOTS:
            f = chosen[slot]
            spec['parts'][slot] = {'file': rel(f), 'clean': clean[slot]} if slot in clean else (
                {'file': rel(f), 'clean': clean[f]} if f in clean else rel(f))
    with open(os.path.join(out, 'spec.json'), 'w') as fh:
        json.dump(spec, fh, indent=1)
    return os.path.join(out, 'spec.json')


def check_sheet(folder, out, chosen, seen):
    """The five slides, and under them each photo as it went in: covers applied and outlined, flags in words."""
    slides = os.path.join(out, 'slides.jpg')
    subprocess.run([sys.executable, os.path.join(HERE, 'sheet.py'), slides] +
                   [f'{i}/5={os.path.join(out, f"0{i}.png")}' for i in range(1, 6)], check=True,
                   stdout=subprocess.DEVNULL)
    top = Image.open(slides)
    slots = [s for s in PHOTO_SLOTS + ('part',) if s in chosen]
    tw, th, lab = top.width // len(slots), 250, 64
    sheet = Image.new('RGB', (top.width, top.height + 44 + th + lab), 'white')
    sheet.paste(top, (0, 0))
    d = ImageDraw.Draw(sheet)
    d.text((8, top.height + 14), 'PLATES AND FACES: each photo as it went in. Red = plate covered, amber = covered '
           'but unsure, blue = face, green = the crop that removes it.', fill='black')
    for i, slot in enumerate(slots):
        e = seen[chosen[slot]]
        im = photo(os.path.join(folder, e['file']))
        for box in e['redact']:
            im = redact(im, box)
        dd = ImageDraw.Draw(im)
        t = max(5, im.width // 120)
        sure = [p['sure'] for p in e['found']['plates']] if e['by'] == 'finder' else []
        for j, box in enumerate(e['redact']):
            dd.rectangle(box, outline=(230, 30, 30) if j >= len(sure) or sure[j] else (255, 170, 0), width=t)
        for f in e['found']['faces']:
            dd.rectangle(f['box'], outline=(40, 110, 255), width=t)
        if e.get('crop'):
            dd.rectangle(e['crop'], outline=(40, 200, 90), width=t)
        im.thumbnail((tw - 12, th))
        x, y = i * tw, top.height + 44
        sheet.paste(im, (x + 6, y))
        line, flag = status(e)
        d.text((x + 6, y + th + 6), f'{SLIDE_OF[slot]}', fill='black')
        for k, part in enumerate(wrap(line, tw // 6 - 2)[:3]):
            d.text((x + 6, y + th + 20 + 13 * k), part, fill=(200, 30, 30) if flag else (40, 40, 40))
    path = os.path.join(out, 'sheet.jpg')
    sheet.save(path, quality=90)
    os.remove(slides)
    return path


def wrap(text, n):
    lines, cur = [], ''
    for w in text.split():
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return lines + [cur]


def digest(out):
    h = hashlib.sha1()
    for i in range(1, 6):
        with open(os.path.join(out, f'0{i}.png'), 'rb') as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def mockup(out, job, approved=False):
    """Fill the post mockup page with these slides: out/mockup/index.html and the slides as JPEGs beside it."""
    post = job.get('post') or {}
    need = [k for k in ('title', 'sub', 'handle', 'caption', 'name') if not post.get(k)]
    if need:
        raise Stop(f'--mockup needs "post" in the words file with: {", ".join(need)}. The caption is copy, so '
                   f'the engine never writes it')
    with open(os.path.join(HERE, '..', 'post-mockup', 'template.html')) as fh:
        page = fh.read()
    dest = os.path.join(out, 'mockup')
    os.makedirs(os.path.join(dest, 'slides'), exist_ok=True)
    labels = ('The hook', 'The part', 'The steps', 'The large photo', 'Call to action')
    for i in range(1, 6):
        Image.open(os.path.join(out, f'0{i}.png')).convert('RGB').save(
            os.path.join(dest, 'slides', f'0{i}.jpg'), quality=93, subsampling=0)
    data = {'title': post['title'], 'sub': post['sub'], 'handle': post['handle'], 'location': post.get('location', ''),
            'avatar': '', 'aspect': '4/5', 'demo': False,
            'variants': [{'id': 'slides', 'label': post.get('version', 'Studio'), 'caption': post['caption']}],
            'items': [{'f': f'0{i}.jpg', 'name': f'{post["name"]}-0{i}.jpg', 'label': labels[i - 1]}
                      for i in range(1, 6)],
            'notes': ['<b>Plates and faces:</b> ' + ('approved on the contact sheet.' if approved else
                      'found by the engine and <b>not approved yet</b>. Look at the contact sheet before posting.')]
            + list(post.get('notes') or []),
            'storageKey': 'post-mockup-' + re.sub(r'\W+', '-', post['name'].lower())}
    page, n = re.subn(r'const POST = \{.*?\n\};\n(?=/\* ======== end of POST)',
                      lambda m: 'const POST = ' + json.dumps(data, indent=2) + ';\n', page, flags=re.S)
    if n != 1:
        raise Stop('the post mockup template has changed: its POST block was not found')
    page = re.sub(r'<title>.*?</title>', f'<title>{re.sub("<[^>]+>", " ", post["title"])}</title>', page, count=1)
    page = re.sub(r'--accent:#[0-9A-Fa-f]{6}', f'--accent:{job["brand"]["colour"]}', page, count=1)
    if post.get('display'):   # {"family": "Big Shoulders Display", "google": "Big+Shoulders+Display:wght@700"}
        page = re.sub(r"--display:'[^']+'", f"--display:'{post['display']['family']}'", page, count=1)
        page = re.sub(r'css2\?family=[^&"]+', 'css2?family=' + post['display']['google'], page, count=1)
    with open(os.path.join(dest, 'index.html'), 'w') as fh:
        fh.write(page)
    return os.path.join(dest, 'index.html')


def run(folder, words, out, with_mockup):
    job = read_job(words)
    os.makedirs(out, exist_ok=True)
    chosen, why, unused = pick(folder, job)
    print('PHOTOS')
    for slot in [s for s in PHOTO_SLOTS + ('part',) + PART_SLOTS if s in chosen]:
        print(f'  {slot:<13}{chosen[slot]:<28}{why[slot]}')
    if unused:
        print(f'  not used: {", ".join(unused)}')
    seen = look(folder, chosen, job)
    spec = write_spec(folder, out, job, chosen, seen)
    fails = qa.check(spec, out)
    if fails:
        for name in ('sheet.jpg',):
            if os.path.exists(os.path.join(out, name)):
                os.remove(os.path.join(out, name))
        raise Stop(f'{len(fails)} check(s) failed, so there is nothing to show yet:\n  ' + '\n  '.join(fails)
                   + f'\nThe slides in {out} are not good to use. Fix the words file or the photos and run it again.')
    sheet = check_sheet(folder, out, chosen, seen)
    with open(spec) as fh:
        data = json.load(fh)
    data['plate_check']['slides'] = digest(out)
    with open(spec, 'w') as fh:
        json.dump(data, fh, indent=1)
    print('PLATES AND FACES')
    flags = 0
    for f, e in seen.items():
        line, flag = status(e)
        flags += flag
        print(f'  {f:<28}{line}')
    print(f'all clear: 5 slides built and checked in {out}')
    covered = sum(len(e['redact']) for e in seen.values())
    print(f'NOT APPROVED YET: {covered} plate box(es) covered across {len(seen)} photo(s), {flags} photo(s) to check '
          f'closely. Look at {sheet}, every photo, because the finder misses plates. Then: engine.py --approve {out}')
    if with_mockup:
        print('mockup page:', mockup(out, job))


def approve(out):
    spec = os.path.join(out, 'spec.json')
    if not os.path.exists(spec):
        raise Stop(f'nothing to approve: {spec} is not there. Build the carousel first')
    with open(spec) as fh:
        data = json.load(fh)
    if data.get('plate_check', {}).get('slides') != digest(out):
        raise Stop('the slides have changed since they were built and checked. Build them again, look at the new '
                   'sheet, then approve')
    data['plate_check'].update({'status': 'approved', 'on': datetime.date.today().isoformat()})
    with open(spec, 'w') as fh:
        json.dump(data, fh, indent=1)
    final = os.path.join(out, 'final')
    os.makedirs(final, exist_ok=True)
    for i in range(1, 6):
        Image.open(os.path.join(out, f'0{i}.png')).convert('RGB').save(os.path.join(final, f'0{i}.jpg'), quality=95,
                                                                       subsampling=0)
    print(f'approved: 5 files to post in {final}')


if __name__ == '__main__':
    args = sys.argv[1:]
    try:
        if '--approve' in args:
            approve(args[args.index('--approve') + 1])
        else:
            opt = {k: args[args.index(k) + 1] for k in ('--words', '--out') if k in args and args.index(k) + 1 < len(args)}
            rest = [a for a in args if a != '--mockup' and a not in opt and a not in opt.values()]
            if len(rest) != 1 or len(opt) != 2:
                sys.exit(__doc__)
            if not os.path.isdir(rest[0]):
                raise Stop(f'{rest[0]} is not a folder of photos')
            run(os.path.abspath(rest[0]), opt['--words'], os.path.abspath(opt['--out']), '--mockup' in args)
    except Stop as e:
        print(f'STOPPED: {e}')
        sys.exit(1)
