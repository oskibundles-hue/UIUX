#!/usr/bin/env python3
"""Emit DELIVERY.md rows (--delivery) or the Dropbox index note (--note) for MR1–MR8 from the batch outputs."""
import json, re, sys
F='/home/user/footage'; CF='https://d2ol7oe51mr4n9.cloudfront.net/user_3EmIbqAsNEPTa3GqLOpFdlVHf2Z/'
SLUG={1:'the shop before',2:'led trim goes in',3:'drilling and the frame',4:'first car rolls in',5:'raising the ceiling',6:'panels up car on lift',7:'aston martin brake job',8:'sf90 pulls up'}
ev=open(F+'/motion2/events.log').read()
def mmss(s): s=int(round(s)); return f'{s//60}:{s%60:02d}'
rows=[]
for r in range(1,9):
    n=f'MR{r}'
    if r==8:
        mid='aed877d4-f282-4c2d-a47d-7246894bf42e'; size=451670381; dur=58.0; ck=json.load(open(f'{F}/motion/M3reel.check.json'))
    else:
        mid=open(f'{F}/motion2/links/media_{n}.id').read().strip(); ck=json.load(open(f'{F}/motion2/{n}.check.json'))
        size=int(re.findall(rf'^\S+ {n} (?:re-)?upload http 200 local (\d+)',ev,re.M)[-1]); dur=json.load(open(f'{F}/motion2/{n}.overlay.json'))['durationSeconds']
    rows.append((n,SLUG[r],mmss(dur),size,round(ck['score']),CF+mid+'.mp4'))
if '--delivery' in sys.argv:
    for n,s,d,size,sc,u in rows: print(f'| {n} · {s}{" (the approved SF90 reel, unchanged)" if n=="MR8" else ""} | {d} · {size/1048576:.0f} MB · score {sc} | [download]({u}) |')
if '--note' in sys.argv:
    print('# Fast Cut · the series in the approved recipe · 2026-09-08\n')
    print('All eight parts rebuilt the way the approved SF90 reel was made: under a minute, hook line and title, shots of 4.5 s or less, your voice only in the captions, chapter bar and lower thirds from the take, FD red and gold, card outro, no CTA. Post in this order. Links save with the real filename. 4K 2160x3840, 29.97 fps, vlog grade, -14 LUFS.\n')
    print('| file | runtime · size · local score | link |\n|---|---|---|')
    for n,s,d,size,sc,u in rows: print(f'| {n} {s} (fast cut, motion graphics).mp4 | {d} · {size/1048576:.0f} MB · {sc} | {u} |')
    print('\nCompare: the vlog cut of each part is in "2026-09-08 VLOG CUT INDEX.md"; the earlier graphics tests are in "2026-09-08 MOTION GRAPHICS INDEX.md".')
