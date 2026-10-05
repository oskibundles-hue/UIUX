#!/usr/bin/env python3
"""build_hud.py -- turn a HUD layout recipe into a renderable layer page for one clip.

    python3 build_hud.py --scene layouts/hud-2-hood.json --tracks examples/2026-09-15-drive-back/tracks.json \
        --side-g examples/2026-09-15-drive-back/side_g.json --name drive-back

Writes ../vlog-kit/.hud_<name>.html (git-ignored): the vlog kit's own kit.html with the scene, the tracks, the
side-G series and the DRV drive plate (drive_deck.js) inlined. It renders with the kit's capture script:

    cd ../vlog-kit && node lib/kcapture.js "file://$PWD/.hud_<name>.html" <outDir> seq 30000/1001 <seconds> --workers 3

Then lay the PNG sequence over the clip with tools/encode.sh. Every component is the kit's (lib/sekit.js) except DRV.
"""
import argparse, base64, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent / 'vlog-kit'
LOGOS = HERE.parent.parent / '02-logos' / 'png'

ap = argparse.ArgumentParser()
ap.add_argument('--scene', required=True); ap.add_argument('--tracks', required=True)
ap.add_argument('--side-g', default=None); ap.add_argument('--name', required=True)
a = ap.parse_args()
scene = json.load(open(a.scene)); tracks = json.load(open(a.tracks))
lat = json.load(open(a.side_g)) if a.side_g else []
logos = {f: 'data:image/png;base64,' + base64.b64encode((LOGOS / f).read_bytes()).decode()
         for f in ['sce-primary-horizontal--white.png', 'sce-icon-mark-only--white.png']}
kit = (KIT / 'kit.html').read_text()
head, rest = kit.split('<script src=".work/scene.js"></script>', 1)
rest = rest.replace('<script src=".work/tracks.js"></script>\n', '').replace('<script src=".work/kitdata.js"></script>\n', '')
inject = ('<script>window.SCENE = ' + json.dumps(scene) + ';\nwindow.TRACKS = ' + json.dumps(tracks) +
          ';\nwindow.KITDATA = ' + json.dumps({'logos': logos}) + ';\nwindow.LAT = ' + json.dumps(lat) + ';</script>\n')
deck = (HERE / 'drive_deck.js').read_text()
rest = rest.replace('<script src="lib/sekit.js"></script>', '<script src="lib/sekit.js"></script>\n<script>' + deck + '</script>', 1)
html = head.replace('<title>SE Vlog Kit Layer</title>', '<title>SE Driving HUD Layer</title>') + inject + rest
html = html.replace("const CHIP = hashArg('chip') !== '0';", 'const CHIP = false;')
out = KIT / f'.hud_{a.name}.html'
out.write_text(html)
print('wrote', out)
