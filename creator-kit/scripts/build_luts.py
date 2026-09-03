#!/usr/bin/env python3
"""
Creator Kit - look LUT generator.

Generates 33x33x33 .cube look LUTs for DJI Osmo Action 6 footage.

IMPORTANT - where these sit in the pipeline
-------------------------------------------
These are LOOK LUTs, not conversion LUTs. They expect footage that is already
in Rec.709 display space. DJI does not publish the D-Log M transfer function,
so any "D-Log M to Rec.709" LUT generated from scratch is guesswork. Use DJI's
official conversion LUT (or your NLE's built-in DJI D-Log M input transform)
first, then stack one of these on top:

    D-Log M clip  ->  DJI official D-Log M -> Rec.709  ->  look LUT (this file)

Every look carries mild "IG-safe" compensation baked in, because Instagram
re-encodes to a fairly low-bitrate 4:2:0 H.264:
  - a small black floor lift, so shadows band and block up less after transcode
  - a guard on extreme red saturation, which is the first thing to smear
  - a highlight rolloff, so skies and highlights compress instead of clipping

Pure standard library. No dependencies.

Usage:
    python3 build_luts.py [--size 33] [--out ../luts]
"""

import argparse
import colorsys
import math
import os

# Rec.709 luma coefficients.
LUMA_R, LUMA_G, LUMA_B = 0.2126, 0.7152, 0.0722

# 18% mid grey in a ~2.2 gamma display space. Used as the contrast pivot so
# that adding contrast pivots around skin/midtone rather than around 0.5.
MID_PIVOT = 0.4468


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------

def clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def luma(r, g, b):
    return LUMA_R * r + LUMA_G * g + LUMA_B * b


def contrast_pivot(x, amount, pivot=MID_PIVOT):
    """S-curve contrast that preserves 0, the pivot, and 1 exactly.

    amount > 0 adds contrast, amount < 0 flattens. Monotonic for amount > -1.
    """
    if amount == 0.0:
        return x
    p = 1.0 + amount if amount >= 0 else 1.0 / (1.0 - amount)
    if x <= 0.0:
        return 0.0
    if x < pivot:
        return (x / pivot) ** p * pivot
    if x >= 1.0:
        return 1.0
    t = (x - pivot) / (1.0 - pivot)
    return pivot + (1.0 - (1.0 - t) ** p) * (1.0 - pivot)


def highlight_rolloff(x, knee):
    """Soft-compress everything above `knee` so highlights roll rather than clip.

    Maps knee -> knee and 1 -> 1, monotonic in between.
    """
    if knee >= 1.0 or x <= knee:
        return x
    t = (x - knee) / (1.0 - knee)
    k = 2.0
    return knee + (1.0 - knee) * (1.0 - math.exp(-k * t)) / (1.0 - math.exp(-k))


def selective_hue(r, g, b, target_deg, width_deg, rotate_deg, sat_mul, val_mul):
    """Nudge one hue family only, leaving the rest of the frame alone.

    Weighted by angular distance from `target_deg` with a gaussian falloff, so
    the adjustment feathers instead of banding at the selection edge.
    """
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s <= 1e-6:
        return r, g, b
    hue_deg = h * 360.0
    d = abs(hue_deg - target_deg)
    d = min(d, 360.0 - d)
    if d > width_deg * 2.5:
        return r, g, b
    w = math.exp(-(d * d) / (2.0 * width_deg * width_deg))
    # Saturated pixels get the full effect; near-neutral ones are left alone
    # so that skin and grey surfaces do not pick up a cast.
    w *= min(1.0, s * 2.5)
    h2 = ((hue_deg + rotate_deg * w) % 360.0) / 360.0
    s2 = clamp01(s * (1.0 + (sat_mul - 1.0) * w))
    v2 = clamp01(v * (1.0 + (val_mul - 1.0) * w))
    return colorsys.hsv_to_rgb(h2, s2, v2)


# --------------------------------------------------------------------------
# look definition
# --------------------------------------------------------------------------

class Look:
    """An ordered creative grade applied to Rec.709 display-referred RGB."""

    def __init__(self, name, description, when,
                 exposure=0.0,
                 temp=0.0, tint=0.0,
                 lift=(0.0, 0.0, 0.0),
                 gain=(1.0, 1.0, 1.0),
                 gamma=(1.0, 1.0, 1.0),
                 contrast=0.0,
                 black_lift=0.0,
                 shadow_tint=(0.0, 0.0, 0.0), shadow_strength=0.0, shadow_falloff=2.0,
                 highlight_tint=(0.0, 0.0, 0.0), highlight_strength=0.0, highlight_falloff=2.0,
                 saturation=1.0,
                 vibrance=0.0,
                 hue_targets=(),
                 knee=0.88,
                 ig_safe=True):
        self.name = name
        self.description = description
        self.when = when
        self.exposure = exposure
        self.temp = temp
        self.tint = tint
        self.lift = lift
        self.gain = gain
        self.gamma = gamma
        self.contrast = contrast
        self.black_lift = black_lift
        self.shadow_tint = shadow_tint
        self.shadow_strength = shadow_strength
        self.shadow_falloff = shadow_falloff
        self.highlight_tint = highlight_tint
        self.highlight_strength = highlight_strength
        self.highlight_falloff = highlight_falloff
        self.saturation = saturation
        self.vibrance = vibrance
        self.hue_targets = hue_targets
        self.knee = knee
        self.ig_safe = ig_safe

    def apply(self, r, g, b):
        # 1. Exposure, applied in linear light so it behaves like a stop change
        #    rather than a gamma smear.
        if self.exposure != 0.0:
            m = 2.0 ** self.exposure
            r = (max(r, 0.0) ** 2.2 * m) ** (1 / 2.2)
            g = (max(g, 0.0) ** 2.2 * m) ** (1 / 2.2)
            b = (max(b, 0.0) ** 2.2 * m) ** (1 / 2.2)

        # 2. White balance. temp warms (R up / B down), tint pushes green/magenta.
        if self.temp or self.tint:
            r *= 1.0 + self.temp * 0.5
            b *= 1.0 - self.temp * 0.5
            g *= 1.0 + self.tint * 0.5

        # 3. Lift / gamma / gain per channel.
        lr, lg, lb = self.lift
        gr, gg, gb = self.gain
        mr, mg, mb = self.gamma
        r = (r * gr) + lr * (1.0 - r)
        g = (g * gg) + lg * (1.0 - g)
        b = (b * gb) + lb * (1.0 - b)
        if mr != 1.0:
            r = max(r, 0.0) ** (1.0 / mr)
        if mg != 1.0:
            g = max(g, 0.0) ** (1.0 / mg)
        if mb != 1.0:
            b = max(b, 0.0) ** (1.0 / mb)

        # 4. Contrast around the midtone pivot.
        if self.contrast:
            r = contrast_pivot(clamp01(r), self.contrast)
            g = contrast_pivot(clamp01(g), self.contrast)
            b = contrast_pivot(clamp01(b), self.contrast)

        # 5. Split toning, weighted by luminance.
        if self.shadow_strength or self.highlight_strength:
            L = clamp01(luma(r, g, b))
            if self.shadow_strength:
                w = (1.0 - L) ** self.shadow_falloff * self.shadow_strength
                r += self.shadow_tint[0] * w
                g += self.shadow_tint[1] * w
                b += self.shadow_tint[2] * w
            if self.highlight_strength:
                w = L ** self.highlight_falloff * self.highlight_strength
                r += self.highlight_tint[0] * w
                g += self.highlight_tint[1] * w
                b += self.highlight_tint[2] * w

        # 6. Saturation, then vibrance (which spares already-saturated pixels).
        if self.saturation != 1.0:
            L = luma(r, g, b)
            r = L + (r - L) * self.saturation
            g = L + (g - L) * self.saturation
            b = L + (b - L) * self.saturation
        if self.vibrance:
            L = luma(r, g, b)
            mx, mn = max(r, g, b), min(r, g, b)
            cur = (mx - mn) if mx > 0 else 0.0
            f = 1.0 + self.vibrance * (1.0 - min(1.0, cur))
            r = L + (r - L) * f
            g = L + (g - L) * f
            b = L + (b - L) * f

        # 7. Hue-selective moves (foliage, skies, skin).
        for t in self.hue_targets:
            r, g, b = selective_hue(clamp01(r), clamp01(g), clamp01(b), *t)

        # 8. Highlight rolloff instead of a hard clip.
        r = highlight_rolloff(clamp01(r), self.knee)
        g = highlight_rolloff(clamp01(g), self.knee)
        b = highlight_rolloff(clamp01(b), self.knee)

        # 9. Black floor lift, so Instagram's encoder has somewhere to put
        #    shadow gradients instead of banding them into flat blocks.
        if self.black_lift:
            f = self.black_lift
            r = f + r * (1.0 - f)
            g = f + g * (1.0 - f)
            b = f + b * (1.0 - f)

        # 10. IG-safe guard: pull back only the most extreme reds, which are
        #     what H.264 4:2:0 chroma subsampling smears first.
        if self.ig_safe:
            if r > 0.55 and r > g * 1.6 and r > b * 1.6:
                excess = (r - 0.55) / 0.45
                pull = 0.12 * excess
                L = luma(r, g, b)
                r = r + (L - r) * pull
                g = g + (L - g) * pull * 0.35
                b = b + (L - b) * pull * 0.35

        return clamp01(r), clamp01(g), clamp01(b)


# --------------------------------------------------------------------------
# the pack
# --------------------------------------------------------------------------

LOOKS = [
    Look(
        "AK_Neutral_Punch",
        "Clean and accurate with just enough contrast and colour to survive "
        "Instagram's encoder. Nothing stylistic - this is the safe default.",
        "Daily driver. Use when the location already looks good, or when you "
        "are not sure which look fits.",
        contrast=0.22,
        saturation=1.10,
        vibrance=0.08,
        black_lift=0.006,
        knee=0.90,
    ),
    Look(
        "AK_Golden_Vlog",
        "Warm, sunlit lifestyle look. Warms midtones and highlights, keeps "
        "shadows slightly cool so the warmth reads as sunlight rather than "
        "an orange cast.",
        "Golden hour, cafes, interiors, anything you want to feel inviting.",
        temp=0.10,
        contrast=0.20,
        gain=(1.02, 1.0, 0.985),
        shadow_tint=(-0.012, 0.0, 0.030), shadow_strength=0.85, shadow_falloff=2.2,
        highlight_tint=(0.026, 0.010, -0.020), highlight_strength=0.85, highlight_falloff=2.0,
        saturation=1.08,
        vibrance=0.12,
        hue_targets=(
            # Anchor skin so the warm push lifts the room, not faces. Without
            # this, deep skin tones slide orange and lose their depth.
            (24.0, 18.0, -4.0, 1.0, 1.0),
        ),
        black_lift=0.010,
        knee=0.86,
    ),
    Look(
        "AK_Garage_Chrome",
        "Automotive and industrial interiors. Cools the concrete and steel, "
        "controls the blowout on chrome and paint highlights, and holds skin "
        "warm and separate from a cold background.",
        "Garages, workshops, showrooms, car builds, warehouse walkthroughs.",
        temp=-0.06,
        contrast=0.24,
        gamma=(1.0, 1.0, 1.02),
        shadow_tint=(-0.016, 0.002, 0.030), shadow_strength=0.95, shadow_falloff=2.0,
        highlight_tint=(0.010, 0.006, 0.004), highlight_strength=0.6, highlight_falloff=2.4,
        saturation=0.98,
        vibrance=0.14,
        hue_targets=(
            # Hold skin warm and saturated against the cold room, and keep the
            # hue from sliding orange - deep skin tones go muddy when a warm
            # grade drags them toward 30 deg.
            (24.0, 20.0, -3.0, 1.12, 1.03),
        ),
        black_lift=0.012,
        knee=0.84,
    ),
    Look(
        "AK_Nordic_Steel",
        "Cold, high-contrast and desaturated. Steel blues in the shadows with "
        "a hard midtone roll - reads as weight and consequence.",
        "Overcast days, battle and combat sequences, winter, dramatic beats.",
        temp=-0.12,
        contrast=0.34,
        gamma=(0.99, 1.0, 1.03),
        shadow_tint=(-0.020, -0.004, 0.034), shadow_strength=1.0, shadow_falloff=1.8,
        highlight_tint=(0.006, 0.008, 0.014), highlight_strength=0.6, highlight_falloff=2.4,
        saturation=0.84,
        vibrance=0.10,
        hue_targets=(
            # Keep skin from going corpse-grey in a cold grade.
            (26.0, 22.0, 0.0, 1.20, 1.03),
        ),
        black_lift=0.012,
        knee=0.82,
    ),
    Look(
        "AK_Film_Halation",
        "Faded film emulation. Lifted matte blacks, cool shadows, warm "
        "highlights, gentle contrast. The most 'edited' look in the pack.",
        "Montages, B-roll, transitions, anything cut to music.",
        contrast=0.14,
        gamma=(1.0, 1.0, 1.0),
        shadow_tint=(-0.010, 0.002, 0.026), shadow_strength=1.0, shadow_falloff=1.6,
        highlight_tint=(0.030, 0.014, -0.016), highlight_strength=0.9, highlight_falloff=1.8,
        saturation=0.92,
        vibrance=0.10,
        hue_targets=(
            (24.0, 18.0, -4.0, 1.05, 1.0),
        ),
        black_lift=0.042,
        knee=0.80,
    ),
    Look(
        "AK_Night_City",
        "Low-light rescue. Opens the shadows without amplifying the noise "
        "floor, splits shadows cyan against magenta-warm highlights, and "
        "holds saturation back so neon and streetlight do not bloom out.",
        "Night vlogs, bars, streets, torch and firelight, indoor low light.",
        exposure=0.16,
        contrast=0.16,
        gamma=(1.05, 1.05, 1.07),
        shadow_tint=(-0.014, 0.006, 0.030), shadow_strength=1.0, shadow_falloff=1.7,
        highlight_tint=(0.022, -0.004, 0.014), highlight_strength=0.8, highlight_falloff=2.2,
        saturation=0.90,
        vibrance=0.16,
        black_lift=0.026,
        knee=0.78,
    ),
]


# --------------------------------------------------------------------------
# writer + validation
# --------------------------------------------------------------------------

def write_cube(look, size, out_dir):
    """Write a .cube LUT. Cube files vary blue slowest, red fastest."""
    path = os.path.join(out_dir, look.name + ".cube")
    n = size - 1
    with open(path, "w") as f:
        f.write("# %s\n" % look.name)
        f.write("# %s\n" % look.description.replace("\n", " "))
        f.write("# Best for: %s\n" % look.when.replace("\n", " "))
        f.write("# Apply AFTER a D-Log M -> Rec.709 conversion, not instead of one.\n")
        f.write('TITLE "%s"\n' % look.name)
        f.write("LUT_3D_SIZE %d\n" % size)
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n\n")
        for bi in range(size):
            for gi in range(size):
                for ri in range(size):
                    r, g, b = look.apply(ri / n, gi / n, bi / n)
                    f.write("%.6f %.6f %.6f\n" % (r, g, b))
    return path


def validate(look, size):
    """Sanity-check a look before we ship it. Returns a list of problems."""
    problems = []
    n = size - 1

    # Every output must be inside the legal 0-1 cube.
    for bi in range(0, size, 4):
        for gi in range(0, size, 4):
            for ri in range(0, size, 4):
                out = look.apply(ri / n, gi / n, bi / n)
                for v in out:
                    if not (0.0 <= v <= 1.0) or v != v:
                        problems.append("out of range at (%d,%d,%d): %s" % (ri, gi, bi, out))
                        break

    # The neutral axis must stay monotonic, or grey ramps will posterise.
    prev = -1.0
    for i in range(size):
        x = i / n
        r, g, b = look.apply(x, x, x)
        L = luma(r, g, b)
        if L < prev - 1e-6:
            problems.append("neutral ramp not monotonic at %.3f" % x)
        prev = L

    # Black and white must land somewhere sane.
    kr, kg, kb = look.apply(0.0, 0.0, 0.0)
    wr, wg, wb = look.apply(1.0, 1.0, 1.0)
    if luma(kr, kg, kb) > 0.10:
        problems.append("black point too high: %.4f" % luma(kr, kg, kb))
    if luma(wr, wg, wb) < 0.85:
        problems.append("white point too low: %.4f" % luma(wr, wg, wb))

    # A neutral grey should not pick up a wild cast. Split toning intentionally
    # shifts it a little, so this is a loose bound, not a strict neutrality test.
    mr, mg, mb = look.apply(0.5, 0.5, 0.5)
    spread = max(mr, mg, mb) - min(mr, mg, mb)
    limit = 0.06 if look.name == "AK_Neutral_Punch" else 0.16
    if spread > limit:
        problems.append("mid-grey cast %.4f exceeds %.2f" % (spread, limit))

    return problems


def main():
    ap = argparse.ArgumentParser(description="Generate Creator Kit look LUTs.")
    ap.add_argument("--size", type=int, default=33,
                    help="cube size per axis (33 is the compatibility sweet spot)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "luts"))
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    failed = False
    for look in LOOKS:
        problems = validate(look, args.size)
        if problems:
            failed = True
            print("FAIL %s" % look.name)
            for p in problems[:5]:
                print("      %s" % p)
            continue
        path = write_cube(look, args.size, out_dir)
        kb = os.path.getsize(path) / 1024.0
        print("ok   %-18s %6.0f KB  %s" % (look.name, kb, look.when.split(".")[0]))

    if failed:
        raise SystemExit(1)
    print("\n%d looks written to %s" % (len(LOOKS), out_dir))


if __name__ == "__main__":
    main()
