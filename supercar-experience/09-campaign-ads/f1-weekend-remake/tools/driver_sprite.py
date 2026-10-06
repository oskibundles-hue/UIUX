"""REV v2: the Supercar Experience pixel driver (helmet on), drawn from the approved 3D concept
(black suit, red side stripes, white SE patch, black helmet with a red centre stripe).

Each pose is built from simple shapes on a 26 x 36 grid, then outlined automatically, so every
pose shares the same helmet, suit and proportions. Writes src/driver_grids.ts (the grids the
animation uses) and, with --preview <png>, a contact sheet of every pose.

  uv run --no-project --with pillow python tools/driver_sprite.py [--preview out.png]
"""
import json, os, sys

W, H = 32, 37
CX = 13.0  # helmet centre line sits between columns 12 and 13

PAL = {
    'k': '#0B0B0C',  # outline
    'h': '#1C1C20',  # helmet shell
    'H': '#5C5C66',  # helmet gloss
    'r': '#E3242B',  # racing red
    'R': '#8E141A',  # red shade
    'v': '#1B2533',  # visor
    'V': '#7FA3CC',  # visor glint
    'e': '#F5F3EE',  # eyes
    'p': '#0B0B0C',  # pupil
    'b': '#2B2B31',  # suit
    'B': '#45454E',  # suit light
    'd': '#151518',  # suit shade
    'w': '#F5F3EE',  # SE patch
    'g': '#101012',  # gloves, belt
    'G': '#5A5A64',  # glove knuckle light
    's': '#0E0E10',  # boots
    'o': '#F5F3EE',  # sticker edge
}


def blank():
    return [['.'] * W for _ in range(H)]


def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(g, x, y, c)


def helmet(g, eyes='open', top=1):
    cy, rx, ry = top + 7.0, 8.2, 7.6
    for y in range(top, top + 14):
        for x in range(W):
            if ((x + 0.5 - CX) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                put(g, x, y, 'h')
    # gloss arc, upper left
    for (x, y) in [(7, top + 2), (8, top + 1), (9, top + 1), (6, top + 3), (6, top + 4), (10, top + 1)]:
        put(g, x, y, 'H')
    # red centre stripe over the crown
    for y in range(top, top + 5):
        put(g, 12, y, 'r'); put(g, 13, y, 'r')
    # chin stripe
    for y in range(top + 11, top + 14):
        put(g, 12, y, 'r'); put(g, 13, y, 'r')
    # visor with a dark rim
    vx0, vx1, vy0, vy1 = 7, 18, top + 5, top + 9
    rect(g, vx0 - 1, vy0 - 1, vx1 + 1, vy1 + 1, 'k')
    rect(g, vx0, vy0, vx1, vy1, 'v')
    for (x, y) in [(vx0 - 1, vy0 - 1), (vx1 + 1, vy0 - 1), (vx0 - 1, vy1 + 1), (vx1 + 1, vy1 + 1)]:
        put(g, x, y, 'h')
    put(g, vx0 + 1, vy0, 'V'); put(g, vx0 + 2, vy0, 'V'); put(g, vx0 + 1, vy0 + 1, 'V')
    put(g, vx1, vy1, 'V')
    ey = vy0 + 1
    for ex, inner in ((9, 10), (15, 15)):
        if eyes == 'open':
            rect(g, ex, ey - 1, ex + 1, ey + 1, 'e')
        elif eyes == 'blink':
            rect(g, ex - 1, ey + 1, ex + 2, ey + 1, 'e')
        elif eyes == 'happy':  # ^ ^
            put(g, ex, ey - 1, 'e'); put(g, ex + 1, ey - 1, 'e'); put(g, ex - 1, ey, 'e'); put(g, ex + 2, ey, 'e')
        elif eyes == 'look':  # glancing up and to the side
            rect(g, ex + 1, ey - 1, ex + 1, ey + 1, 'e'); put(g, ex, ey, 'e'); put(g, ex, ey + 1, 'e')


def torso(g, top=15):
    rect(g, 8, top, 17, top + 8, 'b')
    rect(g, 10, top - 1, 15, top - 1, 'b')  # collar under the helmet
    for y in range(top, top + 9):
        put(g, 8, y, 'r'); put(g, 17, y, 'r')  # side stripes
        put(g, 9, y, 'B')
    rect(g, 14, top + 2, 16, top + 3, 'w')  # SE patch
    rect(g, 8, top + 6, 17, top + 6, 'g')  # belt
    put(g, 12, top + 6, 'G'); put(g, 13, top + 6, 'G')
    for x in range(10, 16):
        put(g, x, top + 8, 'd')


def legs(g, top=24, tuck=0):
    # tuck > 0 lifts the boots (jump)
    h = 7 - tuck
    rect(g, 8, top, 12, top + h - 1, 'b')
    rect(g, 13, top, 17, top + h - 1, 'b')
    rect(g, 12, top, 13, top, 'b')
    put(g, 12, top + 1, '.'); put(g, 13, top + 1, '.')
    for y in range(top + 1, top + h):
        put(g, 12, y, '.'); put(g, 13, y, '.')
        put(g, 8, y, 'r'); put(g, 17, y, 'r')
    for y in range(top, top + h):
        put(g, 9, y, 'B') if y % 3 else None
    by = top + h
    rect(g, 7, by, 11, by + 1, 's'); rect(g, 14, by, 18, by + 1, 's')
    put(g, 7, by + 1, 'r'); put(g, 18, by + 1, 'r')  # red sole flash
    put(g, 8, by + 1, 'r'); put(g, 17, by + 1, 'r')


def arm_down(g, side, top=16):
    x0 = 5 if side == 'L' else 18
    rect(g, x0, top, x0 + 2, top + 6, 'b')
    for y in range(top, top + 7):
        put(g, x0 if side == 'L' else x0 + 2, y, 'r')
    rect(g, x0, top + 7, x0 + 2, top + 8, 'g')
    put(g, x0 + 1, top + 7, 'G')


def raised(g, side, top=16):
    # upper arm out from the shoulder, forearm straight up, well clear of the helmet
    if side == 'R':
        rect(g, 18, top, 25, top + 2, 'b'); rect(g, 23, top - 5, 25, top + 2, 'b'); sx = 25
    else:
        rect(g, 0, top, 7, top + 2, 'b'); rect(g, 0, top - 5, 2, top + 2, 'b'); sx = 0
    for y in range(top - 5, top + 3):
        put(g, sx, y, 'r')
    return 23 if side == 'R' else 0


def arm_thumb(g, top=16):
    x = raised(g, 'R', top)
    rect(g, x, top - 8, x + 2, top - 6, 'g'); put(g, x + 1, top - 7, 'G'); put(g, x + 2, top - 7, 'G')
    rect(g, x, top - 10, x, top - 9, 'g')  # thumb up


def arm_wave(g, phase=0, top=16):
    x = raised(g, 'R', top) + phase  # the open glove rocks one cell out and back
    rect(g, x, top - 9, x + 2, top - 6, 'g'); put(g, x + 1, top - 7, 'G')
    put(g, x, top - 10, 'g'); put(g, x + 2, top - 10, 'g')


def arm_hip(g, top=16):
    # hand on the hip, elbow out: the thinking stance
    rect(g, 18, top, 20, top + 1, 'b')
    rect(g, 20, top + 1, 22, top + 3, 'b')
    rect(g, 19, top + 3, 21, top + 4, 'b')
    for (x, y) in [(22, top + 1), (22, top + 2), (22, top + 3)]:
        put(g, x, y, 'r')
    rect(g, 17, top + 5, 19, top + 6, 'g'); put(g, 18, top + 5, 'G')


def arms_up(g, top=16):
    for side in ('L', 'R'):
        x = raised(g, side, top)
        rect(g, x, top - 8, x + 2, top - 6, 'g'); put(g, x + 1, top - 7, 'G')


def outline(g, ch='k'):
    out = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and g[yy][xx] != '.':
                    out[y][x] = ch
                    break
    return out


def layer(fn, *a, **k):
    g = blank()
    fn(g, *a, **k)
    g = [['.'] * W] + [['.', '.'] + r[:-2] for r in g[:-1]]  # margin for the outline and sticker edge
    return outline(g)


def stack(layers):
    g = blank()
    for L in layers:
        for y in range(H):
            for x in range(W):
                if L[y][x] != '.':
                    g[y][x] = L[y][x]
    return g


def pose(name):
    eyes = {'blink': 'blink', 'happy': 'happy', 'wave_a': 'happy', 'wave_b': 'happy', 'jump': 'happy', 'think': 'look'}.get(name, 'open')
    jump = name == 'jump'
    back, front = [], []
    if name in ('idle', 'blink'):
        back = [layer(arm_down, 'L'), layer(arm_down, 'R')]
    elif name in ('thumb', 'happy'):
        back = [layer(arm_down, 'L')]; front = [layer(arm_thumb)]
    elif name in ('wave_a', 'wave_b'):
        back = [layer(arm_down, 'L')]; front = [layer(arm_wave, 0 if name == 'wave_a' else 1)]
    elif name == 'think':
        back = [layer(arm_down, 'L'), layer(arm_hip)]
    elif name == 'jump':
        front = [layer(arms_up)]
    body = [layer(legs, top=23, tuck=2) if jump else layer(legs), layer(torso)]
    g = stack(body + back + [layer(helmet, eyes)] + front)
    g = outline(g, 'o')  # white sticker edge around the whole figure
    return [''.join(r) for r in g]


POSES = ['idle', 'blink', 'thumb', 'happy', 'wave_a', 'wave_b', 'think', 'jump']


def main():
    grids = {p: pose(p) for p in POSES}
    here = os.path.dirname(os.path.abspath(__file__))
    ts = os.path.join(here, '..', 'src', 'driver_grids.ts')
    with open(ts, 'w') as fh:
        fh.write('// generated by tools/driver_sprite.py, do not edit by hand\n')
        fh.write(f'export const DRIVER_PAL: Record<string, string> = {json.dumps(PAL, indent=1)};\n')
        fh.write(f'export const DRIVER: Record<string, string[]> = {json.dumps(grids, indent=1)};\n')
    print('wrote', os.path.relpath(ts))
    if '--preview' in sys.argv:
        from PIL import Image
        px = 12
        sheet = Image.new('RGB', (len(POSES) * (W * px + 20) + 20, H * px + 40), '#5a5a60')
        for i, p in enumerate(POSES):
            for y, row in enumerate(grids[p]):
                for x, c in enumerate(row):
                    if c == '.':
                        continue
                    col = PAL[c]
                    for yy in range(px):
                        for xx in range(px):
                            sheet.putpixel((20 + i * (W * px + 20) + x * px + xx, 20 + y * px + yy), tuple(int(col[j:j + 2], 16) for j in (1, 3, 5)))
        sheet.save(sys.argv[sys.argv.index('--preview') + 1])


if __name__ == '__main__':
    main()
