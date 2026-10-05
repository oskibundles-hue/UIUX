#!/usr/bin/env python3
"""peek.py -- look inside a multi-GB Osmo clip in Dropbox without downloading it.

The Osmo writes its index (moov) at the END of the file, and each Dropbox download link is single-use (one request,
Range allowed). So: one link fetches the tail, the header is rebuilt locally, and one link per keyframe (or per
segment) fetches just those bytes into a sparse local copy that ffmpeg reads normally.

  peek.py index  <local.mp4> <size> <url>              tail -> sparse file with a rebuilt header; prints the duration
  peek.py keys   <local.mp4> <t1,t2,...>               prints the byte range of the keyframe nearest each time
  peek.py span   <local.mp4> <t0> <t1>                 prints the byte range covering t0..t1 (+-2 MB margin)
  peek.py fill   <local.mp4> <start> <end> <url>       fetches bytes start..end-1 into the sparse file
Get the URLs from the Dropbox connector's download_link (ask for the same file id several times for several links).
"""
import os, struct, subprocess, sys
REF_HEAD = bytes.fromhex('0000001c66747970') + b'isom\x00\x00\x02\x00isomiso2mp41' + struct.pack('>I4s', 8, b'free')

def curl(url, a, b, out):
    subprocess.run(['curl', '-sS', '-r', f'{a}-{b}' if b is not None else f'-{a}', url, '-o', out], check=True)

def keys(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time,pos,size,flags',
                        '-of', 'csv=p=0', path], capture_output=True, text=True).stdout
    return [(float(p[0]), int(p[2]), int(p[1])) for p in (l.split(',') for l in r.splitlines()) if len(p) >= 4 and 'K' in p[3]]

cmd = sys.argv[1]
if cmd == 'index':
    path, size, url = sys.argv[2], int(sys.argv[3]), sys.argv[4]
    n = int(size * 0.0011 * 1.6) + 2_000_000
    subprocess.run(['truncate', '-s', str(size), path], check=True)
    curl(url, n, None, path + '.tail'); t = open(path + '.tail', 'rb').read(); os.remove(path + '.tail')
    with open(path, 'r+b') as f:
        f.seek(size - len(t)); f.write(t)
        i = t.find(b'moov')
        while i != -1:
            s = struct.unpack('>I', t[i-4:i])[0]
            if size - len(t) + i - 4 + s == size: break
            i = t.find(b'moov', i + 1)
        moov = size - len(t) + i - 4
        X = 4072
        f.seek(0); f.write(REF_HEAD); f.write(struct.pack('>I4s', X - 36, b'free'))
        f.seek(X); f.write(struct.pack('>I4sQ', 1, b'mdat', moov - X))
    print(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip(), 's')
elif cmd == 'keys':
    K = keys(sys.argv[2])
    for t in map(float, sys.argv[3].split(',')):
        k = min(K, key=lambda x: abs(x[0] - t)); print(f'{k[0]:.3f} {k[1]} {k[1] + k[2]}')
elif cmd == 'span':
    K = keys(sys.argv[2]); t0, t1 = float(sys.argv[3]), float(sys.argv[4])
    a = min(K, key=lambda x: abs(x[0] - (t0 - 1))); b = min(K, key=lambda x: abs(x[0] - (t1 + 1)))
    print(a[1] - 2_000_000, b[1] + b[2] + 2_000_000)
elif cmd == 'fill':
    path, a, b, url = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    curl(url, a, b - 1, path + '.part'); d = open(path + '.part', 'rb').read(); os.remove(path + '.part')
    assert len(d) == b - a, (len(d), b - a)
    with open(path, 'r+b') as f: f.seek(a); f.write(d)
    print('filled', len(d))
