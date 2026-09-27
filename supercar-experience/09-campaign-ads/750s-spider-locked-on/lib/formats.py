"""
formats.py -- the placement versions of "ROOF DOWN": the approved 9:16 story, a 4:5 feed cut and a 1:1 square.

Every format is the SAME edit, plate, sky matte and sound. A placement version is a crop window of the 1080x1920
plate (rows y0 .. y0 + H, full width) per shot, re-composited so the vignette and grain sit on the new frame:

  9x16  1080x1920  the approved story ad, untouched.
  4x5   1080x1350  one window, y 228-1578 for every shot. Every 9:16 graphic already lives inside the SE story
                   safe zone (y 269-1536, 1267 rows), which fits the window with ~41 px to spare top and bottom, so
                   4:5 reuses the approved 9:16 front and mid layers unchanged: it IS the approved composition.
  1x1   1080x1080  window y 226-1306: the hook, offer and requirements panels land 54 px from the top and every
                   subject sits under them; the behind-the-car type (mid layer) and the sky matte fit as they are.
                   Exceptions: the badge shot (beat 4) uses y 450-1530 so the tracked brackets on the McLaren
                   speedmark (plate y 1365-1474) stay in frame. On the hook shots (beats 1-3) and the front 3/4 pass
                   (beat 14) the car drives toward the lens and its splitter reaches plate y ~1370, so the PICTURE
                   window drops to y 320-1400 while the graphics keep theirs (nothing there is tracked to the plate);
                   for that the square's hook panel is shorter (the lockup moves up onto the offer row). The hook and
                   the end card use the square's own front layer (front_1x1.html); every other frame composites
                   the approved 9:16 front layer itself.

Offsets are in plate pixels. `y0` / `beat_y0` place the graphics (front layer); `plate_y0` overrides the picture
(plate, sky matte and behind-car type) on the beats it names. `front` names the front.html layout of the format's
own front layer, used on the `own_front` frame ranges.
"""
import edl

_END0 = edl.fr(edl.T_END - 0.12)                     # the end card's scrim starts on this frame (front.html)

FORMATS = {
    '9x16': dict(w=1080, h=1920, y0=0, beat_y0={}, front='9x16', rate=(11500, 16000, 23000)),
    '4x5': dict(w=1080, h=1350, y0=228, beat_y0={}, front='9x16', rate=(8100, 11300, 16200)),
    '1x1': dict(w=1080, h=1080, y0=226, beat_y0={4: 450}, plate_y0={1: 320, 2: 320, 3: 320, 14: 320}, front='1x1',
                own_front=[(0, edl.beat(4)['i0']), (_END0, edl.NF)], rate=(6500, 9000, 13000)),
}
# delivery rate (average, max, buffer; kb/s) scales with the pixel count from the approved 9:16 delivery

# SHA-256 of the approved exports (delivery, master). build.py will not re-encode over them without --force.
APPROVED = {
    '9x16': ('22ddf49232086eb8d3856fc05760032d2a9385df77acf0c19eb3ee885e2ca544',
             '73762b7c7c59961b0a524b9fe607d65dc2b185336753389145dd1e26f03ba545'),
}

# ink must stay inside this box (output pixels) on every held frame; the 9:16 box is the SE story safe zone
SAFE = {
    '9x16': dict(x0=54, x1=907, y0=269, y1=1536),
    '4x5': dict(x0=54, x1=1026, y0=40, y1=1310),
    '1x1': dict(x0=54, x1=1026, y0=40, y1=1040),
}

_BEAT = {r['i']: r['beat'] for r in edl.build()}


def y0(fmt, i):
    """top row (plate pixels) of output frame i's graphics window (the front layer)"""
    F = FORMATS[fmt]
    return F['beat_y0'].get(_BEAT[i], F['y0'])


def plate_y0(fmt, i):
    """top row (plate pixels) of output frame i's picture window (plate, sky matte, behind-car type)"""
    return FORMATS[fmt].get('plate_y0', {}).get(_BEAT[i], y0(fmt, i))


def own_front(fmt, i):
    """True where frame i composites the format's own front layer rather than the approved 9:16 one"""
    F = FORMATS[fmt]
    return F['front'] != '9x16' and any(a <= i < b for a, b in F.get('own_front', []))


def front_dir(fmt, i):
    """the .work/ folder holding frame i's front layer"""
    return 'front_' + FORMATS[fmt]['front'] if own_front(fmt, i) else 'front'
