"""
Layout treatments for the Aventador ad.

Same footage, same cut, same copy, same brand furniture — a different way of
arranging it on the frame. A cue file picks one with "layoutStyle".

Each layout supplies four draw functions and gets a `ctx` carrying the cue, the
frame geometry and the kit modules. The CTA caption and end card are full-frame
kit overlays and are shared by every layout, so they are not defined here.

    backdrop(ctx, base, t)   scrim / panel — anything behind the type
    identity(ctx, base, t)   who this is: lockup, mark, ticker
    hook(ctx, base, t)       the opening line
    build(ctx, base, t)      the build sheet

Adding a layout means adding one entry to LAYOUTS. Nothing else changes.
"""

from PIL import Image

import fd_brand as B
import fd_hud as HUD
import fd_render as R


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------


def _fit_lines(ctx, lines, width, max_h_frac=0.10, tracking=0.02, shadow=True):
    key = ("fit", tuple(lines), width, max_h_frac)
    if key not in ctx.cache:
        out = []
        for ln in lines:
            im = R.fit_text(ln, width, max_height=round(ctx.H * max_h_frac),
                            tracking=tracking)
            out.append(R.with_shadow(im, opacity=190) if shadow else im)
        ctx.cache[key] = out
    return ctx.cache[key]


def _vscrim(ctx, top, height, strength, blur=0.05):
    key = ("scrim", top, height, strength, blur)
    if key not in ctx.cache:
        ctx.cache[key] = HUD._scrim(ctx.CANVAS, top, height, strength, blur)
    return ctx.cache[key]


def _ticker(ctx):
    if "ticker" not in ctx.cache:
        ctx.cache["ticker"] = HUD.ticker(ctx.CANVAS, ctx.CUE["ticker"])
    return ctx.cache["ticker"]


# ===========================================================================
# 1. HUD — the original. Bracketed title block bottom-left, ticker under it,
#    left-aligned type in the mid band.
# ===========================================================================


def hud_backdrop(ctx, base, t):
    o = max(ctx.beat(t, "hook")[0], ctx.beat(t, "build")[0])
    if o > 0:
        base.alpha_composite(ctx.faded(_vscrim(ctx, 0.355, 0.31, 205), o))


def hud_identity(ctx, base, t):
    if "title" not in ctx.cache:
        ctx.cache["title"] = HUD.title_block(ctx.CANVAS, ctx.CUE["car"], ctx.CUE["build"])
    o, p = ctx.beat(t, "title", 0.55, 0.55)
    if o > 0:
        R.paste(base, ctx.faded(ctx.cache["title"], o), int((1 - p) * -30), 0)
    o, _ = ctx.beat(t, "ticker", 0.55, 0.55)
    if o > 0:
        base.alpha_composite(ctx.faded(_ticker(ctx), o))


def hud_hook(ctx, base, t):
    o, _ = ctx.beat(t, "hook")
    if o <= 0:
        return
    start = ctx.CUE["beats"]["hook"][0]
    y = ctx.BAND_TOP
    for i, ln in enumerate(_fit_lines(ctx, ctx.CUE["hook"], ctx.X1 - ctx.X0)):
        lp = ctx.ease_out((t - start - i * 0.14) / 0.6)
        if lp > 0:
            R.paste(base, ctx.faded(ln, o * lp), ctx.X0 - 40,
                    int(y - (1 - lp) * 36))
        y += ln.height - round(ctx.H * 0.012)


def hud_build(ctx, base, t):
    o, _ = ctx.beat(t, "build")
    if o <= 0:
        return
    start = ctx.CUE["beats"]["build"][0]
    top = ctx.BAND_TOP
    head = R.text(ctx.CUE["buildHeading"], 34, B.RED, tracking=0.16)
    R.paste(base, ctx.faded(R.with_shadow(head), o), ctx.X0 - 20, top - 20)

    stripe = R.accent_stripe(round((ctx.X1 - ctx.X0) * ctx.ease_out((t - start) / 0.7)), 8)
    if stripe.width > 2:
        R.paste(base, ctx.faded(stripe, o), ctx.X0, top + 54)

    row_h = round(ctx.H * 0.052)
    for i, (idx, label, sub) in enumerate(ctx.CUE["buildRows"]):
        rp = ctx.ease_out((t - start - 0.16 - i * 0.15) / 0.6)
        if rp <= 0:
            continue
        y = top + round(ctx.H * 0.048) + i * row_h + (1 - rp) * 20
        ro = o * rp
        R.paste(base, ctx.faded(R.with_shadow(R.text(idx, 28, B.RED, tracking=0.14)), ro),
                ctx.X0 - 20, y + 16)
        R.paste(base, ctx.faded(R.with_shadow(R.text(label, 62, B.WHITE, tracking=0.03)), ro),
                ctx.X0 + 44, y - 12)
        R.paste(base, ctx.faded(R.with_shadow(R.text(sub, 27, B.WHITE, tracking=0.12)), ro * 0.72),
                ctx.X1 + 20, y + 18, "rt")
        rule = Image.new("RGBA", (ctx.X1 - ctx.X0, 2), B.rgb(B.WHITE) + (58,))
        R.paste(base, ctx.faded(rule, ro), ctx.X0, y + row_h - 14)


# ===========================================================================
# 2. CENTRED — poster treatment. Everything on the vertical axis, the mark
#    above the hook, the lockup centred at the foot. Quieter, more editorial.
# ===========================================================================

CX = 0.5


def centred_backdrop(ctx, base, t):
    o = max(ctx.beat(t, "hook")[0], ctx.beat(t, "build")[0])
    if o > 0:
        base.alpha_composite(ctx.faded(_vscrim(ctx, 0.24, 0.46, 190, 0.06), o))


def centred_identity(ctx, base, t):
    cx = ctx.W * CX
    o, p = ctx.beat(t, "title", 0.55, 0.55)
    if o > 0:
        y = round(ctx.H * 0.845) + int((1 - p) * 20)
        name = R.text(ctx.CUE["car"], 68, B.WHITE, tracking=0.06)
        R.paste(base, ctx.faded(R.with_shadow(name), o), cx, y, "ct")
        sub = R.text(ctx.CUE["build"], 30, B.WHITE, tracking=0.20)
        R.paste(base, ctx.faded(R.with_shadow(sub), o * 0.8), cx, y + 62, "ct")
        stripe = R.accent_stripe(round(ctx.W * 0.30), 8)
        R.paste(base, ctx.faded(stripe, o), cx - stripe.width // 2, y + 108)


def centred_hook(ctx, base, t):
    o, _ = ctx.beat(t, "hook")
    if o <= 0:
        return
    cx = ctx.W * CX
    start = ctx.CUE["beats"]["hook"][0]
    col = round(ctx.W * 0.80)

    mark_p = ctx.ease_out((t - start) / 0.7)
    if mark_p > 0:
        if "mark" not in ctx.cache:
            ctx.cache["mark"] = R.logo("fd-icon-mark-only--white", width=96)
        R.paste(base, ctx.faded(ctx.cache["mark"], o * mark_p),
                cx, round(ctx.H * 0.315) - (1 - mark_p) * 18, "ct")

    y = round(ctx.H * 0.395)
    bottom = y
    for i, ln in enumerate(_fit_lines(ctx, ctx.CUE["hook"], col, 0.085)):
        lp = ctx.ease_out((t - start - 0.12 - i * 0.14) / 0.6)
        if lp > 0:
            R.paste(base, ctx.faded(ln, o * lp), cx, int(y - (1 - lp) * 28), "ct")
        bottom = y + ln.height
        y += ln.height - round(ctx.H * 0.014)

    rp = ctx.ease_out((t - start - 0.35) / 0.7)
    if rp > 0:
        w = round(ctx.W * 0.16 * rp)
        bar = Image.new("RGBA", (max(2, w), 5), B.rgb(B.RED) + (255,))
        R.paste(base, ctx.faded(bar, o), cx - bar.width // 2, bottom - 6)


def centred_build(ctx, base, t):
    o, _ = ctx.beat(t, "build")
    if o <= 0:
        return
    cx = ctx.W * CX
    start = ctx.CUE["beats"]["build"][0]
    top = round(ctx.H * 0.325)

    head = R.text(ctx.CUE["buildHeading"], 30, B.RED, tracking=0.22)
    R.paste(base, ctx.faded(R.with_shadow(head), o), cx, top, "ct")
    sw = round(ctx.W * 0.30 * ctx.ease_out((t - start) / 0.7))
    if sw > 2:
        stripe = R.accent_stripe(sw, 7)
        R.paste(base, ctx.faded(stripe, o), cx - stripe.width // 2, top + 74)

    row_h = round(ctx.H * 0.062)
    for i, (idx, label, sub) in enumerate(ctx.CUE["buildRows"]):
        rp = ctx.ease_out((t - start - 0.16 - i * 0.15) / 0.6)
        if rp <= 0:
            continue
        y = top + round(ctx.H * 0.062) + i * row_h + (1 - rp) * 18
        ro = o * rp
        R.paste(base, ctx.faded(R.with_shadow(R.text(label, 58, B.WHITE, tracking=0.05)), ro),
                cx, y, "ct")
        R.paste(base, ctx.faded(R.with_shadow(R.text(sub, 25, B.WHITE, tracking=0.16)), ro * 0.66),
                cx, y + 52, "ct")


# ===========================================================================
# 3. PANEL — a solid card in the lower half that swaps its contents. Ignores
#    the footage underneath entirely, so it survives any shot. The most
#    legible option and the safest on busy or bright material.
# ===========================================================================

PANEL_TOP = 0.475
PANEL_H = 0.315


def panel_backdrop(ctx, base, t):
    o = max(ctx.beat(t, "hook", 0.4, 0.4)[0], ctx.beat(t, "build", 0.4, 0.4)[0])
    if o <= 0:
        return
    if "panel" not in ctx.cache:
        card = Image.new("RGBA", (ctx.W, ctx.H), (0, 0, 0, 0))
        y0 = round(ctx.H * PANEL_TOP)
        h = round(ctx.H * PANEL_H)
        card.paste(Image.new("RGBA", (ctx.W, h), (5, 5, 6, 242)), (0, y0))
        card.paste(Image.new("RGBA", (ctx.W, 6), B.rgb(B.RED) + (255,)), (0, y0))
        stripe = R.accent_stripe(ctx.W, 7)
        card.alpha_composite(stripe, (0, y0 + h - 7))
        ctx.cache["panel"] = card
    base.alpha_composite(ctx.faded(ctx.cache["panel"], o))


def panel_identity(ctx, base, t):
    o, p = ctx.beat(t, "title", 0.55, 0.55)
    if o > 0:
        y = round(ctx.H * 0.845)
        if "mark" not in ctx.cache:
            ctx.cache["mark"] = R.logo("fd-icon-mark-only--white", width=54)
        x = ctx.X0 + int((1 - p) * -24)
        R.paste(base, ctx.faded(ctx.cache["mark"], o), x, y - 4)
        name = R.text(ctx.CUE["car"], 52, B.WHITE, tracking=0.06)
        R.paste(base, ctx.faded(R.with_shadow(name), o), x + 74, y)
        sub = R.text(ctx.CUE["build"], 26, B.WHITE, tracking=0.18)
        R.paste(base, ctx.faded(R.with_shadow(sub), o * 0.8), x + 74, y + 46)
    o, _ = ctx.beat(t, "ticker", 0.55, 0.55)
    if o > 0:
        base.alpha_composite(ctx.faded(_ticker(ctx), o))


def _panel_inner_top(ctx):
    return round(ctx.H * PANEL_TOP) + round(ctx.H * 0.045)


def panel_hook(ctx, base, t):
    o, _ = ctx.beat(t, "hook")
    if o <= 0:
        return
    start = ctx.CUE["beats"]["hook"][0]
    y = _panel_inner_top(ctx)
    for i, ln in enumerate(_fit_lines(ctx, ctx.CUE["hook"], ctx.X1 - ctx.X0, 0.075,
                                      shadow=False)):
        lp = ctx.ease_out((t - start - i * 0.14) / 0.6)
        if lp > 0:
            R.paste(base, ctx.faded(ln, o * lp), ctx.X0 - int((1 - lp) * 26), y)
        y += ln.height + round(ctx.H * 0.004)


def panel_build(ctx, base, t):
    """Two columns of two — the panel is wide and short, so rows would crowd."""
    o, _ = ctx.beat(t, "build")
    if o <= 0:
        return
    start = ctx.CUE["beats"]["build"][0]
    top = _panel_inner_top(ctx) - 8
    head = R.text(ctx.CUE["buildHeading"], 28, B.RED, tracking=0.20)
    R.paste(base, ctx.faded(head, o), ctx.X0, top)

    col_w = (ctx.X1 - ctx.X0) // 2
    for i, (idx, label, sub) in enumerate(ctx.CUE["buildRows"]):
        rp = ctx.ease_out((t - start - 0.18 - i * 0.13) / 0.55)
        if rp <= 0:
            continue
        cx = ctx.X0 + (i % 2) * col_w
        cy = top + round(ctx.H * 0.036) + (i // 2) * round(ctx.H * 0.072)
        cy += (1 - rp) * 14
        ro = o * rp
        R.paste(base, ctx.faded(R.text(idx, 24, B.RED, tracking=0.14), ro), cx, cy + 8)
        R.paste(base, ctx.faded(R.text(label, 50, B.WHITE, tracking=0.03), ro), cx + 46, cy)
        R.paste(base, ctx.faded(R.text(sub, 23, B.WHITE, tracking=0.13), ro * 0.62),
                cx + 46, cy + 46)


# ===========================================================================
# 4. RAIL — the four-colour stripe stood on end down the left edge, type
#    hanging off it. Uses the brand furniture as structure rather than trim.
# ===========================================================================

RAIL_X = 0.072
RAIL_TOP = 0.255
RAIL_H = 0.417        # ends just above the lockup at 0.688


def rail_backdrop(ctx, base, t):
    o = max(ctx.beat(t, "hook")[0], ctx.beat(t, "build")[0])
    if o <= 0:
        return
    base.alpha_composite(ctx.faded(_vscrim(ctx, 0.235, 0.50, 175, 0.06), o))
    p = ctx.ease_out((t - min(ctx.CUE["beats"]["hook"][0],
                              ctx.CUE["beats"]["build"][0])) / 0.8)
    h = round(ctx.H * RAIL_H * max(0.0, min(1.0, p)))
    if h < 4:
        return
    # Solid red, not the four-colour stripe: the stripe carries a black segment
    # that vanishes on dark footage, so stood on end it reads as a broken line
    # rather than as brand furniture. The stripe still caps the rail head.
    x = round(ctx.W * RAIL_X)
    y = round(ctx.H * RAIL_TOP)
    R.paste(base, ctx.faded(Image.new("RGBA", (10, h), B.rgb(B.RED) + (255,)), o), x, y)
    cap = ctx.ease_out((t - min(ctx.CUE["beats"]["hook"][0],
                                ctx.CUE["beats"]["build"][0]) - 0.25) / 0.6)
    if cap > 0:
        w = round(ctx.W * 0.14 * cap)
        R.paste(base, ctx.faded(R.accent_stripe(max(2, w), 7), o), x, y - 20)


def rail_identity(ctx, base, t):
    o, p = ctx.beat(t, "title", 0.55, 0.55)
    if o > 0:
        x = round(ctx.W * RAIL_X)
        y = round(ctx.H * 0.688)      # above the ticker at 0.775
        if "mark" not in ctx.cache:
            ctx.cache["mark"] = R.logo("fd-icon-mark-only--white", width=50)
        R.paste(base, ctx.faded(ctx.cache["mark"], o), x + int((1 - p) * -20), y)
        name = R.text(ctx.CUE["car"], 46, B.WHITE, tracking=0.08)
        R.paste(base, ctx.faded(R.with_shadow(name), o), x + 68, y + 4)
        sub = R.text(ctx.CUE["build"], 24, B.WHITE, tracking=0.20)
        R.paste(base, ctx.faded(R.with_shadow(sub), o * 0.78), x + 68, y + 46)
    o, _ = ctx.beat(t, "ticker", 0.55, 0.55)
    if o > 0:
        base.alpha_composite(ctx.faded(_ticker(ctx), o))


def _rail_col(ctx):
    x = round(ctx.W * RAIL_X) + 42
    return x, ctx.X1 - x


def rail_hook(ctx, base, t):
    o, _ = ctx.beat(t, "hook")
    if o <= 0:
        return
    x, col = _rail_col(ctx)
    start = ctx.CUE["beats"]["hook"][0]
    y = round(ctx.H * 0.30)
    for i, ln in enumerate(_fit_lines(ctx, ctx.CUE["hook"], col, 0.085)):
        lp = ctx.ease_out((t - start - i * 0.14) / 0.6)
        if lp > 0:
            R.paste(base, ctx.faded(ln, o * lp), x - 40, int(y - (1 - lp) * 30))
        y += ln.height - round(ctx.H * 0.013)


def rail_build(ctx, base, t):
    o, _ = ctx.beat(t, "build")
    if o <= 0:
        return
    x, col = _rail_col(ctx)
    start = ctx.CUE["beats"]["build"][0]
    top = round(ctx.H * 0.295)

    head = R.text(ctx.CUE["buildHeading"], 30, B.RED, tracking=0.20)
    R.paste(base, ctx.faded(R.with_shadow(head), o), x - 20, top)

    row_h = round(ctx.H * 0.078)
    for i, (idx, label, sub) in enumerate(ctx.CUE["buildRows"]):
        rp = ctx.ease_out((t - start - 0.16 - i * 0.15) / 0.6)
        if rp <= 0:
            continue
        y = top + round(ctx.H * 0.055) + i * row_h + (1 - rp) * 18
        ro = o * rp
        # index sits in the rail itself
        R.paste(base, ctx.faded(R.with_shadow(R.text(idx, 26, B.RED, tracking=0.12)), ro),
                round(ctx.W * RAIL_X) - 12, y + 10, "rt")
        R.paste(base, ctx.faded(R.with_shadow(R.text(label, 56, B.WHITE, tracking=0.04)), ro),
                x - 20, y)
        R.paste(base, ctx.faded(R.with_shadow(R.text(sub, 25, B.WHITE, tracking=0.14)), ro * 0.68),
                x - 20, y + 54)


# ===========================================================================

LAYOUTS = {
    "hud": {
        "note": "Bracketed title block bottom-left, ticker under it, left-aligned "
                "type in the mid band. The kit's default; matches the 765LT and Roma.",
        "backdrop": hud_backdrop, "identity": hud_identity,
        "hook": hud_hook, "build": hud_build,
    },
    "centred": {
        "note": "Poster treatment. Mark above the hook, everything on the vertical "
                "axis, lockup centred at the foot. Quieter and more editorial.",
        "backdrop": centred_backdrop, "identity": centred_identity,
        "hook": centred_hook, "build": centred_build,
    },
    "panel": {
        "note": "A solid card in the lower half that swaps its contents. Ignores the "
                "footage underneath, so it survives any shot - the safest option on "
                "busy or bright material. Build sheet runs two columns of two.",
        "backdrop": panel_backdrop, "identity": panel_identity,
        "hook": panel_hook, "build": panel_build,
    },
    "rail": {
        "note": "The four-colour accent stripe stood on end down the left edge with "
                "the type hanging off it, build indices set in the rail. Uses the "
                "brand furniture as structure rather than trim.",
        "backdrop": rail_backdrop, "identity": rail_identity,
        "hook": rail_hook, "build": rail_build,
    },
}
