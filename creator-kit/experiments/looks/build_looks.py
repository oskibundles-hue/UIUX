#!/usr/bin/env python3
"""Talking-head looks: one take in, several styled cuts out (all proposed until Omarie picks).

    python3 build_looks.py base  --spec spec_sep03.json --src take.mov --work work [--size 2160x3840]
    python3 build_looks.py looks --spec spec_sep03.json --work work [--only mono,framed]
    python3 build_looks.py sheets --spec spec_sep03.json --work work

base   cuts the spec's keep ranges out of the take, grades them with the kit LUT at
       W x H / 30, and loudness-normalises the audio once (-14 LUFS, limiter 0.84).
looks  composes every look over the same base, frame by frame (PIL), and writes
       work/<look>.mp4 plus work/manifest.json (every word put on screen, with its box).
sheets grid still, review contact sheet, 3x2 grid video, the 2x2 grid and the cycle reel.

Size comes from --size, else the spec's "size", else 1080x1920. Every pixel constant
below is written at 1080 wide and goes through px(), so one layout serves every size.
base records the size in timeline.json and the later steps refuse a different one.

Every word on screen comes from spec phrases, which come from the transcript; qa.py
checks that, the safe zones and the loudness before anything goes to nq-check.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "../../remotion/public/fonts")
FPS = 30

# theme.ts values (Anti Stock / @nq.young)
YELLOW, ORANGE, DEEP, WHITE, BLACK = "#FBD101", "#E75522", "#C4801B", "#FDFDFD", "#0B0B0B"


def set_size(w, h):
    """Frame size and everything derived from it. S scales the 1080-wide constants."""
    global W, H, S, SAFE, CX, MAXW
    W, H, S = w, h, w / 1080
    # safe zone for Instagram UI, from theme.ts: top .135, bottom .245, left .067, right .176
    SAFE = (round(W * 0.067), round(H * 0.135), round(W * (1 - 0.176)), round(H * (1 - 0.245)))
    CX = (SAFE[0] + SAFE[2]) // 2 + px(30)  # centred text sits a touch right of the safe band's centre
    MAXW = 2 * (SAFE[2] - CX)


def px(v):
    return round(v * S)


def resolve_size(a, spec):
    s = a.size or "x".join(map(str, spec.get("size", (1080, 1920))))
    w, h = map(int, s.lower().split("x"))
    return w, h


S = 1
set_size(1080, 1920)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(cmd[:6])} ...\n{r.stderr[-1500:]}")
    return r


def load_spec(path):
    spec = json.load(open(path))
    spec["_dir"] = os.path.dirname(os.path.abspath(path))
    return spec


def load_timeline(a, spec):
    """timeline.json, after checking base was built at the size asked for."""
    tl = json.load(open(os.path.join(a.work, "timeline.json")))
    want, have = resolve_size(a, spec), tuple(tl.get("size", (1080, 1920)))
    if want != have:
        sys.exit(f"base in {a.work} is {have[0]}x{have[1]}, asked for {want[0]}x{want[1]}: run base again")
    set_size(*have)
    return tl


# ---------------------------------------------------------------- base

def cmd_base(a):
    spec = load_spec(a.spec)
    set_size(*resolve_size(a, spec))
    os.makedirs(a.work, exist_ok=True)
    lut = os.path.normpath(os.path.join(spec["_dir"], spec["lut"]))
    # One seeked input per keep range: trimming a single [0:v] six ways buffers decoded frames
    # for every branch, and at 2160x3840 that ran ffmpeg to 9.7 GB and an OOM kill (2026-10-27).
    inputs, parts, labels = [], [], []
    last = len(spec["keep"]) - 1
    for i, (s, e) in enumerate(spec["keep"]):
        d = e - s
        inputs += ["-ss", f"{s}", "-t", f"{d:.3f}", "-i", a.src]
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS},"
                     f"scale={W}:{H}:flags=lanczos:in_color_matrix=bt709:out_color_matrix=bt709,"
                     f"format=gbrp,lut3d='{lut}',format=yuv420p[v{i}]")
        # the last cut ends on silence: a 60 ms fade, then the final 50 ms at zero (Locked-On bar)
        fade = f"st={d - 0.11:.3f}:d=0.06" if i == last else f"st={d - 0.015:.3f}:d=0.015"
        parts.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,"
                     f"afade=t=in:d=0.015,afade=t=out:{fade}[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    fc = ";".join(parts) + f";{''.join(labels)}concat=n={len(labels)}:v=1:a=1[v][a]"
    base = os.path.join(a.work, "base.mp4")
    raw = os.path.join(a.work, "base_raw.wav")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc,
         "-map", "[v]", "-c:v", "libx264", "-crf", "12", "-preset", "medium",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", base,
         "-map", "[a]", "-c:a", "pcm_s16le", raw])
    # two-pass loudnorm to -14 LUFS, then the kit's limiter at 0.84
    r = run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
             "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true,"
          # limit at 4x so inter-sample peaks are caught: at 48 kHz the 0.84 limiter left -1.4 dBTP
          f"aresample=192000,alimiter=limit=0.84:attack=5:release=60:level=false,aresample=48000,"
          # 0.3 dB of headroom for the AAC encode, which added 0.1 dB of true peak on the Sep 3 take
          f"volume=-0.3dB")
    run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", ln, "-c:a", "pcm_s16le",
         os.path.join(a.work, "base.wav")])
    face = find_face(base)
    words = remap_words(spec)
    json.dump({"size": [W, H], "face": face, "phrases": words, "frames": nframes(base)},
              open(os.path.join(a.work, "timeline.json"), "w"), indent=1)
    print(f"base: {W}x{H}, {nframes(base)} frames, face {face}, loudness in {m['input_i']} LUFS")


def nframes(path):
    r = run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
             "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path])
    return int(r.stdout.strip())


def find_face(base):
    """Median face box over the base (one frame in 15), so crops and punch-ins centre on it.
    YuNet (opencv_zoo, MIT), because the Haar cascade jumped all over this footage."""
    import cv2
    det = cv2.FaceDetectorYN.create(os.path.join(HERE, "face_detection_yunet_2023mar.onnx"), "",
                                    (W // 2, H // 2), 0.7)
    boxes = []
    for i, f in enumerate(frames(base)):
        if i % 15:
            continue
        _, faces = det.detect(cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2BGR), (W // 2, H // 2)))
        if faces is not None:
            fc = max(faces, key=lambda fc: fc[2] * fc[3])
            x, y, w, h = fc[:4] * 2
            boxes.append((x + w / 2, y + h / 2, h, fc[11] + fc[13]))  # mouth corners' mean y, x2 scale
    if not boxes:
        return {"cx": W / 2, "cy": H * 0.42, "h": H * 0.3, "mouth": H * 0.5, "found": 0}
    cx, cy, fh, mouth = np.median(np.array(boxes), axis=0)
    return {"cx": round(float(cx)), "cy": round(float(cy)), "h": round(float(fh)),
            "mouth": round(float(mouth)), "found": len(boxes)}


def remap_words(spec):
    """Source-time words -> base-time words. A word that starts in a cut pause moves to the
    next kept range; ends are clamped to their range."""
    starts, acc = [], 0.0
    for s, e in spec["keep"]:
        starts.append(acc)
        acc += e - s

    def to_base(t):
        for (s, e), o in zip(spec["keep"], starts):
            if t < s:
                return o
            if t <= e:
                return o + (t - s)
        return acc

    def range_end(t):
        return next((e for s, e in spec["keep"] if t <= e), spec["keep"][-1][1])

    out = []
    for p in spec["phrases"]:
        ws = []
        for w in p["words"]:
            t0 = to_base(w["t0"])
            t1 = max(t0 + 0.12, to_base(min(w["t1"], range_end(w["t0"]))))
            ws.append({"w": w["w"], "t0": round(t0, 3), "t1": round(t1, 3), "key": w["key"]})
        out.append({"text": p["text"], "words": ws})
    # a phrase holds until the next one starts, at most 1.2 s past its last word
    for i, p in enumerate(out):
        nxt = out[i + 1]["words"][0]["t0"] if i + 1 < len(out) else acc
        p["t0"], p["t1"] = p["words"][0]["t0"], round(min(nxt, p["words"][-1]["t1"] + 1.2), 3)
        for j, w in enumerate(p["words"]):
            w["on"] = w["t0"]
            w["off"] = p["words"][j + 1]["t0"] if j + 1 < len(p["words"]) else p["t1"]
    return out


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=in_color_matrix=bt709",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()


# ---------------------------------------------------------------- type

_font_cache, _text_cache = {}, {}


def font(name, size, weight=None):
    """size is at 1080 wide; scaled here."""
    size = px(size)
    k = (name, size, weight)
    if k not in _font_cache:
        f = ImageFont.truetype(os.path.join(FONTS, name), size)
        if weight:
            f.set_variation_by_axes([weight, 100])
        _font_cache[k] = f
    return _font_cache[k]


def text_img(s, f, fill, stroke=0, stroke_fill=BLACK, shadow=0):
    """Rendered word or line as RGBA, cropped to its ink plus padding, cached."""
    k = (s, id(f), fill, stroke, shadow)
    if k in _text_cache:
        return _text_cache[k]
    pad = stroke + shadow * 3 + px(4) + (px(30) if stroke >= px(7) else 0)
    l, t, r, b = f.getbbox(s, stroke_width=stroke)
    asc, desc = f.getmetrics()
    w, h = r - l + 2 * pad, asc + desc + 2 * pad
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", (w, h))
        ImageDraw.Draw(sh).text((pad - l, pad + shadow), s, font=f, fill=(0, 0, 0, 170),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(shadow)))
        d = ImageDraw.Draw(im)
    d.text((pad - l, pad), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    _text_cache[k] = (im, pad, asc)
    return _text_cache[k]


def wrap(words, f, maxw, space):
    """Greedy wrap of word dicts into lines that fit maxw."""
    lines, cur, cw = [], [], 0
    for w in words:
        ww = f.getlength(w["s"])
        if cur and cw + space + ww > maxw:
            lines.append(cur)
            cur, cw = [], 0
        cw += (space if cur else 0) + ww
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def tag(img, s, f, x, y, fill, ink, ph=20, pv=16):
    """A box fitted to the caps of s (same height for every line in a font), text centred in it."""
    ph, pv = px(ph), px(pv)
    _, ct, _, cb = f.getbbox("H")
    l, _, r, _ = f.getbbox(s)
    box = (x, y, x + (r - l) + 2 * ph, y + (cb - ct) + 2 * pv)
    ImageDraw.Draw(img).rectangle(box, fill=fill)
    im, pad, _ = text_img(s, f, ink)
    img.paste(im, (x + ph - pad, y + pv - pad - ct), im)
    return box


_glow_cache = {}


def with_glow(im):
    """Adds a soft dark halo under rendered type so it holds on bright backgrounds."""
    k = id(im)
    if k not in _glow_cache:
        a = im.getchannel("A").filter(ImageFilter.MaxFilter(2 * px(7) + 1)).filter(ImageFilter.GaussianBlur(px(22)))
        halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
        halo.putalpha(a.point(lambda v: int(v * 0.55)))
        _glow_cache[k] = Image.alpha_composite(halo, im)
    return _glow_cache[k]


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- framing

class Frame:
    def __init__(self, tl, spec):
        self.face = tl["face"]
        self.spec = spec
        self.mouths = set()  # (x, y) of his mouth in output pixels, for qa's mouth check
        self.cuts, acc = [], 0.0
        for s, e in spec["keep"]:
            self.cuts.append(acc)
            acc += e - s

    def seg(self, t):
        return max(i for i, c in enumerate(self.cuts) if c <= t + 1e-6)

    def punch(self, t):
        p = self.spec["punch"]
        return p[self.seg(t) % len(p)]

    def fill(self, img, box_w, box_h, scale, face_y=0.42, face_frac=None, at=(0, 0)):
        """Crop the frame to box_w:box_h around the face at the given zoom and resize;
        the face centre lands face_y of the way down the box, which is pasted at `at`."""
        fx, fy = self.face["cx"], self.face["cy"]
        aspect = box_w / box_h
        cw = min(W, H * aspect) / scale
        ch = cw / aspect
        if face_frac:  # make the face this fraction of the crop's height
            ch = min(H, self.face["h"] / face_frac)
            cw = ch * aspect
            if cw > W:
                cw, ch = W, W / aspect
        x0 = min(max(fx - cw / 2, 0), W - cw)
        y0 = min(max(fy - ch * face_y, 0), H - ch)
        k = box_h / ch
        self.mouths.add((round(at[0] + (fx - x0) * k), round(at[1] + (self.face["mouth"] - y0) * k)))
        return img.resize((box_w, box_h), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


# ---------------------------------------------------------------- looks
# Each look is a function (img, t, ctx) -> img, and logs the words it puts on screen
# through ctx.put(kind, text, box) so qa.py can check them.

def active(phrases, t):
    for p in phrases:
        if p["t0"] <= t < p["t1"]:
            return p
    return None


def place_lines(ctx, lines, f, space, cx, top, lead, draw_word):
    """Lay out wrapped lines centred on cx from top; draw_word(word, x, y) draws one word."""
    y = top
    for line in lines:
        widths = [f.getlength(w["s"]) for w in line]
        lw = sum(widths) + space * (len(line) - 1)
        x = cx - lw / 2
        for w, ww in zip(line, widths):
            draw_word(w, x, y, ww)
            x += ww + space
        y += lead
    return y


def look_highlighter(img, t, ctx):
    """Archivo 800 captions, the word being said gets a yellow marker swipe."""
    img = ctx.fr.fill(img, W, H, ctx.fr.punch(t))
    p = active(ctx.phrases, t)
    if not p:
        return img
    f = font("Archivo.ttf", 74, 800)
    words = [dict(w, s=w["w"]) for w in p["words"]]
    lines = wrap(words, f, MAXW, px(20))
    lead = px(96)
    top = SAFE[3] - px(24) - lead * len(lines)
    d = ImageDraw.Draw(img, "RGBA")
    asc = f.getmetrics()[0]

    def draw(w, x, y, ww):
        on = w["on"] <= t < w["off"]
        if on:
            k = ease_out((t - w["on"]) * FPS / 4)
            d.rounded_rectangle((x - px(12), y + px(4), x - px(12) + (ww + px(24)) * k, y + asc + px(18)),
                                px(10), fill=YELLOW)
        im, pad, _ = text_img(w["s"], f, BLACK if on else WHITE, shadow=0 if on else px(6))
        img.paste(im, (int(x - pad), int(y - pad + px(8))), im)

    place_lines(ctx, lines, f, px(20), CX, top, lead, draw)
    ctx.put("caption", p["text"], (CX - MAXW / 2, top, CX + MAXW / 2, top + lead * len(lines)), p)
    return img


def look_one_word(img, t, ctx):
    """One word at a time, big Anton, key words in yellow, pop in."""
    seg_t = t - ctx.fr.cuts[ctx.fr.seg(t)]
    img = ctx.fr.fill(img, W, H, ctx.fr.punch(t) * (1 + 0.012 * seg_t))
    p = active(ctx.phrases, t)
    if not p:
        return img
    w = next((w for w in p["words"] if w["on"] <= t < w["off"]), None)
    if not w:
        return img
    s = w["w"].strip(",.").upper()
    f = font("Anton-Regular.ttf", 168)
    size = 168
    while f.getlength(s) * 1.18 + px(14) > MAXW:  # fits at the top of the pop, stroke included
        size -= 8
        f = font("Anton-Regular.ttf", size)
    im, pad, asc = text_img(s, f, YELLOW if w["key"] else WHITE, stroke=px(7), shadow=px(8))
    im = with_glow(im)
    k = 1.18 - 0.18 * ease_out((t - w["on"]) * FPS / 4)
    if k > 1.001:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.BILINEAR)
        pad *= k
    cy = round(H * 0.665)  # under his chin (YuNet at 1080: mouth ~930, chin ~1110 on this take)
    x, y = int(CX - im.width / 2), int(cy - im.height / 2)
    img.paste(im, (x, y), im)
    ctx.put("caption", w["w"], (x + pad, y + pad, x + im.width - pad, y + im.height - pad), w)
    return img


def look_tag_stack(img, t, ctx):
    """Black-on-yellow tag boxes that stack line by line as he speaks; orange hook tab up top."""
    img = ctx.fr.fill(img, W, H, ctx.fr.punch(t))
    if t >= ctx.phrases[1]["t0"]:  # phrase 1 is the hook line, so the tab waits until it's said
        hook = ctx.spec["hook_alt"][0].strip(",.").upper()
        box = tag(img, hook, font("Anton-Regular.ttf", 62), SAFE[0], SAFE[1] + px(10), ORANGE, WHITE, 18, 14)
        ctx.put("hook", ctx.spec["hook_alt"][0], box, ctx.phrases[1])
    p = active(ctx.phrases, t)
    if not p:
        return img
    f = font("Anton-Regular.ttf", 88)
    said = [dict(w, s=w["w"].upper()) for w in p["words"] if w["on"] <= t]
    allw = [dict(w, s=w["w"].upper()) for w in p["words"]]
    lines = wrap(allw, f, SAFE[2] - SAFE[0] - px(26) - 2 * px(20) - px(6), px(22))
    lead = px(114)
    top = SAFE[3] - px(10) - lead * len(lines)
    n, y = len(said), top
    for li, line in enumerate(lines):
        shown = line[:max(0, n)]
        n -= len(line)
        if not shown:
            break
        tag(img, " ".join(w["s"] for w in shown), f, SAFE[0] + (li % 2) * px(26), y, YELLOW, BLACK)
        y += lead
    ctx.put("caption", p["text"], (SAFE[0], top, SAFE[2], top + lead * len(lines)), p)
    return img


def look_framed(img, t, ctx):
    """Yellow page, the take in a rounded card, black headline above, caption pill inside."""
    page = Image.new("RGB", (W, H), YELLOW)
    d = ImageDraw.Draw(page)
    hf = font("Anton-Regular.ttf", 112)
    words = [dict(w=x, s=x.strip(",.").upper()) for x in ctx.spec["hook"][0].split()]
    lines = wrap(words, hf, MAXW, px(24))
    y, half = SAFE[1] + px(6), 0
    for line in lines:
        s = " ".join(w["s"] for w in line)
        im, pad, _ = text_img(s, hf, BLACK)
        page.paste(im, (int(CX - im.width / 2), y - pad), im)
        half = max(half, im.width / 2 - pad)
        y += px(124)
    ctx.put("hook", ctx.spec["hook"][0], (CX - half, SAFE[1], CX + half, y), None)
    cx0, cy0 = px(96), y + px(24)
    cw, ch = W - 2 * cx0, H - px(220) - cy0  # card runs under the UI zone; text doesn't
    # face high in the card so the caption pill sits under his chin; half-strength punch
    card = ctx.fr.fill(img, cw, ch, 1 + (ctx.fr.punch(t) - 1) / 2, face_y=0.30, at=(cx0, cy0))
    d.rounded_rectangle((cx0 - px(7), cy0 - px(7), cx0 + cw + px(7), cy0 + ch + px(7)), px(46), fill=BLACK)
    page.paste(card, (cx0, cy0), rounded_mask(cw, ch, px(40)))
    p = active(ctx.phrases, t)
    if p:
        f = font("Archivo.ttf", 58, 800)
        ws = [dict(w, s=w["w"]) for w in p["words"]]
        lines = wrap(ws, f, cw - px(120), px(16))
        lead = px(74)
        top = SAFE[3] - px(30) - lead * len(lines)
        bw = max(sum(f.getlength(w["s"]) for w in line) + px(16) * (len(line) - 1) for line in lines)
        d.rounded_rectangle((CX - bw / 2 - px(26), top - px(14), CX + bw / 2 + px(26),
                             top + lead * len(lines) + px(4)), px(22), fill=BLACK)

        def draw(w, x, yy, ww):
            on = w["on"] <= t
            im, pad, _ = text_img(w["s"], f, YELLOW if (on and w["key"]) else (WHITE if on else "#6B6B6B"))
            page.paste(im, (int(x - pad), int(yy - pad)), im)

        place_lines(ctx, lines, f, px(16), CX, top, lead, draw)
        ctx.put("caption", p["text"], (CX - bw / 2, top, CX + bw / 2, top + lead * len(lines)), p)
    return page


def look_mono(img, t, ctx):
    """Black and white, only the yellow survives: karaoke caps and a thin yellow border."""
    img = ctx.fr.fill(img, W, H, ctx.fr.punch(t))
    a = np.asarray(img).astype(np.float32) / 255
    y = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    y = np.clip((y - 0.45) * 1.28 + 0.45, 0, 1) ** 1.05
    img = Image.fromarray((np.repeat(y[..., None], 3, 2) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle((px(26), px(26), W - 1 - px(26), H - 1 - px(26)), outline=YELLOW, width=px(5))
    p = active(ctx.phrases, t)
    if not p:
        return img
    f = font("Anton-Regular.ttf", 104)
    ws = [dict(w, s=w["w"].upper()) for w in p["words"]]
    lines = wrap(ws, f, MAXW, px(24))
    lead = px(122)
    top = SAFE[3] - px(20) - lead * len(lines)
    d.rectangle((CX - px(70), top - px(34), CX + px(70), top - px(24)), fill=YELLOW)

    def draw(w, x, yy, ww):
        on = w["on"] <= t < w["off"]
        im, pad, _ = text_img(w["s"], f, YELLOW if on else WHITE, stroke=px(5), shadow=px(6))
        img.paste(im, (int(x - pad), int(yy - pad)), im)

    place_lines(ctx, lines, f, px(24), CX, top, lead, draw)
    ctx.put("caption", p["text"], (CX - MAXW / 2, top, CX + MAXW / 2, top + lead * len(lines)), p)
    return img


def look_headline(img, t, ctx):
    """Editorial: a tall black band carries the serif + Anton hook and the captions, so the
    picture below stays clean; orange progress bar along the band's edge."""
    band = px(830)
    page = Image.new("RGB", (W, H), BLACK)
    page.paste(ctx.fr.fill(img, W, H - band, ctx.fr.punch(t), face_y=0.36, at=(0, band)), (0, band))
    d = ImageDraw.Draw(page)
    hook = ctx.spec["hook_alt"][0].strip(",.").split()
    a_s, b_s = " ".join(hook[:2]), " ".join(hook[2:]).upper() + "."
    im1, p1, _ = text_img(a_s, font("InstrumentSerif-Italic.ttf", 104), WHITE)
    im2, p2, _ = text_img(b_s, font("Anton-Regular.ttf", 116), YELLOW)
    x = SAFE[0] + px(8)
    page.paste(im1, (x - p1, SAFE[1] + px(4) - p1), im1)
    page.paste(im2, (x - p2, SAFE[1] + px(118) - p2), im2)
    hook_bottom = SAFE[1] + px(118) + im2.height - 2 * p2
    ctx.put("hook", ctx.spec["hook_alt"][0],
            (x, SAFE[1], x + max(im1.width - 2 * p1, im2.width - 2 * p2), hook_bottom), None)
    d.rectangle((0, band - px(10), int(W * t / ctx.dur), band), fill=ORANGE)
    p = active(ctx.phrases, t)
    if not p or p is ctx.phrases[0]:  # phrase 1 is the headline itself
        return page
    # serif for the plain words, Anton caps for the key ones, left aligned under the hook;
    # shrinks until the block clears the progress bar
    top, size = hook_bottom + px(30), 80
    while True:
        sf, kf, space = font("InstrumentSerif-Italic.ttf", size), font("Anton-Regular.ttf", size * 0.85), px(22)
        ws = [dict(w, s=w["w"].upper().strip(",.") if w["key"] else w["w"], f=kf if w["key"] else sf)
              for w in p["words"]]

        def gap(prev, w):  # extra air where the italic meets Anton, so the words don't touch
            return space + (px(10) if prev and prev["f"] is not w["f"] else 0)

        lines, cur, cw = [], [], 0
        for w in ws:
            ww = w["f"].getlength(w["s"])
            g = gap(cur[-1] if cur else None, w)
            if cur and cw + g + ww > SAFE[2] - x:
                lines.append(cur)
                cur, cw = [], 0
            cw += (g if cur else 0) + ww
            cur.append(w)
        lines.append(cur)
        lead = px(size * 1.2)
        if top + lead * len(lines) <= band - px(30) or size <= 56:
            break
        size -= 4
    asc = max(sf.getmetrics()[0], kf.getmetrics()[0])
    right = x
    for i, ln in enumerate(lines):
        xx, base, prev = x, top + i * lead + asc, None
        for w in ln:
            xx += gap(prev, w) if prev else 0
            col = (YELLOW if w["key"] else WHITE) if w["on"] <= t else "#7A7A7A"
            im, pad, a_ = text_img(w["s"], w["f"], col)
            page.paste(im, (int(xx - pad), int(base - a_ - pad)), im)
            xx += w["f"].getlength(w["s"])
            prev = w
        right = max(right, xx)
    ctx.put("caption", p["text"], (x, top, right, top + lead * len(lines)), p)
    return page


LOOKS = {
    "highlighter": ("Highlighter", look_highlighter),
    "one_word": ("One Word", look_one_word),
    "tag_stack": ("Tag Stack", look_tag_stack),
    "framed": ("Framed", look_framed),
    "mono": ("Mono", look_mono),
    "headline": ("Headline", look_headline),
}


class Ctx:
    def __init__(self, spec, tl):
        self.spec, self.phrases = spec, tl["phrases"]
        self.fr = Frame(tl, spec)
        self.dur = tl["frames"] / FPS
        self.log = {}

    def put(self, kind, text, box, src):
        key = (kind, text)
        if key not in self.log:
            self.log[key] = {"kind": kind, "text": text, "box": [round(v) for v in box],
                             "t0": src["t0"] if src and "t0" in src else 0}
        else:  # keep the widest box seen
            b = self.log[key]["box"]
            self.log[key]["box"] = [min(b[0], round(box[0])), min(b[1], round(box[1])),
                                    max(b[2], round(box[2])), max(b[3], round(box[3]))]


def cmd_looks(a):
    spec = load_spec(a.spec)
    tl = load_timeline(a, spec)
    names = a.only.split(",") if a.only else spec["looks"]
    mpath = os.path.join(a.work, "manifest.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    for name in names:
        title, fn = LOOKS[name]
        ctx = Ctx(spec, tl)
        out = os.path.join(a.work, f"{name}.mp4")
        enc = subprocess.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-", "-i", os.path.join(a.work, "base.wav"),
             "-map", "0:v", "-map", "1:a", "-vf", "scale=out_color_matrix=bt709,format=yuv420p",
             "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-profile:v", "high",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out],
            stdin=subprocess.PIPE)
        for i, f in enumerate(frames(os.path.join(a.work, "base.mp4"))):
            im = fn(Image.fromarray(f), i / FPS, ctx).convert("RGB")
            enc.stdin.write(im.tobytes())
        enc.stdin.close()
        if enc.wait():
            sys.exit(f"encode failed for {name}")
        status = "picked" if name == spec.get("picked") else spec.get("status", "proposed")
        manifest[name] = {"title": title, "file": f"{name}.mp4", "status": status, "size": [W, H],
                          # where his mouth lands across every crop and punch, as an x and y range
                          "mouth": {"x": [min(m[0] for m in ctx.fr.mouths), max(m[0] for m in ctx.fr.mouths)],
                                    "y": [min(m[1] for m in ctx.fr.mouths), max(m[1] for m in ctx.fr.mouths)]},
                          "face_h": round(tl["face"]["h"] * max(ctx.spec["punch"])),
                          "elements": sorted(ctx.log.values(), key=lambda e: e["t0"])}
        json.dump(manifest, open(mpath, "w"), indent=1)
        print(f"{name}: {out}")


# ---------------------------------------------------------------- sheets

def grab(path, t, w):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", path, "-frames:v", "1",
                        "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    import io
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def cmd_sheets(a):
    spec = load_spec(a.spec)
    tl = load_timeline(a, spec)
    # only the looks built at this size; a 4K pass may build just the picked one
    man = json.load(open(os.path.join(a.work, "manifest.json")))
    names = [n for n in spec["looks"] if n in man and os.path.exists(os.path.join(a.work, f"{n}.mp4"))]
    path = lambda n: os.path.join(a.work, f"{n}.mp4")
    label = font("Archivo.ttf", 30, 700)
    # grid still: 3x2 at the "energy drink" line
    t_grid = next(w["on"] for p in tl["phrases"] for w in p["words"] if w["w"].startswith("drink")) + 0.15
    cw, g = px(480), px(24)
    chh = round(cw * H / W)
    rows = (len(names) + 2) // 3
    grid = Image.new("RGB", (3 * cw + 4 * g, rows * (chh + px(56)) + (rows + 1) * g), "#111111")
    d = ImageDraw.Draw(grid)
    for i, n in enumerate(names):
        x, y = g + (i % 3) * (cw + g), g + (i // 3) * (chh + px(56) + g)
        grid.paste(grab(path(n), t_grid, cw), (x, y))
        d.text((x, y + chh + px(12)), f"{i + 1}  {LOOKS[n][0]}  ({man[n]['status']})", font=label, fill=WHITE)
    grid.save(os.path.join(a.work, "grid.png"))
    # review contact sheet: each look at four moments
    ts = [tl["phrases"][k]["words"][-1]["on"] + 0.1 for k in (0, 2, 4, 6)]
    tw, th = px(270), px(480)
    sheet = Image.new("RGB", (4 * tw + 5 * px(8) + px(180), len(names) * (th + px(8)) + px(8)), "#111111")
    d = ImageDraw.Draw(sheet)
    small = font("Archivo.ttf", 22, 700)
    for r, n in enumerate(names):
        d.text((px(8), px(8) + r * (th + px(8)) + px(8)), LOOKS[n][0], font=small, fill=WHITE)
        for c, t in enumerate(ts):
            sheet.paste(grab(path(n), t, tw), (px(188) + c * (tw + px(8)), px(8) + r * (th + px(8))))
    sheet.save(os.path.join(a.work, "contact_sheet.jpg"), quality=88)
    outs = ["grid.png", "contact_sheet.jpg"]
    if len(names) >= 2:
        # grid video, 3 across, cells a third of the frame
        qw, qh = W // 3 // 2 * 2, H // 3 // 2 * 2
        ins = sum([["-i", path(n)] for n in names], [])
        sc = "".join(f"[{i}:v]scale={qw}:{qh},setsar=1[c{i}];" for i in range(len(names)))
        layout = "|".join(f"{(i % 3) * qw}_{(i // 3) * qh}" for i in range(len(names)))
        run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
             sc + "".join(f"[c{i}]" for i in range(len(names))) +
             f"xstack=inputs={len(names)}:layout={layout}:fill=black[v]",
             "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-c:a", "copy",
             "-movflags", "+faststart", os.path.join(a.work, "grid.mp4")])
        # cycle reel: the take once, a different look on each phrase
        bounds = [0.0] + [p["t0"] for p in tl["phrases"][1:]] + [tl["frames"] / FPS]
        parts, labels = [], []
        for i in range(len(bounds) - 1):
            k = i % len(names)
            parts.append(f"[{k}:v]trim=start={bounds[i]:.4f}:end={bounds[i + 1]:.4f},setpts=PTS-STARTPTS[s{i}]")
            labels.append(f"[s{i}]")
        run(["ffmpeg", "-y", "-v", "error", *ins, "-i", os.path.join(a.work, "base.wav"), "-filter_complex",
             ";".join(parts) + f";{''.join(labels)}concat=n={len(labels)}:v=1:a=0[v]",
             "-map", "[v]", "-map", f"{len(names)}:a", "-c:v", "libx264", "-crf", "17",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
             os.path.join(a.work, "cycle.mp4")])
        outs += ["grid.mp4", "cycle.mp4"]
    # 2x2 grid (@aslaniedits' format): four looks in one full-size frame, each quadrant
    # playing the whole take in sync, split by a thin black cross. No labels: only his words.
    quad = spec.get("grid2x2", [])
    missing = [n for n in quad if n not in names]
    if len(quad) == 4 and not missing:
        qw, qh, gut = W // 2, H // 2, max(2, px(4)) // 2 * 2
        ins = sum([["-i", path(n)] for n in quad], [])
        sc = "".join(f"[{i}:v]scale={qw}:{qh}:flags=lanczos,setsar=1[q{i}];" for i in range(4))
        run(["ffmpeg", "-y", "-v", "error", *ins, "-i", os.path.join(a.work, "base.wav"), "-filter_complex",
             sc + f"[q0][q1][q2][q3]xstack=inputs=4:layout=0_0|{qw}_0|0_{qh}|{qw}_{qh},"
             f"drawbox=x={qw - gut // 2}:y=0:w={gut}:h={H}:color=black:t=fill,"
             f"drawbox=x=0:y={qh - gut // 2}:w={W}:h={gut}:color=black:t=fill,format=yuv420p[v]",
             "-map", "[v]", "-map", "4:a", "-c:v", "libx264", "-crf", "17", "-preset", "medium",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
             os.path.join(a.work, "grid2x2.mp4")])
        outs.append("grid2x2.mp4")
    elif quad:
        print(f"grid2x2 skipped: build {', '.join(missing)} at {W}x{H} first (looks --only ...)")
    print("sheets:", " ".join(outs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["base", "looks", "sheets"])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--src")
    ap.add_argument("--work", default="work")
    ap.add_argument("--only")
    ap.add_argument("--size", help="WxH, e.g. 2160x3840 (default: spec \"size\", else 1080x1920)")
    a = ap.parse_args()
    {"base": cmd_base, "looks": cmd_looks, "sheets": cmd_sheets}[a.step](a)


if __name__ == "__main__":
    main()
