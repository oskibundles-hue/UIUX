"""index: the day, laid out for the editor.

Writes to OUT (default: the day directory):
  day.md          every transcript line on the camera clock, clip by clip: speaker + confidence, flags,
                  the clip's picture note and its contact sheet (sheets/<id>.jpg)
  speakers.json   per clip: every piece (segment split at pauses) with HOST/OTHER, confidence, voice score
  moments.json/md candidate moments per category (clip, in/out, clock, speaker, text, why) + a keyframe strip
                  each (sheets/moments/<category>_<rank>.jpg); blocked candidates listed separately
  flags.json      exclusion flags (block / caution) with word-accurate spans
  quality.json    per-clip picture notes (dark, covered, sideways, upside down)
Works on this engine's day layout and on the Sep 15 scratch layout (kf/<id>_<n>.jpg, names.txt, phone_starts.json).
"""
import glob
import os
import re
import time

import numpy as np

from . import flags as F
from . import moments as M
from . import quality as Q
from . import sheets
from . import speaker as SP
from . import thumbs
from .common import DJI_RE, fmt_clock, log, name_clock, read_json, write_json


# ------------------------------------------------------------------ the day's clips
def load_clips(day):
    reg = read_json(os.path.join(day, 'clips.json'), {}) or {}
    clips = {cid: dict(rec) for cid, rec in reg.items()}
    names = os.path.join(day, 'names.txt')
    if os.path.exists(names):
        for n in open(names).read().split():
            m = DJI_RE.search(n)
            if m:
                c = name_clock(n)
                clips.setdefault(m.group(7), {}).update({'name': n, 'clock': c[1], 'date': c[0]})
    ps = read_json(os.path.join(day, 'phone_starts.json'), {}) or {}
    for cid, v in ps.items():
        clips.setdefault(cid, {}).update({'clock': v})
    for f in glob.glob(os.path.join(day, 'tr', '*.json')):
        cid = os.path.basename(f)[:-5]
        if cid.endswith('.spk'):
            continue
        clips.setdefault(cid, {})
    for cid, c in clips.items():
        idx = read_json(os.path.join(day, 'idx', cid + '.json'), {}) or {}
        if c.get('clock') is None and idx.get('clock') is not None:
            c['clock'] = idx['clock']
        c['camera'] = bool(re.fullmatch(r'\d{4}', cid)) or 'DJI' in (c.get('name') or idx.get('name') or '')
        c['idx'] = idx
    return clips


def parse_ref(s):
    m = re.fullmatch(r'([^:]+):([\d.]+)-([\d.]+)', s.strip())
    if not m:
        raise SystemExit(f'--host-ref wants CLIP:T0-T1, got {s!r}')
    return m.group(1), float(m.group(2)), float(m.group(3))


# ------------------------------------------------------------------ build
def build_index(day, out=None, host_ref=(), voiceprint=None, sheets_on=True):
    t_start = time.time()
    day = os.path.abspath(day)
    out = os.path.abspath(out or day)
    cache = os.path.join(out, 'cache')
    os.makedirs(cache, exist_ok=True)
    clips = load_clips(day)
    tr = {}
    for cid in list(clips):
        d = read_json(os.path.join(day, 'tr', cid + '.json'))
        if d is None:
            continue
        tr[cid] = d
    order = sorted(tr, key=lambda c: (clips[c].get('clock') if clips[c].get('clock') is not None else 1e9, c))
    log(f'index: {len(order)} transcribed clips in {day}')

    # ---- pieces + voice embeddings (cached per clip)
    E = None
    pieces, V = {}, {}
    for cid in order:
        segs = tr[cid]['segments']
        ps = SP.pieces_of(segs)
        for p in ps:
            s = segs[p['seg']]
            p['avg_logprob'] = s.get('avg_logprob', -0.4)
            p['no_speech'] = s.get('no_speech', 0)
        pieces[cid] = ps
        cf = os.path.join(cache, f'spk_{cid}.npz')
        src = os.path.join(day, 'tr', cid + '.json')
        key = f'{os.path.getmtime(src):.0f}:{len(ps)}'
        if os.path.exists(cf):
            z = np.load(cf, allow_pickle=False)
            if str(z['key']) == key:
                V[cid] = z['V']
                continue
        if not ps:
            V[cid] = np.zeros((0, 256), np.float32)
            continue
        if E is None:
            E = SP.Embedder(threads=2)
        audio = SP.load_audio(os.path.join(day, 'aud', cid + '.m4a'))
        V[cid] = SP.embed_pieces(E, audio, ps)
        np.savez(cf, V=V[cid], key=key)
    t_emb = time.time() - t_start
    kind = E.kind if E else 'wespeaker-resnet34-LM (cached)'

    # ---- host voice
    tau = SP.TAU
    vp_path = voiceprint or SP.VOICEPRINT
    if host_ref:
        if E is None:
            E = SP.Embedder(threads=2)
        refs = [parse_ref(r) for r in host_ref]
        c0, m_ref = SP.host_centroid_from_refs(E, lambda c: SP.load_audio(os.path.join(day, 'aud', c + '.m4a')), refs)
        tau = round(m_ref - 0.20, 3)
        src_note = f'reference narration {", ".join(host_ref)} (self-similarity {m_ref:.2f})'
        np.save(os.path.join(out, 'host_voiceprint.npy'), c0)
        if not os.path.exists(vp_path):
            os.makedirs(os.path.dirname(vp_path), exist_ok=True)
            np.save(vp_path, c0)
            src_note += f'; saved as {vp_path}'
    elif os.path.exists(vp_path):
        c0 = np.load(vp_path)
        src_note = f'saved voiceprint {vp_path}'
    else:
        # no reference at all: the most common voice among long pieces from the camera clips
        cand = [V[c][i] for c in order if clips[c]['camera'] for i, p in enumerate(pieces[c]) if p['end'] - p['start'] >= 2.0]
        X = np.asarray(cand) if cand else np.concatenate([V[c] for c in order])
        c0 = SP.centroid(X)
        for _ in range(4):
            s = X @ c0
            c0 = SP.centroid(X[s >= np.percentile(s, 60)])
        src_note = 'no reference given: the dominant voice of the camera clips (check a few labels)'
    allV = np.concatenate([V[c] for c in order if len(V[c])])
    alld = np.concatenate([[p['end'] - p['start'] for p in pieces[c]] for c in order if len(V[c])])
    cA, n_adapt = SP.adapt_centroid(c0, allV, alld, tau)
    labels = {}
    for cid in order:
        sc = (V[cid] @ cA) if len(V[cid]) else np.zeros(0)
        labels[cid] = SP.label_pieces(pieces[cid], sc, camera=clips[cid]['camera'], tau=tau)
    spk_meta = {'model': kind, 'host_reference': src_note, 'threshold': tau, 'adapted_on_pieces': n_adapt}

    # ---- flags
    flags = []
    for cid in order:
        flags += F.flags_for_clip(cid, tr[cid]['segments'], tr[cid].get('duration'))

    # ---- picture notes
    kfs, quality = {}, {}
    for cid in order:
        kfs[cid] = thumbs.list_keyframes(day, cid)
        st = None
        sj = os.path.join(day, 'kf', cid, 'stats.json')
        if os.path.exists(sj):
            fr = read_json(sj)['frames']
            st = sorted((int(k[:-4]) / 1000.0, v) for k, v in fr.items())
        else:
            cf = os.path.join(cache, f'kfstats_{cid}.json')
            st = read_json(cf)
            if st is None or len(st) != len(kfs[cid]):
                from PIL import Image
                st = [(t, thumbs.frame_stats(Image.open(p))) for t, p in kfs[cid]]
                write_json(cf, st, indent=None)
        quality[cid] = Q.clip_notes(st)

    # ---- moments
    clocks = [clips[c]['clock'] for c in order if clips[c].get('clock') is not None]
    d0 = min(clocks) if clocks else 0
    d1 = max((clips[c]['clock'] + tr[c].get('duration', 0)) for c in order if clips[c].get('clock') is not None) if clocks else 1
    allsc = []
    for k, cid in enumerate(order):
        ck = clips[cid].get('clock')
        pos = ((ck - d0) / max(1.0, d1 - d0)) if ck is not None else k / max(1, len(order) - 1)

        def qa(c, a, b, _q=quality[cid]):
            iss = Q.issues_between(_q, a, b)
            return ', '.join(Q.LABEL[x['kind']] for x in iss) or None
        allsc += M.score_clip(cid, pieces[cid], labels[cid], pos, flags, qa)
    ranked, blocked = M.rank(allsc)
    for cat, lst in ranked.items():
        for r, c in enumerate(lst, 1):
            c['rank'] = r
            ck = clips[c['clip']].get('clock')
            c['clock'] = fmt_clock(ck + c['in']) if ck is not None else None
            if sheets_on:
                c['sheet'] = os.path.relpath(sheets.strip(kfs[c['clip']], os.path.join(out, 'sheets', 'moments', f'{cat}_{r:02d}.jpg'),
                                                          c['clip'], c['in'], c['out']) or '', out) if kfs[c['clip']] else None
    # ---- contact sheets
    sheet_of = {}
    if sheets_on:
        for cid in order:
            if kfs[cid]:
                p = sheets.sheet(kfs[cid], os.path.join(out, 'sheets', f'{cid}.jpg'), cid, clock=clips[cid].get('clock'),
                                 max_tiles=60, tile_w=135)
                sheet_of[cid] = os.path.relpath(p, out) if p else None

    # ---- write
    spk_out = {cid: [dict(start=p['start'], end=p['end'], text=p['text'], seg=p['seg'], **l)
                     for p, l in zip(pieces[cid], labels[cid])] for cid in order}
    write_json(os.path.join(out, 'speakers.json'), {'meta': spk_meta, 'clips': spk_out})
    write_json(os.path.join(out, 'flags.json'), flags)
    write_json(os.path.join(out, 'quality.json'), quality)
    write_json(os.path.join(out, 'moments.json'), {'categories': M.CATEGORY_TITLES, 'moments': ranked, 'blocked': blocked})
    write_moments_md(os.path.join(out, 'moments.md'), ranked, blocked)
    write_day_md(os.path.join(out, 'day.md'), day, order, clips, tr, pieces, labels, flags, quality, sheet_of, spk_meta)
    log(f'index done in {time.time() - t_start:.0f}s (voice embeddings {t_emb:.0f}s): {sum(len(p) for p in pieces.values())} lines, '
        f'{len(flags)} flags ({sum(1 for f in flags if f["severity"] == "block")} block), '
        f'{sum(len(v) for v in ranked.values())} moments -> {out}')
    return {'out': out, 'pieces': pieces, 'labels': labels, 'flags': flags, 'moments': ranked, 'quality': quality,
            'speaker_meta': spk_meta}


def _flag_note(flags, cid, a, b):
    fs = F.overlaps(flags, cid, a, b)
    if not fs:
        return ''
    return '  **[' + '; '.join(f"{'NO' if f['severity'] == 'block' else 'bleep'}: {f['category']}" for f in fs) + ']**'


def write_day_md(path, day, order, clips, tr, pieces, labels, flags, quality, sheet_of, spk_meta):
    L = []
    dates = sorted({c.get('date') for c in clips.values() if c.get('date')})
    L.append(f'# Day index {" / ".join(dates) if dates else ""}\n')
    tot = sum(tr[c].get('duration', 0) for c in order)
    nh = sum(1 for c in order for l in labels[c] if l['speaker'] == 'HOST')
    nl = sum(len(labels[c]) for c in order)
    L.append(f'{len(order)} clips, {tot / 60:.0f} min of footage, {nl} transcript lines ({nh} HOST / {nl - nh} OTHER).  ')
    L.append(f'Speaker model: {spk_meta["model"]}; host voice from {spk_meta["host_reference"]}; '
             f'threshold {spk_meta["threshold"]}. Confidence is the chance the label is right; below 0.65 treat it as a guess.  ')
    L.append(f'Flags: {sum(1 for f in flags if f["severity"] == "block")} never-use spans, '
             f'{sum(1 for f in flags if f["severity"] == "caution")} bleep spans (flags.json). '
             'Moments by category: moments.md.\n')
    L.append('| clip | clock | length | picture |')
    L.append('|---|---|---|---|')
    for cid in order:
        ck = clips[cid].get('clock')
        L.append(f"| [{cid}](#{cid.lower()}) | {fmt_clock(ck) if ck is not None else '?'} | {tr[cid].get('duration', 0) / 60:.1f} min | "
                 f"{quality[cid]['summary']} |")
    L.append('')
    for cid in order:
        ck = clips[cid].get('clock')
        c = clips[cid]
        L.append(f"## {cid}")
        L.append(f"{c.get('name') or c.get('idx', {}).get('name') or ''}  ")
        L.append(f"start {fmt_clock(ck) if ck is not None else '?'}, {tr[cid].get('duration', 0):.0f} s, "
                 f"{'camera (DJI)' if c['camera'] else 'phone'}; picture: {quality[cid]['summary']}  ")
        if sheet_of.get(cid):
            L.append(f"contact sheet: [{sheet_of[cid]}]({sheet_of[cid]})  ")
        cf = [f for f in flags if f['clip'] == cid and f['severity'] == 'block']
        if cf:
            L.append('NEVER USE: ' + '; '.join(f"{f['category']} {_mmss(f['t0'])}-{_mmss(f['t1'])}" for f in cf) + '  ')
        L.append('')
        L.append('```')
        for p, l in zip(pieces[cid], labels[cid]):
            clock = fmt_clock(ck + p['start']) if ck is not None else '--:--:--'
            fl = _flag_note(flags, cid, p['start'], p['end']).replace('**', '')
            L.append(f"{clock}  {_mmss(p['start'], 1):>7}-{_mmss(p['end'], 1):<7} {l['speaker']:5s} {l['conf']:.2f}  {p['text']}{fl}")
        if not pieces[cid]:
            L.append('(no speech)')
        L.append('```')
        L.append('')
    with open(path, 'w') as f:
        f.write('\n'.join(L) + '\n')


def write_moments_md(path, ranked, blocked):
    L = ['# Moments\n',
         'Candidates per category, best first. In/out are clip seconds (the line itself; add handles in the EDL). '
         'Speaker is the majority of the lines (confidence per line in speakers.json). Strips: keyframes around the moment.\n']
    for cat, title in M.CATEGORY_TITLES.items():
        L.append(f'## {title} (`{cat}`)\n')
        lst = ranked.get(cat, [])
        if not lst:
            L.append('(none found)\n')
        for c in lst:
            note = []
            if c['caution']:
                note.append('bleep: ' + ', '.join(c['caution']))
            if c['picture']:
                note.append('picture: ' + c['picture'])
            L.append(f"{c['rank']}. **{c['clip']} {c['in']:.2f}-{c['out']:.2f}** ({c['dur']:.1f} s, {c['clock'] or '?'}, "
                     f"{c['speaker']}, score {c['score']:.1f}) \"{c['text']}\"  ")
            L.append(f"   why: {', '.join(c['hits'])}" + (f"; {'; '.join(note)}" if note else '') +
                     (f"  [strip]({c['sheet']})" if c.get('sheet') else ''))
        bl = blocked.get(cat, [])
        if bl:
            L.append('\n   blocked (never use): ' + '; '.join(f"{b['clip']} {b['in']:.1f}-{b['out']:.1f} ({', '.join(b['blocked'])}) \"{b['text'][:60]}\"" for b in bl))
        L.append('')
    with open(path, 'w') as f:
        f.write('\n'.join(L) + '\n')


def _mmss(t, dec=0):
    if dec:
        return f'{int(t // 60)}:{t % 60:04.1f}'
    return f'{int(t // 60)}:{int(t % 60):02d}'
