#!/usr/bin/env python3
"""Render one FD "Livery" reel from a cut sheet (JSON).

    python3 build.py cuts/fd-zr1.json --lut ~/.local/vlogtools/gR2.cube
    python3 build.py cuts/fd-zr1.json --ungraded      # test only: no R2 LUT on this box

Cut sheet:
{
  "id": "fd-zr1", "name": "ZR1 Coilovers", "end": "build" | "store",
  "audio": "real" | "mute",
  "beats": [
    {"num": "01", "word": "ON THE LIFT",
     "shots": [{"src": "/abs/clip.mov", "in": 3.2, "out": 5.0,
                "blur": [[0.0, 1.8, x, y, w, h]]}]}   # plate/face boxes, output px, shot-relative s
  ]
}

Each beat opens with its number-board plate; beats change under a stripe pass; the
last beat hands to the end card under a final pass. Cuts inside a beat are straight.
Audio is the clips' own sound (real sound on), a whoosh under each pass, mastered
with 99-toolkit/fd_master.py to -14 LUFS / -1.0 dBTP.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "99-toolkit"))
from PIL import Image  # noqa: E402
import livery as L  # noqa: E402
import fd_master  # noqa: E402

W, H, FPS = L.W, L.H, L.FPS
SFX = HERE.parent / "10-motion-sfx/sfx/whoosh-in.wav"
END_S = 2.6
PLATE_S = 1.8
# RGB graphics -> video with the BT.709 matrix (ffmpeg's default is BT.601, which turns
# FD red #FE0F13 orange-ish on phones), and tag every encode as BT.709
CM = "scale=out_color_matrix=bt709:out_range=tv"
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
SFX_GAIN = 0.45          # accents sit about 45% under the bed (Locked-On rule 7)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write("\n".join(r.stderr.strip().splitlines()[-12:]) + "\n")
        raise SystemExit(f"ffmpeg failed: {' '.join(map(str, cmd[:6]))} ...")
    return r


IMG_EXT = {".jpg", ".jpeg", ".png"}


def ease(u):
    """Cosine ease in-out, 0..1 -> 0..1 (slow push/pan on stills)."""
    import math
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, u)))


def render_still(shot, out, grade):
    """A photo as a shot: a 9:16 window that pushes/pans across it with sub-pixel accuracy.
    shot: {"src": photo, "dur": s, "move": {"from": [cx, cy, zoom], "to": [cx, cy, zoom]},
           "blur_src": [[x, y, w, h], ...],   # fractions of the photo, blurred before the move
           "audio_from": [clip, t0]}           # optional room tone; otherwise silence
    cx, cy are the window centre as fractions of the photo; zoom 1.0 = the largest 9:16 window."""
    from PIL import Image, ImageFilter, ImageOps
    dur = float(shot["dur"])
    im = ImageOps.exif_transpose(Image.open(shot["src"])).convert("RGB")
    iw, ih = im.size
    for (x, y, w, h) in shot.get("blur_src", []):
        box = tuple(int(v) for v in (x * iw, y * ih, (x + w) * iw, (y + h) * ih))
        reg = im.crop(box)
        reg = reg.resize((max(1, reg.width // 24), max(1, reg.height // 24)), Image.BILINEAR)
        reg = reg.resize((box[2] - box[0], box[3] - box[1]), Image.BILINEAR).filter(ImageFilter.GaussianBlur(12))
        im.paste(reg, box[:2])
    bw, bh = (ih * W / H, ih) if iw / ih > W / H else (iw, iw * H / W)
    k = min(1.0, 2.0 * H / bh)                       # keep ~2x headroom over the output
    if k < 1.0:
        im = im.resize((round(iw * k), round(ih * k)), Image.LANCZOS)
        iw, ih, bw, bh = im.width, im.height, bw * k, bh * k
    mv = shot.get("move", {"from": [0.5, 0.5, 1.0], "to": [0.5, 0.5, 1.06]})
    f0, f1 = mv["from"], mv["to"]
    n = max(2, round(dur * FPS))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if shot.get("audio_from"):              # room tone from a clip of the same job (stills have no sound)
        asrc, a0 = shot["audio_from"]
        cmd += ["-ss", str(a0), "-t", f"{n / FPS:.3f}", "-i", asrc]
    else:
        cmd += ["-f", "lavfi", "-t", f"{n / FPS:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    vf = ["setsar=1"] + ([grade] if grade else [])
    chain, last = f"[0:v]{','.join(vf)}[v0]", "v0"
    for j, (t0, t1, x, y, w, h) in enumerate(shot.get("blur", [])):
        chain += (f";[{last}]split[a{j}][b{j}];[b{j}]crop={w}:{h}:{x}:{y},{bblur(w, h)}[c{j}];"
                  f"[a{j}][c{j}]overlay={x}:{y}:enable='between(t,{t0},{t1})'[v{j+1}]")
        last = f"v{j+1}"
    chain += f";[{last}]{CM},format=yuv420p[vout]"
    chain += ";[1:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.08[aa]"
    cmd += ["-filter_complex", chain, "-map", "[vout]", "-map", "[aa]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", *TAGS,
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-shortest", str(out)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for i in range(n):
        u = ease(i / (n - 1))
        cx, cy, z = (a + (b - a) * u for a, b in zip(f0, f1))
        ww, wh = bw / z, bh / z
        x0 = min(max(cx * iw - ww / 2, 0), iw - ww)
        y0 = min(max(cy * ih - wh / 2, 0), ih - wh)
        fr = im.transform((W, H), Image.EXTENT, (x0, y0, x0 + ww, y0 + wh), resample=Image.BICUBIC)
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    err = pr.stderr.read().decode()
    if pr.wait():
        sys.stderr.write(err[-1500:])
        raise SystemExit(f"still render failed: {shot['src']}")
    return n / FPS


def bblur(w, h):
    """boxblur sized to the box: ffmpeg refuses a radius over half the plane (a quarter for chroma)."""
    r = max(1, min(28, min(w, h) // 2 - 1)); rc = max(1, min(r, min(w, h) // 4 - 1))
    return f"boxblur={r}:3:{rc}:3"


def scrim(bbox, strength):
    """Full-frame RGBA: black behind the board's box, feathered out, so white type
    reads over blown-out shop lights. strength = peak alpha 0..1."""
    from PIL import Image, ImageDraw, ImageFilter
    m = Image.new("L", (W, H), 0)
    x0, y0, x1, y1 = bbox
    ImageDraw.Draw(m).rectangle((0, max(0, y0 - 90), min(W, x1 + 160), y1 + 90), fill=int(255 * strength))
    m = m.filter(ImageFilter.GaussianBlur(70))
    sc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sc.putalpha(m)
    return sc


def render_shot(shot, out, grade, mute):
    if Path(shot["src"]).suffix.lower() in IMG_EXT:
        return render_still(shot, out, grade)
    dur = shot["out"] - shot["in"]
    pre = [f"crop={shot['crop'][2]}:{shot['crop'][3]}:{shot['crop'][0]}:{shot['crop'][1]}"] if shot.get("crop") else []
    vf = pre + [f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos",
          f"crop={W}:{H}", f"fps={FPS}", "setsar=1"]
    if grade:
        vf.append(grade)
    chain = f"[0:v]{','.join(vf)}[v0]"
    last = "v0"
    for k, (t0, t1, x, y, w, h) in enumerate(shot.get("blur", [])):
        chain += (f";[{last}]split[a{k}][b{k}];[b{k}]crop={w}:{h}:{x}:{y},{bblur(w, h)}[c{k}];"
                  f"[a{k}][c{k}]overlay={x}:{y}:enable='between(t,{t0},{t1})'[v{k+1}]")
        last = f"v{k+1}"
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(shot["in"]), "-t", f"{dur:.3f}", "-i", shot["src"]]
    has_a = not mute and fd_master.has_audio(Path(shot["src"]))
    if not has_a:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-filter_complex", chain, "-map", f"[{last}]", "-map", "0:a:0" if has_a else "1:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", *TAGS,
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-shortest", str(out)]
    run(cmd)
    return dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cut")
    ap.add_argument("--lut", help="R2 reel grade cube (~/.local/vlogtools/gR2.cube)")
    ap.add_argument("--ungraded", action="store_true", help="test render without the R2 grade")
    ap.add_argument("-o", "--out", default=str(HERE / "renders"))
    ap.add_argument("--shots-only", action="store_true",
                    help="render the shots into work/<id>/ and stop (pre-render frame gate)")
    a = ap.parse_args()
    cut = json.loads(Path(a.cut).read_text())
    if a.lut:
        grade = f"lut3d={a.lut},hqdn3d=2:1.5:3:3,unsharp=5:5:0.45:5:5:0"
    elif a.ungraded:
        grade = None
    else:
        raise SystemExit("R2 grade needed: pass --lut <gR2.cube>, or --ungraded for a test render")

    work = HERE / "work" / cut["id"]
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    mute = cut.get("audio", "real") == "mute"

    # 1. shots -> segments, beat start times
    segs, beat_t, t = [], [], 0.0
    for bi, beat in enumerate(cut["beats"]):
        beat_t.append(t)
        plate = L.beat_plate(beat["num"], beat["word"], beat.get("sub"))
        if cut.get("scrim"):                    # bright shop footage: shade the board's area
            plate = Image.alpha_composite(scrim(plate.getbbox(), cut["scrim"]), plate)
        plate.save(work / f"plate{bi}.png")
        for si, shot in enumerate(beat["shots"]):
            p = work / f"s{bi:02d}_{si:02d}.mov"
            t += render_shot(shot, p, grade, mute)
            segs.append(p)
    body_end = t
    if a.shots_only:
        print(f"shots in {work}  body {body_end:.2f}s")
        return
    card = work / "endcard.png"
    (L.endcard_store() if cut.get("end") == "store" else L.endcard()).convert("RGB").save(card)
    ec = work / "endcard.mov"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-t", str(END_S), "-i", str(card),
         "-f", "lavfi", "-t", str(END_S), "-i", "anullsrc=r=48000:cl=stereo",
         "-vf", f"{CM},format=yuv420p", "-c:v", "libx264", "-crf", "14", *TAGS, "-c:a", "pcm_s16le", "-shortest", str(ec)])
    segs.append(ec)
    total = body_end + END_S
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    body = work / "body.mov"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "copy", "-c:a", "pcm_s16le", str(body)])

    # 1b. ambience bed (stills reels have no sound of their own): clips concatenated with
    # short fades, trimmed to the body, placed under the whooshes
    bed = None
    if cut.get("bed"):
        bd = cut["bed"]; ins, parts = [], []
        for k, (src, b0, b1) in enumerate(bd["clips"]):
            ins += ["-ss", str(b0), "-t", f"{b1 - b0:.3f}", "-i", src]
            parts.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,"
                         f"afade=t=in:d=0.25,afade=t=out:st={b1 - b0 - 0.25:.3f}:d=0.25[b{k}]")
        n_b = len(bd["clips"])
        g = (";".join(parts) + ";" + "".join(f"[b{k}]" for k in range(n_b)) +
             f"concat=n={n_b}:v=0:a=1,volume={bd.get('gain_db', 0)}dB,atrim=0:{body_end:.3f},"
             f"afade=t=in:d=0.3,afade=t=out:st={body_end - 0.4:.3f}:d=0.4[bed]")
        bed = work / "bed.wav"
        run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", g, "-map", "[bed]",
             "-c:a", "pcm_s16le", str(bed)])

    # 2. stripe pass clip (RGBA) once
    pdir = work / "pass"; pdir.mkdir()
    for i in range(L.PASS_FRAMES + 1):
        L.stripe_pass_frame(i).save(pdir / f"p{i:02d}.png")
    pmov = work / "pass.mov"
    run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(pdir / "p%02d.png"),
         "-c:v", "qtrle", "-pix_fmt", "argb", str(pmov)])

    # 3. overlay graph: plates (fade + slide along the line), passes at beat changes + end card
    cuts_at = beat_t[1:] + [body_end]
    inputs = ["-i", str(body)]
    fc, last, n = [], "0:v", 1
    for bi, t0 in enumerate(beat_t):
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", str(work / f"plate{bi}.png")]
        t_in = t0 + (L.PASS_CUT / FPS if bi else 0.0)
        t_out = t_in + PLATE_S + (0.15 if bi == 0 else 0.0)
        fin = f"fade=t=in:st={t_in:.3f}:d=0.2:alpha=1," if bi else ""   # frame 0: hook already built
        fc.append(f"[{n}:v]format=rgba,{fin}fade=t=out:st={t_out:.3f}:d=0.2:alpha=1,{CM},format=yuva420p[pl{bi}]")
        xs = f"-70*pow(max(0\\,1-(t-{t_in:.3f})/0.25)\\,3)" if bi else "0"
        fc.append(f"[{last}][pl{bi}]overlay=x='{xs}':y=0:"
                  f"enable='between(t,{t_in:.3f},{t_out + 0.2:.3f})':eval=frame[o{bi}]")
        last, n = f"o{bi}", n + 1
    for ci, tc in enumerate(cuts_at):
        st = max(0.0, tc - L.PASS_CUT / FPS)
        inputs += ["-i", str(pmov)]
        fc.append(f"[{n}:v]setpts=PTS-STARTPTS+{st:.3f}/TB,{CM},format=yuva420p[ps{ci}]")
        fc.append(f"[{last}][ps{ci}]overlay=0:0:eof_action=pass[q{ci}]")
        last, n = f"q{ci}", n + 1
    # whooshes under each pass
    amix = ["[0:a]anull[a0]"]
    alabels = ["[a0]"]
    if bed:
        inputs += ["-i", str(bed)]
        amix.append(f"[{n}:a]anull[bd]"); alabels.append("[bd]"); n += 1
    for ci, tc in enumerate(cuts_at):
        st = max(0.0, tc - L.PASS_CUT / FPS - 0.12)
        inputs += ["-i", str(SFX)]
        amix.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={SFX_GAIN},"
                    f"adelay={int(st * 1000)}|{int(st * 1000)}[w{ci}]")
        alabels.append(f"[w{ci}]"); n += 1
    amix.append(f"{''.join(alabels)}amix=inputs={len(alabels)}:normalize=0:duration=first,"
                f"afade=t=out:st={total - 0.05:.3f}:d=0.05[aout]")
    graph = ";".join(fc + amix)
    pre = work / "composite.mp4"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", f"[{last}]", "-map", "[aout]",
         "-t", f"{total:.3f}", "-r", str(FPS), "-c:v", "libx264", "-profile:v", "high", "-preset", "slow",
         "-crf", "17", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", *TAGS,
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(pre)])

    # 4. loudness: FD pipeline target via fd_master (-14 LUFS / -1.0 dBTP, two-pass)
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    tag = "INSTAGRAM" if grade else "UNGRADED PREVIEW"
    final = outdir / f"FD {cut['name']} - {tag} 1080x1920.mp4"
    fd_master.TARGET_TP = -1.5        # margin under -1.0 after the platform's encode (Locked-On bar)
    fd_master.master(pre, final)
    # alimiter holds sample peaks; the AAC encode adds inter-sample overs on top (detail v4
    # landed at -1.2 dBTP). Re-master from the pre-mix with the ceiling lowered by the overshoot.
    for _ in range(2):
        tp = fd_master.measure(final)["input_tp"]
        if float(tp) <= -1.5:
            break
        fd_master.TARGET_TP -= float(tp) + 1.5 + 0.1
        fd_master.master(pre, final)
    manifest = dict(id=cut["id"], final=str(final), duration=round(total, 3), graded=bool(grade),
                    lut=a.lut, beats=[dict(num=b["num"], word=b["word"], t=round(bt, 3),
                                           shots=[Path(s["src"]).name for s in b["shots"]])
                                      for b, bt in zip(cut["beats"], beat_t)],
                    passes_at=[round(c, 3) for c in cuts_at])
    (outdir / f"{cut['id']}.manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"{final}  {total:.2f}s  graded={bool(grade)}")


if __name__ == "__main__":
    main()
