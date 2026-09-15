#!/usr/bin/env python3
"""
build_kinetic.py - the Kinetic Cut: a monochrome, letterboxed, strobing edit
with staircase type, built from a shot list and a text script.

Measured off the reference edit, not invented:

  canvas      9:16, 30 fps
  band        anchored at the bottom, the TOP edge moves. 1.30:1 in the build,
              1.90:1 through the strobe, 1.77:1 to finish
  grade       near-monochrome with crushed blacks; saturation returns only on
              the smear frames, which is where all the colour in the piece lives
  cuts        2-3s in the build, 0.12-0.45s through the strobe, long to finish
  transitions directional RGB smears cut in as their own 3-6 frame shots, plus
              single white flash frames
  type        Archivo heavy caps, staircase indent, one word at a time, one
              accent-coloured word per block carrying an RGB split

Shot list entries are either footage or an effect derived from the shot before:

  {"clip": "18 red supercar.mp4", "in": 12.0, "dur": 2.4}
  {"fx": "smear", "dur": 0.2, "angle": 0}      RGB-split directional smear
  {"fx": "flash", "dur": 0.07}                 white frame

Nothing here is specific to one edit: the band keyframes, the grade and the
strobe all read from the JSON, so a second piece is a second JSON.
"""
import argparse, json, os, shlex, subprocess, sys

def run(cmd, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:] + "\n")
        raise SystemExit(f"failed: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    return r

def dur_of(shot, fps):
    """A shot's length: exact frames when given, otherwise seconds."""
    return shot["frames"] / fps if "frames" in shot else shot["dur"]


def shot_cmd(src, tin, dur, W, H, fps, g, out):
    """One piece of footage, scaled to the canvas and graded down to near-mono."""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"eq=saturation={g['saturation']}:contrast={g['contrast']}:"
          f"brightness={g['brightness']}:gamma={g['gamma']},"
          f"fps={fps},setsar=1")
    return ["ffmpeg", "-y", "-ss", f"{tin}", "-i", src, "-t", f"{dur}",
            "-vf", vf, "-an", "-c:v", "libx264", "-crf", "14",
            "-pix_fmt", "yuv420p", "-loglevel", "error", out]

def smear(prev, dur, angle, W, H, fps, work, idx, out):
    """
    Freeze the last frame of the shot before, smear it along one axis and pull
    the red and blue channels apart. Squeezing the frame to a sliver and
    stretching it back is what makes the smear directional; rgbashift is the
    split. These frames carry all the saturation in the piece.
    """
    still = os.path.join(work, f"still{idx:03d}.png")
    run(["ffmpeg", "-y", "-sseof", "-0.15", "-i", prev, "-frames:v", "1",
         "-update", "1", "-loglevel", "error", still])
    if angle == 0:
        squeeze = f"scale={max(2, W // 26)}:{H},scale={W}:{H}:flags=bilinear"
        shift = "rgbashift=rh=-20:bh=20"
    else:
        squeeze = f"scale={W}:{max(2, H // 26)},scale={W}:{H}:flags=bilinear"
        shift = "rgbashift=rv=-20:bv=20"
    vf = f"{squeeze},{shift},eq=saturation=3.2:contrast=1.18,fps={fps},setsar=1"
    run(["ffmpeg", "-y", "-loop", "1", "-i", still, "-t", f"{dur}", "-vf", vf,
         "-an", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
         "-loglevel", "error", out])


def flash_cmd(dur, W, H, fps, out):
    return ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=white:s={W}x{H}:r={fps}",
            "-t", f"{dur}", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
            "-loglevel", "error", out]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--footage", required=True, help="directory holding the clips")
    ap.add_argument("--work", default="work")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()

    spec = json.load(open(a.spec))
    W, H, fps = a.width, a.height, a.fps
    os.makedirs(a.work, exist_ok=True)

    # 1. every shot, in order, as its own file
    parts, prev = [], None
    for i, s in enumerate(spec["shots"]):
        p = os.path.join(a.work, f"s{i:03d}.mp4")
        d = dur_of(s, fps)
        if s.get("fx") == "smear":
            smear(prev, d, s.get("angle", 0), W, H, fps, a.work, i, p)
        elif s.get("fx") == "flash":
            run(flash_cmd(d, W, H, fps, p))
        else:
            run(shot_cmd(os.path.join(a.footage, s["clip"]), s["in"], d,
                         W, H, fps, spec["grade"], p))
            prev = p
        parts.append(p)
    lst = os.path.join(a.work, "concat.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    cuts = os.path.join(a.work, "cuts.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-loglevel", "error", cuts])

    total = sum(dur_of(s, fps) for s in spec["shots"])

    # 2. the overlay layer: bars, bug and type, one PNG per frame
    tdir = os.path.join(a.work, "type")
    bkeys = os.path.join(a.work, "band.json")
    json.dump(spec["band"], open(bkeys, "w"))
    run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "type_frames.py"),
         "--script", spec["type_script"], "--out", tdir, "--seconds", f"{total}",
         "--width", str(W), "--height", str(H), "--fps", str(fps),
         "--font", spec["font"], "--band-keys", bkeys, "--bug", spec["bug"],
         "--accent", spec["accent"]])

    # 3. lay the overlay over the cuts and place the audio
    vf = "[0:v][1:v]overlay=0:0[v]"
    cmd = ["ffmpeg", "-y", "-i", cuts,
           "-framerate", str(fps), "-i", os.path.join(tdir, "%05d.png")]
    if spec.get("audio_track"):
        cmd += ["-i", spec["audio_track"]]
        af = "[2:a]anull[a]"
        cmd += ["-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]",
                "-t", f"{total}", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-loglevel", "error", a.out]
        run(cmd)
        print(f"{a.out}  {total:.2f}s  {len(spec['shots'])} shots")
        return
    amix, ai = [], 2
    for seg in spec["audio"]:
        cmd += ["-ss", f"{seg['in']}", "-t", f"{seg['dur']}", "-i",
                os.path.join(a.footage, seg["clip"]) if "clip" in seg else seg["file"]]
        amix.append(f"[{ai}:a]adelay={int(seg['at']*1000)}|{int(seg['at']*1000)},"
                    f"volume={seg.get('gain',1.0)}[a{ai}]")
        ai += 1
    af = ";".join(amix) + ";" + "".join(f"[a{i}]" for i in range(2, ai)) + \
         f"amix=inputs={ai-2}:normalize=0,dynaudnorm=f=250:g=15,alimiter=limit=0.84[a]"
    cmd += ["-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]",
            "-t", f"{total}", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-loglevel", "error", a.out]
    run(cmd)
    print(f"{a.out}  {total:.2f}s  {len(spec['shots'])} shots")

if __name__ == "__main__":
    main()
