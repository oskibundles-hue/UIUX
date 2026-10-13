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
import livery as L  # noqa: E402
import fd_master  # noqa: E402

W, H, FPS = L.W, L.H, L.FPS
SFX = HERE.parent / "10-motion-sfx/sfx/whoosh-in.wav"
END_S = 2.6
PLATE_S = 1.8
SFX_GAIN = 0.45          # accents sit about 45% under the bed (Locked-On rule 7)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write("\n".join(r.stderr.strip().splitlines()[-12:]) + "\n")
        raise SystemExit(f"ffmpeg failed: {' '.join(map(str, cmd[:6]))} ...")
    return r


def render_shot(shot, out, grade, mute):
    dur = shot["out"] - shot["in"]
    vf = [f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos",
          f"crop={W}:{H}", f"fps={FPS}", "setsar=1"]
    if grade:
        vf.append(grade)
    chain = f"[0:v]{','.join(vf)}[v0]"
    last = "v0"
    for k, (t0, t1, x, y, w, h) in enumerate(shot.get("blur", [])):
        chain += (f";[{last}]split[a{k}][b{k}];[b{k}]crop={w}:{h}:{x}:{y},boxblur=28:3[c{k}];"
                  f"[a{k}][c{k}]overlay={x}:{y}:enable='between(t,{t0},{t1})'[v{k+1}]")
        last = f"v{k+1}"
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(shot["in"]), "-t", f"{dur:.3f}", "-i", shot["src"]]
    has_a = not mute and fd_master.has_audio(Path(shot["src"]))
    if not has_a:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-filter_complex", chain, "-map", f"[{last}]", "-map", "0:a:0" if has_a else "1:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-shortest", str(out)]
    run(cmd)
    return dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cut")
    ap.add_argument("--lut", help="R2 reel grade cube (~/.local/vlogtools/gR2.cube)")
    ap.add_argument("--ungraded", action="store_true", help="test render without the R2 grade")
    ap.add_argument("-o", "--out", default=str(HERE / "renders"))
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
        L.beat_plate(beat["num"], beat["word"], beat.get("sub")).save(work / f"plate{bi}.png")
        for si, shot in enumerate(beat["shots"]):
            p = work / f"s{bi:02d}_{si:02d}.mov"
            t += render_shot(shot, p, grade, mute)
            segs.append(p)
    body_end = t
    card = work / "endcard.png"
    (L.endcard_store() if cut.get("end") == "store" else L.endcard()).convert("RGB").save(card)
    ec = work / "endcard.mov"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-t", str(END_S), "-i", str(card),
         "-f", "lavfi", "-t", str(END_S), "-i", "anullsrc=r=48000:cl=stereo",
         "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "14", "-c:a", "pcm_s16le", "-shortest", str(ec)])
    segs.append(ec)
    total = body_end + END_S
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    body = work / "body.mov"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "copy", "-c:a", "pcm_s16le", str(body)])

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
        t_in = t0 + (L.PASS_CUT / FPS if bi else 0.15)
        t_out = t_in + PLATE_S
        fc.append(f"[{n}:v]format=rgba,fade=t=in:st={t_in:.3f}:d=0.2:alpha=1,"
                  f"fade=t=out:st={t_out:.3f}:d=0.2:alpha=1[pl{bi}]")
        fc.append(f"[{last}][pl{bi}]overlay=x='-70*pow(max(0\\,1-(t-{t_in:.3f})/0.25)\\,3)':y=0:"
                  f"enable='between(t,{t_in:.3f},{t_out + 0.2:.3f})':eval=frame[o{bi}]")
        last, n = f"o{bi}", n + 1
    for ci, tc in enumerate(cuts_at):
        st = max(0.0, tc - L.PASS_CUT / FPS)
        inputs += ["-i", str(pmov)]
        fc.append(f"[{n}:v]setpts=PTS-STARTPTS+{st:.3f}/TB[ps{ci}]")
        fc.append(f"[{last}][ps{ci}]overlay=0:0:eof_action=pass[q{ci}]")
        last, n = f"q{ci}", n + 1
    # whooshes under each pass
    amix = ["[0:a]anull[a0]"]
    alabels = ["[a0]"]
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
         "-crf", "17", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(pre)])

    # 4. loudness: FD pipeline target via fd_master (-14 LUFS / -1.0 dBTP, two-pass)
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    final = outdir / f"FD {cut['name']} - INSTAGRAM 1080x1920.mp4"
    fd_master.master(pre, final)
    manifest = dict(id=cut["id"], final=str(final), duration=round(total, 3), graded=bool(grade),
                    lut=a.lut, beats=[dict(num=b["num"], word=b["word"], t=round(bt, 3),
                                           shots=[s["src"] for s in b["shots"]])
                                      for b, bt in zip(cut["beats"], beat_t)],
                    passes_at=[round(c, 3) for c in cuts_at])
    (outdir / f"{cut['id']}.manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"{final}  {total:.2f}s  graded={bool(grade)}")


if __name__ == "__main__":
    main()
