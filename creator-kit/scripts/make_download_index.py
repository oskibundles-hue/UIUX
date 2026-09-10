#!/usr/bin/env python3
"""Anti Stock download index generator.

DO NOT re-publish this to artifact fb14668e-2db5-4cf4-9e6c-ae9df97b0d82 without merging first.
Another session maintains that page and has added an Archive section, QC caption flags and the
grade spec that this generator does not produce. Read the live page, merge, then publish.

The all-workstreams index is a different page and is not generated from here:
https://claude.ai/code/artifact/c2501ca3-40ac-4b1d-833e-1b7c98f9abad
"""
import re, html
D=open('/home/user/UIUX/creator-kit/DELIVERY.md').read()
OUT='/tmp/claude-0/-home-user-UIUX/9f8eba81-4152-5a0b-b716-361fabe7a36c/scratchpad/downloads.html'
CF='https://d2ol7oe51mr4n9.cloudfront.net/user_3EmIbqAsNEPTa3GqLOpFdlVHf2Z/'
rows=[]; sec=None
for line in D.split('\n'):
    if line.startswith('## '): sec=line[3:].split(' ·')[0].strip(); continue
    m=re.match(r'\|\s*(?:\d+\s*\|\s*)?([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*(.*)\|',line)
    if m and 'http' in m.group(3):
        for lab,u in re.findall(r'\[([^\]]+)\]\((https://[^)]+)\)',m.group(3)):
            name=m.group(1).strip(); 
            if lab not in ('download',): name=f'{name} ({lab})'
            name=name.replace('SFX pack · 17 synthesised effects (clicks, thocks, ticks, impacts, whooshes, risers, pop, ding, shutter) + audition (zip)','SFX pack · 17 sounds + manifest (zip)').replace('SFX pack · 17 synthesised effects (clicks, thocks, ticks, impacts, whooshes, risers, pop, ding, shutter) + audition (audition mp3)','SFX audition · all 17 in one mp3')
            name=name.replace('Deliverables index PDF (everything in this file, one page set for Dropbox; evening build includes the Fast Cut series) (morning build)','Deliverables index PDF · morning build').replace('Deliverables index PDF (everything in this file, one page set for Dropbox; evening build includes the Fast Cut series)','Deliverables index PDF · evening build, includes Fast Cut')
            rows.append((sec,name,m.group(2).strip(),u))
def pick(pred, seen): 
    out=[]
    for r in rows:
        if pred(r) and r[3] not in seen: out.append(r); seen.add(r[3])
    return out
seen=set()
G=[]
G.append(('Fast Cut reels', 'The current series. Post in this order. Folder: 04 Exports / 2026-09-08 Fast Cut', pick(lambda r:r[0].startswith('Fast Cut'),seen)))
kit=[('Creator kit','Kit zip: 9 LUTs, Supercar Experience overlay pack, handle overlays, SFX pack, Remotion motion-graphics templates, scripts, voice profile, docs · 11 MB',CF+'f7b61649-d326-4400-a9f4-64caaeb034e7.zip')]
kit+= [(r[1],r[2],r[3]) for r in pick(lambda r:'SFX' in r[1],seen)]
G.append(('Creator kit', 'Everything that is not a video. Folder: 05 Creator Kit', [('Creator kit',)+k[1:] if False else ('',)+k for k in kit]))
G.append(('Intros', 'Channel intro tests, 5 s each. Folder: 04 Exports / 2026-09-08 Intros', pick(lambda r:'INTRO' in r[1],seen)))
G.append(('Index PDF', 'The full deliverables index as one PDF. Folder: 04 Exports', pick(lambda r:'index PDF' in r[1],seen)))
G.append(('Motion graphics tests', 'Earlier versions of the SF90 reel and the R9 cuts. Folder: 04 Exports / 2026-09-08 Motion tests', pick(lambda r:re.match(r'(M[123]|R9|V1|Cover)',r[1]) is not None,seen)))
G.append(('Vlog Cut series', 'VR1–VR8 in the natural grade with pop captions, about 1:30 each. Folder: 04 Exports / 2026-09-08 Vlog Cut', pick(lambda r:r[0].startswith('Vlog Cut'),seen)))
G.append(('Original reel series', 'R1–R8 in the reference grade with classic captions, plus the trial cuts. Folder: 04 Exports / 2026-09-07 Reel series', pick(lambda r:r[0].startswith('Reel series') or r[0]=='Tests',seen)))
G.append(('Singles', '18 clips cut and graded, no captions, for your own edits. Folder: 04 Exports / 2026-09-07 Singles', pick(lambda r:r[0].startswith('Singles'),seen)))
def row(r):
    sec,name,meta,u = (r if len(r)==4 else (None,)+tuple(r))
    fname=u.rsplit('/',1)[1]
    return f'<li class="row"><div class="t"><span class="n">{html.escape(name)}</span><span class="m">{html.escape(meta)}</span></div><a class="dl" href="{u}" target="_blank" rel="noopener">Download</a></li>'
total=sum(len(g[2]) for g in G)
nav=''.join(f'<a href="#g{i}">{html.escape(g[0])} <b>{len(g[2])}</b></a>' for i,g in enumerate(G))
body=''.join(f'<section id="g{i}"><h2>{html.escape(g[0])}</h2><p class="d">{html.escape(g[1])}</p><ol class="rows">{"".join(row(r) for r in g[2])}</ol></section>' for i,g in enumerate(G))
page=f'''<title>Anti Stock Downloads</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,400..900&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#F2F0EB;--panel:#FBFAF7;--ink:#151618;--mute:#63655F;--line:#D8D5CC;--red:#DE1A22;--gold:#FBD101;--goldink:#141414}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#121316;--panel:#1A1B1F;--ink:#F3F2ED;--mute:#A4A59E;--line:#2C2D33;--red:#E8272F;--gold:#FBD101;--goldink:#141414}}}}
:root[data-theme="dark"]{{--bg:#121316;--panel:#1A1B1F;--ink:#F3F2ED;--mute:#A4A59E;--line:#2C2D33;--red:#E8272F;--gold:#FBD101;--goldink:#141414}}
*{{box-sizing:border-box}} body{{background:var(--bg);color:var(--ink);font-family:Archivo,"Helvetica Neue",Arial,sans-serif;font-size:15px;line-height:1.45;margin:0}}
a{{color:inherit}} a:focus-visible{{outline:3px solid var(--gold);outline-offset:2px}}
.wrap{{max-width:900px;margin:0 auto;padding:28px 18px 80px}}
header{{padding-bottom:16px;position:relative}} header:after{{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,var(--red) 0 34%,var(--line) 34%)}}
.eyebrow{{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);font-weight:600}}
h1{{font-weight:900;font-stretch:88%;font-size:clamp(40px,9vw,72px);line-height:.92;margin:6px 0 0;text-transform:uppercase;letter-spacing:-.01em}}
.lede{{color:var(--mute);margin:12px 0 0;max-width:60ch}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 0}} nav a{{text-decoration:none;font-size:13px;font-weight:600;padding:7px 11px;border:1px solid var(--line);background:var(--panel)}} nav a b{{font-family:"IBM Plex Mono",monospace;font-weight:500;color:var(--mute);margin-left:4px}}
h2{{font-weight:900;font-stretch:88%;text-transform:uppercase;font-size:21px;margin:40px 0 4px}} .d{{margin:0 0 10px;color:var(--mute);font-size:13px}}
.rows{{list-style:none;margin:0;padding:0;border:1px solid var(--line);background:var(--panel)}}
.row{{display:flex;align-items:center;gap:14px;padding:12px 14px;border-top:1px solid var(--line)}} .row:first-child{{border-top:0}}
.t{{flex:1;min-width:0;display:flex;flex-direction:column}} .n{{font-weight:700}} .m{{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--mute);margin-top:2px;overflow-wrap:anywhere}}
.dl{{flex:none;text-decoration:none;font-weight:700;font-size:14px;padding:11px 16px;background:var(--ink);color:var(--bg);border:2px solid var(--ink);min-width:112px;text-align:center}}
.dl:hover{{background:var(--red);border-color:var(--red);color:#fff}} .dl:active{{transform:translateY(1px)}}
.note{{color:var(--mute);font-size:13px;max-width:66ch;margin:40px 0 0}}
.super{{border:2px solid var(--red);background:var(--panel);padding:14px 16px;margin:18px 0 0;font-size:14px;max-width:70ch}} .super b{{color:var(--ink)}} .super a{{color:var(--red);font-weight:700}}
@media (max-width:560px){{.row{{flex-direction:column;align-items:stretch;gap:8px}} .dl{{width:100%;padding:13px 16px}}}}
@media (prefers-reduced-motion:no-preference){{.dl{{transition:background .15s,color .15s}}}}
</style>
<div class="wrap">
<header><span class="eyebrow">Anti Stock Media · Formula Dynamics build · updated 2026-09-08</span>
<h1>Downloads</h1>
<p class="lede">The Anti Stock shop-build series, one tap each. Files save with their real names. The folder line under each heading is where it lives in Dropbox.</p>
<div class="super"><b>This page covers Anti Stock only.</b> Everything delivered across all three workstreams — the Formula Dynamics car ads, service ads and service reels, the brand kits, and these reels — is indexed on one page: <a href="https://claude.ai/code/artifact/c2501ca3-40ac-4b1d-833e-1b7c98f9abad">Download Everything</a>. Supercar Experience has <a href="https://claude.ai/code/artifact/9bca62e7-2acb-437d-af68-da260daf2fdb">its own index</a>.</div>
<nav>{nav}</nav></header>
{body}
<p class="note">{total} files. The FD overlay pack was yours to begin with and is already in Dropbox. Upload page for the Fast Cut folder, if you want to drop files from the phone: <a href="https://www.dropbox.com/request/cw52bjv1jh0edz6s4mhf">dropbox.com/request/cw52bjv1jh0edz6s4mhf</a>.</p>
</div>
'''
open(OUT,'w').write(page); print('wrote',OUT,total,'files', [ (g[0],len(g[2])) for g in G])
