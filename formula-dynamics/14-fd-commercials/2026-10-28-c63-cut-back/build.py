#!/usr/bin/env python3
"""FD C63 - "Cut Back" reel (exhaust), Instagram 1080x1920 @ 30 fps.

One car, one question: open on the payoff (a rev), cut back to the stock car
(SEP 29), the new parts (OCT 7), then the cold start and a held rev, end mark.

Pipeline: ffmpeg decodes each source window (autorotated to 2160x3840 portrait)
-> numpy/OpenCV per frame: plate + meter redaction (tracked, in source space),
crop/push, grade, text -> raw frames piped to libx264. Audio is rebuilt in numpy
from the same windows only (the car's own sound, no music, no added effects),
then two-pass loudnorm.

Usage:
  python3 build.py --raw <dir with IMG_0325/0579/0590.MOV> [--stills] [--only-audio]
Needs: ffmpeg 6+, numpy, Pillow, opencv-python-headless.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FD = HERE.parents[1]                       # formula-dynamics/
sys.path.insert(0, str(FD / "99-toolkit"))
import fd_brand  # noqa: E402  brand values come from here and nowhere else

W, H, FPS = 1080, 1920, 30
SW, SH = 2160, 3840                         # autorotated source frame
SR = 48000
FONT = str(fd_brand.FONT_BEBAS)
RED = fd_brand.rgb(fd_brand.RED)
ICON = FD / "02-logos/png-transparent/fd-icon-mark-only--white_1000w.png"
EXPORTS = HERE / "exports"
QA = EXPORTS / "qa"
OUT_MP4 = EXPORTS / "FD C63 - Cut Back (exhaust, 15s) - INSTAGRAM 1080x1920.mp4"
OUT_COVER = EXPORTS / "FD C63 - Cut Back - cover STATIC 1080x1920.jpg"

# 9:16 keep-out zones: top 11%, bottom 20%, left 5%, right 16%
SAFE = dict(x0=int(W * 0.05), x1=int(W * 0.84), y0=int(H * 0.11), y1=int(H * 0.80))

# ---------------------------------------------------------------------------
# Redaction boxes, source pixels (x0, y0, x1, y1) on the shot's first frame.
# Tracked per frame by template match, then smoothed.
# ---------------------------------------------------------------------------
PLATE_0590 = (690, 745, 1100, 1015)
METER_0590 = (632, 2075, 910, 2480)       # LCD readout of the sound meter
PLATE_0325 = (1165, 1880, 1395, 2050)
LIVERY_0325 = (1495, 1610, 1610, 1750)    # another customer's car: sponsor logo + name on its side
CRATE_0325 = (1640, 2050, 1780, 2150)     # printed maker emblems on a parts box by the tail light

# ---------------------------------------------------------------------------
# Shot list. crop = ((cx, cy, w) at start, (cx, cy, w) at end) in source px;
# h = w * 16/9.  t0 = timeline start (s).
# ---------------------------------------------------------------------------
SHOTS = [
    dict(name="hook", src="IMG_0590.MOV", t_in=63.40, dur=2.0,
         crop=((1530, 1120, 1260), (1565, 1200, 1120)),
         redact=[("plate", PLATE_0590, (6, 3)), ("meter", METER_0590, (3, 4))]),
    # crop top held at source y 1380: the lift posts' maker branding sits above y 1290
    dict(name="before", src="IMG_0325.MOV", t_in=4.25, dur=3.0,
         crop=((1150, 2500, 1260), (1150, 2447, 1200)),
         redact=[("plate", PLATE_0325, (6, 3)), ("livery", LIVERY_0325, (3, 3)),
                 ("crate", CRATE_0325, (3, 2))]),
    # Parts (0579). Part brands stay off screen, by framing only:
    #  - the hang tag (maker's logo, serial, address) hangs under the X-pipe's second brace;
    #    parts1 is framed left of / above it for every frame;
    #  - the muffler can carries an etched maker name and text lines on its side; parts2 and
    #    parts3 are framed below / above the can.
    dict(name="parts1", src="IMG_0579.MOV", t_in=5.10, dur=1.1,
         crop=((530, 1400, 1060), (500, 1650, 980)), redact=[]),
    dict(name="parts2", src="IMG_0579.MOV", t_in=7.45, dur=0.5,
         crop=((420, 3200, 800), (420, 3260, 760)), redact=[]),
    dict(name="parts3", src="IMG_0579.MOV", t_in=10.35, dur=0.5,
         crop=((600, 1740, 1200), (800, 1800, 1100)), redact=[]),
    dict(name="coldstart", src="IMG_0590.MOV", t_in=6.20, dur=74 / 30, a_pre=0.50,
         crop=((1330, 1475, 1659), (1350, 1475, 1590)),
         redact=[("plate", PLATE_0590, (6, 3)), ("meter", METER_0590, (3, 4))]),
    # the new burnt piping under the bumper, between the tip pairs; source y 1027-2093
    # keeps the plate (ends y 1015) out and the meter's logo box far below
    dict(name="piping", src="IMG_0590.MOV", t_in=53.90, dur=0.8,
         crop=((880, 1560, 520), (880, 1580, 470)),
         redact=[("plate", PLATE_0590, (6, 3)), ("meter", METER_0590, (3, 4))]),
    dict(name="rev", src="IMG_0590.MOV", t_in=54.70, dur=3.10,
         crop=((1420, 1300, 1400), (1420, 1300, 1400)),
         redact=[("plate", PLATE_0590, (6, 3)), ("meter", METER_0590, (3, 4))]),
    dict(name="end", src="IMG_0590.MOV", t_in=57.80, dur=1.7,
         crop=((1420, 1300, 1400), (1420, 1300, 1400)),
         redact=[("plate", PLATE_0590, (6, 3)), ("meter", METER_0590, (3, 4))],
         darken=True),
]
t = 0.0
for s in SHOTS:
    s["t0"] = round(t, 4)
    s["n"] = int(round(s["dur"] * FPS))
    t += s["dur"]
TOTAL = t
NFRAMES = sum(s["n"] for s in SHOTS)


def shot_at(name):
    return next(s for s in SHOTS if s["name"] == name)


# ---------------------------------------------------------------------------
# Text cards (timeline seconds)
# ---------------------------------------------------------------------------
P1 = shot_at("parts1")["t0"]
CARDS = [
    dict(id="hook", t_in=0.0, t_out=shot_at("before")["t0"]),
    dict(id="SEP 29", t_in=shot_at("before")["t0"], t_out=shot_at("before")["t0"] + 1.0, typed=True),
    dict(id="OCT 7", t_in=P1, t_out=P1 + 1.0, typed=True),
    dict(id="NEW.", t_in=P1 + 6 / FPS, t_out=P1 + 6 / FPS + 0.7),     # on the X-pipe
    dict(id="endmark", t_in=shot_at("end")["t0"], t_out=TOTAL),
]


def font(size):
    return ImageFont.truetype(FONT, size)


def shadowed(layer, radius=10, alpha=0.55, offset=(0, 4)):
    """Soft drop shadow under an RGBA text layer (legibility on bright ground)."""
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(radius))
    a = a.point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, offset)
    out.alpha_composite(layer)
    return out


def card_hook():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    l1, l2 = "WHAT DID WE DO", "TO THIS C63?"
    maxw = SAFE["x1"] - SAFE["x0"] - 20
    size = 200
    while d.textlength(l1, font=font(size)) > maxw:
        size -= 2
    f = font(size)
    x = SAFE["x0"] + 10
    y = SAFE["y0"] + 70                       # 40 px lower than v1: clears the grid's 3:4 crop
    asc, desc = f.getmetrics()
    lh = int(size * 0.92)
    d.text((x, y), l1, font=f, fill=(255, 255, 255, 255))
    d.text((x, y + lh), l2, font=f, fill=(255, 255, 255, 255))
    # red underline under "C63" only
    pre = "TO THIS "
    ux0 = x + d.textlength(pre, font=f)
    ux1 = ux0 + d.textlength("C63", font=f)
    bb = d.textbbox((x, y + lh), "C63", font=f)
    uy = bb[3] + 14
    d.rectangle([ux0, uy, ux1, uy + 12], fill=RED + (255,))
    return shadowed(im, radius=18, alpha=0.6), dict(size=size, underline=(ux0, uy, ux1, uy + 12),
                                                    bbox=(x, y, x + maxw, uy + 12))


def card_stamp(text, nchars):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(72)
    d.text((SAFE["x0"] + 10, SAFE["y0"] + 20), text[:nchars], font=f, fill=(255, 255, 255, 255))
    return shadowed(im, radius=8, alpha=0.6, offset=(0, 3))


def card_new():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(380)
    tw = d.textlength("NEW.", font=f)
    cx = (SAFE["x0"] + SAFE["x1"]) / 2
    bb = d.textbbox((0, 0), "NEW.", font=f)
    th = bb[3] - bb[1]
    y = (SAFE["y0"] + SAFE["y1"]) / 2 - th / 2 - bb[1]
    d.text((cx - tw / 2, y), "NEW.", font=f, fill=RED + (255,))
    return shadowed(im, radius=22, alpha=0.7, offset=(0, 6))


def card_endmark():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    icon = Image.open(ICON).convert("RGBA")
    iw = 380
    icon = icon.resize((iw, int(icon.height * iw / icon.width)), Image.LANCZOS)
    x0 = (W - iw) // 2
    y0 = 700
    im.alpha_composite(icon, (x0, y0))
    # official five-segment stripe from fd_brand.ACCENT_STRIPE (black vanishes on dark: correct)
    sy = y0 + icon.height + 34
    sh = 12
    d = ImageDraw.Draw(im)
    x = float(x0)
    for col, share in fd_brand.ACCENT_STRIPE:
        w = share * iw
        d.rectangle([round(x), sy, round(x + w) - 1, sy + sh - 1], fill=fd_brand.rgb(col) + (255,))
        x += w
    f = font(60)
    txt = "DM TO BOOK YOUR BUILD"
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2, sy + sh + 90), txt, font=f, fill=(255, 255, 255, 255))
    return im


def to_np(im):
    a = np.asarray(im).astype(np.float32)
    return a[..., :3], a[..., 3:4] / 255.0


def comp(frame, layer, opacity=1.0):
    rgb, a = layer
    if opacity <= 0:
        return frame
    a = a * opacity
    f = frame.astype(np.float32)
    return (f * (1 - a) + rgb * a).astype(np.uint8)


# ---------------------------------------------------------------------------
# Grade: gentle cinematic. Slight S-contrast, lifted blacks, a touch of warmth.
# One LUT for all three clips; per-clip exposure trim to sit them together.
# ---------------------------------------------------------------------------
TRIM = {"IMG_0590.MOV": 1.00, "IMG_0325.MOV": 0.96, "IMG_0579.MOV": 0.97}
LUTS = {}


def grade(fr, src):
    if src not in LUTS:
        x = np.arange(256, dtype=np.float32) / 255.0
        x = np.clip(x * TRIM[src], 0, 1)
        s = x + 0.10 * (x - 0.5) * (1 - np.abs(2 * x - 1))
        s = 0.035 + s * 0.945
        r = np.clip(s * 1.025 + 0.005, 0, 1)
        g = np.clip(s * 1.005, 0, 1)
        b = np.clip(s * 0.965, 0, 1)
        LUTS[src] = np.stack([(c * 255 + 0.5).astype(np.uint8) for c in (r, g, b)], axis=1)  # 256x3
    lut = LUTS[src]
    out = np.empty_like(fr)
    for c in range(3):
        out[..., c] = lut[fr[..., c], c]
    # slight desaturation so gloss (0325) and satin-looking (0590) sit together
    gray = fr.mean(axis=2, keepdims=True)
    return np.clip(out * 0.92 + gray * 0.08, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Decode / track / redact
# ---------------------------------------------------------------------------
def decode(src_path, t_in, dur):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t_in:.3f}", "-i", str(src_path), "-t", f"{dur:.3f}",
           "-map", "0:v:0", "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    sz = SW * SH * 3
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz:
            break
        yield np.frombuffer(b, np.uint8).reshape(SH, SW, 3)
    p.wait()


class Tracker:
    """Template match at half res within a search window; positions smoothed later."""

    def __init__(self, first, box, search=90):
        self.box = box
        g = cv2.cvtColor(first, cv2.COLOR_RGB2GRAY)
        x0, y0, x1, y1 = box
        self.tmpl = cv2.resize(g[y0:y1, x0:x1], None, fx=0.5, fy=0.5)
        self.pos = (x0, y0)
        self.search = search
        self.w, self.h = x1 - x0, y1 - y0

    def step(self, fr):
        g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY)
        px, py = self.pos
        sx0 = max(0, px - self.search); sy0 = max(0, py - self.search)
        sx1 = min(SW, px + self.w + self.search); sy1 = min(SH, py + self.h + self.search)
        win = cv2.resize(g[sy0:sy1, sx0:sx1], None, fx=0.5, fy=0.5)
        res = cv2.matchTemplate(win, self.tmpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        nx, ny = sx0 + loc[0] * 2, sy0 + loc[1] * 2
        self.pos = (nx, ny)
        return (nx, ny, nx + self.w, ny + self.h), score


def colour_field(fr, box, blocks, feather=24):
    """Collapse box to a blocks[0] x blocks[1] colour field with a feathered outer edge.
    The box itself is always 100% covered; the feather lives outside it."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    e = feather
    X0, Y0, X1, Y1 = max(0, x0 - e), max(0, y0 - e), min(SW, x1 + e), min(SH, y1 + e)
    reg = fr[Y0:Y1, X0:X1].astype(np.float32)
    small = cv2.resize(fr[y0:y1, x0:x1], blocks, interpolation=cv2.INTER_AREA)
    fill = cv2.resize(small, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_NEAREST).astype(np.float32)
    fill[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = cv2.resize(small, (x1 - x0, y1 - y0),
                                                       interpolation=cv2.INTER_NEAREST)
    mask = np.zeros((Y1 - Y0, X1 - X0), np.float32)
    mask[max(0, y0 - Y0 - e // 2):y1 - Y0 + e // 2, max(0, x0 - X0 - e // 2):x1 - X0 + e // 2] = 1.0
    mask = cv2.GaussianBlur(mask, (0, 0), e / 3)
    mask[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = 1.0
    m = mask[..., None]
    out = fr.copy()
    out[Y0:Y1, X0:X1] = (reg * (1 - m) + fill * m).astype(np.uint8)
    return out


def smooth(boxes, k=5):
    a = np.array(boxes, np.float32)
    if len(a) < k:
        return a
    pad = k // 2
    ap = np.pad(a, ((pad, pad), (0, 0)), mode="edge")
    ker = np.ones(k) / k
    return np.stack([np.convolve(ap[:, i], ker, mode="valid") for i in range(4)], axis=1)


def crop_rect(shot, u):
    (cx0, cy0, w0), (cx1, cy1, w1) = shot["crop"]
    e = u  # linear push (constant speed reads as a camera move)
    cx, cy, w = cx0 + (cx1 - cx0) * e, cy0 + (cy1 - cy0) * e, w0 + (w1 - w0) * e
    h = w * 16 / 9
    x0 = min(max(cx - w / 2, 0), SW - w)
    y0 = min(max(cy - h / 2, 0), SH - h)
    return x0, y0, w, h


def render_shot(raw, shot):
    """Returns list of (frame 1080x1920 uint8, meta) for a shot, redacted and graded."""
    frames = list(decode(raw / shot["src"], shot["t_in"], shot["dur"]))
    n = shot["n"]
    if len(frames) < n:
        frames += [frames[-1]] * (n - len(frames))
    frames = frames[:n]
    tracks = {}
    for name, box, blocks in shot["redact"]:
        tr = Tracker(frames[0], box)
        bxs, scores = [], []
        for fr in frames:
            b, sc = tr.step(fr)
            bxs.append(b); scores.append(sc)
        tracks[name] = (smooth(bxs), blocks, scores)
    out = []
    for i, fr in enumerate(frames):
        meta = {"boxes": {}}
        for name, (bxs, blocks, scores) in tracks.items():
            b = bxs[i]
            fr = colour_field(fr, b, blocks)
            meta["boxes"][name] = [float(v) for v in b]
            meta.setdefault("scores", {})[name] = float(scores[i])
        x0, y0, w, h = crop_rect(shot, i / max(1, n - 1))
        M = np.float32([[W / w, 0, -x0 * W / w], [0, H / h, -y0 * H / h]])
        o = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_AREA if w > W else cv2.INTER_CUBIC)
        meta["crop"] = (x0, y0, w, h)
        o = grade(o, shot["src"])
        if shot.get("darken"):
            k = min(1.0, i / 6.0)
            o = (o.astype(np.float32) * (1 - 0.72 * k)).astype(np.uint8)
            o = cv2.GaussianBlur(o, (0, 0), 1 + 5 * k)
        # output-space redaction boxes for QA
        meta["out_boxes"] = {nm: [(bb[0] - x0) * W / w, (bb[1] - y0) * H / h,
                                  (bb[2] - x0) * W / w, (bb[3] - y0) * H / h]
                             for nm, bb in meta["boxes"].items()}
        out.append((o, meta))
    return out


def overlay_text(o, tsec, layers):
    for c in CARDS:
        if not (c["t_in"] - 1e-6 <= tsec < c["t_out"] - 1e-6):
            continue
        if c["id"] == "hook":
            o = comp(comp(o, layers["scrim_hook"]), layers["hook"])
        elif c.get("typed"):
            o = comp(o, layers["scrim_stamp"])
            k = int((tsec - c["t_in"]) * FPS) // 2 + 1                # 2 frames per character
            k = min(k, len(c["id"]))
            o = comp(o, layers[(c["id"], k)])
        elif c["id"] == "NEW.":
            o = comp(o, layers["NEW."])
        elif c["id"] == "endmark":
            op = min(1.0, (tsec - c["t_in"]) * FPS / 6.0)
            o = comp(o, layers["endmark"], op)
    return o


def scrim(alpha, height):
    """Soft top gradient so white type holds over a bright car or shop lights."""
    y = np.arange(H, dtype=np.float32)[:, None, None]
    a = np.clip(1 - y / height, 0, 1) ** 1.6 * alpha
    return np.zeros((H, W, 3), np.float32), np.broadcast_to(a, (H, W, 1)).copy()


def build_layers():
    hook, info = card_hook()
    L = {"hook": to_np(hook), "scrim_hook": scrim(0.55, 900), "scrim_stamp": scrim(0.50, 560), "NEW.": to_np(card_new()), "endmark": to_np(card_endmark())}
    for txt in ("SEP 29", "OCT 7"):
        for k in range(1, len(txt) + 1):
            L[(txt, k)] = to_np(card_stamp(txt, k))
    return L, info


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
def read_audio(path, t_in, dur):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t_in:.3f}", "-i", str(path), "-t", f"{dur:.3f}",
           "-map", "0:a:0", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    a = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
    return a.reshape(-1, 2).copy()


def fade(a, fin=0.008, fout=0.012):
    n = len(a); i = int(fin * SR); o = int(fout * SR)
    if i: a[:i] *= np.linspace(0, 1, i)[:, None]
    if o: a[-o:] *= np.linspace(1, 0, o)[:, None]
    return a


GAIN_DB = {"hook": 0, "before": 0, "parts1": 0, "parts2": 0, "parts3": 0,
           "coldstart": 0, "piping": 0, "rev": 0, "end": 0}
A_POST = {"before": 1.20}      # L-cut: the stock car's rev and idle carry 1.2 s into the parts


def build_audio(raw, wav_path):
    N = int(round(NFRAMES / FPS * SR))      # exactly the video length, so the mux drops no frames
    mix = np.zeros((N + SR, 2), np.float32)
    # Each window's own audio only. J-cut (a_pre): the cold start's own cranking comes in
    # under the last parts cut; L-cut (A_POST): the stock rev decays under the first.
    for s in SHOTS:
        pre, post = s.get("a_pre", 0.0), A_POST.get(s["name"], 0.0)
        dur = s["dur"] + pre + post
        a = read_audio(raw / s["src"], s["t_in"] - pre, dur)
        a = a[: int(round(dur * SR))]
        a = fade(a, fin=0.0 if s["name"] == "hook" else (0.15 if pre else 0.008),
                 fout=1.3 if s["name"] == "end" else (0.50 if post else 0.012)) * (10 ** (GAIN_DB[s["name"]] / 20))
        i0 = int(round((s["t0"] - pre) * SR))
        mix[i0:i0 + len(a)] += a
    mix = mix[:N]
    mix *= 0.7 / max(1e-9, float(np.abs(mix).max()))   # headroom before 16-bit; loudnorm sets level
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes()
    import wave
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm)


def loudnorm(src, dst):
    target = "I=-14:TP=-1.5:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"loudnorm={target}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm={target}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:"
          f"linear=true,aresample={SR}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", str(SR), str(dst)], check=True)
    return js


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--stills", action="store_true", help="only write check stills to exports/qa/stills")
    ap.add_argument("--audio-only", action="store_true", help="reuse <work>/video.mp4, rebuild sound + mux")
    ap.add_argument("--work", default=os.environ.get("TMPDIR", "/tmp") + "/fd_c63_work")
    a = ap.parse_args()
    raw = Path(a.raw)
    work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    layers, info = build_layers()
    print("hook text size", info["size"], "bbox", info["bbox"])

    if a.stills:
        sd = QA / "stills"; sd.mkdir(exist_ok=True)
        for s in SHOTS:
            fr = render_shot(raw, s)
            for j in (0, len(fr) // 2, len(fr) - 1):
                o, _ = fr[j]
                tsec = s["t0"] + j / FPS
                Image.fromarray(overlay_text(o, tsec, layers)).save(sd / f"{s['name']}_{j:03d}.jpg", quality=88)
        return

    if a.audio_only:
        return finish(raw, work)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-vf", "scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv420p",
                            "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17",
                            "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-movflags", "+faststart", str(work / "video.mp4")],
                           stdin=subprocess.PIPE)
    log = []
    fidx = 0
    for s in SHOTS:
        for j, (o, meta) in enumerate(render_shot(raw, s)):
            tsec = fidx / FPS
            o = overlay_text(o, tsec, layers)
            if s["name"] == "hook" and j == 12:
                Image.fromarray(o).save(OUT_COVER, quality=93)
            enc.stdin.write(o.tobytes())
            if meta["boxes"]:
                log.append(dict(frame=fidx, t=round(tsec, 3), shot=s["name"], **meta))
            if s["name"].startswith("parts") or s["name"] == "piping":
                # every frame of the parts (brand scan) and of the piping close-up
                sd = work / "scan_frames"; sd.mkdir(exist_ok=True)
                Image.fromarray(o).resize((540, 960), Image.LANCZOS).save(
                    sd / f"{'parts' if s['name'].startswith('parts') else 'piping'}__{fidx:04d}.jpg", quality=92)
            if meta["boxes"] and fidx % 2 == 0:
                # QA crops written now from the final frame (text included)
                save_qa_tiles(o, meta, s["name"], fidx, work)
            fidx += 1
    enc.stdin.close(); enc.wait()
    (work / "redaction_log.json").write_text(json.dumps(log))
    print("frames", fidx)
    finish(raw, work)


def finish(raw, work):

    build_audio(raw, work / "mix.wav")
    js = loudnorm(work / "mix.wav", work / "mix_ln.wav")
    print("loudnorm pass1", json.dumps({k: js[k] for k in ("input_i", "input_tp", "input_lra")}))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(work / "video.mp4"), "-i", str(work / "mix_ln.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", str(OUT_MP4)], check=True)
    make_qa_sheets(work)


def save_qa_tiles(o, meta, shot, fidx, work):
    d = work / "qa_tiles"; d.mkdir(exist_ok=True)
    for nm, (x0, y0, x1, y1) in meta["out_boxes"].items():
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bw, bh = max(x1 - x0, 60), max(y1 - y0, 60)
        side = int(max(bw, bh) * 1.8)
        X0, Y0 = int(cx - side / 2), int(cy - side / 2)
        X1, Y1 = X0 + side, Y0 + side
        if X1 < 0 or Y1 < 0 or X0 > W or Y0 > H:
            continue                                                 # box off-frame in this crop
        pad = np.zeros((side, side, 3), np.uint8)
        sx0, sy0, sx1, sy1 = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
        pad[sy0 - Y0:sy1 - Y0, sx0 - X0:sx1 - X0] = o[sy0:sy1, sx0:sx1]
        tile = Image.fromarray(pad).resize((240, 240), Image.LANCZOS)
        ImageDraw.Draw(tile).text((4, 2), f"{fidx/FPS:05.2f}s", fill=(255, 255, 0))
        tile.save(d / f"{shot}__{nm}__{fidx:04d}.png")


def make_qa_sheets(work):
    d = work / "qa_tiles"
    groups = {}
    for p in sorted(d.glob("*.png")):
        shot, nm, _ = p.stem.split("__")
        groups.setdefault((shot, nm), []).append(p)
    for (shot, nm), ps in groups.items():
        cols = 8
        rows = (len(ps) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 240, rows * 240), (20, 20, 20))
        for i, p in enumerate(ps):
            sheet.paste(Image.open(p), ((i % cols) * 240, (i // cols) * 240))
        sheet.save(QA / f"redaction_{shot}_{nm}.jpg", quality=90)
    # brand scan: every frame of the parts section, and every frame of the piping shot,
    # 540x960 tiles (half the delivered size), 6 x 2 per sheet, stamped with timeline time
    for old in QA.glob("brandscan_*.jpg"):
        old.unlink()
    for old in QA.glob("piping_*.jpg"):
        old.unlink()
    sf = work / "scan_frames"
    for kind, stem in (("parts", "brandscan_parts"), ("piping", "piping_every_frame")):
        ps = sorted(sf.glob(f"{kind}__*.jpg"))
        for k in range(0, len(ps), 12):
            sheet = Image.new("RGB", (6 * 540, 2 * 960), (20, 20, 20))
            for i, pth in enumerate(ps[k:k + 12]):
                tile = Image.open(pth)
                fi = int(pth.stem.split("__")[1])
                d = ImageDraw.Draw(tile)
                d.rectangle([0, 0, 170, 44], fill=(0, 0, 0))
                d.text((6, 4), f"{fi / FPS:05.2f}s f{fi}", font=font(36), fill=(255, 255, 0))
                sheet.paste(tile, ((i % 6) * 540, (i // 6) * 960))
            sheet.save(QA / f"{stem}_{k // 12 + 1:02d}.jpg", quality=88)
    # whole render, 1 frame per 0.5 s
    sd = work / "every05"; sd.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT_MP4), "-vf",
                    "fps=2,scale=270:-2,drawtext=fontfile=" + FONT +
                    ":text='%{pts\\:hms}':x=6:y=6:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=9x4",
                    "-frames:v", "1", str(QA / "render_every_0.5s.jpg")], check=True)


if __name__ == "__main__":
    main()
