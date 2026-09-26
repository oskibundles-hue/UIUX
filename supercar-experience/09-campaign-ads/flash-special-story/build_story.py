#!/usr/bin/env python3
"""Supercar Experience, Lamborghini Huracan STO, 2-hour flash special. Story 9:16, 15.5 s, 24 fps.

One command builds everything (see cue.md):

    python3 build_story.py [--src STO.mp4] [--ffmpeg /path/to/ffmpeg]

  1. plate    cut + grade the 7 source ranges from the cue (speed ramp via setpts, 10-bit -> 8-bit, 24 fps),
              tone-lock B2 (crest strobe) and B8 (white-balance steps) in 16-bit, knock back the third-party
              marks in B8, the B6 push (1.00 -> 1.03), then 59 black end-card frames      -> .work/plate/
  2. overlay  node render_overlay.js: story.html renderAt(i/24), transparent PNGs       -> .work/overlay/
  3. audio    original sound bed synthesised with numpy (seeded), two-pass loudnorm -14 LUFS -> .work/bed.wav
  4. encode   ffmpeg overlay in RGB, BT.709 limited-range yuv420p, H.264 High CRF 17, AAC 192k 48 kHz
  5. QA       stills at every text beat, poster, contact sheet, stream check            -> exports/

Flags: --skip-plate / --skip-overlay / --skip-audio reuse what is already in .work/.
Needs: ffmpeg with overlay/eq/vignette/minterpolate/loudnorm/libx264/ebur128; Python 3 + Pillow + numpy;
Node 22 + Playwright (Chromium).
"""
import argparse, json, os, re, shutil, subprocess, sys, wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
WORK = HERE / ".work"
EXPORTS = HERE / "exports"
SCRATCH = Path("/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad")
DEFAULT_SRC = SCRATCH / "footage/STO.mp4"
DEFAULT_FF = SCRATCH / "ffmpeg"
OUT_NAME = "SCE_Lamborghini-Huracan-STO_Flash-Special-11AM-1PM_15s-9x16.mp4"

FPS = 24
TOTAL = 372                       # 15.500 s
PLATE_FRAMES = 313                # 0000-0312 footage; 0313-0371 end card (black)
W, H = 1080, 1920

# (name, src_in_frame, src_out_frame_excl, speed, out_frames, interpolation)
# Every range sits wholly inside one take, except B5+B7, which is one continuous source range whose
# in-source cut (357) lands exactly on output frame 174 (7.250 s). See cue.md section 1.
BEATS = [
    ("B1 hook",          393, 437, 1.0, 44, None),
    ("B2 brand lock",     55,  78, 1.0, 23, None),     # whole crest take at 1.0x; tone-locked below (strobe)
    ("B3 model lock",    148, 180, 0.8, 40, "blend"),
    ("B4 flash window",  279, 312, 1.0, 33, None),
    ("B5+B7 requirements", 323, 382, 1.0, 59, None),   # side profile 323-356 | wide roll-by 357-381
    ("B6 hero (clean)",  189, 233, 1.0, 44, None),
    ("B8 the ask",       498, 568, 1.0, 70, None),     # tone-locked below (reel white-balance steps)
]
B2_FIRST = 44                     # plate frames 44-66  <- src 55-77
B6_FIRST, B6_LAST = 199, 242      # plate frames that get the push 1.00 -> 1.03
B6_T0, B6_T1 = 199 / 24, 243 / 24
B8_FIRST, B8_LAST = 243, 312      # plate frames 243-312 <- src 498-567
B8_REF = range(510, 531)          # src frames 21.25-22.08 s: the blue-white facade state (reference look)
GRADE = "eq=contrast=1.04:saturation=0.96:gamma=1.0,vignette=angle=PI/5"
TO_RGB = "scale=in_color_matrix=bt709:in_range=tv:out_range=pc"

QA_TIMES = [0.000, 1.000, 2.500, 3.600, 5.500, 5.958, 7.100, 8.000, 9.400, 11.000, 12.500, 14.600]
POSTER_T = 1.000


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:220] + (" ..." if len(" ".join(map(str, cmd))) > 220 else ""))
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


# ---------------------------------------------------------------- 1. plate
def _extract16(ff, src, a, b, d):
    """Ungraded source frames a..b-1 as 16-bit RGB (BT.709 limited -> full), as a float32 array (n, H, W, 3)."""
    p = subprocess.run([str(ff), "-loglevel", "error", "-i", str(src), "-vf",
                        f"trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,{TO_RGB},format=rgb48le",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, "<u2").reshape(-1, H, W, 3)
    if len(x) != b - a:
        sys.exit(f"extract16 {a}-{b}: got {len(x)} frames")
    return x


Q = np.linspace(0.002, 0.998, 250)


def _quantiles(fr):
    s = fr[::4, ::4].reshape(-1, 3).astype(np.float32)
    return np.stack([np.quantile(s[:, c], Q) for c in range(3)])            # (3, len(Q))


def _match(fr, qsrc, qref):
    """Per-channel quantile (histogram) match of one frame to a reference distribution, in 16-bit float."""
    out = np.empty(fr.shape, np.float32)
    for c in range(3):
        xp = qsrc[c] + np.arange(len(Q)) * 1e-3                                # strictly increasing
        fp = qref[c]
        v = fr[..., c].astype(np.float32)
        y = np.interp(v, xp, fp)
        lo, hi = v < xp[0], v > xp[-1]                                         # linear tails beyond the quantiles
        y[lo] = fp[0] * v[lo] / max(xp[0], 1.0)
        y[hi] = fp[-1] + (v[hi] - xp[-1]) * (65535 - fp[-1]) / max(65535 - xp[-1], 1.0)
        out[..., c] = y
    return np.clip(out, 0, 65535)


LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def _yquantiles(fr):
    y = fr[::4, ::4].reshape(-1, 3).astype(np.float32) @ LUMA
    return np.quantile(y, Q)


def _match_luma(fr, qsrc, qref):
    """Luma-only quantile match, applied as a gain on RGB so hue and the crest's blacks are preserved."""
    x = fr.astype(np.float32)
    y = x @ LUMA
    xp = qsrc + np.arange(len(Q)) * 1e-3
    y2 = np.interp(y, xp, qref)
    hi = y > xp[-1]
    y2[hi] = qref[-1] + (y[hi] - xp[-1]) * (65535 - qref[-1]) / max(65535 - xp[-1], 1.0)
    g = np.clip(y2 / np.maximum(y, 64.0), 0.25, 4.0)
    return np.clip(x * g[..., None], 0, 65535)


def _balance(frames):
    """Per-channel mean gains toward the take's average colour, luma-neutral (evens out warm/cool frames)."""
    means = np.array([f[::4, ::4].reshape(-1, 3).mean(0) for f in frames])
    ref = means.mean(0)
    out = []
    for f, m in zip(frames, means):
        g = ref / np.maximum(m, 1.0)
        g *= (m @ LUMA) / max((m * g) @ LUMA, 1.0)
        out.append(np.clip(f * g.astype(np.float32), 0, 65535))
    return out


def _grade_into(ff, frames16, d, first, tmp):
    """Write 16-bit frames, run the house grade on them exactly like the main pass, land them as plate frames."""
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    raw = tmp / "in.rgb48"
    with open(raw, "wb") as f:
        for fr in frames16:
            f.write(np.round(fr).astype("<u2").tobytes())
    run([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", FPS,
         "-i", raw, "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv444p," + GRADE + f",{TO_RGB},format=rgb24",
         "-fps_mode", "passthrough", "-start_number", first, d / "%04d.png"])
    raw.unlink()


def tone_lock(ff, src, d):
    """B2: the crest take carries a light strobe (luma 50 <-> 160 every 2-3 frames). Each frame's luma is
    quantile-matched to the take's own mean luma distribution and applied as an RGB gain (hue kept), so the strobe
    is gone and the look is the take's average.
    B8: the reel's grade steps white balance inside the locked-off LVCC take (src 507, 547). Each frame is matched to
    the blue-white state (src 510-530), so the facade holds one colour for the whole ask."""
    x = _extract16(ff, src, 55, 78, d)
    qs = [_yquantiles(f) for f in x]
    qref = np.mean(qs, 0)
    _grade_into(ff, _balance([_match_luma(f, q, qref) for f, q in zip(x, qs)]), d, B2_FIRST, WORK / "tl")
    ref = _extract16(ff, src, B8_REF.start, B8_REF.stop, d)
    qref = np.mean([_quantiles(f) for f in ref], 0)
    del ref
    x = _extract16(ff, src, 498, 568, d)
    _grade_into(ff, [_match(f, _quantiles(f), qref) for f in x], d, B8_FIRST, WORK / "tl")
    del x
    print("tone lock: B2 (strobe) and B8 (white balance) matched")


def _soft_rect(x0, x1, y0, y1, fx, fy):
    """Soft-edged rectangle mask on the frame grid (fractions), smoothstep feather fx / fy."""
    xx = np.arange(W, dtype=np.float32) / W
    yy = np.arange(H, dtype=np.float32) / H
    def ss(v):
        v = np.clip(v, 0, 1)
        return v * v * (3 - 2 * v)
    mx = ss((xx - (x0 - fx)) / fx) * ss(((x1 + fx) - xx) / fx)
    my = ss((yy - (y0 - fy)) / fy) * ss(((y1 + fy) - yy) / fy)
    return my[:, None] * mx[None, :]


def b8_cleanup(d, frames=None):
    """Third-party marks on the LVCC facade are knocked back (cue.md D12). The IBIE banner and its sponsor logos
    (x 43-76%, y 11-25%) sit under a full-width graduated defocus + darken (x0.45 above y 23%, easing out by 27.5%,
    clear of the LAS VEGAS lettering), so it reads as depth of field rather than a patch. The small IBIE door sign
    (x 73-80%, y 37.5-39.5%) and the doorway poster face (centre x 76.1%, y 42.4%) are softened in place. Positions are
    measured on plate frames 243 and 312 by template match (background drift +1.1% x, -0.6% y: the camera dollies
    toward the car, so the facade barely moves)."""
    grad = _soft_rect(-1, 2, -1, 0.23, 0.01, 0.045)                  # 1 above y 23%, smoothstep to 0 by 27.5%
    dark = 1 - 0.55 * grad
    yy = np.arange(H, dtype=np.float32)[:, None] / H
    xx = np.arange(W, dtype=np.float32)[None, :] / W
    for f in (frames or range(B8_FIRST, B8_LAST + 1)):
        p = d / f"{f:04d}.png"
        im = Image.open(p).convert("RGB")
        a = np.asarray(im, np.float32)
        b_hi = np.asarray(im.filter(ImageFilter.GaussianBlur(16)), np.float32)
        b_lo = np.asarray(im.filter(ImageFilter.GaussianBlur(6)), np.float32)
        k = (f - B8_FIRST) / (B8_LAST - B8_FIRST)
        dx, dy = 0.011 * k, -0.006 * k
        face = np.exp(-((((xx - 0.761 - dx) / 0.028) ** 2 + ((yy - 0.424 - dy) / 0.022) ** 2) ** 2))
        sign = _soft_rect(0.728 + dx, 0.80 + dx, 0.374 + dy, 0.396 + dy, 0.008, 0.004)
        m_lo = np.maximum(face, sign)[..., None]
        out = a * (1 - m_lo) + b_lo * m_lo
        g = grad[..., None]
        out = out * (1 - g) + b_hi * g
        out *= (dark * (1 - 0.25 * face))[..., None]
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(p, compress_level=1)


def build_plate(ff, src):
    d = WORK / "plate"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    n = len(BEATS)
    parts = [f"[0:v]split={n}" + "".join(f"[s{i}]" for i in range(n))]
    for i, (_, a, b, speed, nout, interp) in enumerate(BEATS):
        f = f"[s{i}]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS"
        if speed != 1.0:
            f += f",setpts=(PTS-STARTPTS)/{speed}"
            f += ",minterpolate=fps=24:mi_mode=blend" if interp == "blend" else ",fps=24"
            f += f",tpad=stop_mode=clone:stop=3,trim=end_frame={nout},setpts=PTS-STARTPTS"
        parts.append(f + f"[v{i}]")
    parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,settb=1/24,setpts=N," + GRADE +
                 f",{TO_RGB},format=rgb24[out]")
    run([ff, "-y", "-loglevel", "error", "-i", src, "-filter_complex", ";".join(parts),
         "-map", "[out]", "-an", "-fps_mode", "passthrough", "-start_number", "0", d / "%04d.png"])
    got = len(list(d.glob("*.png")))
    if got != PLATE_FRAMES:
        sys.exit(f"plate: expected {PLATE_FRAMES} frames, got {got}")
    tone_lock(ff, src, d)
    b8_cleanup(d)
    # B6 push: scale 1.00 -> 1.03 linear in t, origin 50% 45% (plate only)
    ox, oy = 0.50 * W, 0.45 * H
    for f in range(B6_FIRST, B6_LAST + 1):
        t = f / FPS
        s = 1 + 0.03 * min(1, max(0, (t - B6_T0) / (B6_T1 - B6_T0)))
        if s <= 1.0001:
            continue
        p = d / f"{f:04d}.png"
        im = Image.open(p)
        l, tp = ox - ox / s, oy - oy / s
        im.resize((W, H), Image.LANCZOS, box=(l, tp, l + W / s, tp + H / s)).save(p, compress_level=1)
    black = Image.new("RGB", (W, H), (0, 0, 0))
    for f in range(PLATE_FRAMES, TOTAL):
        black.save(d / f"{f:04d}.png", compress_level=1)
    print(f"plate: {PLATE_FRAMES} footage + {TOTAL - PLATE_FRAMES} end-card frames")


# ---------------------------------------------------------------- 2. overlay
def build_overlay():
    d = WORK / "overlay"
    shutil.rmtree(d, ignore_errors=True)
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    run(["node", HERE / "render_overlay.js", d, FPS, TOTAL, 4], env=env)
    got = len(list(d.glob("*.png")))
    if got != TOTAL:
        sys.exit(f"overlay: expected {TOTAL} frames, got {got}")
    # Chromium writes a fully opaque page (the end card) as an RGB PNG. A pixel-format change mid-sequence makes
    # ffmpeg re-initialise the filter graph and slips the overlay against the plate by several frames, so every
    # frame is normalised to RGBA here.
    fixed = 0
    for f in sorted(d.glob("*.png")):
        im = Image.open(f)
        if im.mode != "RGBA":
            im.convert("RGBA").save(f, compress_level=1)
            fixed += 1
    print(f"overlay: {fixed} opaque frames normalised to RGBA")


# ---------------------------------------------------------------- 3. audio (cue.md section 5)
SR = 48000
DUR = TOTAL / FPS
CUTS = [1.833, 2.792, 4.458, 5.833, 7.250, 8.292, 10.125]
T_END = 13.042                     # end card hard cut


def _spectral(x, lo=None, hi=None, pink=False):
    """FFT-domain filter with soft (cosine) skirts; pink=True tilts to 1/f power."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if pink:
        g /= np.sqrt(np.maximum(f, 20.0))
    if lo:
        g *= np.clip((f - lo * 0.7) / (lo * 0.3), 0, 1) ** 2
    if hi:
        g *= np.clip((hi * 1.4 - f) / (hi * 0.4), 0, 1) ** 2
    y = np.fft.irfft(X * g, len(x))
    return y / (np.max(np.abs(y)) + 1e-12)


def synth_bed(path_raw):
    """Original bed, seeded. Built for phone speakers: every element carries energy above 200 Hz (harmonic pad,
    saturated impact bodies with a transient and a metallic ring, 0.7-6 kHz whooshes); the sub is a layer, not the
    mix. Checked through a 200 Hz high-pass (cue.md section 5)."""
    rng = np.random.default_rng(20260926)
    n = int(round(DUR * SR))
    t = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)

    def add(sig, t0, gl=1.0, gr=1.0):
        i0 = int(round(t0 * SR))
        i1 = min(n, i0 + len(sig))
        if i0 >= n or i1 <= 0:
            return
        s = sig[max(0, -i0): i1 - i0]
        L[max(0, i0):i1] += s * gl
        R[max(0, i0):i1] += s * gr

    def ramp(sig, a=0.002, r=0.004):
        k = np.ones(len(sig))
        na, nr = int(a * SR), int(r * SR)
        if na: k[:na] = np.linspace(0, 1, na)
        if nr: k[-nr:] *= np.linspace(1, 0, nr)
        return sig * k

    def tt(dur):
        return np.arange(int(dur * SR)) / SR

    # 1. pad: A-minor stack with harmonics, slow tremolo, detuned L/R; air noise on top. 0.3 s in, fades 14.7-15.5
    env = np.clip(t / 0.3, 0, 1) * np.clip((DUR - t) / 0.8, 0, 1)
    trem = 0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t)
    parts = [(55, .010), (110, .012), (164.8, .010), (220, .026), (261.6, .016), (329.6, .022), (440, .018),
             (523.3, .008), (659.3, .010), (880, .005)]
    for det, gl, gr in ((1.0, 1, 0), (1.0035, 0, 1)):
        x = sum(a * np.sin(2 * np.pi * f * det * t + f) for f, a in parts)
        add(np.tanh(3 * x) / 3 * env * trem * 1.7, 0, gl, gr)
    air = _spectral(rng.standard_normal(n), lo=3000, hi=9000) * 0.010 * env
    add(air, 0, 1, 0.7)

    # 2. impacts: sub + pitch-drop body (saturated -> harmonics) + noise transient + metallic ring
    def impact(length, decay, ring=0.05):
        x = tt(length)
        sub = 0.32 * np.sin(2 * np.pi * 45 * x) * np.exp(-decay * x)
        f = 70 + 170 * np.exp(-x / 0.07)                             # 240 -> 70 Hz pitch drop, saturated
        body = np.tanh(3.2 * 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-decay * 1.6 * x)) * 0.32
        crack = _spectral(rng.standard_normal(len(x)), lo=1500, hi=8000) * 0.30 * np.exp(-x / 0.035)
        metal = sum(np.sin(2 * np.pi * fr * x + ph) for fr, ph in ((523.3, 0), (1244, 1), (2093, 2), (3322, 3))) * ring
        metal *= np.exp(-x / (length * 0.35))
        boom = _spectral(rng.standard_normal(len(x)), lo=200, hi=1200) * 0.20 * np.exp(-x / 0.18)
        return ramp(sub + body + crack + metal + boom, a=0.0005, r=0.05)
    add(impact(0.9, 7), 0.0)
    add(impact(2.0, 2.6, ring=0.06), T_END)

    # 3. whooshes into each cut: pink noise, band 0.7-6 kHz, centre swept up into the cut then down; panned L->R
    wn = int(0.42 * SR)
    for i, c in enumerate(CUTS):
        x = _spectral(rng.standard_normal(wn * 3), lo=700, hi=6000, pink=True)[:wn]
        shimmer = _spectral(rng.standard_normal(wn * 3), lo=4000, hi=10000)[:wn] * 0.35
        e = np.concatenate([np.linspace(0, 1, int(wn * 0.7)) ** 2, np.linspace(1, 0, wn - int(wn * 0.7)) ** 1.5])
        w = (x + shimmer * np.linspace(0, 1, wn)) * e * 0.32
        pan = np.linspace(0.2, 0.8, wn) if i % 2 == 0 else np.linspace(0.8, 0.2, wn)
        add(w * (1 - pan) * 1.4, c - 0.29, 1, 0)
        add(w * pan * 1.4, c - 0.29, 0, 1)

    # 4. ticks (lock-ons, requirement rows): 2.2 kHz blip with an octave, short
    def blip(amp=0.30, f=2200, k=110, dur=0.03):
        x = tt(dur)
        return ramp(amp * (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * 2 * f * x)) * np.exp(-k * x), 0.0003, 0.002)
    for c in (2.208, 3.208, 10.708):              # double lock ticks: B2, B3, B8 brackets
        add(blip(), c); add(blip(amp=0.22), c + 0.060)
    for c in (6.667, 6.833, 7.000):               # requirement rows land
        add(blip(amp=0.26, f=1760), c)

    # 5. fill sweep 4.917-5.833: harmonic tone 220 -> 880 Hz (the bar filling), then the arrival bell at 5.833
    x = tt(5.833 - 4.917)
    ph = 2 * np.pi * np.cumsum(220 * 4 ** (x / x[-1])) / SR
    sweep = sum(np.sin(k * ph) / k for k in range(1, 6)) * 0.07 * (0.4 + 0.6 * x / x[-1])
    add(ramp(sweep, 0.02, 0.01), 4.917, 0.8, 1)
    x = tt(0.9)
    bell = (np.sin(2 * np.pi * 1760 * x) + 0.5 * np.sin(2 * np.pi * 2637 * x) + 0.25 * np.sin(2 * np.pi * 3520 * x))
    add(ramp(0.20 * bell * np.exp(-x / 0.22), 0.0005), 5.833)

    # 6. riser into the ask 8.90-10.125: rising band noise + rising tone, exponential swell, hard stop on the cut
    x = tt(10.125 - 8.90)
    sw = (np.exp(np.clip(x / x[-1], 0, 1) * 4) - 1) / (np.e ** 4 - 1)
    tone = np.sin(2 * np.pi * np.cumsum(220 * 3 ** (x / x[-1])) / SR) * 0.05
    for ch in (0, 1):
        nz = _spectral(rng.standard_normal(len(x)), lo=900, hi=7000) * 0.20
        add(ramp((nz + tone) * sw, 0.0, 0.006), 8.90, 1 - ch, ch)

    # 7. CTA pop 10.167: small sub + click + 1.2 kHz blip
    x = tt(0.4)
    pop = 0.30 * np.sin(2 * np.pi * 62 * x) * np.exp(-12 * x) + np.tanh(2 * 0.25 * np.sin(2 * np.pi * 124 * x)) * np.exp(-18 * x)
    add(ramp(pop, 0.0005), 10.167)
    add(blip(amp=0.22, f=1200, k=60, dur=0.08), 10.167)

    st = np.stack([L, R], 1)
    st /= max(1e-9, np.max(np.abs(st)))
    st = np.tanh(1.6 * st) / np.tanh(1.6) * 0.89     # gentle saturation: lower crest factor, a little more harmonic
    pcm = (st * 32767).astype("<i2")
    with wave.open(str(path_raw), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build_audio(ff):
    raw, bed = WORK / "bed_raw.wav", WORK / "bed.wav"
    WORK.mkdir(exist_ok=True)
    synth_bed(raw)
    # two-pass linear loudnorm: I -14, TP -2.0 (headroom for AAC overshoot), LRA 7
    p = subprocess.run([str(ff), "-hide_banner", "-i", str(raw), "-af",
                        "loudnorm=I=-14:TP=-2.0:LRA=7:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(p.stderr[p.stderr.rindex("{"): p.stderr.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-2.0:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          f"aresample=48000,apad,atrim=end_sample={int(round(DUR * SR))}")
    run([ff, "-y", "-loglevel", "error", "-i", raw, "-af", af, "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", bed])
    print(f"audio: raw {m['input_i']} LUFS -> target -14 (bed.wav)")


# ---------------------------------------------------------------- 4. encode
def encode(ff):
    EXPORTS.mkdir(exist_ok=True)
    out = EXPORTS / OUT_NAME
    run([ff, "-y", "-loglevel", "error",
         "-framerate", FPS, "-start_number", 0, "-i", WORK / "plate/%04d.png",
         "-framerate", FPS, "-start_number", 0, "-i", WORK / "overlay/%05d.png",
         "-i", WORK / "bed.wav",
         "-filter_complex", "[0:v]format=rgb24[p];[1:v]format=rgba[o];[p][o]overlay=0:0:format=rgb,"
                            "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]",
         "-map", "[v]", "-map", "2:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", 17, "-profile:v", "high", "-r", FPS,
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
         "-c:a", "aac", "-b:a", "192k", "-ar", 48000, "-ac", 2, "-movflags", "+faststart", "-shortest", out])
    return out


# ---------------------------------------------------------------- 5. QA
def probe(ff, path):
    def null(*extra):
        return subprocess.run([str(ff), "-hide_banner", "-stats", "-i", str(path), *extra, "-f", "null", "-"],
                              capture_output=True, text=True).stderr.replace("\r", "\n")
    e = null("-map", "0:v")
    a = null("-map", "0:a")
    lo = null("-map", "0:a", "-af", "ebur128=peak=true")
    streams = [s.strip() for s in re.findall(r"Stream #0:\d.*", e)]
    return {"container_duration": re.search(r"Duration: ([\d:.]+)", e).group(1),
            "video_frames": int(re.findall(r"frame=\s*(\d+)", e)[-1]),
            "video_decoded_time": re.findall(r"time=([\d:.]+)", e)[-1],
            "audio_decoded_time": re.findall(r"time=([\d:.]+)", a)[-1],
            "integrated_lufs": float(re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)[-1]),
            "true_peak_dbfs": float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lo)[-1]),
            "streams": streams[:2]}


def stills(ff, mp4):
    for old in EXPORTS.glob("still-*.jpg"):
        old.unlink()
    paths = []
    sel = "+".join(f"eq(n\\,{round(t * FPS)})" for t in QA_TIMES)
    tmp = WORK / "qa"
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    run([ff, "-y", "-loglevel", "error", "-i", mp4, "-vf", f"select='{sel}'", "-fps_mode", "passthrough",
         "-q:v", 2, tmp / "%02d.jpg"])
    for i, t in enumerate(QA_TIMES):
        s, cs = int(t), int(round((t - int(t)) * 100))
        dst = EXPORTS / f"still-{s:02d}_{cs:02d}s.jpg"
        shutil.move(tmp / f"{i + 1:02d}.jpg", dst)
        paths.append(dst)
    # poster (the hook, fully built)
    run([ff, "-y", "-loglevel", "error", "-i", mp4, "-vf", f"select='eq(n\\,{round(POSTER_T * FPS)})'",
         "-fps_mode", "passthrough", "-frames:v", 1, "-q:v", 2, EXPORTS / "poster.jpg"])
    # contact sheet (6 per row) with timestamps
    tw, th, cols = 324, 576, 6
    rows = (len(QA_TIMES) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols + (cols + 1) * 12, th * rows + (rows + 1) * 12 + rows * 34), (12, 12, 12))
    try:
        font = ImageFont.truetype(str(HERE.parent.parent / "07-fonts/Michroma-Regular.ttf"), 18)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (t, p) in enumerate(zip(QA_TIMES, paths)):
        cx, cy = 12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 34 + 12)
        sheet.paste(Image.open(p).resize((tw, th), Image.LANCZOS), (cx, cy + 34))
        d.text((cx, cy + 6), f"{t:0.3f} s  f{round(t * FPS)}", fill=(251, 209, 1), font=font)
    sheet.save(EXPORTS / "contact-sheet.jpg", quality=90)
    return paths


def verify_sync(ff, mp4):
    """Every sampled MP4 frame must match plate+overlay of the same index (catches any frame slip)."""
    idx = [0, 43, 44, 106, 140, 198, 199, 242, 243, 312, 313, 330, 371]
    sel = "+".join(f"eq(n\\,{i})" for i in idx)
    p = subprocess.run([str(ff), "-loglevel", "error", "-i", str(mp4), "-vf", f"select='{sel}',scale=270:480,format=rgb24",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True)
    got = np.frombuffer(p.stdout, np.uint8).reshape(-1, 480, 270, 3).astype(np.float32)
    bad = []
    for k, i in enumerate(idx):
        c = Image.alpha_composite(Image.open(WORK / f"plate/{i:04d}.png").convert("RGBA"),
                                  Image.open(WORK / f"overlay/{i:05d}.png").convert("RGBA"))
        ref = np.asarray(c.convert("RGB").resize((270, 480), Image.BILINEAR), np.float32)
        err = float(np.abs(got[k] - ref).mean())
        if err > 8:
            bad.append((i, round(err, 1)))
    print(f"sync: {len(idx)} sampled frames vs plate+overlay, mismatches: {bad or 'none'}")
    if bad:
        sys.exit("sync check failed")


def safe_zone_report():
    """Overlay ink (alpha > 8) on footage frames must sit inside y 14%-80% (stories profile bar / reply bar).
    Transit scan-line frames are exempt (they sweep through in < 0.2 s)."""
    exempt = set(range(43, 46)) | set(range(238, 244))              # transit scan lines 1.792-1.875, 9.917-10.125
    worst = [100.0, 0.0, 100.0, 0.0]
    bad = []
    for f in range(PLATE_FRAMES):
        if f in exempt:
            continue
        px = np.asarray(Image.open(WORK / f"overlay/{f:05d}.png").convert("RGBA"))
        a = (px[..., 3] > 8) & (px[..., :3].max(2) > 60)      # visible ink; black scrims/shadows excluded
        ys = np.nonzero(a.any(1))[0]
        if not len(ys):
            continue
        xs = np.nonzero(a.any(0))[0]
        y0, y1, x0, x1 = ys[0] / H * 100, ys[-1] / H * 100, xs[0] / W * 100, xs[-1] / W * 100
        worst = [min(worst[0], y0), max(worst[1], y1), min(worst[2], x0), max(worst[3], x1)]
        if y0 < 14 or y1 > 80:
            bad.append((f, round(y0, 1), round(y1, 1)))
    print(f"safe zones: overlay ink spans y {worst[0]:.1f}-{worst[1]:.1f}%, x {worst[2]:.1f}-{worst[3]:.1f}% "
          f"(ticker text runs full width under its edge fade); out-of-band frames: {bad or 'none'}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--ffmpeg", default=str(DEFAULT_FF) if DEFAULT_FF.exists() else (shutil.which("ffmpeg") or "ffmpeg"))
    ap.add_argument("--skip-plate", action="store_true")
    ap.add_argument("--skip-overlay", action="store_true")
    ap.add_argument("--skip-audio", action="store_true")
    a = ap.parse_args()
    WORK.mkdir(exist_ok=True)
    if not a.skip_plate:
        print("1/5 plate"); build_plate(a.ffmpeg, a.src)
    if not a.skip_overlay:
        print("2/5 overlay"); build_overlay()
    if not a.skip_audio:
        print("3/5 audio"); build_audio(a.ffmpeg)
    print("4/5 encode"); out = encode(a.ffmpeg)
    print("5/5 QA"); stills(a.ffmpeg, out)
    verify_sync(a.ffmpeg, out)
    safe_zone_report()
    info = probe(a.ffmpeg, out)
    (WORK / "probe.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))
    print("done:", out)


if __name__ == "__main__":
    main()
