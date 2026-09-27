#!/usr/bin/env python3
"""vlog.py - the ingest and planning half of the SE vlog pipeline (everything before the render).

  links      DAY --clips FILE     register the day's clips, write DAY/links/request.json (2 links/clip, <=25/call)
  ingest     DAY                  survey every clip from its links: moov, audio, thumbnails, transcripts
  transcribe DAY                  (re)transcribe audio that has no transcript yet (ingest already does this)
  status     DAY                  one line per clip
  index      DAY [--out DIR]      day.md, speaker labels, moments.json/.md, flags.json, quality notes
  plan       DAY --edl edl.json   byte spans for every shot (+handles) -> fetchplan.json + links request
  fetch      DAY --out MEZZ       range-fetch the spans (links in DAY/fetch/links/) and cut mezzanines, all cores busy

See README.md for the runbook.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.common import Day, fmt_clock, read_json  # noqa: E402


def load_clip_list(path):
    """Paths from a text file (one per line, optional TAB size), a JSON list, or Dropbox list_folder JSON."""
    txt = open(path).read()
    out = []
    s = txt.strip()
    if s.startswith('{') or s.startswith('['):
        obj = json.loads(s)
        stack = [obj]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                p = o.get('path_display') or o.get('path') or o.get('path_lower')
                if p and (o.get('.tag', 'file') == 'file') and ('size' in o or '.' in os.path.basename(p)):
                    out.append({'path': p, 'name': o.get('name') or os.path.basename(p), 'size': o.get('size')})
                else:
                    stack.extend(o.values())
            elif isinstance(o, list):
                stack.extend(reversed(o))
            elif isinstance(o, str) and o.startswith('/'):
                out.append({'path': o, 'name': os.path.basename(o), 'size': None})
    else:
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            size = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else None
            out.append({'path': parts[0].strip(), 'name': os.path.basename(parts[0].strip()), 'size': size})
    vids = [e for e in out if os.path.splitext(e['path'])[1].lower() in ('.mp4', '.mov', '.m4v')]
    return vids


def cmd_links(a):
    from lib.ingest import plan_links
    entries = load_clip_list(a.clips)
    reg, obj = plan_links(a.day, entries, clips_per_call=a.clips_per_call, big_first=a.big_first)
    n = sum(len(b['entries']) for b in obj['batches'])
    print(f'{len(reg)} clips registered in {a.day}/clips.json; {n} links in {len(obj["batches"])} call(s) '
          f'-> {a.day}/links/request.json')
    for b in obj['batches']:
        print(f'  call {b["batch"]}: {len(b["entries"])} entries')


def cmd_ingest(a):
    from lib.ingest import Ingest
    ing = Ingest(a.day, streams=a.streams, kf_step=a.kf_step, kf_workers=a.kf_workers, asr_max=a.asr_workers,
                 asr=not a.no_asr, tail_mb=a.tail_mb, wait_links=a.wait_links, clips_per_call=a.clips_per_call,
                 reserve_gb=a.reserve_gb, big_first=a.big_first)
    sys.exit(ing.run())


def cmd_transcribe(a):
    import time
    from lib.asr import AsrPool
    from lib.common import log
    day = Day(a.day)
    pool = AsrPool(day.p('tr'), max_workers=a.workers, threads=1)
    pool.target = a.workers
    n = 0
    for f in sorted(os.listdir(day.p('aud'))):
        if not f.endswith('.m4a') or f.startswith('.'):
            continue
        cid = f[:-4]
        if os.path.exists(day.p('tr', cid + '.json')) and not a.force:
            continue
        meta = read_json(day.p('idx', cid + '.json'), {})
        pool.add(cid, day.p('aud', f), priority=meta.get('duration') or os.path.getsize(day.p('aud', f)))
        n += 1
    log(f'transcribe: {n} file(s), {a.workers} worker(s)')
    t0 = time.time()
    while not pool.idle() or pool.queue:
        pool.pump(log)
        time.sleep(0.5)
    pool.stop()
    log(f'transcribe done in {time.time() - t0:.0f}s; errors: {pool.errors or "none"}')


def cmd_status(a):
    day = Day(a.day)
    clips = day.clips
    for cid in sorted(clips, key=lambda c: (clips[c].get('clock') or 0, c)):
        c = clips[cid]
        st = day.state(cid)
        tr = os.path.exists(day.p('tr', cid + '.json'))
        print(f"{cid:8s} {fmt_clock(c['clock']) if c.get('clock') is not None else '--:--:--'} "
              f"{(c.get('size') or 0) / 1e9:6.2f} GB  {st.get('status', 'new'):9s} {'tr' if tr else '  '} "
              f"{(st.get('error') or '')[:80]}")


def cmd_index(a):
    from lib.dayindex import build_index
    build_index(a.day, out=a.out or a.day, host_ref=a.host_ref, voiceprint=a.voiceprint, sheets_on=not a.no_sheets)


def cmd_plan(a):
    from lib.fetch import make_plan
    make_plan(a.day, a.edl, out=a.out, handles=a.handles, merge_gap=a.merge_gap, audio_only_vo=a.audio_only_vo)


def cmd_fetch(a):
    from lib.fetch import run_fetch
    sys.exit(run_fetch(a.day, a.plan, a.links, out=a.out, workers=a.workers, crf=a.crf, preset=a.preset,
                       streams=a.streams))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('links', help='register clips and write the Dropbox link request')
    p.add_argument('day')
    p.add_argument('--clips', required=True, help='clip list: text (path[TAB size] per line) or list_folder JSON')
    p.add_argument('--clips-per-call', type=int, default=12)
    p.add_argument('--big-first', type=int, default=2, help='largest clips started first, then smallest first')
    p.set_defaults(fn=cmd_links)

    p = sub.add_parser('ingest', help='survey all clips from their single-use links')
    p.add_argument('day')
    p.add_argument('--streams', type=int, default=5, help='clips downloading at once (default 5)')
    p.add_argument('--kf-step', type=float, default=2.0, help='seconds between kept keyframes (default 2)')
    p.add_argument('--kf-workers', type=int, default=2)
    p.add_argument('--asr-workers', type=int, default=4, help='max whisper processes (1 thread each)')
    p.add_argument('--no-asr', action='store_true')
    p.add_argument('--tail-mb', type=int, default=16)
    p.add_argument('--wait-links', type=int, default=900, help='stop after this many idle seconds without links')
    p.add_argument('--clips-per-call', type=int, default=12)
    p.add_argument('--reserve-gb', type=float, default=2.0, help='free disk to keep')
    p.add_argument('--big-first', type=int, default=2, help='largest clips started first, then smallest first')
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser('transcribe', help='transcribe audio without a transcript')
    p.add_argument('day')
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--force', action='store_true')
    p.set_defaults(fn=cmd_transcribe)

    p = sub.add_parser('status')
    p.add_argument('day')
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser('index', help='day.md, speakers, moments, flags, quality notes')
    p.add_argument('day')
    p.add_argument('--out')
    p.add_argument('--host-ref', action='append', default=[],
                   help='clip:t0-t1 of clearly-host narration (repeatable); default: the saved host voiceprint')
    p.add_argument('--voiceprint', help='host voiceprint .npy (default engine/voiceprints/host.npy)')
    p.add_argument('--no-sheets', action='store_true')
    p.set_defaults(fn=cmd_index)

    p = sub.add_parser('plan', help='edl.json -> fetchplan.json + links request')
    p.add_argument('day')
    p.add_argument('--edl', required=True)
    p.add_argument('--out', help='work dir for the fetch (default DAY/fetch)')
    p.add_argument('--handles', type=float, default=0.8)
    p.add_argument('--merge-gap', type=float, default=2.0)
    p.add_argument('--audio-only-vo', action='store_true',
                   help='VO / nat ranges not on screen -> <src>_<t0>-<t1>.wav, no video decode (~20%% faster cuts)')
    p.set_defaults(fn=cmd_plan)

    p = sub.add_parser('fetch', help='range-fetch planned spans and cut mezzanines')
    p.add_argument('day')
    p.add_argument('--plan', help='fetchplan.json (default DAY/fetch/fetchplan.json)')
    p.add_argument('--links', help='a Dropbox tool answer for fetch/request.json (default: every file in DAY/fetch/links/)')
    p.add_argument('--out', required=True, help='mezzanine directory')
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--streams', type=int, default=6)
    p.add_argument('--crf', type=float, default=13)
    p.add_argument('--preset', default='superfast', help='x264 preset (superfast: 4.7 fps/core, beats the Sep 15 mezz)')
    p.set_defaults(fn=cmd_fetch)

    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
