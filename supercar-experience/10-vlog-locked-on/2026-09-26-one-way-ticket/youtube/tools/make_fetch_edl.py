"""make_fetch_edl.py -- fetch-only EDLs for the long-form: every PLAN.md span padded 3 s, plus every range the
approved opening (opening-test/edl_B2.json) and chapter 3 test (test-ch3/edl.json) use.

    python3 tools/make_fetch_edl.py OUTDIR   -> OUTDIR/fetchA/edl.json (opening + ch1-4), OUTDIR/fetchB/edl.json (ch5-8)

Run vlog.py plan on each, A first; B only once A's mezzanines are built and A's sources trimmed (disk)."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
YT = os.path.dirname(HERE)
PAD = 3.0
CH = {
 1: [('0076',24.9,34.4),('0076',88.4,134.4),('0077',78.4,98),('0080',51.7,54.1),('0081',2.9,7.6)],
 2: [('0082',0,12),('0084',1,14.1),('0085',50,69),('0086',32,33.5)],
 4: [('0093',3.9,8.2),('0093',127.8,142.1),('0094',151.2,165.5),('0095',0,58),('0098',0,60),('0100',20.1,38.7)],
 5: [('0102',17.4,25.4),('0102',58.3,62.7),('0105',4.9,13.8),('0106',283.6,296.5),('0107',232.4,237.7),('0112',13.8,32.6)],
 6: [('0114',3.9,30.5),('0114',87.9,89),('0115',2.3,36.8)],
 7: [('0116',4.6,13.0),('0116',52.1,54.7),('0116',121.4,127.7),('0117',74.9,81.4),('0117',100.9,113.2),('0118',61.9,91.2),('0119',1.0,11.7),('0119',52.0,59.1)],
 8: [('0119',84.9,91.5),('0119',227.8,245),('0121',80,120),('0122',43.3,47.4),('0122',552,570),('0122',582,600),('0123',4.1,12.4),('0123',17.1,27.2),('0123',39.9,59.4)],
}


def from_edl(path):
    e = json.load(open(path))
    out = []
    for s in e.get('shots', []):
        if s.get('src') not in (None, 'card'):
            out.append((s['src'], s['in'], s['in'] + (s['out'] - s['in'])))
    for d in e.get('dialog', []) + e.get('audio_extra', []):
        if d.get('src') not in (None, 'card'):
            out.append((d['src'], d['in'], d['out']))
    return out


def edl(spans):
    shots = [{'src': s, 'in': round(max(0.0, a - PAD), 2), 'out': round(b + PAD, 2), 'speed': 1.0}
             for s, a, b in sorted(spans)]
    return {'fps': 29.97, 'size': [3840, 2160], 'shots': shots, 'dialog': [], 'audio_extra': []}


def main():
    out = sys.argv[1]
    a = [x for c in (1, 2, 4) for x in CH[c]]
    a += from_edl(os.path.join(YT, 'opening-test', 'edl_B2.json')) + from_edl(os.path.join(YT, 'test-ch3', 'edl.json'))
    b = [x for c in (5, 6, 7, 8) for x in CH[c]]
    for name, spans in (('fetchA', a), ('fetchB', b)):
        os.makedirs(os.path.join(out, name), exist_ok=True)
        e = edl(spans)
        json.dump(e, open(os.path.join(out, name, 'edl.json'), 'w'), indent=1)
        print(name, len({s['src'] for s in e['shots']}), 'clips', len(e['shots']), 'ranges')


if __name__ == '__main__':
    main()
