#!/usr/bin/env python3
"""aud_from_mezz.py -- rebuild DAY/aud/<clip>.m4a from the fetched mezzanines when the survey audio is gone
(the container reset of 2026-10-08 kept the transcripts but not the camera audio, which is never committed).

Every mezzanine MEZZ/<clip>_<t0>-<t1>.mov starts at exactly t0 (input seek) and carries the camera sound as
48 kHz stereo PCM. Each clip gets one full-length track (length from DAY/idx/<clip>.json), the mezzanine audio
placed at its source time and silence everywhere else, written as lossless ALAC so mix.py and words_medium.py
read the same clip times they always did. Only the ranges the EDL fetched have sound; anything outside them is
silent, so a mix that reaches past a fetched range shows up as a hole, not as wrong audio.

An existing aud/<clip>.m4a is kept as the base, so a second fetch group adds its ranges without losing the first's.

usage: python3 aud_from_mezz.py DAY MEZZ [clip ...]   (FETCHPLAN=path overrides DAY/fetch/fetchplan.json)
"""
import glob, json, os, re, subprocess, sys
import numpy as np

SR = 48000


def secs(s):
    return float(s)


def main():
    day, mezz = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    exact = {}
    fp = os.environ.get('FETCHPLAN') or os.path.join(day, 'fetch', 'fetchplan.json')
    if os.path.exists(fp):  # the plan's t0 has 3 decimals; the file name rounds it to 2
        exact = {j['out']: j['t0'] for j in json.load(open(fp))['jobs']}
    pieces = {}
    for f in sorted(glob.glob(os.path.join(mezz, '*.mov'))):
        m = re.match(r'(\d{4})_([\d.]+)-([\d.]+)\.mov$', os.path.basename(f))
        if m and (not only or m.group(1) in only):
            pieces.setdefault(m.group(1), []).append((exact.get(os.path.basename(f), secs(m.group(2))), f))
    os.makedirs(os.path.join(day, 'aud'), exist_ok=True)
    for cid, items in sorted(pieces.items()):
        dur = json.load(open(os.path.join(day, 'idx', cid + '.json')))['duration']
        buf = np.zeros((int(round(dur * SR)) + SR, 2), np.float32)
        old = os.path.join(day, 'aud', cid + '.m4a')
        if os.path.exists(old):  # keep the ranges an earlier fetch group placed
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', old, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                                 capture_output=True, check=True).stdout
            a = np.frombuffer(raw, np.float32).reshape(-1, 2)[:len(buf)]
            buf[:len(a)] = a
        for t0, f in items:
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-map', '0:a:0', '-f', 'f32le', '-ac', '2',
                                  '-ar', str(SR), '-'], capture_output=True, check=True).stdout
            a = np.frombuffer(raw, np.float32).reshape(-1, 2)
            i = int(round(t0 * SR))
            n = min(len(a), len(buf) - i)
            seg = buf[i:i + n]
            # overlapping mezzanines hold the same source samples; keep whichever is already there
            np.copyto(seg, a[:n], where=(seg == 0))
        out = os.path.join(day, 'aud', cid + '.m4a')
        part = os.path.join(day, 'aud', f'.{cid}.part.m4a')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-',
                        '-t', f'{dur:.3f}', '-c:a', 'alac', '-sample_fmt', 's32p', part],
                       input=buf.tobytes(), check=True)
        os.replace(part, out)
        print(cid, len(items), 'pieces', f'{dur:.1f}s', os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
