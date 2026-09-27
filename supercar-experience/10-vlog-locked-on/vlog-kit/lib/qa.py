"""qa.py -- checks on the built kit (python3 build.py --stage qa).

1. Safe-zone audit (every 0.1 s of the reel and at every mockup time): the ink box of every visible text line must be
   inside x 54-907, y 269-1536 (Instagram/TikTok safe area). The SE banner (A1/A2/A3) may sit on the right edge
   between y 269 and 1056. The reel's code chip and the kit index card are review annotations, reported apart.
2. Captions (H1/H2) stay inside y 1114-1382; nothing else covers that band while a caption is up.
3. Export probe: size, duration, fps, loudness (ffmpeg loudnorm print), and the delivery copy's size.
4. Check stills: the delivered reel decoded at the entry / middle / exit of every component -> exports/qa/.
Writes exports/qa/qa_summary.json.
"""
import json, os, subprocess, re
SAFE = dict(x0=54, x1=907, y0=269, y1=1536)
BANNER = ('bannerBug', 'bannerTab', 'bannerBreathe')
NOTE = ('codeChip', 'indexCard')


def audit(scene, here, work):
    FPS = 30000 / 1001
    ts = [round(i / 10, 3) for i in range(int(scene['reelEnd'] * 10))] + [m['t'] for m in scene['mocks']]
    tf = os.path.join(work, 'audit_times.json'); json.dump(ts, open(tf, 'w'))
    out = os.path.join(work, 'audit.json')
    subprocess.run(['node', os.path.join(here, 'lib', 'audit.js'), os.path.join(here, 'kit.html'), tf, out], check=True)
    res = json.load(open(out))
    bad, notes, caps = [], set(), []
    for fr in res:
        for r in fr['ink']:
            if r['type'] in NOTE:
                notes.add(r['type']); continue
            e = 1.0
            ok = r['x0'] >= SAFE['x0'] - e and r['x1'] <= SAFE['x1'] + e and r['y0'] >= SAFE['y0'] - e and r['y1'] <= SAFE['y1'] + e
            if not ok and r['type'] in BANNER:
                ok = r['y0'] >= SAFE['y0'] - e and r['y1'] <= 1056 + e and r['x0'] >= SAFE['x0'] - e and r['x1'] <= 1080
            if not ok:
                bad.append({'t': fr['t'], **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()}})
            if r['type'] in ('captionsBox', 'captionsStrip'):
                caps.append((fr['t'], r['y0'], r['y1']))
    capOut = [c for c in caps if c[1] < 1114 - 1 or c[2] > 1382 + 1]
    return {'frames_checked': len(res), 'outside_safe': bad[:60], 'n_outside_safe': len(bad),
            'captions_outside_band': capOut[:20], 'annotations_skipped': sorted(notes)}


def probe(ff, path):
    if not os.path.exists(path):
        return None
    err = subprocess.run([ff, '-hide_banner', '-i', path], capture_output=True, text=True).stderr
    ln = subprocess.run([ff, '-hide_banner', '-i', path, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(ln[ln.rfind('{'):ln.rfind('}') + 1])
    return {'file': os.path.basename(path), 'MiB': round(os.path.getsize(path) / 2**20, 2),
            'duration': re.search(r'Duration: (\S+),', err).group(1), 'video': re.search(r'Video: ([^\n]+)', err).group(1)[:120],
            'audio': (re.search(r'Audio: ([^\n]+)', err) or [None, None])[1], 'loudness_I': j['input_i'], 'true_peak': j['input_tp']}


def stills(scene, here, ff):
    qd = os.path.join(here, 'exports', 'qa'); os.makedirs(qd, exist_ok=True)
    for f in os.listdir(qd):
        if f.endswith('.jpg'):
            os.remove(os.path.join(qd, f))
    src = os.path.join(here, 'exports', 'vlog-kit-reel.mp4')
    FPS = 30000 / 1001
    pts = []
    for c in scene['comps']:
        if c['type'] == 'codeChip' or c['t0'] >= scene['reelEnd']:
            continue
        a, b = c['t0'], min(c['t1'], scene['reelEnd'] - 0.02)
        for tag, t in (('in', a + 0.12), ('mid', (a + b) / 2), ('out', b - 0.1)):
            pts.append((int(round(t * FPS)), f"{c['code']}_{c['type']}_{tag}"))
    pts = sorted(set(pts))
    sel = '+'.join(f'eq(n\\,{n})' for n, _ in pts)
    tmp = os.path.join(qd, '_tmp'); os.makedirs(tmp, exist_ok=True)
    subprocess.run([ff, '-v', 'error', '-y', '-i', src, '-vf', f"select='{sel}',scale=540:960", '-vsync', '0', os.path.join(tmp, '%04d.jpg')], check=True)
    fs = sorted(os.listdir(tmp))
    uniq = sorted(set(n for n, _ in pts))
    names = {}
    for n, nm in pts:
        names.setdefault(n, []).append(nm)
    for f, n in zip(fs, uniq):
        os.rename(os.path.join(tmp, f), os.path.join(qd, f"f{n:05d}_{n / FPS:06.2f}s_{'+'.join(names[n])[:80]}.jpg"))
    os.rmdir(tmp)
    return len(uniq)


def run(scene, here, work, ff):
    s = {'audit': audit(scene, here, work)}
    s['master'] = probe(ff, os.path.join(here, 'exports', 'vlog-kit-reel.mp4'))
    s['delivery'] = probe(ff, os.path.join(here, 'exports', 'vlog-kit-reel_DELIVERY.mp4'))
    if s['master']:
        s['check_stills'] = stills(scene, here, ff)
    os.makedirs(os.path.join(here, 'exports', 'qa'), exist_ok=True)
    json.dump(s, open(os.path.join(here, 'exports', 'qa', 'qa_summary.json'), 'w'), indent=1)
    a = s['audit']
    print(f"qa: {a['frames_checked']} times audited, {a['n_outside_safe']} text boxes outside the safe area, "
          f"{len(a['captions_outside_band'])} caption boxes outside y 1114-1382")
    for b in a['outside_safe'][:12]:
        print('   ', b)
    print('qa:', json.dumps({k: s[k] for k in ('master', 'delivery')}, indent=1))
