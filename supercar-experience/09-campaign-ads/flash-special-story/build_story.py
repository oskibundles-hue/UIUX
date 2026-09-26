#!/usr/bin/env python3
"""Supercar Experience, Lamborghini Huracan STO, 2-hour flash special. Story 9:16, 15.5 s, 24 fps.

One command builds everything (see cue.md):

    python3 build_story.py [--src STO.mp4] [--ffmpeg /path/to/ffmpeg]

  1. plate    cut + grade the 8 source ranges from the cue (speed ramps via setpts, 10-bit -> 8-bit,
              24 fps), the B6 push (1.00 -> 1.03), then 44 black end-card frames      -> .work/plate/
  2. overlay  node render_overlay.js: story.html renderAt(i/24), transparent PNGs       -> .work/overlay/
  3. audio    original sound bed synthesised with numpy (seeded), two-pass loudnorm -14 LUFS -> .work/bed.wav
  4. encode   ffmpeg overlay in RGB, BT.709 limited-range yuv420p, H.264 High CRF 17, AAC 192k 48 kHz
  5. QA       stills at every text beat, poster, contact sheet, stream check            -> exports/

Flags: --skip-plate / --skip-overlay / --skip-audio reuse what is already in .work/.
Needs: ffmpeg with overlay/eq/vignette/minterpolate/loudnorm/libx264; Python 3 + Pillow + numpy;
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
    """B2: the crest take carries a light strobe (luma 50 <-> 160 every 2-3 frames). Each frame is quantile-matched
    to the take's own mean distribution (per-channel barycentre), so the strobe is gone and the look is its average.
    B8: the reel's grade steps white balance inside the locked-off LVCC take (src 507, 547). Each frame is matched to
    the blue-white state (src 510-530), so the facade holds one colour for the whole ask."""
    x = _extract16(ff, src, 55, 78, d)
    qs = [_quantiles(f) for f in x]
    qref = np.mean(qs, 0)
    _grade_into(ff, [_match(f, q, qref) for f, q in zip(x, qs)], d, B2_FIRST, WORK / "tl")
    ref = _extract16(ff, src, B8_REF.start, B8_REF.stop, d)
    qref = np.mean([_quantiles(f) for f in ref], 0)
    del ref
    x = _extract16(ff, src, 498, 568, d)
    _grade_into(ff, [_match(f, _quantiles(f), qref) for f in x], d, B8_FIRST, WORK / "tl")
    del x
    print("tone lock: B2 (strobe) and B8 (white balance) matched")


def b8_cleanup(d):
    """Third-party marks on the LVCC facade (IBIE banner and sponsor logos, y ~11-25%) are darkened and softened;
    a poster face in the right-hand doorway is softened. Masks are soft and static (the in-camera push is slow)."""
    yy = np.arange(H, dtype=np.float32)[:, None] / H
    xx = np.arange(W, dtype=np.float32)[None, :] / W
    band = np.clip((0.34 - yy) / 0.08, 0, 1) * np.ones_like(xx)                  # 1 above y 26%, 0 below y 34%
    band = band * band * (3 - 2 * band)                                          # smoothstep
    dark = 1 - 0.58 * band                                                       # 58% darker at the top
    for f in range(B8_FIRST, B8_LAST + 1):
        p = d / f"{f:04d}.png"
        im = Image.open(p).convert("RGB")
        a = np.asarray(im, np.float32)
        b = np.asarray(im.filter(ImageFilter.GaussianBlur(9)), np.float32)
        k = (f - B8_FIRST) / (B8_LAST - B8_FIRST)
        cx, cy = 0.745 + 0.02 * k, 0.425 + 0.004 * k                            # doorway poster (see cue.md D12)
        face = np.exp(-(((xx - cx) / 0.05) ** 2 + ((yy - cy) / 0.028) ** 2)) * 1.0
        mix = np.clip(np.maximum(band, face), 0, 1)[..., None]
        out = (a * (1 - mix) + b * mix) * (dark * (1 - 0.35 * face))[..., None]
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


# ---------------------------------------------------------------- 3. audio (cue.md section 5)
SR = 48000
DUR = TOTAL / FPS
CUTS = [1.833, 3.083, 4.750, 6.542, 7.833, 9.958, 11.000]


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
    rng = np.random.default_rng(20260926)
    n = int(round(DUR * SR))
    t = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)

    def add(sig, t0, gain_l=1.0, gain_r=1.0):
        i0 = int(round(t0 * SR))
        i1 = min(n, i0 + len(sig))
        if i0 >= n or i1 <= 0:
            return
        s = sig[max(0, -i0): i1 - i0]
        L[max(0, i0):i1] += s * gain_l
        R[max(0, i0):i1] += s * gain_r

    def env_ramp(sig, a=0.002, r=0.004):
        k = np.ones(len(sig))
        na, nr = int(a * SR), int(r * SR)
        if na: k[:na] = np.linspace(0, 1, na)
        if nr: k[-nr:] *= np.linspace(1, 0, nr)
        return sig * k

    # drone 0-15.5, 0.3 s in, 0.5 s out
    drone = 0.045 * np.sin(2 * np.pi * 55 * t) + 0.025 * np.sin(2 * np.pi * 110 * t)
    drone *= np.clip(t / 0.3, 0, 1) * np.clip((DUR - t) / 0.5, 0, 1)
    add(drone, 0)

    # sub thumps: hook (0.000) and end card (13.667, longer + pink tail lowpassed 400 Hz)
    tt = np.arange(int(0.6 * SR)) / SR
    add(env_ramp(0.9 * np.sin(2 * np.pi * 45 * tt) * np.exp(-9 * tt), a=0.0005), 0.0)
    tt = np.arange(int(1.6 * SR)) / SR
    end = 0.9 * np.sin(2 * np.pi * 45 * tt) * np.exp(-3 * tt)
    tail_l = _spectral(rng.standard_normal(len(tt)), hi=400, pink=True) * 0.22 * np.exp(-tt / 1.5 * 4.6)
    tail_r = _spectral(rng.standard_normal(len(tt)), hi=400, pink=True) * 0.22 * np.exp(-tt / 1.5 * 4.6)
    add(env_ramp(end + tail_l, a=0.0005, r=0.05), 13.667, 1, 0)
    add(env_ramp(end + tail_r, a=0.0005, r=0.05), 13.667, 0, 1)

    # whooshes on each cut: pink noise, bandpass 1.8 kHz (2 octaves: 0.9-3.6 kHz), 0.3 s, peak -12 dBFS
    wn = int(0.3 * SR)
    wenv = np.minimum(np.linspace(0, 2, wn), np.linspace(2, 0, wn))    # linear in 0.15 / out 0.15
    peak = 10 ** (-12 / 20)
    for c in CUTS:
        for ch in (0, 1):
            wsh = _spectral(rng.standard_normal(wn * 4), lo=900, hi=3600, pink=True)[:wn] * wenv * peak
            add(wsh, c - 0.15, 1 - ch, ch)

    def blip(amp=0.4, f=2200, k=120, dur=0.025):
        x = np.arange(int(dur * SR)) / SR
        return env_ramp(amp * np.sin(2 * np.pi * f * x) * np.exp(-k * x), a=0.0003, r=0.002)

    for c in (2.250, 3.500, 11.583):              # double lock ticks
        add(blip(), c)
        add(blip(), c + 0.060)
    for c in (6.958, 7.125, 7.292):               # row ticks
        add(blip(), c)

    # fill sweep 5.208-6.125, 300 -> 900 Hz
    x = np.arange(int((6.125 - 5.208) * SR)) / SR
    add(env_ramp(0.12 * np.sin(2 * np.pi * (300 * x + 327 * x * x)), a=0.01, r=0.01), 5.208)
    # arrival ping 6.125
    x = np.arange(int(0.25 * SR)) / SR
    add(env_ramp(0.35 * np.sin(2 * np.pi * 1800 * x) * np.exp(-30 * x), a=0.0005), 6.125)

    # riser 9.55-11.00: white noise HP 800 Hz, exponential fade-in over 1.4 s, stop at 11.00
    rn = int((11.0 - 9.55) * SR)
    x = np.arange(rn) / SR
    renv = (np.exp(np.clip(x / 1.4, 0, 1) * 4) - 1) / (np.e ** 4 - 1)
    for ch in (0, 1):
        rs = _spectral(rng.standard_normal(rn), lo=800) * 0.28 * renv
        add(env_ramp(rs, a=0.0, r=0.006), 9.55, 1 - ch, ch)

    # pop on the CTA 11.042
    x = np.arange(int(0.45 * SR)) / SR
    add(env_ramp(0.8 * np.sin(2 * np.pi * 60 * x) * np.exp(-14 * x), a=0.0005), 11.042)

    st = np.stack([L, R], 1)
    st /= max(1e-9, np.max(np.abs(st)))
    st = np.tanh(2.2 * st) / np.tanh(2.2) * 0.89     # gentle saturation on the thumps: lower crest, audible on phones
    pcm = (st * 32767).astype("<i2")
    with wave.open(str(path_raw), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build_audio(ff):
    raw, bed = WORK / "bed_raw.wav", WORK / "bed.wav"
    WORK.mkdir(exist_ok=True)
    synth_bed(raw)
    # two-pass loudnorm: I -14, TP -1.0, LRA 7
    p = subprocess.run([str(ff), "-hide_banner", "-i", str(raw), "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(p.stderr[p.stderr.rindex("{"): p.stderr.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
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
    # contact sheet 5 x 2 with timestamps
    tw, th = 324, 576
    sheet = Image.new("RGB", (tw * 5 + 6 * 12, th * 2 + 3 * 12 + 2 * 34), (12, 12, 12))
    try:
        font = ImageFont.truetype(str(HERE.parent.parent / "07-fonts/Michroma-Regular.ttf"), 18)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (t, p) in enumerate(zip(QA_TIMES, paths)):
        cx, cy = 12 + (i % 5) * (tw + 12), 12 + (i // 5) * (th + 34 + 12)
        sheet.paste(Image.open(p).resize((tw, th), Image.LANCZOS), (cx, cy + 34))
        d.text((cx, cy + 6), f"{t:0.3f} s  f{round(t * FPS)}", fill=(251, 209, 1), font=font)
    sheet.save(EXPORTS / "contact-sheet.jpg", quality=90)
    return paths


def safe_zone_report():
    """Overlay ink (alpha > 8) on footage frames must sit inside y 14%-80% (stories profile bar / reply bar).
    Transit scan-line frames are exempt (they sweep through in < 0.2 s)."""
    exempt = set(range(43, 46)) | set(range(259, 265))
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
    safe_zone_report()
    info = probe(a.ffmpeg, out)
    (WORK / "probe.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))
    print("done:", out)


if __name__ == "__main__":
    main()
