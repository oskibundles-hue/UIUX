"""Service-word treatments for the spec run.

The stock chip (`build_overlays.badge`) sets the service inside a rounded box
with a red border. It reads as a UI element sitting on top of the film rather
than as part of it, and four of them in a row make the ad look like a form.

These are the alternatives. None of them puts the words in a container: the
type is the graphic, and the only furniture is a rule, a numeral or a bar that
belongs to the brand already. Each is a different LAYOUT, not a restyle of the
same one, so a set of ads can be told apart at a glance.

    rule    word over a red rule, low-left. Quiet; lets footage carry.
    index   numeral hard left, word hard right, hairline between them.
    tab     slim red bar up the left edge, word rotated inside it.
    panel   frosted glass: the picture behind the words is blurred in place,
            so the panel is made OF the footage instead of sitting on it.

All return a full-canvas RGBA layer, so the caller composites at 0,0 and the
layout owns its own position in frame.
"""
from PIL import Image, ImageDraw

import fd_brand as B
import fd_render as R

SAFE = B.SAFE_ZONES_9X16


def _canvas(canvas):
    return Image.new("RGBA", B.CANVASES[canvas], (0, 0, 0, 0))


def _scrim(im, top, height, strength=140):
    """A soft vertical gradient so type survives a bright frame.

    Drawn as its own layer and alpha-composited, because drawing straight onto
    the canvas would punch a hard edge where the gradient ends.
    """
    w, _ = im.size
    band = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    for y in range(height):
        # ease in and out so neither edge of the band is visible
        t = y / max(1, height - 1)
        a = int(strength * (1 - abs(2 * t - 1)) ** 0.7)
        d.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    im.alpha_composite(band, (0, top))


def rule(canvas, label, kicker="INCLUDED", tone="dark"):
    """Word over a red rule, sitting low-left.

    The rule is the whole device: it is the same red the stripe uses, it is
    exactly as wide as the word it underlines, and it gives the type a base to
    sit on so it does not float.
    """
    im = _canvas(canvas)
    W, H = im.size
    x = int(W * SAFE["left"])
    ink = B.WHITE if tone == "dark" else B.BLACK

    word = R.text(label, 92, ink, tracking=0.045)
    kick = R.text(kicker, 30, B.RED, tracking=0.30) if kicker else None

    block_h = word.height + 26 + (kick.height + 20 if kick else 0)
    top = int(H * 0.545)
    _scrim(im, top - 90, block_h + 190, 150)

    y = top
    if kick:
        R.paste(im, kick, x + 3, y)
        y += kick.height + 20
    R.paste(im, R.with_shadow(word), x, y)
    y += word.height + 26

    d = ImageDraw.Draw(im)
    d.rectangle([x, y, x + word.width, y + 9], fill=B.rgb(B.RED) + (255,))
    return im


def index(canvas, label, n, total, tone="dark"):
    """Numeral hard left, word hard right, a hairline running between them.

    Reads as a line off a spec sheet rather than a caption. The counter is
    honest furniture - it tells the viewer how many more of these are coming,
    which is the thing a run of chips never says.
    """
    im = _canvas(canvas)
    W, H = im.size
    ink = B.WHITE if tone == "dark" else B.BLACK
    x0 = int(W * SAFE["left"])
    x1 = W - int(W * SAFE["right"])

    num = R.text(f"{n:02d}", 78, B.RED, tracking=0.02)
    word = R.text(label, 74, ink, tracking=0.05)
    of = R.text(f"/{total:02d}", 30, ink, tracking=0.14)

    top = int(H * 0.555)
    _scrim(im, top - 80, word.height + 210, 150)

    base = top + word.height          # shared baseline
    R.paste(im, num, x0, base, anchor="lb")
    R.paste(im, of, x0 + num.width + 10, base - 6, anchor="lb")
    R.paste(im, R.with_shadow(word), x1, base, anchor="rb")

    d = ImageDraw.Draw(im)
    y = top - 26
    d.line([(x0, y), (x1, y)], fill=B.rgb(B.WHITE) + (70,), width=2)
    # a red tick under the numeral, so the eye starts at the left
    d.rectangle([x0, base + 20, x0 + num.width, base + 27],
                fill=B.rgb(B.RED) + (255,))
    return im


def tab(canvas, label, tone="dark"):
    """A slim red bar up the left edge with the word rotated inside it.

    Borrowed from the dealer templates: the vertical tab reads as a section
    marker rather than a caption, so it can hold for longer without feeling
    like something is being sold at you. It also leaves the whole frame clear,
    which is the point on footage this good.
    """
    im = _canvas(canvas)
    W, H = im.size
    x = int(W * SAFE["left"])

    word = R.text(label, 64, B.WHITE, tracking=0.24)
    pad = 42
    bar_w = word.height + pad * 2
    bar_h = word.width + pad * 2

    bar = Image.new("RGBA", (word.width + pad * 2, word.height + pad * 2),
                    B.rgb(B.RED) + (255,))
    R.paste(bar, word, bar.width // 2, bar.height // 2, anchor="cm")
    bar = bar.rotate(90, expand=True)          # reads bottom-to-top

    y = int(H * 0.62) - bar_h // 2
    im.alpha_composite(bar, (x, max(int(H * SAFE["top"]), y)))

    # a white hairline down the outside edge of the bar, the same device the
    # title block uses to tie a mark to the frame
    d = ImageDraw.Draw(im)
    d.line([(x + bar_w + 12, y + 8), (x + bar_w + 12, y + bar_h - 8)],
           fill=B.rgb(B.WHITE) + (90,), width=2)
    return im


STYLES = {"rule": rule, "index": index, "tab": tab}


def build(style, canvas, label, n=1, total=1, tone="dark"):
    """Render one spec layer in the named style."""
    kick, lab = split_label(label)
    if style == "index":
        return index(canvas, lab, n, total, tone)
    if style == "tab":
        return tab(canvas, lab, tone)
    if style == "rule":
        return rule(canvas, lab, kicker=kick, tone=tone)
    if style == "panel":
        kick, lab = split_label(label)
        return panel(canvas, lab, kicker=kick, tone=tone)[0]
    raise ValueError(f"unknown spec style: {style}")


# ---------------------------------------------------------------- frosted

# One fixed rectangle for the whole run, so four specs read as one component
# changing its contents rather than four different objects. It stops short of
# x=904 because Instagram's action rail starts at 907.
PANEL_BOX = (54, 1104, 850, 210)


def split_label(text, default="INCLUDED"):
    """Pull an optional kicker off a spec value: "SERVICE|FULL CAR PPF".

    The kicker is what makes the hierarchy readable. A service and the things
    thrown in with it are not the same kind of thing, and a run of identically
    labelled panels says they are. "SERVICE" then "INCLUDED" says: this is the
    job, and this comes with it.
    """
    if "|" in text:
        kick, _, lab = text.partition("|")
        return kick.strip().upper(), lab.strip()
    return default, text


def panel(canvas, label, kicker="INCLUDED", tone="dark"):
    """Text for a frosted-glass panel, plus the rectangle to blur behind it.

    Returns (layer, box). The layer carries type only - no fill, no border.
    The panel itself is made by the render: that rectangle of the picture is
    cropped out, blurred, darkened and put back, so the car keeps moving
    behind the glass. A drawn plate cannot do that, and a bordered chip does
    the opposite - it announces itself as something stuck on top.
    """
    im = _canvas(canvas)
    x, y, w, h = PANEL_BOX
    pad = 34
    ink = B.WHITE if tone == "dark" else B.BLACK

    k = R.text(kicker, 26, B.RED, tracking=0.26)
    R.paste(im, k, x + pad, y + pad)

    word = R.fit_text(label, w - pad * 2, max_height=int(h * 0.44),
                      color=ink, tracking=0.03)
    R.paste(im, word, x + pad, y + pad + k.height + 20)

    # a short red rule along the panel's bottom edge, the only furniture
    d = ImageDraw.Draw(im)
    d.rectangle([x, y + h - 6, x + int(w * 0.30), y + h - 1],
                fill=B.rgb(B.RED) + (255,))
    return im, PANEL_BOX
