#!/usr/bin/env python3
"""Build every media file the Job Board site uses, except the 720p episode web copies
(those use the one ffmpeg line in ../16-website/HANDOFF.md) and the share cards
(make_episode_pages.py).

    python3 build_media.py [--src DIR] [--store DIR] [--only eps|ba|products|ads|logos]

--src    folder with the 12 approved Instagram episode files, named <key>.mp4
--store  folder with products.json, p01-p21.mp4 and valvecontroller-spotlight.mp4

Writes into ../16-website/media/:
  ep/<k>-loop.mp4      8 s muted loop, 360x640 (LOOP[k] is its start second)
  ep/<k>.jpg           cover, 540 wide (COVER[k] is the frame's second)
  ep/<k>-thumbs.jpg    scrub sprite: 96x170 tiles, 6 across, one every 5 s
  ba/<id>-a.jpg, -b.jpg  before/after frames (BA below), real frames from one job, never composited
  parts/<n>.jpg        store listing photo (ungraded, only resized), parts/<n>.mp4 the store ad loop
  parts/valve.jpg / valve-spot.mp4  the part fitted in Jobs 11-12 and its approved spotlight
  ads/<id>.mp4 + .jpg  the approved service ads at 540x960
  brand/               FD logo SVGs copied from ../02-logos
"""
import json, os, shutil, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.normpath(os.path.join(HERE, '..'))
OUT = os.path.join(FD, '16-website', 'media')
FF = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
SCR = '/tmp/claude-0/-home-user-UIUX/76da08ac-c037-5a8c-9a03-2cfb39602b99/scratchpad'


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SRC = arg('--src', os.path.join(SCR, 'fd-src'))
STORE = arg('--store', os.path.join(SCR, 'fd-store-ads'))
ONLY = arg('--only', None)

# loop start / cover second per episode, picked off contact sheets (no hp callouts, no spec cards)
LOOP = dict(floor=65, sf90=55, tune=80, movein=56, inventory=99, mc20=136, rangerover=102,
            stage2=146, detail=60, ppf=50, valve1=42, valve2=121)
COVER = dict(floor=72.9, sf90=57.6, tune=85.3, movein=58.6, inventory=104.3, mc20=143.9,
             rangerover=47.6, stage2=150, detail=62.6, ppf=52.6, valve1=44.6, valve2=123.6)

# before/after pairs: (id, episode, before second, after second, crop "w:h:x:y" or None for a full 9:16 split card)
BA = [
    # ('detail', ...) dropped 30 Sept: nq-check found it read backwards (clean car, then foam).
    ('ppf', 'ppf', 52.5, 60.0, '1080:860:0:430'),
    ('floor', 'floor', 32.0, 116.0, None),
    ('sf90', 'sf90', 90.0, 118.0, None),
]

ADS = [  # id, approved file (SFX = the version the shop posts), poster second
    ('aventador-tune', 'Aventador-FreeTune-SFX.mp4', 2.6),
    ('roma-tune', 'Roma-FreeTune-RYFT-SFX.mp4', 1.2),
    ('sf90-annual', 'FD-Annual-Service-3999-SFX.mp4', 1.2),
    ('f296-oil', 'Ferrari296-OilService-SFX.mp4', 1.2),
    ('sf90-pricing', 'SF90-Service-Pricing-SFX.mp4', 1.2),
    ('urus-diag', 'Urus-Diagnostics-SFX.mp4', 1.2),
    ('gt3-brakes', 'GT3RS-BrakeService-SFX.mp4', 1.2),
    ('roma-susp', 'Roma-Suspension-SFX.mp4', 1.2),
    ('gt3-ppf', 'GT3RS-WindshieldPPF-SFX.mp4', 1.2),
    ('roma-ppf', 'Roma-FullCarPPF-SFX.mp4', 1.2),
    ('urus-ppf', 'Urus-GradientPPF-SFX.mp4', 1.2),
]


def ff(*a):
    r = subprocess.run([FF, '-v', 'error', '-y', *map(str, a)], capture_output=True, text=True)
    if r.returncode:
        sys.exit('ffmpeg failed: ' + ' '.join(map(str, a)) + '\n' + r.stderr)


def eps():
    d = os.path.join(OUT, 'ep'); os.makedirs(d, exist_ok=True)
    for k, t in LOOP.items():
        s = os.path.join(SRC, k + '.mp4')
        ff('-ss', t, '-t', 8, '-i', s, '-an', '-vf', 'scale=360:640:flags=lanczos,fps=30', '-c:v', 'libx264',
           '-preset', 'slow', '-crf', 29, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(d, k + '-loop.mp4'))
        ff('-ss', COVER[k], '-i', s, '-frames:v', 1, '-vf', 'scale=540:-2:flags=lanczos', '-q:v', 4, os.path.join(d, k + '.jpg'))
        ff('-i', s, '-vf', 'fps=1/5,scale=96:170,tile=6x7', '-frames:v', 1, '-q:v', 6, os.path.join(d, k + '-thumbs.jpg'))
        print('ep', k)


def ba():
    d = os.path.join(OUT, 'ba'); os.makedirs(d, exist_ok=True)
    for i, k, a, b, crop in BA:
        vf = ('crop=' + crop + ',scale=900:-2:flags=lanczos') if crop else 'scale=540:-2:flags=lanczos'
        for side, t in (('a', a), ('b', b)):
            ff('-ss', t, '-i', os.path.join(SRC, k + '.mp4'), '-frames:v', 1, '-vf', vf, '-q:v', 3, os.path.join(d, f'{i}-{side}.jpg'))
        print('ba', i)


def get(url, path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, 'wb') as f:
        f.write(r.read())


def photo(url, out_jpg):
    from PIL import Image
    tmp = out_jpg + '.src'
    get(url, tmp)
    im = Image.open(tmp)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3]); im = bg
    else:
        im = im.convert('RGB')
    im.thumbnail((800, 800), Image.LANCZOS)
    im.save(out_jpg, quality=84, optimize=True, progressive=True)
    im.save(out_jpg[:-4] + '.webp', quality=82)
    os.remove(tmp)


def products():
    d = os.path.join(OUT, 'parts'); os.makedirs(d, exist_ok=True)
    data = json.load(open(os.path.join(STORE, 'products.json')))
    for p in data['store_ads_21']:
        n = '%02d' % p['n']
        photo(p['images'][0], os.path.join(d, n + '.jpg'))
        ff('-i', os.path.join(STORE, p['ad_video']), '-an', '-t', 8, '-vf', 'scale=540:676:flags=lanczos,fps=30', '-c:v', 'libx264',
           '-preset', 'slow', '-crf', 27, '-maxrate', '1000k', '-bufsize', '2000k', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
           os.path.join(d, n + '.mp4'))
        ff('-ss', 1.5, '-i', os.path.join(STORE, p['ad_video']), '-frames:v', 1, '-vf', 'scale=540:-2', '-q:v', 5, os.path.join(d, n + '-ad.jpg'))
        print('part', n)
    v = data['installed_on_camera']
    photo(v['images'][0], os.path.join(d, 'valve.jpg'))
    # the site copy starts at 3.9 s, after the spotlight's 'F8 SPYDER' title card (the page says 'F8 Spider'); the approved master is untouched
    ff('-ss', 3.9, '-i', os.path.join(STORE, 'valvecontroller-spotlight.mp4'), '-vf', 'scale=720:900:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow',
       '-crf', 23, '-maxrate', '2500k', '-bufsize', '5000k', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
       os.path.join(d, 'valve-spot.mp4'))
    ff('-ss', 4.5, '-i', os.path.join(STORE, 'valvecontroller-spotlight.mp4'), '-frames:v', 1, '-vf', 'scale=720:-2', '-q:v', 4, os.path.join(d, 'valve-spot.jpg'))
    print('valve')


def ads():
    d = os.path.join(OUT, 'ads'); os.makedirs(d, exist_ok=True)
    src = os.path.join(FD, '12-service-ads-footage', 'approved')
    for i, f, t in ADS:
        ff('-i', os.path.join(src, f), '-vf', 'scale=540:960:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', 26,
           '-maxrate', '1400k', '-bufsize', '2800k', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
           os.path.join(d, i + '.mp4'))
        ff('-ss', t, '-i', os.path.join(src, f), '-frames:v', 1, '-vf', 'scale=540:-2', '-q:v', 4, os.path.join(d, i + '.jpg'))
        print('ad', i)


def logos():
    d = os.path.join(OUT, 'brand'); os.makedirs(d, exist_ok=True)
    for f in ('fd-primary-horizontal--white.svg', 'fd-icon-mark-only--white.svg', 'fd-icon--white.svg', 'fd-primary-horizontal--black.svg'):
        shutil.copy(os.path.join(FD, '02-logos', 'svg-vector', f), d)
    shutil.copy(os.path.join(FD, '02-logos', 'png-transparent', 'fd-icon-mark-only--white_1000w.png'), os.path.join(d, 'icon-512.png'))


if __name__ == '__main__':
    for name, fn in (('logos', logos), ('ba', ba), ('eps', eps), ('products', products), ('ads', ads)):
        if ONLY in (None, name):
            fn()
