#!/usr/bin/env python3
"""Re-run `index` on the Sep 15 survey and check it against what we know about that day.

usage: validate_sep15.py DAY OUT [--edl edl.json] [--no-build]
  DAY  the Sep 15 survey (tr/, aud/, kf/, idx/, names.txt, phone_starts.json)
  OUT  where index writes

Checks
  speakers  0021 23-37 s (the Roma answer) HOST; P2236 guide briefing OTHER; 0034 check-in answers
            ("Wonderful time. Good time." ~431 s, "Awesome" ~549 s) OTHER
  flags     every known never-use span is covered by a block flag of the right category
  moments   every dialog piece of the approved cut (edl.json) shows up near the top of a fitting category
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib.dayindex import build_index  # noqa: E402

# approved dialog piece -> the categories it belongs to
APPROVED = {
    ('0034', 431.5): ['reaction'], ('0001', 2.0): ['intro'], ('0001', 83.2): ['offer'], ('0001', 92.05): ['offer'],
    ('0013', 0.0): ['lineup'], ('0013', 5.4): ['lineup'], ('0013', 26.6): ['arrival'], ('0013', 58.6): ['offer'],
    ('0013', 73.1): ['offer'], ('0013', 387.9): ['arrival'], ('0011', 221.0): ['briefing'],
    ('0013', 757.1): ['lineup', 'arrival'], ('0013', 606.8): ['convoy'], ('0016', 195.0): ['arrival'],
    ('0017', 11.4): ['convoy', 'food'], ('0017', 17.9): ['convoy'], ('0017', 21.1): ['convoy'],
    ('0021', 23.4): ['lineup', 'reaction'], ('0021', 28.5): ['lineup', 'reaction'], ('0021', 35.2): ['lineup', 'reaction'],
    ('0025', 17.0): ['food'], ('0022', 116.0): ['food', 'offer'], ('0030', 48.4): ['closing'],
    ('P2236', 37.5): ['briefing'], ('P2236', 66.5): ['briefing'], ('P2236', 114.3): ['briefing'],
    ('0034', 428.6): ['reaction'], ('0034', 545.4): ['reaction'], ('0032', 1442.2): ['reaction'],
    ('0034', 190.4): ['closing'], ('0034', 96.8): ['offer'],
}

FLAGS = [  # clip, t0, t1, category, what
    ('0008', 217, 231, 'password', 'spoken password "two zero two four capital H..." ~3:37'),
    ('0022', 68, 95, 'cut_request', '"don\'t post that" / "take that out" 1:08-1:35'),
    ('0032', 1455, 1457, 'speed', '"I hit 114" ~24:15'),
    # word timing, identical in both transcriptions ("going" 641.85, "100" 641.97-642.3); the segment start (~638) is a smeared "Oh"
    ('0034', 641.8, 642.4, 'speed', '"going 100 and some" ~10:42'),
    ('0034', 654, 681, 'weapons', 'gun talk 10:54-11:21'),
    ('P2236', 95, 113, 'unsafe_driving', 'double yellow / "go a little faster" 1:35-1:53'),
    ('0009', 136, 138, 'fleet_fault', '"the door handle just broke"'),
    ('0024', 82, 85, 'fleet_fault', '"broken door handle and a nasty misfire"'),
    ('0020', 67, 71, 'fleet_fault', '"sounded like it was knocking"'),
    ('0006', 10, 20, 'police', '"busty cops"'),
    ('0022', 386, 392, 'police', '"that pulled us over"'),
    ('0034', 611, 612, 'profanity', 'profanity (bleep, not block)'),
    ('0022', 45, 45.5, 'slur', 'slur (bleep, not block)'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('day')
    ap.add_argument('out')
    ap.add_argument('--edl')
    ap.add_argument('--no-build', action='store_true')
    a = ap.parse_args()
    if a.no_build:
        res = None
    else:
        res = build_index(a.day, out=a.out, host_ref=['0001:0-48', '0001:83-105'])
    spk = json.load(open(os.path.join(a.out, 'speakers.json')))['clips']
    flags = json.load(open(os.path.join(a.out, 'flags.json')))
    mom = json.load(open(os.path.join(a.out, 'moments.json')))['moments']
    ok_all = True

    print('\n== speakers')

    def span_label(cid, t0, t1):
        ps = [p for p in spk[cid] if p['end'] > t0 and p['start'] < t1]
        host = sum((p['end'] - p['start']) * (p['conf'] if p['speaker'] == 'HOST' else 1 - p['conf']) for p in ps)
        tot = sum(p['end'] - p['start'] for p in ps)
        return ps, host / max(tot, 1e-6)
    cases = [('0021', 23, 37, 'HOST', 'the Roma answer'), ('P2236', 23.9, 71, 'OTHER', 'guide briefing, part 1'),
             ('P2236', 95, 118, 'OTHER', 'guide briefing, part 2'),
             ('0034', 431, 433.4, 'OTHER', '"Wonderful time. Good time."'), ('0034', 548.8, 549.3, 'OTHER', '"Awesome"')]
    for cid, t0, t1, want, what in cases:
        ps, hp = span_label(cid, t0, t1)
        got = 'HOST' if hp >= 0.5 else 'OTHER'
        ok = got == want
        ok_all &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {cid} {t0}-{t1} {what}: {got} (P(host) {hp:.2f}); lines: " +
              ' | '.join(f"{p['text'][:28]!r} {p['speaker']} {p['conf']:.2f}" for p in ps[:6]))

    print('\n== flags')
    for cid, t0, t1, cat, what in FLAGS:
        hit = [f for f in flags if f['clip'] == cid and f['category'] == cat and f['t0'] <= t0 + 0.5 and f['t1'] >= t1 - 0.5]
        ok = bool(hit)
        ok_all &= ok
        sev = hit[0]['severity'] if hit else '-'
        print(f"{'PASS' if ok else 'FAIL'}  {cid} {what}: " + (f"{cat} [{sev}] {hit[0]['t0']:.1f}-{hit[0]['t1']:.1f}" if hit else 'not flagged'))
    edl = json.load(open(a.edl)) if a.edl else None
    if edl:
        used = [(d['src'], d['in'], d['out']) for d in edl['dialog']] + [(x['src'], x['in'], x['out']) for x in edl['audio_extra'] if x['kind'] == 'dialog']
        bad = [f for f in flags if f['severity'] == 'block' for (s, i, o) in used if f['clip'] == s and f['t0'] < o and f['t1'] > i]
        print(('PASS' if not bad else 'FAIL') + f'  no block flag overlaps any dialog of the approved cut ({len(used)} pieces)' +
              ('' if not bad else ': ' + str(bad)))
        ok_all &= not bad

    print('\n== moments (approved cut dialog -> best rank in a fitting category)')
    if edl:
        pieces = {(d['src'], d['in']): d for d in edl['dialog']}
        for x in edl['audio_extra']:
            if x['kind'] == 'dialog':
                pieces[(x['src'], x['in'])] = x
        ranks = []
        for key, d in sorted(pieces.items(), key=lambda kv: kv[1].get('t', 0)):
            cats = APPROVED.get(key, list(mom))
            best = None
            for cat in cats:
                for c in mom.get(cat, []):
                    ov = min(c['out'], d['out']) - max(c['in'], d['in'])
                    if c['clip'] == d['src'] and ov >= 0.5 * min(d['out'] - d['in'], c['out'] - c['in']):
                        if best is None or c['rank'] < best[1]:
                            best = (cat, c['rank'], c)
                        break
            ranks.append(best[1] if best else 99)
            txt = best[2]['text'][:70] if best else ''
            print(f"  {'top5 ' if best and best[1] <= 5 else 'top10' if best and best[1] <= 10 else 'MISS '} {d['src']:6s} "
                  f"{d['in']:7.2f}-{d['out']:7.2f} -> " + (f"{best[0]} #{best[1]} ({best[2]['in']:.1f}-{best[2]['out']:.1f}) \"{txt}\"" if best else f'not in top 15 of {cats}'))
        n = len(ranks)
        print(f"  {sum(r <= 3 for r in ranks)}/{n} in the top 3, {sum(r <= 5 for r in ranks)}/{n} top 5, "
              f"{sum(r <= 10 for r in ranks)}/{n} top 10, {sum(r > 15 for r in ranks)} missing")
        ok_all &= sum(r <= 10 for r in ranks) == n
    print('\nALL CHECKS PASS' if ok_all else '\nSOME CHECKS FAIL')
    return res


if __name__ == '__main__':
    main()
