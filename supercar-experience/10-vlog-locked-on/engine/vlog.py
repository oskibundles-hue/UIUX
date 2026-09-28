#!/usr/bin/env python3
"""vlog.py - the ingest and planning half of the SE vlog pipeline (everything before the render).

  links      DAY --clips FILE     register the day's clips, write DAY/links/request.json (2 links/clip, <=25/call)
             DAY --local FOLDER   ... or register the videos in a folder on this machine (local mode)
  ingest     DAY [--local]        survey every clip from its links: moov, audio, thumbnails, transcripts
                                  (--local: serve the files from this machine instead of Dropbox links)
  transcribe DAY                  (re)transcribe audio that has no transcript yet (ingest already does this)
  status     DAY                  one line per clip
  index      DAY [--out DIR]      day.md, speaker labels, moments.json/.md, flags.json, quality notes
  tails      DAY --clips LIST --edl EDL   (no ingest on this machine) register the clips, request one link per clip
             DAY --run            ... fetch each clip's moov from its tail (+ head for phone clips) -> idx/ for plan / fetch
  plan       DAY --edl edl.json   byte spans for every shot (+handles) -> fetchplan.json + links request
                                  (--waves-gb X: spans grouped in waves that fit the disk; later waves via NEED.json)
  fetch      DAY --out MEZZ       range-fetch the spans (links in DAY/fetch/links/) and cut mezzanines, all cores busy
                                  (--local: from this machine; VLOG_HWACCEL=videotoolbox decodes on the Mac's media engine)

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
    entries = load_clip_list(a.clips) if a.clips else []
    if a.local:
        from lib.localsrc import scan_folder
        for folder in a.local:
            entries += scan_folder(folder, recursive=a.recursive)
    if not entries:
        sys.exit('no clips: give --clips FILE and/or --local FOLDER')
    reg, obj = plan_links(a.day, entries, clips_per_call=a.clips_per_call, big_first=a.big_first)
    n = sum(len(b['entries']) for b in obj['batches'])
    print(f'{len(reg)} clips registered in {a.day}/clips.json; {n} links in {len(obj["batches"])} call(s) '
          f'-> {a.day}/links/request.json')
    for b in obj['batches']:
        print(f'  call {b["batch"]}: {len(b["entries"])} entries')


def _local(a, links_dir):
    """Start local mode (or None): serves this machine's files as links written into links_dir."""
    if not (a.local or a.local_root):
        return None
    from lib.localsrc import LocalLinks, dropbox_roots
    roots = a.local_root or dropbox_roots()
    loc = LocalLinks(links_dir, roots)
    print(f'local mode: serving files from {roots or "their own absolute paths"}', flush=True)
    return loc


def cmd_ingest(a):
    from lib.ingest import Ingest
    day = Day(a.day)
    only = None
    if a.edl:
        e = read_json(a.edl)
        only = {x['src'] for k in ('shots', 'dialog', 'audio_extra') for x in e.get(k, [])} & set(day.clips)
        print(f'--edl: surveying the {len(only)} clip(s) the cut uses', flush=True)
    loc = _local(a, day.p('links'))
    if loc:
        from lib.localsrc import disk_guard
        todo = [c['path'] for cid, c in day.clips.items()
                if not day.state(cid).get('surveyed') and (only is None or cid in only)]
        ok, msg = disk_guard([loc.resolve(p) for p in todo], a.reserve_gb + 18)
        if msg:
            print('local mode: ' + msg, flush=True)
        if not ok:
            loc.stop()
            sys.exit(2)
        n, missing = loc.write([p for p in todo for _ in range(2)])
        print(f'local mode: {n} links for {len(todo) - len(missing)} clip(s)', flush=True)
        if missing:
            print(f'local mode: not found on this machine ({len(missing)}): ' + '; '.join(missing[:5]) +
                  (' ...' if len(missing) > 5 else '') + '  (--local-root <your Dropbox folder>?)', flush=True)
        loc.watch()
    ing = Ingest(a.day, streams=a.streams, kf_step=a.kf_step, kf_workers=a.kf_workers, asr_max=a.asr_workers,
                 asr=not a.no_asr, tail_mb=a.tail_mb, wait_links=a.wait_links if not loc else min(a.wait_links, 60),
                 clips_per_call=a.clips_per_call, reserve_gb=a.reserve_gb, big_first=a.big_first, only=only)
    try:
        rc = ing.run()
    finally:
        if loc:
            loc.stop()
    sys.exit(rc)


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


def cmd_tails(a):
    from lib import tails
    if a.run:
        sys.exit(tails.run(a.day, tail_mb=a.tail_mb, head_mb=a.head_mb, wait=a.wait_links))
    if not a.clips or not a.edl:
        sys.exit('tails: give --clips LIST (repeatable) and --edl EDL, or --run')
    tails.request(a.day, a.clips, a.edl, load_clip_list)


def cmd_plan(a):
    from lib.fetch import make_plan
    make_plan(a.day, a.edl, out=a.out, handles=a.handles, merge_gap=a.merge_gap, audio_only_vo=a.audio_only_vo, waves_gb=a.waves_gb)


def cmd_fetch(a):
    from lib.fetch import run_fetch
    wdir = os.path.dirname(os.path.abspath(a.plan)) if a.plan else Day(a.day).p('fetch')
    loc = _local(a, os.path.join(wdir, 'links'))
    if loc:
        from lib.localsrc import request_paths, disk_guard
        paths = request_paths(os.path.join(wdir, 'request.json'))
        ok, msg = disk_guard([loc.resolve(p) for p in paths])
        if msg:
            print('local mode: ' + msg, flush=True)
        if not ok:
            loc.stop()
            sys.exit(2)
        n, missing = loc.write(paths)
        print(f'local mode: {n} span link(s)' + (f'; not found on this machine: {missing}' if missing else ''), flush=True)
    try:
        rc = run_fetch(a.day, a.plan, a.links, out=a.out, workers=a.workers, crf=a.crf, preset=a.preset,
                       streams=a.streams, budget_gb=a.budget_gb, reserve_gb=a.reserve_gb, wait_links=a.wait_links)
    finally:
        if loc:
            loc.stop()
    sys.exit(rc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('links', help='register clips and write the Dropbox link request')
    p.add_argument('day')
    p.add_argument('--clips', help='clip list: text (path[TAB size] per line) or list_folder JSON')
    p.add_argument('--local', action='append', default=[], metavar='FOLDER',
                   help='register the videos in this local folder (repeatable; local mode)')
    p.add_argument('--recursive', action='store_true', help='with --local: include subfolders')
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
    p.add_argument('--edl', help='survey only the clips this edl.json uses (e.g. to rebuild a finished vlog elsewhere)')
    p.add_argument('--local', action='store_true', help='read the files on this machine (Dropbox desktop folder)')
    p.add_argument('--local-root', action='append', default=[], metavar='DIR',
                   help='folder that Dropbox paths are found under (default: the Dropbox desktop folder)')
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

    p = sub.add_parser('tails', help='moov-only survey: one link per clip (two for phone clips), for plan / fetch')
    p.add_argument('day')
    p.add_argument('--clips', action='append', default=[], help='Dropbox list_folder answer or path list (repeatable)')
    p.add_argument('--edl', help='the cut: only the clips it uses get links')
    p.add_argument('--run', action='store_true', help='fetch the tails with the links saved in DAY/links/')
    p.add_argument('--tail-mb', type=int, default=24)
    p.add_argument('--head-mb', type=int, default=8)
    p.add_argument('--wait-links', type=int, default=600)
    p.set_defaults(fn=cmd_tails)

    p = sub.add_parser('plan', help='edl.json -> fetchplan.json + links request')
    p.add_argument('day')
    p.add_argument('--edl', required=True)
    p.add_argument('--out', help='work dir for the fetch (default DAY/fetch)')
    p.add_argument('--handles', type=float, default=0.8)
    p.add_argument('--merge-gap', type=float, default=2.0)
    p.add_argument('--audio-only-vo', action='store_true',
                   help='VO / nat ranges not on screen -> <src>_<t0>-<t1>.wav, no video decode (~20%% faster cuts)')
    p.add_argument('--waves-gb', type=float, help='group the spans in waves of at most this many GB on disk')
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
    p.add_argument('--budget-gb', type=float, help='keep at most this many GB of spans on disk (waves; frees each span once cut)')
    p.add_argument('--reserve-gb', type=float, default=0.6, help='free disk always left (with --budget-gb)')
    p.add_argument('--wait-links', type=int, default=1800, help='give up after this many seconds without new links')
    p.add_argument('--local', action='store_true', help='read the files on this machine (Dropbox desktop folder)')
    p.add_argument('--local-root', action='append', default=[], metavar='DIR',
                   help='folder that Dropbox paths are found under (default: the Dropbox desktop folder)')
    p.set_defaults(fn=cmd_fetch)

    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
