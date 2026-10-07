"""Pixel side views of two real Supercar Experience Las Vegas cars, for the shot 7 thought bubble.

  evo    Lamborghini Huracán EVO, Verde green, roof up       ("Coupe?")
  m750   McLaren 750S Spider, graphite, gold wheels, top down  ("Spyder?")

Colours from the cars' own pages on supercarexp.vip (Las Vegas fleet, checked 2026-10-05). Same build as
tools/driver_sprite.py: simple shapes on a grid (nose to the right), shaded, then outlined automatically.
Proportions are the real ones at ~74 mm a cell (length, height, wheelbase, wheel size).

Writes src/car_grids.ts and, with --preview <png>, a contact sheet.

  uv run --no-project --with pillow python tools/car_sprites.py [--preview out.png]
"""
import json, math, os, sys

W, H = 66, 21
GROUND = 19.0   # tyre contact line
AXLE_Y = 14.4   # wheel centre

PAL = {
    'k': '#0B0B0C',  # outline
    't': '#1B1B1E',  # tyre
    'T': '#3C3C42',  # tyre sidewall light
    'x': '#141416',  # black trim, intakes, carbon
    'X': '#34353A',  # trim light
    'w': '#22303F',  # glass
    'W': '#9CC2E6',  # glass glint
    'e': '#F4F8FF',  # LED
    'r': '#E3242B',  # tail light
    'z': '#D7D2C7',  # ground shadow on the bubble
    # Huracán EVO, Verde
    'G': '#72C02C', 'L': '#C2F06A', 'D': '#3E7D16',
    's': '#8E9097', 'S': '#D8DADF',  # dark-silver rims
    # McLaren 750S, graphite, gold wheels
    'm': '#4E535B', 'M': '#8D949E', 'n': '#2C2F34',
    'u': '#B88A2E', 'U': '#F0CF78',
    'q': '#2A2A2E',  # seats
}


def blank():
    return [['.'] * W for _ in range(H)]


def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c


def inside(px, py, pts):
    hit = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def poly(g, pts, c, only=None):
    for y in range(H):
        for x in range(W):
            if inside(x + 0.5, y + 0.5, pts) and (only is None or g[y][x] in only):
                g[y][x] = c


def disc(g, cx, cy, r, c, only=None):
    for y in range(H):
        for x in range(W):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r and (only is None or g[y][x] in only):
                g[y][x] = c


def line(g, x0, y0, x1, y1, c, only=None):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * i / n
        xi, yi = int(x), int(y)
        if 0 <= xi < W and 0 <= yi < H and (only is None or g[yi][xi] in only):
            g[yi][xi] = c


def shade(g, base, hi, lo, lo_from):
    # top edge catches the light, the lower flank sits in shade
    for y in range(H):
        for x in range(W):
            if g[y][x] != base:
                continue
            if y == 0 or g[y - 1][x] == '.':
                g[y][x] = hi
            elif y >= lo_from:
                g[y][x] = lo


def wheel(g, cx, r, rim, rim_hi, spokes=5):
    cy = GROUND - r
    disc(g, cx, cy, r, 't')
    disc(g, cx, cy, r - 0.9, 'T')
    disc(g, cx, cy, r - 1.4, 'x')                  # dark barrel behind the spokes
    for k in range(spokes):
        a = -math.pi / 2 + k * 2 * math.pi / spokes
        line(g, cx, cy, cx + math.cos(a) * (r - 1.5), cy + math.sin(a) * (r - 1.5), rim)
    ring = [(x, y) for y in range(H) for x in range(W)
            if (r - 2.1) ** 2 < (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (r - 1.4) ** 2]
    for x, y in ring:                              # rim lip, lit along the top
        g[y][x] = rim_hi if y + 0.5 < cy - 1 else rim
    disc(g, cx, cy, 0.8, rim_hi)


def arch(g, cx, r):
    disc(g, cx, GROUND - r, r + 1.0, '.', only=set('GLDmMnx'))


def outline(g, ch='k'):
    out = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and g[yy][xx] not in '.z':
                    out[y][x] = ch
                    break
    return out


def ground(g, x0, x1):
    for x in range(x0, x1):
        if g[H - 1][x] == '.':
            g[H - 1][x] = 'z'


def evo():
    """Huracán EVO coupe: 4520 long, 1165 high, 2620 wheelbase, 20in wheels. Rear at x=2, nose at x=63."""
    g = blank()
    rx, fx, r = 14.0, 49.5, 4.7
    body = [(2.0, 17.0), (2.0, 10.2), (2.6, 8.9), (7.0, 8.6), (13.0, 7.8), (20.0, 6.2), (26.5, 4.2),
            (30.5, 3.3), (34.5, 3.4), (37.5, 4.2), (44.5, 9.3), (51.0, 10.5), (57.0, 11.7), (61.5, 12.9),
            (63.6, 13.9), (63.6, 15.2), (62.0, 16.6), (55.0, 17.2), (8.0, 17.4)]
    poly(g, body, 'G')
    arch(g, rx, r); arch(g, fx, r)
    shade(g, 'G', 'L', 'D', 14)
    # side glass: long triangle that tapers back into the rear haunch
    poly(g, [(37.2, 4.7), (42.6, 8.8), (31.0, 8.6), (23.5, 6.9), (27.6, 4.9), (31.0, 4.1)], 'w')
    line(g, 29.5, 4.6, 28.0, 7.6, 'x')            # quarter-glass divider
    put(g, 36, 5, 'W'); put(g, 37, 6, 'W'); put(g, 35, 5, 'W')
    # the big side intake ahead of the rear wheel
    poly(g, [(20.5, 9.2), (26.5, 9.5), (31.5, 12.6), (21.0, 13.4)], 'x')
    line(g, 21.5, 11.5, 28.5, 11.4, 'X')
    # crease from the front arch to the intake, sill, splitter, diffuser
    line(g, 31.5, 12.3, 43.5, 12.0, 'D', only='G')
    poly(g, [(20.0, 15.6), (43.6, 15.6), (43.6, 17.4), (20.0, 17.4)], 'x')
    poly(g, [(54.0, 16.4), (63.6, 15.3), (63.6, 16.6), (54.0, 17.4)], 'x')
    poly(g, [(2.0, 14.2), (8.4, 15.2), (8.4, 17.4), (2.0, 17.4)], 'x')
    poly(g, [(59.0, 14.2), (62.6, 14.4), (62.0, 15.4), (58.6, 15.3)], 'x')  # front intake
    line(g, 57.0, 12.6, 61.0, 13.4, 'e', only='GLD')  # Y-shaped LED, seen side-on
    put(g, 3, 10, 'r'); put(g, 3, 11, 'r'); put(g, 4, 10, 'r')            # tail light
    poly(g, [(40.6, 7.6), (43.4, 7.8), (43.0, 9.2), (40.6, 9.0)], 'G')    # mirror
    for x in (10, 13, 16):                         # engine-cover louvres
        put(g, x, 8 + (x < 12), 'D')
    wheel(g, rx, r, 's', 'S', 5); wheel(g, fx, r, 's', 'S', 5)
    g = outline(g)
    ground(g, 5, 61)
    return g


def m750():
    """750S Spider, roof down: 4569 long, 1196 high, 2670 wheelbase, 19/20in wheels. Rear at x=2, nose at x=64."""
    g = blank()
    rx, fx = 14.0, 50.2
    body = [(2.0, 16.8), (2.0, 9.6), (1.4, 8.4), (6.0, 7.9), (14.0, 7.1), (21.0, 6.1), (25.6, 5.2),
            (27.4, 5.4), (28.6, 8.4), (40.0, 8.4), (45.0, 9.3), (51.0, 10.3), (57.0, 11.4), (62.0, 12.6),
            (64.4, 13.6), (64.4, 15.0), (62.6, 16.4), (55.0, 17.2), (8.0, 17.4)]
    poly(g, body, 'm')
    arch(g, rx, 4.8); arch(g, fx, 4.6)
    shade(g, 'm', 'M', 'n', 14)
    # raked windscreen seen edge-on, roof stowed
    poly(g, [(36.8, 4.2), (39.2, 3.9), (45.0, 9.3), (42.0, 8.8)], 'w')
    put(g, 39, 5, 'W'); put(g, 40, 6, 'W')
    line(g, 39.6, 3.9, 45.0, 9.0, 'n', only='w')   # A-pillar on the leading edge
    poly(g, [(36.6, 3.7), (39.4, 3.5), (39.4, 4.4), (36.6, 4.6)], 'n')   # header rail
    # seat back and headrest in the open cabin
    poly(g, [(29.6, 8.6), (30.2, 6.2), (32.4, 5.8), (33.0, 8.6)], 'q')
    put(g, 31, 6, 'X')
    # flying-buttress tonneau: dark sail gap behind the headrest
    poly(g, [(26.0, 6.2), (16.0, 7.9), (16.0, 8.7), (26.4, 7.2)], 'n')
    # door scallop narrowing forward into the big intake ahead of the rear wheel
    poly(g, [(38.6, 11.4), (31.0, 10.0), (23.0, 9.8), (22.6, 13.4), (31.0, 13.2)], 'n')
    poly(g, [(22.8, 10.2), (26.6, 10.4), (26.6, 13.0), (22.8, 13.2)], 'x')
    # sill, splitter, big diffuser, active-wing lip
    poly(g, [(20.0, 15.6), (44.4, 15.6), (44.4, 17.4), (20.0, 17.4)], 'x')
    poly(g, [(55.0, 16.4), (64.4, 15.1), (64.4, 16.5), (55.0, 17.4)], 'x')
    poly(g, [(2.0, 13.4), (9.6, 14.8), (9.6, 17.4), (2.0, 17.4)], 'x')
    poly(g, [(1.0, 7.6), (7.0, 7.3), (7.0, 8.2), (1.0, 8.6)], 'x')
    # eye-socket headlight
    poly(g, [(56.4, 11.8), (61.6, 12.9), (61.2, 14.2), (57.2, 13.4)], 'x')
    line(g, 57.0, 12.2, 61.0, 13.1, 'e')
    put(g, 3, 9, 'r'); put(g, 3, 10, 'r'); put(g, 4, 9, 'r')
    wheel(g, rx, 4.8, 'u', 'U', 5); wheel(g, fx, 4.6, 'u', 'U', 5)
    g = outline(g)
    ground(g, 5, 62)
    return g


CARS = {'evo': evo, 'm750': m750}


def main():
    grids = {k: [''.join(r) for r in fn()] for k, fn in CARS.items()}
    here = os.path.dirname(os.path.abspath(__file__))
    ts = os.path.join(here, '..', 'src', 'car_grids.ts')
    with open(ts, 'w') as fh:
        fh.write('// generated by tools/car_sprites.py, do not edit by hand\n')
        fh.write(f'export const CAR_PAL: Record<string, string> = {json.dumps(PAL, indent=1)};\n')
        fh.write(f'export const CAR_GRIDS: Record<string, string[]> = {json.dumps(grids, indent=1)};\n')
    print('wrote', os.path.relpath(ts))
    if '--preview' in sys.argv:
        from PIL import Image
        px = 14
        sheet = Image.new('RGB', (W * px + 40, len(grids) * (H * px + 30) + 20), '#F5F3EE')
        for i, k in enumerate(grids):
            for y, row in enumerate(grids[k]):
                for x, c in enumerate(row):
                    if c == '.':
                        continue
                    col = tuple(int(PAL[c][j:j + 2], 16) for j in (1, 3, 5))
                    x0, y0 = 20 + x * px, 20 + i * (H * px + 30) + y * px
                    sheet.paste(col, (x0, y0, x0 + px, y0 + px))
        sheet.save(sys.argv[sys.argv.index('--preview') + 1])


if __name__ == '__main__':
    main()
