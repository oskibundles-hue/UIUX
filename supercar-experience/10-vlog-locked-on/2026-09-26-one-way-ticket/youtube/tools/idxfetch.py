"""idxfetch.py -- rebuild DAY/idx/<id>.{moov,head,tail.json,json} for the clips a cut uses, from Dropbox
download links (two per clip: tail first, then head), so `vlog.py plan` works on a fresh copy of the survey.

    python3 tools/idxfetch.py DAY LINKS.json      LINKS.json = a download_link answer ({"entries": [...]}),
                                                  each clip's path listed twice, in that order
Links are single-use: each one gets exactly one Range request."""
import json, os, subprocess, sys, tempfile

ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'engine')
sys.path.insert(0, os.path.abspath(ENGINE))
from lib import mp4, stream  # noqa: E402

HEAD = 1 << 20


def head_atoms(buf, size):
    out, off = [], 0
    while off + 8 <= len(buf):
        n = int.from_bytes(buf[off:off + 4], 'big')
        typ = buf[off + 4:off + 8].decode('latin1')
        hdr = 8
        if n == 1:
            n = int.from_bytes(buf[off + 8:off + 16], 'big'); hdr = 16
        elif n == 0:
            n = size - off
        out.append([typ, off, n])
        if typ == 'mdat':
            return out, off + hdr
        off += n
    raise SystemExit('mdat header not in the first MiB')


def main():
    day, links = sys.argv[1], json.load(open(sys.argv[2]))['entries']
    clips = json.load(open(os.path.join(day, 'clips.json')))
    by_path = {c['path'].lower(): cid for cid, c in clips.items()}
    os.makedirs(os.path.join(day, 'idx'), exist_ok=True)
    pairs = {}
    for e in links:
        cid = by_path[(e.get('path_display') or e['path']).lower()]
        pairs.setdefault(cid, []).append(e)
    for cid, (lt, lh) in pairs.items():
        size = lt['size']
        n = min(size, max(16 << 20, size // 1000))
        found = mp4.find_moov_in_tail(stream.http_range(lt['download_url'], size - n, size), size)
        if not found:
            raise SystemExit(f'{cid}: moov not in tail')
        off, moov, rest = found
        head = bytes(stream.http_range(lh['download_url'], 0, HEAD))
        atoms, head_end = head_atoms(head, size)
        p = lambda ext: os.path.join(day, 'idx', cid + ext)
        open(p('.moov'), 'wb').write(moov)
        open(p('.head'), 'wb').write(head[:head_end])
        json.dump({'moov_offset': off, 'atoms_from_moov': rest, 'tail_bytes': n}, open(p('.tail.json'), 'w'))
        with tempfile.NamedTemporaryFile(suffix='.mp4') as t:
            t.truncate(size); t.seek(0); t.write(head[:head_end]); t.seek(off); t.write(moov); t.flush()
            probe = subprocess.run(['ffmpeg', '-hide_banner', '-i', t.name], capture_output=True, text=True).stderr
        mv = mp4.parse_moov(moov)
        v = mv.video
        meta = {'id': cid, 'name': lt['name'], 'path': clips[cid]['path'], 'size': size,
                'atoms': atoms + [list(r) for r in rest], 'probe': probe,
                'duration': round(v.duration(), 3),
                'video': {'codec': v.codec, 'w': v.width, 'h': v.height, 'rotation': v.rotation,
                          'hlg': 'arib-std-b67' in probe, 'sync': len(v.sync_indices())}}
        json.dump(meta, open(p('.json'), 'w'))
        print(cid, v.width, v.height, meta['duration'], 'HLG' if meta['video']['hlg'] else '')


if __name__ == '__main__':
    main()
