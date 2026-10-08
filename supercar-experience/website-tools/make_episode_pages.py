#!/usr/bin/env python3
"""Build the share page and share card for every episode of Behind the Wheel.

Reads the episode list (EP[]) from ../11-website/index.html, then for each episode writes
  11-website/ep/<k>/index.html     a tiny page with that episode's title, text and picture for link
                                   previews (iMessage, Instagram DMs, WhatsApp, X); it opens the episode
                                   on the main page (#watch-<k>)
  11-website/media/share/<k>.jpg   the 1200x630 picture those previews show (rendered from share-card.html)
plus media/share/series.jpg for the main page.

    python3 make_episode_pages.py            # pages + cards
    python3 make_episode_pages.py --pages    # pages only (no Chrome needed)

Needs Google Chrome for the cards, and ffmpeg (~/.local/vlogtools/bin/ffmpeg) to save them as JPG.
Run it after adding an episode to EP[], then commit ep/ and media/share/.
"""
import html, json, os, re, subprocess, sys, tempfile, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, '..', '11-website'))
BASE = 'https://supercar-experience-garage.onrender.com'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FFMPEG = os.path.expanduser('~/.local/vlogtools/bin/ffmpeg')


def episodes():
    src = open(os.path.join(SITE, 'index.html'), encoding='utf-8').read()
    block = src[src.index('const EP=['):]
    block = block[:block.index('];')]
    eps = []
    for m in re.finditer(r'\{k:"([a-z0-9]+)",d:"([^"]+)",t:"([^"]+)",s:"([^"]+)",len:"([^"]+)",sec:(\d+),where:"([^"]+)"', block):
        k, d, t, s, ln, sec, where = m.groups()
        eps.append(dict(k=k, d=d, t=t, s=s, len=ln, sec=int(sec), where=where, n=len(eps) + 1))
    if not eps:
        sys.exit('No episodes found in EP[]; has its format changed?')
    return eps


def iso_day(d):  # "Sep 15" -> 2026-09-15
    mon = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split().index(d.split()[0]) + 1
    return '2026-%02d-%02d' % (mon, int(d.split()[1]))


def page(e, total):
    k, n = e['k'], '%02d' % e['n']
    title = f"EP {n} · {e['t']} · Behind the Wheel"
    url = f"{BASE}/ep/{k}/"
    img = f"{BASE}/media/share/{k}.jpg"
    desc = f"{e['s']} Full episode, {e['len']}, filmed {e['d']}, 2026. Supercar Experience, Las Vegas."
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": f"{e['t']} · Behind the Wheel EP {n}",
          "description": e['s'], "thumbnailUrl": [f"{BASE}/media/ep/{k}.jpg", img], "uploadDate": "2026-09-29",
          "duration": "PT%dM%dS" % divmod(e['sec'], 60), "contentUrl": f"{BASE}/media/ep/{k}.mp4",
          "embedUrl": f"{BASE}/#watch-{k}", "publisher": {"@type": "Organization", "name": "Supercar Experience"}}
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
<meta property="og:site_name" content="Supercar Experience">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{h(e['t'])} · Behind the Wheel EP {n}">
<meta property="og:description" content="{h(desc)}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Episode {n} of Behind the Wheel: {h(e['t'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{h(e['t'])} · Behind the Wheel EP {n}">
<meta name="twitter:description" content="{h(desc)}">
<meta name="twitter:image" content="{img}">
<meta name="theme-color" content="#0A0A0C">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script>location.replace("../../#watch-{k}")</script>
<meta http-equiv="refresh" content="1; url=../../#watch-{k}">
<style>
:root{{--o:#FF4F16;--ink:#0A0A0C}}
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--ink);color:#fff;font:500 16px/1.5 "Hanken Grotesk",system-ui,-apple-system,Arial,sans-serif;padding:24px}}
main{{max-width:420px;text-align:center}}
img{{width:180px;border-radius:12px;display:block;margin:0 auto 18px}}
small{{font:600 12px ui-monospace,Menlo,monospace;letter-spacing:.14em;color:var(--o);text-transform:uppercase}}
h1{{margin:8px 0 10px;font-size:30px;line-height:1.05}}
a{{display:inline-block;margin-top:14px;background:var(--o);color:var(--ink);font-weight:700;text-decoration:none;padding:12px 20px;border-radius:999px}}
</style>
</head>
<body>
<main>
<img src="../../media/ep/{k}.jpg" alt="">
<small>Behind the Wheel · Episode {n} of {total:02d}</small>
<h1>{h(e['t'])}</h1>
<p>{h(e['s'])}</p>
<a href="../../#watch-{k}">Watch the full episode</a>
</main>
</body>
</html>
"""


def card(q, out_jpg):
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, 'card.png')
        src = 'file://' + os.path.join(HERE, 'share-card.html') + '?' + urllib.parse.urlencode(q)
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                        '--window-size=1200,630', '--virtual-time-budget=6000', '--screenshot=' + png, src],
                       check=True, capture_output=True)
        subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', png, '-q:v', '3', out_jpg], check=True)


def main():
    eps = episodes()
    media = 'file://' + os.path.join(SITE, 'media') + '/'
    os.makedirs(os.path.join(SITE, 'media', 'share'), exist_ok=True)
    for e in eps:
        d = os.path.join(SITE, 'ep', e['k']); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page(e, len(eps)))
        if '--pages' not in sys.argv:
            card(dict(k=e['k'], m=media, n='%02d' % e['n'], d=e['d'], t=e['t'], len=e['len'], where=e['where']),
                 os.path.join(SITE, 'media', 'share', e['k'] + '.jpg'))
        print('ep/%s/' % e['k'])
    if '--pages' not in sys.argv:
        card(dict(k='series', m=media, count=len(eps)), os.path.join(SITE, 'media', 'share', 'series.jpg'))
        print('media/share/series.jpg')


if __name__ == '__main__':
    main()
