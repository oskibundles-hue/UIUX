# gen.py -- writes ../../vlog-kit/.hud_mock-mclaren-run.html (git-ignored) and slots.json. Then, per slot:
#   node ../../hud-layouts/tools/hud_still.js <page> <slot.at> bg/<slot.bg>.png out/<slot.id>.png   and   python3 board.py
# bg/ holds the 9:16 frames (1080x1920 crops of the clips at the times in README.md); not committed.
# Mockup stills for the Sep 26-27 McLaren trip vlog (two parts): rally v2 components + the one-strip HUD, glass-orange.
import json, re, pathlib, subprocess, sys
LO = pathlib.Path(__file__).resolve().parents[2]  # 10-vlog-locked-on
KIT, V2, HUD = LO / 'vlog-kit', LO / '2026-09-15-rally-v2', LO / 'hud-layouts'
M = pathlib.Path(__file__).resolve().parent
theme = json.load(open(HUD / 'themes/glass-orange.json'))
def hms(s): h, m, x = map(int, s.split(':')); return h * 3600 + m * 60 + x

# one 10 s slot per still; the still is taken at slot + 3.0 unless 'at' says otherwise
S = [  # id, bg, clock at the still (camera time), comps (times relative to the slot), still offset
 ('p1-01', 'x6', '13:30:02', [('HOOK', 'v2hook', 0, 2, {'eyebrow': 'SUPERCAR EXPERIENCE · ROAD TRIP', 'line1': 'ONE-WAY TICKET', 'line2': 'PART 1 · SEP 26 2026', 'x': 54, 'y': 330, 'w': 853, 'exit': 1.42})], 0.3),
 ('p1-02', 'p1b', '04:58:16', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                               ('G1', 'chapterSlam', 2.1, 4.05, {'tag': '04:56 · CH 01 / 03', 'title': 'WHEELS UP', 'y': 350, 'maxW': 700, 'maxS': 215})], 3.0),
 ('p1-03', 'p1c', '05:31:59', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                               ('B1', 'personLock', 1.5, 5, {'track': 'face', 'name': 'OMARIE', 'handle': '@NQ.YOUNG', 'acquire': 1.5, 'exit': 4.7, 'maxBottom': 1100})], 3.0),
 ('p1-04', 'p1d', '09:00:17', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                               ('D1', 'clockStamp', 1.0, 6, {'x': 54, 'y': 300, 'start': '00:00:00', 'place': 'IN THE AIR', 'date': 'SEP 26 2026', 'built': False})], 3.0),
 ('p1-05', 'p1e', '10:14:40', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                               ('G1', 'chapterSlam', 2.1, 4.05, {'tag': '10:14 · CH 02 / 03', 'title': 'THE PICKUP', 'y': 350, 'maxW': 700, 'maxS': 215})], 3.0),
 ('p1-06', 'x1', '12:17:33', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                              ('G1', 'chapterSlam', 2.1, 4.05, {'tag': '12:10 · CH 03 / 03', 'title': 'HIT THE ROAD', 'y': 350, 'maxW': 700, 'maxS': 215})], 3.0),
 ('p1-07', 'x7', '13:28:24', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                              ('STRIP', 'driveStrip', 1.0, 9, {'start': '00:00:00', 'place': 'INTO THE MOUNTAINS', 'heading': 160, 'range': [0, 9]})], 4.2),
 ('p1-08', 'p1h', '15:42:03', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                               ('STRIP', 'driveStrip', 1.0, 9, {'start': '00:00:00', 'place': 'OPEN ROAD', 'heading': 150, 'range': [0, 9]})], 6.5),
 ('p1-09', 'p1i', '16:48:48', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 1', 'enter': 'slide', 'progress': [0, 170]}),
                               ('TEASE', 'v2place', 2.0, 7, {'x': 54, 'y': 300, 'kicker': 'TO BE CONTINUED', 'name': 'PART 2: THE NIGHT'})], 3.2),
 ('p2-01', 'p2e', '06:26:39', [('HOOK', 'v2hook', 0, 2, {'eyebrow': 'SUPERCAR EXPERIENCE · ROAD TRIP', 'line1': 'ONE-WAY TICKET', 'line2': 'PART 2 · SEP 26–27 2026', 'x': 54, 'y': 330, 'w': 853, 'exit': 1.42})], 0.3),
 ('p2-02', 'p2b', '19:53:12', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('G1', 'chapterSlam', 2.1, 4.05, {'tag': '19:23 · CH 01 / 03', 'title': 'NIGHT SHIFT', 'y': 350, 'maxW': 700, 'maxS': 215})], 3.0),
 ('p2-03', 'p2c', '19:55:35', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('PLACE', 'v2place', 2.0, 7, {'x': 54, 'y': 300, 'kicker': 'PIT STOP', 'name': 'IN-N-OUT'})], 3.2),
 ('p2-04', 'x3', '01:29:45', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                              ('D1', 'clockStamp', 1.0, 6, {'x': 54, 'y': 300, 'start': '00:00:00', 'place': 'STILL DRIVING', 'date': 'SEP 27 2026', 'built': False})], 3.0),
 ('p2-05', 'p2f', '07:11:32', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('G1', 'chapterSlam', 2.1, 4.05, {'tag': '06:24 · CH 02 / 03', 'title': 'FIRST LIGHT', 'y': 350, 'maxW': 700, 'maxS': 215})], 3.0),
 ('p2-06', 'p2g', '07:26:04', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('LOCK', 'v2lock', 1.4, 5.5, {'track': 'car', 'kicker': 'LOCKED ON', 'name': 'MCLAREN', 'acquire': 1.45, 'exit': 5.0, 'side': 'above'})], 3.0),
 ('p2-07', 'p2h', '07:35:54', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('G1', 'chapterSlam', 2.1, 4.05, {'tag': '07:32 · CH 03 / 03', 'title': 'HOME STRETCH', 'y': 350, 'maxW': 700, 'maxS': 215})], 3.0),
 ('p2-08', 'p2i', '09:04:35', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('STRIP', 'driveStrip', 1.0, 9, {'start': '00:00:00', 'place': 'LAS VEGAS', 'heading': 175, 'range': [0, 9],
                                 'route': {'waypoints': ['LAS VEGAS', 'SUPERCAR EXPERIENCE'], 'steps': [{'t': 0, 'k': 0}]}})], 5.5),
 ('p2-09', 'p2j', '09:10:57', [('A2', 'bannerTab', 0, 9, {'name': 'SUPERCAR EXPERIENCE', 'label': 'ONE-WAY TICKET · PART 2', 'enter': 'slide', 'progress': [0, 170]}),
                               ('ARRIVE', 'v2place', 2.0, 7, {'x': 54, 'y': 300, 'kicker': '09:10 · ARRIVED', 'name': 'SUPERCAR EXPERIENCE'})], 3.2),
 ('p2-10', 'p2k', '09:10:12', [('END', 'v2end', 0, 9, {'tagline': 'A RIDE OF A LIFETIME.', 'cta': 'TEXT OR DM TO BOOK', 'phone': '(725) 425-3583', 'url': 'SUPERCAREXP.VIP',
                               'handle': '@SUPERCAR_EXPERIENCE_', 'locations': 'LAS VEGAS · SCOTTSDALE · BOISE', 'fine': 'RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE', 'credit': 'FILMED BY @NQ.YOUNG'})], 4.0),
]
# the approved end card's own params, so the copy is exactly the rally's
rally = json.load(open(V2 / 'config.json'))
endp = next(c['p'] for c in rally['layer']['comps'] if c['code'] == 'END')
comps, slots = [], []
for k, (sid, bg, clk, cs, at) in enumerate(S):
    T = k * 10.0
    for code, typ, a, b, p in cs:
        p = dict(p)
        for key in ('exit', 'acquire', 'progress', 'range'):
            if key in p and typ != 'v2hook':
                p[key] = [T + v for v in p[key]] if isinstance(p[key], list) else T + p[key]
        if typ == 'v2hook': p['exit'] = T + p['exit']
        if typ == 'v2end': p = dict(endp)
        if typ == 'driveStrip' and p.get('route'):
            p['route'] = {'waypoints': p['route']['waypoints'], 'steps': [{'t': T + s['t'], 'k': s['k']} for s in p['route']['steps']]}
        comps.append({'code': f'{code}-{k}', 'type': typ, 't0': T + a, 't1': T + b, 'p': p})
    slots.append({'id': sid, 'bg': bg, 'T': T, 'at': T + at, 'clock': hms(clk)})
boxes = {'face': {'x': 430, 'y': 470, 'w': 290, 'h': 340, 'conf': 1}, 'car': {'x': 90, 'y': 720, 'w': 540, 'h': 620, 'conf': 1}}
v2 = (V2 / 'lib/v2kit.js').read_text().replace('#FBD101', theme['accent']).replace('#fbd101', theme['accent']).replace('251,209,1', theme['glow']).replace('251, 209, 1', theme['glow'])
strip = (HUD / 'drive_strip.js').read_text()
head = (V2 / 'story.html').read_text().split('<script src=".work/scene.js"></script>')[0]
head = head.replace('</style>', theme['css'] + '\n</style>', 1)
page = head + f'''<script>window.THEME = {json.dumps({'accent': theme['accent'], 'glow': theme['glow']})};
window.SCENE = {json.dumps({'dur': len(S) * 10, 'comps': comps})}; window.SLOTS = {json.dumps(slots)}; window.BOXES = {json.dumps(boxes)}; window.LAT = [];</script>
<script src="lib/kinetic.js"></script>
<script src="lib/sekit.js"></script>
<script>// v2kit (rally v2) reads a few helpers the vlog kit keeps private: the same one-liners, and the theme accent as GOLD
Object.assign(SEK.helpers, {{ px: v => v.toFixed(2) + 'px', f2: v => v.toFixed(2), GOLD: window.THEME.accent, SAFE: SEK.SAFE,
  routeGeom: () => {{ throw new Error('route card not in this mockup'); }} }});</script>
<script>{v2}</script>
<script>{strip}</script>
</head><body>
<div id="stage" class="a" style="width:1080px;height:1920px"></div>
<script>
const SC = window.SCENE, stage = document.getElementById('stage');
const slotAt = t => SLOTS[Math.max(0, Math.min(SLOTS.length - 1, Math.floor(t / 10)))];
// the camera clock (seconds of the day) of the still's frame, running on from it
const CTX = {{ dur: SC.dur, box(name) {{ return BOXES[name] || null; }}, clip(t) {{ const s = slotAt(t); return s.clock + (t - s.at); }}, data() {{ return null; }} }};
let comps = [];
(async () => {{
  await document.fonts.load('100px Bebas'); await document.fonts.load('40px Michroma'); await KT.ready();
  SEK.init(stage, CTX); SEK.v2init(CTX);
  const Z = {{ chapterSlam: 10, bannerTab: 50, v2hook: 70, v2end: 90 }};
  comps = SC.comps.map(c => {{
    const f = SEK[c.type]; if (!f) throw new Error('unknown component type ' + c.type);
    const n0 = stage.childElementCount, o = f(c);
    for (let i = n0; i < stage.childElementCount; i++) {{ const e = stage.children[i]; e.style.zIndex = Z[c.type] ?? 20; }}
    o.t0 = c.t0; o.t1 = c.t1; return o;
  }});
  await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => {{ i.onload = r; i.onerror = r; }})));
  window.renderAt(0); window.__ktReady = true;
}})().catch(e => {{ console.error(e); throw e; }});
window.renderAt = t => {{ window.FX = {{}}; for (const c of comps) c.render(t); }};
</script></body></html>'''
out = KIT / '.hud_mock-mclaren-run.html'
out.write_text(page)
json.dump(slots, open(M / 'slots.json', 'w'))
print(out, len(comps), 'comps')
