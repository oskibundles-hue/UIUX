"""Real Las Vegas map for shots 18, 24 and 26, built from OpenStreetMap and AWS terrain tiles.

Inputs (downloaded once, cached): ~/.local/vlogtools/cache/vegas_map/
  osm_major.json  motorway..tertiary         osm_minor.json  residential streets
  osm_water.json  water + Red Rock boundary   osm_bldg.json   buildings around the Strip
  terrain/12_x_y.png  terrarium elevation tiles (z12)

Writes public/map/:
  base.jpg        night terrain: hillshade, Lake Mead, no lights
  lit.jpg         the same with the city lit up (streets, highways, buildings)
  pickup_tile.jpg close top-down crop around the pickup, for the asset board
  data.json       stops, the driven route (real roads, shortest path), Strip towers with heights

Map data (c) OpenStreetMap contributors, ODbL. The ad credits it on the map shots.

  uv run --no-project --with numpy --with pillow --with scipy python tools/vegas_map.py
"""
import heapq, json, math, os, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

CACHE = os.path.expanduser('~/.local/vlogtools/cache/vegas_map')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'map')

SS = 2  # supersampling for the line work
VALLEY = (-115.46, 35.98, -114.74, 36.30, 3600)  # the whole valley, Red Rock to Lake Mead, ~18 m per px

merc = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def set_view(lon0, lat0, lon1, lat1, w):
    """Point every drawing function at one Web Mercator window, w px wide."""
    global LON0, LAT0, LON1, LAT1, TW, TH, K, M_PER_PX, Z
    LON0, LAT0, LON1, LAT1, TW = lon0, lat0, lon1, lat1, w
    K = TW / (LON1 - LON0)                              # px per degree of longitude
    TH = int(round((merc(LAT1) - merc(LAT0)) * K * 180 / math.pi))
    M_PER_PX = (LON1 - LON0) / TW * 111320 * math.cos(math.radians((LAT0 + LAT1) / 2))
    Z = 18 / M_PER_PX                                   # glow radii are tuned at 18 m per px


set_view(*VALLEY)


def uv(lon, lat):
    return (lon - LON0) * K, (merc(LAT1) - merc(lat)) * K * 180 / math.pi


def lonlat(u, v):
    m = merc(LAT1) - v / (K * 180 / math.pi)
    return LON0 + u / K, math.degrees(2 * math.atan(math.exp(m)) - math.pi / 2)


# the five stops, in the order of the ad's STOPS list (pins and photo cards)
STOPS = [
    ('PICKUP', -115.1585, 36.1337),      # placeholder: LVCC West Hall (OSM centroid), where the pickup photo was shot
    ('RED ROCK', -115.4277, 36.1359),    # Red Rock Canyon visitor centre
    ('THE STRIP', -115.1728, 36.1126),   # Las Vegas Blvd at the Bellagio fountains
    ('THE SPHERE', -115.1621, 36.1209),
    ('LAKE MEAD', -114.8430, 36.0960),   # Las Vegas Bay, the end of Lake Mead Parkway
]
DRIVE = [0, 1, 2, 3, 4]  # the order the route visits them
CITY = (1230, 830, 1770, 1370)  # valley px box (u0, v0, u1, v1) also drawn at 4x for close-ups


def load(name):
    return json.load(open(os.path.join(CACHE, f'osm_{name}.json')))['elements']


# ---------------------------------------------------------------- terrain
def elevation():
    xs, ys = range(732, 744), range(1603, 1610)
    mos = np.zeros((len(ys) * 256, len(xs) * 256), np.float32)
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            a = np.asarray(Image.open(os.path.join(CACHE, 'terrain', f'12_{x}_{y}.png')).convert('RGB'), np.float32)
            mos[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    n = 4096 * 256
    gx = lambda lon: (lon + 180) / 360 * n - 732 * 256
    gy = lambda lat: (1 - merc(lat) / math.pi) / 2 * n - 1603 * 256
    box = (gx(LON0), gy(LAT1), gx(LON1), gy(LAT0))
    im = Image.fromarray(mos, 'F').resize((TW, TH), Image.BICUBIC, box=box)
    return np.asarray(im, np.float32)


def hillshade(z, exag=2.2, az=315, alt=38):
    dzdx = np.gradient(z, axis=1) / M_PER_PX * exag
    dzdn = -np.gradient(z, axis=0) / M_PER_PX * exag    # rows run south, so flip to north
    nrm = np.sqrt(dzdx ** 2 + dzdn ** 2 + 1)
    a, e = math.radians(az), math.radians(alt)
    L = (math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))
    return np.clip((-dzdx * L[0] - dzdn * L[1] + L[2]) / nrm, 0, 1)


# ---------------------------------------------------------------- water
def rings(members):
    """Stitch a multipolygon's member ways into closed rings."""
    segs = [[(p['lon'], p['lat']) for p in m['geometry']] for m in members if m.get('geometry')]
    out = []
    while segs:
        ring = segs.pop(0)
        grown = True
        while grown and ring[0] != ring[-1]:
            grown = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s + ring[1:]
                elif s[0] == ring[0]:
                    ring = s[::-1] + ring[1:]
                else:
                    continue
                segs.pop(i)
                grown = True
                break
        out.append(ring)
    return out


def water_mask():
    m = Image.new('L', (TW * SS, TH * SS), 0)
    d = ImageDraw.Draw(m)
    poly = lambda pts: [(u * SS, v * SS) for u, v in (uv(lo, la) for lo, la in pts)]
    for e in load('water'):
        t = e.get('tags', {})
        if t.get('natural') != 'water':
            continue
        if e['type'] == 'way' and e.get('geometry'):
            d.polygon(poly([(p['lon'], p['lat']) for p in e['geometry']]), fill=255)
        elif e['type'] == 'relation':
            outer = [m_ for m_ in e['members'] if m_.get('role') == 'outer']
            inner = [m_ for m_ in e['members'] if m_.get('role') == 'inner']
            for r in rings(outer):
                if len(r) > 2:
                    d.polygon(poly(r), fill=255)
            for r in rings(inner):
                if len(r) > 2:
                    d.polygon(poly(r), fill=0)
    return np.asarray(m.resize((TW, TH), Image.LANCZOS), np.float32) / 255


# ---------------------------------------------------------------- roads + buildings
CLASS = {'motorway': 3, 'trunk': 3, 'motorway_link': 2, 'trunk_link': 2, 'primary': 2, 'secondary': 1, 'tertiary': 1}


def line_layers():
    """Light layers at SS x: streets, arterials, highways, building footprints."""
    size = (TW * SS, TH * SS)
    L = {k: Image.new('L', size, 0) for k in ('minor', 'art', 'hwy', 'bldg')}
    D = {k: ImageDraw.Draw(v) for k, v in L.items()}
    pts = lambda g: [(u * SS, v * SS) for u, v in (uv(p['lon'], p['lat']) for p in g)]
    wid = lambda metres, least: max(least, round(metres / M_PER_PX * SS))  # real road widths when zoomed in
    for e in load('minor'):
        if e.get('geometry'):
            D['minor'].line(pts(e['geometry']), fill=255, width=wid(9, 1), joint='curve')
    for e in load('major'):
        c = CLASS.get(e.get('tags', {}).get('highway'), 1)
        if e.get('geometry'):
            if c == 3:
                D['hwy'].line(pts(e['geometry']), fill=255, width=wid(36, 5), joint='curve')
            else:
                D['art'].line(pts(e['geometry']), fill=255 if c == 2 else 190, width=wid(22, 3) if c == 2 else wid(15, 2), joint='curve')
    for e in load('bldg'):
        g = e.get('geometry') or next((m['geometry'] for m in e.get('members', []) if m.get('role') == 'outer' and m.get('geometry')), None)
        if g and len(g) > 2:
            D['bldg'].polygon(pts(g), fill=120, outline=255)
    return {k: np.asarray(v.resize((TW, TH), Image.LANCZOS), np.float32) / 255 for k, v in L.items()}


def blur(a, r):
    return gaussian_filter(a, r).astype(np.float32)


def colour(hex_):
    return np.array([int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def screen(base, light, col):
    return 1 - (1 - base) * (1 - light[..., None] * col)


# ---------------------------------------------------------------- route on real roads
def route():
    nodes, adj = {}, {}
    speed = {3: 1.0, 2: 1.35, 1: 1.6}
    for e in load('major'):
        ids, g = e.get('nodes'), e.get('geometry')
        if not ids or not g or len(ids) != len(g):
            continue
        w = speed[CLASS.get(e['tags'].get('highway'), 1)]
        for a, b, pa, pb in zip(ids, ids[1:], g, g[1:]):
            nodes[a] = (pa['lon'], pa['lat'])
            nodes[b] = (pb['lon'], pb['lat'])
            dx = (pb['lon'] - pa['lon']) * math.cos(math.radians(pa['lat']))
            dist = math.hypot(dx, pb['lat'] - pa['lat']) * 111320 * w
            adj.setdefault(a, []).append((b, dist))
            adj.setdefault(b, []).append((a, dist))
    ids = list(nodes)
    arr = np.array([nodes[i] for i in ids])

    def snap(lon, lat):
        d = ((arr[:, 0] - lon) * math.cos(math.radians(lat))) ** 2 + (arr[:, 1] - lat) ** 2
        k = int(np.argmin(d))
        return ids[k], math.sqrt(d[k]) * 111320

    def dijkstra(s, t):
        dist, prev, pq = {s: 0}, {}, [(0, s)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == t:
                break
            if d > dist[u]:
                continue
            for v, w in adj.get(u, ()):
                nd = d + w
                if nd < dist.get(v, 1e18):
                    dist[v], prev[v] = nd, u
                    heapq.heappush(pq, (nd, v))
        path = [t]
        while path[-1] != s:
            path.append(prev[path[-1]])
        return path[::-1]

    snaps = []
    for name, lon, lat in STOPS:
        n, off = snap(lon, lat)
        snaps.append(n)
        print(f'  {name:11s} snapped {off:5.0f} m from the landmark')
    line, marks = [], []
    for a, b in zip(DRIVE, DRIVE[1:]):
        seg = [uv(*nodes[n]) for n in dijkstra(snaps[a], snaps[b])]
        if not line:
            line.append(uv(*STOPS[a][1:]))
            marks.append(0)
        line += seg
        line.append(uv(*STOPS[b][1:]))
        marks.append(len(line) - 1)
    return line, marks


def simplify(pts, marks, tol=1.2):
    keep = set(marks) | {0, len(pts) - 1}

    def rdp(i, j):
        if j <= i + 1:
            return
        (x0, y0), (x1, y1) = pts[i], pts[j]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1e-9
        best, k = -1, None
        for m in range(i + 1, j):
            d = abs(dy * (pts[m][0] - x0) - dx * (pts[m][1] - y0)) / n
            if d > best:
                best, k = d, m
        if best > tol:
            keep.add(k)
            rdp(i, k)
            rdp(k, j)

    s = sorted(keep)
    for a, b in zip(s, s[1:]):
        rdp(a, b)
    idx = sorted(keep)
    return [pts[i] for i in idx], [idx.index(m) for m in marks]


def towers(min_h=45):
    out = []
    for e in load('bldg'):
        t = e.get('tags', {})
        h = None
        if 'height' in t:
            m = re.match(r'[\d.]+', t['height'])
            h = float(m.group()) if m else None
        elif 'building:levels' in t:
            m = re.match(r'[\d.]+', t['building:levels'])
            h = float(m.group()) * 3.4 if m else None
        g = e.get('geometry') or next((m['geometry'] for m in e.get('members', []) if m.get('role') == 'outer' and m.get('geometry')), None)
        if not h or h < min_h or not g or len(g) < 3:
            continue
        pts = [uv(p['lon'], p['lat']) for p in g]
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        out.append(dict(name=t.get('name', ''), h=round(h, 1), pts=[[round(u, 1), round(v, 1)] for u, v in pts]))
    return out


def compose():
    """Night map for the current view: (base, lit) as float RGB arrays."""
    print(f'  view {TW} x {TH}, {M_PER_PX:.1f} m per px')
    z = elevation()
    hs = hillshade(z)
    low, high = float(np.percentile(z, 2)), float(np.percentile(z, 99.5))
    zn = np.clip((z - low) / max(high - low, 1), 0, 1)
    # night desert: cool slate relief, a touch warmer on the valley floor
    dark, lite = colour('#07090d'), colour('#3a4658')
    base = dark + (lite - dark) * (hs[..., None] ** 1.6) * (0.55 + 0.45 * zn[..., None])
    base = base * (1 - 0.18 * (1 - zn[..., None])) + colour('#120d08') * 0.18 * (1 - zn[..., None])
    wm = water_mask()
    soft = blur(wm, 1.2 * Z)
    shore = np.clip((np.abs(np.gradient(soft, axis=0)) + np.abs(np.gradient(soft, axis=1))) * 3 * Z, 0, 1)
    deep = colour('#04162a') * (0.8 + 0.4 * blur(wm, 18 * Z)[..., None])
    base = base * (1 - wm[..., None]) + deep * wm[..., None]
    base = screen(base, shore * 0.55, colour('#3f8fd0'))

    Ls = line_layers()
    sodium, warm, hot, glass = colour('#ff8a2a'), colour('#ffc98a'), colour('#fff2dc'), colour('#ffd7a8')
    lit = base.copy()
    lit = screen(lit, np.clip(blur(Ls['minor'], 7 * Z) * 1.4, 0, 1) * 0.55, sodium)    # the city glow
    lit = screen(lit, Ls['minor'] * 0.55, sodium)
    lit = screen(lit, np.clip(blur(Ls['bldg'], 10 * Z) * 2, 0, 1) * 0.35, glass)       # casino glow round the Strip
    lit = screen(lit, Ls['bldg'] * 0.35, glass)
    lit = screen(lit, np.clip(blur(Ls['art'], 4 * Z) * 1.6, 0, 1) * 0.6, warm)
    lit = screen(lit, Ls['art'] * 0.9, warm)
    lit = screen(lit, np.clip(blur(Ls['hwy'], 6 * Z) * 1.8, 0, 1) * 0.7, hot)
    lit = screen(lit, Ls['hwy'], hot)
    return base, lit


def save(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, name), quality=90)
    print('wrote', name)


def main():
    os.makedirs(OUT, exist_ok=True)
    set_view(*VALLEY)
    base, lit = compose()
    save(base, 'base.jpg')
    save(lit, 'lit.jpg')

    line, marks = route()
    line, marks = simplify(line, marks)
    tw = towers()
    stops = [dict(name=n, u=round(uv(lo, la)[0], 1), v=round(uv(lo, la)[1], 1)) for n, lo, la in STOPS]
    data = dict(w=TW, h=TH, m_per_px=round(M_PER_PX, 2), bbox=[LON0, LAT0, LON1, LAT1], city=CITY, stops=stops,
                route=[[round(u, 1), round(v, 1)] for u, v in line], route_marks=marks, towers=tw,
                credit='© OpenStreetMap contributors')
    json.dump(data, open(os.path.join(OUT, 'data.json'), 'w'))
    print(f'wrote data.json: route {len(line)} points, {len(tw)} towers')

    # sharp city centre for the close camera: valley px CITY, 4x the detail
    (lon0, lat1), (lon1, lat0) = lonlat(*CITY[:2]), lonlat(*CITY[2:])
    set_view(lon0, lat0, lon1, lat1, 4 * (CITY[2] - CITY[0]))
    _, hd = compose()
    save(hd, 'city_hd.jpg')

    # pickup tile for the asset board: street level, ~3 km square, the pickup dead centre
    _, lon, lat = STOPS[0]
    half_lon = 1600 / (111320 * math.cos(math.radians(lat)))
    half_lat = half_lon * math.cos(math.radians(lat))
    set_view(lon - half_lon, lat - half_lat, lon + half_lon, lat + half_lat, 1000)
    _, tile = compose()
    save(tile, 'pickup_tile.jpg')


if __name__ == '__main__':
    main()
