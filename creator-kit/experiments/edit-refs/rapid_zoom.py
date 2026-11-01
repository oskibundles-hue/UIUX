#!/usr/bin/env python3
"""
The @cinamiti rapid-zoom open (https://www.instagram.com/cinamiti/), rebuilt as a tool.

    10 clips x 3 frames, a duplicate layer with 2 frames trimmed off each clip
    composited on top with Add, a zoom/radial blur that peaks on every cut and
    eases out, then a hard land on the payoff clip, sharp, by 2.0 s.

How each part is done (DaVinci Resolve has these as timeline tools; ffmpeg
does not, so they are per-frame numpy/Pillow here):

  * Duplicate + Add. Track 2 is a copy of track 1 with each 3-frame clip
    trimmed by 2 frames, so only one frame of each clip survives on top
    (--trim-from tail keeps the first frame, so the flash sits on the cut;
    head keeps the last). Add = base + top, clipped to 1.0. On that one frame
    the picture doubles in brightness and the highlights blow out: a flash
    made from the shot itself, not a white frame.
  * Zoom / radial blur. A punch-in scale plus a radial blur made by averaging
    --samples copies of the frame scaled up about the centre (1.0 to 1+blur).
    Both are keyed per frame: peak on the cut frame, then an ease-out curve
    ((1 - k/K)^2) over --ease frames. Applied over the Add composite, like an
    adjustment layer above both tracks.
  * Land. The payoff clip starts sharp on the frame after the run
    (--land-ease 0) and holds for --hold seconds.

Output: 2160x3840 at 29.97 fps (the Fast Cut spec), H.264 + AAC. --work-res
processes at a smaller size and upscales at encode for speed. --remainder
splices the open ahead of another clip. --sfx lays kit-v2 sounds on the cuts.
Audio is mastered like fastcut: loudnorm I=-14 TP=-1.5 LRA=11 (two-pass),
then alimiter limit=0.84 level=false.

Example:
    python3 rapid_zoom.py --clips a.mp4@3.2 b.mp4@10 ... (10 of them) \\
        --payoff hero.mp4 --payoff-in 4.5 --sfx --out open.mp4
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media as M  # noqa: E402


def parse_clip(s):
    if "@" in s:
        p, t = s.rsplit("@", 1)
        return p, float(t)
    return s, 0.0


def zoom_stack(frame, punch, blur, samples):
    """Scale frame by `punch` about the centre and radial-blur it by averaging
    `samples` copies at scales punch*(1 .. 1+blur). Returns uint8."""
    if punch <= 1.0005 and blur < 1e-3:
        return frame
    h, w = frame.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    img = Image.fromarray(frame)
    n = max(2, samples) if blur >= 1e-3 else 1
    acc = np.zeros((h, w, 3), np.float32)
    for i in range(n):
        s = punch * (1.0 + blur * (i / (n - 1) if n > 1 else 0.0))
        a = 1.0 / s
        coeffs = (a, 0, cx * (1 - a), 0, a, cy * (1 - a))
        acc += np.asarray(img.transform((w, h), Image.AFFINE, coeffs,
                                        resample=Image.BILINEAR), np.float32)
    return np.clip(acc / n + 0.5, 0, 255).astype(np.uint8)


def ease(k, K):
    """Strength k frames after a cut: 1 on the cut, easing out to 0 at K."""
    return 0.0 if k >= K else (1.0 - k / K) ** 2


def build_plan(a):
    clips = [parse_clip(c) for c in a.clips]
    if not clips:
        raise SystemExit("no --clips given")
    run_clips = []
    for i in range(a.count):
        p, t = clips[i % len(clips)]
        rep = i // len(clips)
        if rep:
            t += rep * a.repeat_step   # cycling: move the in-point so no frame repeats
        run_clips.append((p, t))
    if len(clips) < a.count:
        print(f"note: {len(clips)} clips for {a.count} slots; reusing them with in-points "
              f"advanced {a.repeat_step}s per pass", file=sys.stderr)
    fpc = a.frames
    run_n = a.count * fpc
    land_frame = run_n + a.land_ease
    land_t = land_frame / M.FPS
    if land_t > 2.0 + 1e-9:
        raise SystemExit(f"land at {land_t:.3f}s is past 2.0s: lower --count, --frames or --land-ease")
    hold_n = max(a.land_ease + 1, int(round(a.hold * M.FPS)))
    return run_clips, fpc, run_n, land_frame, land_t, hold_n


def render_opening(a, run_clips, fpc, run_n, land_frame, hold_n, wW, wH, out_v):
    keep = fpc - a.trim                  # frames of each clip that survive on the top layer
    if keep < 0:
        raise SystemExit("--trim is longer than --frames")
    wr = M.FrameWriter(out_v, wW, wH, M.W, M.H, crf=a.crf)
    log = []
    for ci, (src, t_in) in enumerate(run_clips):
        frames = M.read_frames(src, t_in, fpc, wW, wH)
        for k, fr in enumerate(frames):
            top = (k < keep) if a.trim_from == "tail" else (k >= fpc - keep)
            base = fr
            if top and a.add:
                base = np.clip(fr.astype(np.uint16) * 2, 0, 255).astype(np.uint8)
            e = ease(k, a.ease)
            out = zoom_stack(base, 1.0 + a.punch * e, a.blur * e, a.samples)
            wr.write(out)
            log.append({"frame": ci * fpc + k, "clip": os.path.basename(src), "src_t": round(t_in + k / M.FPS, 4),
                        "add": bool(top and a.add), "strength": round(e, 3)})
    pay = M.read_frames(a.payoff, a.payoff_in, hold_n, wW, wH)
    for k, fr in enumerate(pay):
        if k < a.land_ease:
            e = ease(k, a.land_ease)
            fr = zoom_stack(fr, 1.0 + a.punch * e, a.blur * e, a.samples)
        else:
            e = 0.0
        wr.write(fr)
        log.append({"frame": run_n + k, "clip": os.path.basename(a.payoff),
                    "src_t": round(a.payoff_in + k / M.FPS, 4), "add": False, "strength": round(e, 3),
                    "land": run_n + k == land_frame})
    wr.close()
    return log


def opening_audio(a, n_frames, run_n, land_t):
    n = int(round(n_frames / M.FPS * M.SR))
    bed = np.zeros((n, 2), np.float32)
    placed = []
    if a.sfx:
        meta = M.kit_meta().get("sounds", {})
        run_s = run_n / M.FPS
        clicks = M.kit_sound(a.click_sound)[:int(run_s * M.SR) + int(0.02 * M.SR)]
        M.place(bed, clicks, 0.0, a.click_db); placed.append((a.click_sound, 0.0))
        if not a.no_riser:
            r = M.kit_sound("zoom_riser")
            t0 = land_t - len(r) / M.SR
            M.place(bed, r, t0, a.riser_db); placed.append(("zoom_riser", round(t0, 4)))
        wf = M.kit_sound("whoosh_flash")
        hit = meta.get("whoosh_flash", {}).get("hit", 0.62)
        t0 = land_t - hit
        M.place(bed, wf, t0, 0.0); placed.append(("whoosh_flash", round(t0, 4)))
    return bed, placed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clips", nargs="+", required=True, help="clip paths, each optionally @in-point seconds")
    ap.add_argument("--payoff", required=True)
    ap.add_argument("--payoff-in", type=float, default=0.0)
    ap.add_argument("--hold", type=float, default=1.0, help="seconds of payoff in the open (default 1.0)")
    ap.add_argument("--count", type=int, default=10, help="clips in the run (default 10)")
    ap.add_argument("--frames", type=int, default=3, help="frames per clip (default 3)")
    ap.add_argument("--trim", type=int, default=2, help="frames trimmed off each duplicate-layer clip (default 2)")
    ap.add_argument("--trim-from", choices=["tail", "head"], default="tail")
    ap.add_argument("--no-add", dest="add", action="store_false", help="skip the duplicate Add layer")
    ap.add_argument("--blur", type=float, default=0.22, help="radial blur at the cut: extra scale of the outermost copy")
    ap.add_argument("--punch", type=float, default=0.12, help="punch-in scale at the cut (0.12 = 112%%)")
    ap.add_argument("--samples", type=int, default=12, help="copies averaged for the radial blur")
    ap.add_argument("--ease", type=int, default=3, help="frames the zoom eases out over after each cut")
    ap.add_argument("--land-ease", type=int, default=0, help="blurred frames on the payoff before it is sharp")
    ap.add_argument("--repeat-step", type=float, default=0.5)
    ap.add_argument("--work-res", default=f"{M.W}x{M.H}", help="processing size, e.g. 1080x1920; output is always 2160x3840")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--sfx", action="store_true", help="rapid_click on the run, zoom_riser into the land, whoosh_flash on the land")
    ap.add_argument("--click-sound", default="rapid_click_3f")
    ap.add_argument("--click-db", type=float, default=-4.0)
    ap.add_argument("--riser-db", type=float, default=-8.0)
    ap.add_argument("--no-riser", action="store_true")
    ap.add_argument("--remainder", help="clip to splice after the open")
    ap.add_argument("--remainder-in", type=float, default=0.0)
    ap.add_argument("--remainder-dur", type=float)
    ap.add_argument("--work", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    wW, wH = map(int, a.work_res.lower().split("x"))
    work = a.work or os.path.splitext(a.out)[0] + "_work"
    os.makedirs(work, exist_ok=True)

    run_clips, fpc, run_n, land_frame, land_t, hold_n = build_plan(a)
    open_v = os.path.join(work, "opening_v.mp4")
    log = render_opening(a, run_clips, fpc, run_n, land_frame, hold_n, wW, wH, open_v)
    n_open = run_n + hold_n
    bed, placed = opening_audio(a, n_open, run_n, land_t)

    video = open_v
    if a.remainder:
        rem_v = os.path.join(work, "rem_v.mp4")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a.remainder_in:.4f}", "-i", a.remainder]
        if a.remainder_dur:
            cmd += ["-t", f"{a.remainder_dur:.4f}"]
        cmd += ["-vf", M.fill_vf(M.W, M.H) + ",format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                "-crf", str(a.crf), "-profile:v", "high", "-r", M.FPS_STR, "-an", rem_v]
        M.run(cmd)
        rem_info = M.probe(rem_v)
        rem_a = M.read_audio(a.remainder, t_in=a.remainder_in, dur=rem_info["duration"])
        need = int(round(rem_info["duration"] * M.SR))
        rem_a = np.pad(rem_a, ((0, max(0, need - len(rem_a))), (0, 0)))[:need]
        bed = np.concatenate([bed, rem_a])
        lst = os.path.join(work, "concat.txt")
        open(lst, "w").write(f"file '{os.path.abspath(open_v)}'\nfile '{os.path.abspath(rem_v)}'\n")
        video = os.path.join(work, "joined_v.mp4")
        M.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    raw = os.path.join(work, "audio_raw.wav")
    mastered = os.path.join(work, "audio_master.wav")
    M.write_wav(raw, bed)
    loud = None
    if np.abs(bed).max() > 1e-6:
        loud = M.master_audio(raw, mastered)
    else:
        mastered = raw   # digital silence: nothing to normalise
    M.mux(video, mastered, a.out)

    info = M.probe(a.out)
    side = {"out": a.out, "duration": info["duration"], "width": info["width"], "height": info["height"],
            "fps": info["fps"], "run_frames": run_n, "land_frame": land_frame, "land_time": round(land_t, 4),
            "opening_frames": n_open, "sfx": placed,
            "loudness_in": loud and {"I": loud["input_i"], "TP": loud["input_tp"]},
            "frames": log}
    json.dump(side, open(os.path.splitext(a.out)[0] + ".json", "w"), indent=1)
    print(f"{a.out}: {info['width']}x{info['height']} {info['fps']:.3f} fps {info['duration']:.3f} s; "
          f"land frame {land_frame} at {land_t:.3f} s")


if __name__ == "__main__":
    main()
