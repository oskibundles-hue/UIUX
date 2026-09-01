"""
Formula Dynamics Performance - shared rendering helpers.

Small, dependency-light utilities used by the overlay builders: logo loading
from the traced vectors, Bebas Neue text rendering with letter-spacing, and
the four-colour accent stripe.
"""

import io

import cairosvg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import fd_brand as B

_FONT_CACHE = {}


# --------------------------------------------------------------------------
# Logos
# --------------------------------------------------------------------------
def logo(stem, width=None, height=None):
    """Render a logo SVG to an RGBA image at an exact pixel size.

    `stem` is a file name in 02-logos/svg-vector without the extension,
    e.g. "fd-primary-horizontal--white".
    """
    path = B.LOGOS / "svg-vector" / f"{stem}.svg"
    kw = {}
    if width:
        kw["output_width"] = int(width)
    if height:
        kw["output_height"] = int(height)
    png = cairosvg.svg2png(url=str(path), **kw)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def logo_aspect(stem):
    """Width / height of a logo lockup."""
    im = logo(stem, width=400)
    return im.width / im.height


# --------------------------------------------------------------------------
# Type
# --------------------------------------------------------------------------
def font(size):
    key = int(size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(str(B.FONT_BEBAS), key)
    return _FONT_CACHE[key]


def text(msg, size, color=B.WHITE, tracking=0.0, italic=0.0):
    """Render a line of Bebas Neue to a tightly-cropped RGBA image.

    tracking - extra letter spacing as a fraction of the font size.
    italic   - shear factor; approximates the brand's italic accent face.
               The real accent typeface (Neuropol X) is commercially licensed
               and is not bundled, see 07-fonts/FONTS.md.

    The canvas is sized from the font's own ascent/descent metrics so tall
    glyphs are never clipped, then cropped back to the inked pixels.
    """
    msg = msg.upper()
    f = font(size)
    space = size * tracking

    # Measure on a throwaway canvas so the real one is guaranteed big enough.
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    widths = [probe.textlength(ch, font=f) for ch in msg]
    total = sum(widths) + space * max(0, len(msg) - 1)

    ascent, descent = f.getmetrics()
    pad = int(size * 0.35) + 2
    canvas = Image.new(
        "RGBA",
        (int(total) + pad * 2, ascent + descent + pad * 2),
        (0, 0, 0, 0),
    )
    d = ImageDraw.Draw(canvas)
    x = pad
    for ch, w in zip(msg, widths):
        d.text((x, pad + ascent), ch, font=f,
               fill=B.rgb(color) + (255,), anchor="ls")
        x += w + space

    if italic:
        w, h = canvas.size
        shift = int(h * italic)
        canvas = canvas.transform(
            (w + shift, h), Image.AFFINE, (1, italic, 0, 0, 1, 0),
            resample=Image.BICUBIC,
        )

    box = canvas.getbbox()
    return canvas.crop(box) if box else canvas


def with_shadow(layer, blur=None, offset=None, opacity=170):
    """Drop a soft shadow behind a layer so type stays legible over footage.

    Preferred over a visible scrim box, which reads as a smudge on video.
    """
    blur = blur if blur is not None else max(3, layer.height * 0.06)
    dx, dy = offset if offset else (0, max(2, int(layer.height * 0.035)))
    grow = int(blur * 3)

    canvas = Image.new("RGBA",
                       (layer.width + grow * 2, layer.height + grow * 2),
                       (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    solid = Image.new("RGBA", layer.size, (0, 0, 0, opacity))
    shadow.paste(solid, (grow + dx, grow + dy), layer)
    canvas = Image.alpha_composite(canvas,
                                   shadow.filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(layer, (grow, grow))
    return canvas


def fit_text(msg, target_width, max_height=None, **kw):
    """Render text at the font size that naturally lands on `target_width`.

    The point size is solved first and the glyphs are then rasterised once at
    that size, so nothing is upscaled and the edges stay crisp. `max_height`
    stops short words (\"THE\", \"FD\") from ballooning when they are set to the
    same measure as a long one.
    """
    probe = text(msg, 100, **kw)
    if probe.width == 0 or probe.height == 0:
        return probe

    size = 100.0 * target_width / probe.width
    if max_height:
        size = min(size, 100.0 * max_height / probe.height)

    im = text(msg, max(8, round(size)), **kw)

    # Rounding the point size leaves a sub-percent error; correct it so
    # stacked lines align exactly.
    if max_height is None and im.width != target_width:
        h = max(1, round(im.height * target_width / im.width))
        im = im.resize((int(target_width), h), Image.LANCZOS)
    return im


# --------------------------------------------------------------------------
# Brand furniture
# --------------------------------------------------------------------------
def accent_stripe(width, height):
    """The four-colour racing stripe, left to right, as an RGBA image."""
    im = Image.new("RGBA", (int(width), max(1, int(height))), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 0.0
    for hex_color, share in B.ACCENT_STRIPE:
        w = width * share
        d.rectangle([x, 0, x + w, height], fill=B.rgb(hex_color) + (255,))
        x += w
    return im


def paste(base, layer, x, y, anchor="lt"):
    """Composite `layer` onto `base`; anchor is horizontal+vertical keyword.

    Horizontal: l(eft) c(entre) r(ight).  Vertical: t(op) m(iddle) b(ottom).
    """
    ax, ay = anchor[0], anchor[1]
    if ax == "c":
        x -= layer.width // 2
    elif ax == "r":
        x -= layer.width
    if ay == "m":
        y -= layer.height // 2
    elif ay == "b":
        y -= layer.height
    base.alpha_composite(layer, (int(x), int(y)))
    return base


def frame(canvas_key, fill=None):
    """A blank frame for one of the standard video canvases."""
    w, h = B.CANVASES[canvas_key]
    rgba = (0, 0, 0, 0) if fill is None else B.rgb(fill) + (255,)
    return Image.new("RGBA", (w, h), rgba)


def save(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)
    return path
