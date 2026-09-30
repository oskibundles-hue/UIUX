#!/usr/bin/env python3
"""Build the share page and share card for every job on the Formula Dynamics Job Board.
(Adapted from supercar-experience/website-tools/make_episode_pages.py.)

Reads the episode list (EP) from the JSON data block in ../16-website/index.html, then for each episode writes
  16-website/ep/<k>/index.html     a small page with that job's title, text and picture for link previews
                                   (iMessage, Instagram DMs, WhatsApp, X); it sends the visitor on to /#watch-<k>
  16-website/media/share/<k>.jpg   the 1200x630 picture those previews show (rendered from share-card.html)
plus media/share/series.jpg for the main page.

    python3 make_episode_pages.py            # pages + cards
    python3 make_episode_pages.py --pages    # pages only (no browser needed)

Cards need Node Playwright (npm i -g playwright) with its Chromium; set CHROME to use another binary.
Run it after adding an episode to EP, then commit ep/ and media/share/.
"""
import html, json, os, re, subprocess, sys, tempfile, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, '..', '16-website'))
BASE = 'https://formula-dynamics-job-board.onrender.com'
CHROME = os.environ.get('CHROME', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
FFMPEG = os.environ.get('FFMPEG', '/usr/local/bin/ffmpeg')


def data():
    src = open(os.path.join(SITE, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', src, re.S)
    if not m:
        sys.exit('No data block in index.html; has its format changed?')
    return json.loads(m.group(1))


def iso_day(d):  # "Sep 18" -> 2026-09-18
    mon = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split().index(d.split()[0]) + 1
    return '2026-%02d-%02d' % (mon, int(d.split()[1]))


def page(e, total):
    k, n = e['k'], e['no']
    title = f"Job {n}: {e['t']} · Formula Dynamics"
    url = f"{BASE}/ep/{k}/"
    img = f"{BASE}/media/share/{k}.jpg"
    desc = f"{e['s']} Full episode, {e['len']}, filmed {e['d']}, 2026, in our Las Vegas shop."
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": f"Job {n}: {e['t']}",
          "description": e['s'], "thumbnailUrl": [f"{BASE}/media/ep/{k}.jpg", img], "uploadDate": iso_day(e['d']),
          "duration": "PT%dM%dS" % divmod(e['sec'], 60), "contentUrl": f"{BASE}/media/ep/{k}.mp4",
          "embedUrl": f"{BASE}/#watch-{k}", "publisher": {"@type": "Organization", "name": "Formula Dynamics Performance"}}
    h = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{h(title)}</title>
<meta name="description" content="{h(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="video.episode">
<meta property="og:site_name" content="Formula Dynamics">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{h(title)}">
<meta property="og:description" content="{h(desc)}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Job {n} on the Formula Dynamics job board: {h(e['t'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{h(title)}">
<meta name="twitter:description" content="{h(desc)}">
<meta name="twitter:image" content="{img}">
<meta name="theme-color" content="#000000">
<link rel="icon" type="image/png" href="../../media/brand/icon-64.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script>location.replace("../../#watch-{k}")</script>
<meta http-equiv="refresh" content="1; url=../../#watch-{k}">
<style>
@font-face{{font-family:"Bebas Neue";src:url(../../media/fonts/BebasNeue-400.woff2) format("woff2")}}
@font-face{{font-family:"Barlow";font-weight:500;src:url(../../media/fonts/Barlow-500.woff2) format("woff2")}}
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#000;color:#fff;font:500 16px/1.5 Barlow,system-ui,-apple-system,Arial,sans-serif;padding:24px}}
main{{max-width:420px;text-align:center}}
img{{width:180px;display:block;margin:0 auto 18px}}
small{{font:600 12px ui-monospace,Menlo,monospace;letter-spacing:.14em;color:#FE0F13;text-transform:uppercase}}
h1{{margin:8px 0 10px;font:400 44px/1 "Bebas Neue",Impact,sans-serif;letter-spacing:.02em;text-transform:uppercase}}
a{{display:inline-block;margin-top:14px;background:#FE0F13;color:#fff;text-decoration:none;padding:12px 20px;font:400 24px/1 "Bebas Neue",Impact,sans-serif;letter-spacing:.04em;text-transform:uppercase}}
</style>
</head>
<body>
<main>
<img src="../../media/ep/{k}.jpg" alt="">
<small>Formula Dynamics · Job {n} of {total:02d}</small>
<h1>{h(e['t'])}</h1>
<p>{h(e['s'])}</p>
<a href="../../#watch-{k}">Watch the full episode</a>
</main>
</body>
</html>
"""


SHOT_JS = r"""
const {chromium}=require(process.env.PW||'playwright');
(async()=>{const b=await chromium.launch({executablePath:process.env.CHROME});const p=await b.newPage({viewport:{width:1200,height:630}});
await p.goto(process.argv[2]);await p.waitForLoadState('networkidle');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
await p.screenshot({path:process.argv[3]});await b.close()})().catch(e=>{console.error(e);process.exit(1)});
"""


def card(q, out_jpg):
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, 'card.png')
        js = os.path.join(tmp, 'shot.js')
        open(js, 'w').write(SHOT_JS)
        src = 'file://' + os.path.join(HERE, 'share-card.html') + '?' + urllib.parse.urlencode(q)
        env = dict(os.environ, CHROME=CHROME)
        if 'PW' not in env:
            root = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()
            env['PW'] = os.path.join(root, 'playwright')
        subprocess.run(['node', js, src, png], check=True, env=env)
        subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', png, '-q:v', '3', out_jpg], check=True)


def main():
    eps = data()['EP']
    media = 'file://' + os.path.join(SITE, 'media') + '/'
    os.makedirs(os.path.join(SITE, 'media', 'share'), exist_ok=True)
    for e in eps:
        d = os.path.join(SITE, 'ep', e['k']); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page(e, len(eps)))
        if '--pages' not in sys.argv:
            card(dict(k=e['k'], m=media, no=e['no'], d=e['d'], t=e['t'], car=e['car'], len=e['len']),
                 os.path.join(SITE, 'media', 'share', e['k'] + '.jpg'))
        print('ep/%s/' % e['k'])
    if '--pages' not in sys.argv:
        card(dict(k='series', m=media, count=len(eps)), os.path.join(SITE, 'media', 'share', 'series.jpg'))
        print('media/share/series.jpg')


if __name__ == '__main__':
    main()
