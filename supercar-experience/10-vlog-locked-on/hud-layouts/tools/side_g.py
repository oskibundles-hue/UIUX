#!/usr/bin/env python3
"""side_g.py -- the SIDE G series for the DRV plate, from the Osmo's own motion sensor (no GPS needed).

  side_g.py <clip.mp4> <start_s> <dur_s> <out.json> [--turn a,b,right|left]

Reads the camera's metadata track (djmd, one record per frame; needs `pip install pyosmogps`), low-passes the
accelerometer over 1 s, removes gravity and keeps the horizontal component along one axis, sampled at 30 fps.
--turn names a stretch with a known turn: the axis is the one that swings most there, and the sign is set so the
turn reads toward its own side. Without --turn the camera's x axis is used (cabin mount, as on the Oct 3 clip) and
left/right is NOT confirmed. Values are in g; the plate shows +-0.5 g full scale.
"""
import json, math, subprocess, sys
from pyosmogps import dji_pb2
clip, start, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
turn = sys.argv[sys.argv.index('--turn') + 1].split(',') if '--turn' in sys.argv else None
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-i', clip, '-t', str(dur), '-map', '0:2', '-c', 'copy', '-f', 'data', out + '.bin'], check=True)
m = dji_pb2.GenericMessage(); m.ParseFromString(open(out + '.bin', 'rb').read())
A = [(e.camera_info.accelerometer2.x, e.camera_info.accelerometer2.y, e.camera_info.accelerometer2.z) for e in m.gps_info]
n = len(A); rate = n / dur; W = max(1, int(rate))
g = [sum(a[k] for a in A) / n for k in range(3)]; gl = math.sqrt(sum(c * c for c in g)); gu = [c / gl for c in g]
lp = [[sum(x[k] for x in A[max(0, i - W // 2):min(n, i + W // 2)]) / len(A[max(0, i - W // 2):min(n, i + W // 2)]) for k in range(3)] for i in range(n)]
hor = []
for a in lp:
    d = [a[k] - g[k] for k in range(3)]; p = sum(d[k] * gu[k] for k in range(3)); hor.append([d[k] - p * gu[k] for k in range(3)])
def unit(v): l = math.sqrt(sum(c * c for c in v)); return [c / l for c in v]
def perp(v): p = sum(v[k] * gu[k] for k in range(3)); return unit([v[k] - p * gu[k] for k in range(3)])
if turn:
    i0, i1 = int(float(turn[0]) * rate), int(float(turn[1]) * rate)
    u = perp([1, 0, 0] if abs(gu[0]) < 0.9 else [0, 1, 0]); v = [gu[1]*u[2]-gu[2]*u[1], gu[2]*u[0]-gu[0]*u[2], gu[0]*u[1]-gu[1]*u[0]]
    best = None
    for ang in range(0, 180, 2):
        th = math.radians(ang); ax = [math.cos(th) * u[k] + math.sin(th) * v[k] for k in range(3)]
        var = sum(sum(h[k] * ax[k] for k in range(3)) ** 2 for h in hor[i0:i1])
        if best is None or var > best[0]: best = (var, ax)
    ax = best[1]
else:
    ax = perp([1, 0, 0])
lat = [sum(h[k] * ax[k] for k in range(3)) for h in hor]
if turn:
    mt = sum(lat[i0:i1]) / max(1, i1 - i0)
    if (mt < 0) == (turn[2] == 'right'): lat = [-x for x in lat]
series = [round(lat[min(n - 1, int(i / 30 * n / dur))], 4) for i in range(int(dur * 30))]
json.dump(series, open(out, 'w'))
print('side G', min(series), max(series))
