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
                   Two exceptions: the badge shot (beat 4) uses y 450-1530 so the tracked brackets on the McLaren
                   speedmark (plate y 1365-1474) stay in frame, and the end card is re-laid out for the square
                   (front.html#fmt=1x1: the call to action moves into a right-hand column beside the price, the two
                   requirement lines sit under the taillight).

Offsets are in plate pixels; `front` names the front.html layout a format renders with.
"""
import edl

FORMATS = {
    '9x16': dict(w=1080, h=1920, y0=0, beat_y0={}, front='9x16', rate=(11500, 16000, 23000)),
    '4x5': dict(w=1080, h=1350, y0=228, beat_y0={}, front='9x16', rate=(8100, 11300, 16200)),
    '1x1': dict(w=1080, h=1080, y0=226, beat_y0={4: 450}, front='1x1', rate=(6500, 9000, 13000)),
}
# delivery rate (average, max, buffer; kb/s) scales with the pixel count from the approved 9:16 delivery

# ink must stay inside this box (output pixels) on every held frame; the 9:16 box is the SE story safe zone
SAFE = {
    '9x16': dict(x0=54, x1=907, y0=269, y1=1536),
    '4x5': dict(x0=54, x1=1026, y0=40, y1=1310),
    '1x1': dict(x0=54, x1=1026, y0=40, y1=1040),
}

_BEAT = {r['i']: r['beat'] for r in edl.build()}


def y0(fmt, i):
    """top row (plate pixels) of output frame i's crop window"""
    F = FORMATS[fmt]
    return F['beat_y0'].get(_BEAT[i], F['y0'])
