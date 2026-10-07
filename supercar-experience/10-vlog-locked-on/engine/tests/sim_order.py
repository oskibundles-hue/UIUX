#!/usr/bin/env python3
"""Stream-order simulation behind ingest.stream_order (README "Why this order").

usage: sim_order.py SURVEY_DIR   (a surveyed day: idx/*.json with size, tr/*.json)
Model: aggregate bandwidth B split over live streams (per-stream cap), 4 cores minus 1 while streaming;
per clip: thumbnails duration/2 x 0.11 core-s (max 2 at once), whisper speech_s x 0.37 core-s (1 core each)."""
import sys
import json, glob, os
clips=[]
os.chdir(sys.argv[1])
for f in glob.glob('idx/*.json'):
    j=json.load(open(f)); cid=os.path.basename(f)[:-5]
    if not os.path.exists(f'tr/{cid}.json'): continue
    t=json.load(open(f'tr/{cid}.json')); sp=sum(s['end']-s['start'] for s in t['segments'])
    clips.append(dict(id=cid,size=j['size'],dur=t['duration'],speech=sp))
def sim(order_fn, B=300e6, cap=90e6, slots=5, cores=4, kf_cost=0.11, asr_rate=0.37, asr_fixed=1.0, dt=0.5):
    todo=order_fn(list(clips)); act=[]; t=0; cpu_jobs=[]  # (kind, remaining)
    running=[]; done_t={}
    while todo or act or cpu_jobs or running:
        # start streams
        while len(act)<slots and todo:
            c=todo.pop(0); act.append([c, c['size']])
        # bandwidth share
        if act:
            share=min(cap, B/len(act))
            for a in act: a[1]-=share*dt
            for a in [a for a in act if a[1]<=0]:
                act.remove(a); c=a[0]
                cpu_jobs.append(['kf', c['dur']/2*kf_cost, c['id']])
                cpu_jobs.append(['asr', c['speech']*asr_rate+asr_fixed, c['id']])
        # CPU: cores minus stream load
        free=cores-(1 if act else 0)
        # prioritize: asr longest first, then kf (kf max 2 at a time)
        cpu_jobs.sort(key=lambda j:(-j[1]))
        run=[]; kfn=0
        for j in cpu_jobs:
            if len(run)>=free: break
            if j[0]=='kf':
                if kfn>=2: continue
                kfn+=1
            run.append(j)
        for j in run: j[1]-=dt
        for j in [j for j in cpu_jobs if j[1]<=0]:
            cpu_jobs.remove(j); done_t[j[2]]=max(done_t.get(j[2],0),t)
        t+=dt
    return t
lpt=lambda cs: sorted(cs,key=lambda c:-c['size'])
spt=lambda cs: sorted(cs,key=lambda c:c['size'])
def mix(k):
    def f(cs):
        s=sorted(cs,key=lambda c:-c['size']); big=s[:k]; rest=s[k:][::-1]
        return big+rest
    return f
def alt(cs):
    s=sorted(cs,key=lambda c:-c['size']); out=[]
    while s:
        out.append(s.pop(0))
        if s: out.append(s.pop())
    return out
for B in (280e6, 350e6, 420e6):
  for name,fn in [('LPT',lpt),('SPT',spt),('big3+smallfirst',mix(3)),('big5+smallfirst',mix(5)),('alternate',alt)]:
    for slots in (5,6):
        print(f'B={B/1e6:.0f} slots={slots} {name:16s} {sim(fn,B=B,slots=slots)/60:.1f} min')
tot_cpu=sum(c['dur']/2*0.11+c['speech']*0.37+1 for c in clips)
print('cpu work (kf+asr) core-min', tot_cpu/60, 'streaming GB', sum(c['size'] for c in clips)/1e9)
print('--- per-stream cap sensitivity')
def mix2(k):
    def f(cs):
        s=sorted(cs,key=lambda c:-c['size']); big=s[:k]; rest=sorted(s[k:],key=lambda c:c['size'])
        # interleave: big ones first k slots, then smallest-first
        return big+rest
    return f
for cap in (50e6,70e6,97e6):
  for B in (280e6,420e6):
    res=[]
    for name,fn in [('LPT',lpt),('SPT',spt),('big2+SPT',mix(2)),('big3+SPT',mix(3)),('big4+SPT',mix(4))]:
        res.append(f'{name} {sim(fn,B=B,cap=cap,slots=5)/60:.1f}')
    print(f'cap={cap/1e6:.0f} B={B/1e6:.0f}: '+' | '.join(res))
