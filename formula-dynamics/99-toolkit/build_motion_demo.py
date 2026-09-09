#!/usr/bin/env python3
"""
Formula Dynamics - motion + SFX demo.

Burns the four animated components onto a clip and lays the sound-effect
pack under them, one hit per element. This exists to be watched: it is the
proof that the components and the sounds work together before either is
used on a real edit.

    python3 99-toolkit/build_motion_demo.py CLIP.mov -o demo.mp4

The cue list below is the thing to argue with. Each entry is
(component, start, duration, kwargs, [(sfx, offset, gain), ...]) - the SFX
offsets are relative to the component's own start, so moving a beat moves
its sound with it.
"""

import argparse
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

import fd_brand as B
import fd_motion as M

FPS = 30
SR = 48000
SFX = B.KIT / "10-motion-sfx" / "sfx"


def cues():
    """The demo's beat sheet. Times in seconds from the top of the clip."""
    return [
        ("glow-burst", 0.30, 1.60,
         dict(text="FORMULA DYNAMICS", y=0.40),
         [("riser-short", 0.00, 0.55), ("impact-hard", 0.38, 1.00),
          ("sub-thump", 0.38, 0.70), ("ui-tick-soft", 1.05, 0.55)]),

        # 22 characters typed over dur*0.85, so one click every 0.081 s.
        # Gain is high because a key click is 55 ms of band-limited noise:
        # at 0.4 it measured 0.003 RMS against an impact's 0.11 and was
        # simply not audible.
        ("type-on", 2.30, 2.10,
         dict(text="WHAT YOUR EXOTIC NEEDS", y=0.42),
         [(f"key-click-{1 + i % 3}", 0.05 + i * 0.081, 1.0) for i in range(22)]),

        ("scramble", 5.00, 1.30,
         dict(text="STAGE 2 TUNE", y=0.42),
         [("scramble", 0.00, 0.50), ("ui-tick-2", 1.05, 0.85),
          ("impact-tight", 1.05, 0.60)]),

        ("scramble", 6.80, 1.30,
         dict(text="QUAD EXHAUST", y=0.42),
         [("scramble", 0.00, 0.50), ("ui-tick-3", 1.05, 0.85),
          ("impact-tight", 1.05, 0.60)]),

        # Chip i lands at progress 0.35 + i*0.12, so its tick has to sit at
        # that fraction of the cue's duration - not at a fixed offset. The
        # first pass used 0.49/0.61/0.73 s and every tick fired about half a
        # second before its chip appeared.
        ("panel-rise", 8.70, 2.60,
         dict(title="FERRARI ROMA", chips=["PPF", "WHEELS", "QUAD EXHAUST"], y=0.62),
         [("whoosh-in", 0.00, 0.70), ("sub-drop", 0.10, 0.60)]
         + [(f"ui-tick-{i + 1}", (0.35 + i * 0.12) * 2.60, 0.85) for i in range(3)]
         + [("impact-soft", (0.35 + 2 * 0.12) * 2.60, 0.60),
            ("sub-thump", (0.35 + 2 * 0.12) * 2.60, 0.45)]),
    ]


def has_audio(ff, path):
    out = subprocess.run([ff, "-i", path], capture_output=True, text=True).stderr
    return "Audio:" in out


def build_audio(cue_list, dur):
    """Mix the sound effects onto one track, then soft-limit."""
    bed = np.zeros(int(SR * (dur + 1.0)), dtype=np.float32)
    used = 0
    for _, start, _, _, hits in cue_list:
        for name, off, gain in hits:
            p = SFX / f"{name}.wav"
            if not p.exists():
                raise SystemExit(f"missing sound: {p}")
            with wave.open(str(p)) as w:
                a = np.frombuffer(w.readframes(w.getnframes()),
                                  dtype=np.int16).astype(np.float32) / 32768
            i = int((start + off) * SR)
            n = min(len(a), len(bed) - i)
            if n > 0:
                bed[i:i + n] += a[:n] * gain
                used += 1
    peak = np.abs(bed).max()
    if peak > 0.89:                       # limit rather than clip
        bed *= 0.89 / peak
    return bed, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("-o", "--out", default="motion-demo.mp4")
    ap.add_argument("--canvas", default="9x16")
    ap.add_argument("--sfx-gain", type=float, default=1.6,
                    help="level of the effects bed against the clip's own audio")
    ap.add_argument("--duck", action="store_true",
                    help="duck the clip audio under the effects. Measured "
                         "WORSE than the flat mix on this footage - the "
                         "sidechain pulls the engine down, then the summed "
                         "bus hits the limiter and the effects lose what the "
                         "duck gained. Kept for footage with dialogue.")
    ap.add_argument("--source-gain", type=float, default=1.0,
                    help="level of the clip's own audio; 0 drops it")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cue_list = cues()
    end = max(s + d for _, s, d, _, _ in cue_list)

    print(f"\n  MOTION DEMO  ·  {a.canvas}  ·  {end:.1f}s of cues")
    print("  " + "-" * 68)
    print(f"  {'IN':>6} {'OUT':>6}  {'COMPONENT':<12} {'SFX':>4}  DETAIL")
    print("  " + "-" * 68)
    for name, start, dur, kw, hits in cue_list:
        detail = kw.get("text") or kw.get("title") or ""
        print(f"  {start:6.2f} {start + dur:6.2f}  {name:<12} {len(hits):>4}  {detail}")
    print("  " + "-" * 68)
    bed, used = build_audio(cue_list, end)
    print(f"  {used} sound effects, {used / end:.1f} per second\n")
    if a.dry_run:
        return

    tmp = Path(tempfile.mkdtemp())
    try:
        wav = tmp / "bed.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(bed, -1, 1) * 32767).astype(np.int16).tobytes())

        inputs = ["-i", a.clip]
        filt = [f"[0:v]scale={B.CANVASES[a.canvas][0]}:{B.CANVASES[a.canvas][1]}"
                f":force_original_aspect_ratio=increase,"
                f"crop={B.CANVASES[a.canvas][0]}:{B.CANVASES[a.canvas][1]},"
                f"trim=0:{end},setpts=PTS-STARTPTS[base]"]
        last = "base"

        for idx, (name, start, dur, kw, _) in enumerate(cue_list):
            seq = tmp / f"c{idx}"
            seq.mkdir()
            frames = max(1, int(dur * FPS))
            for f in range(frames):
                im = M.COMPONENTS[name](a.canvas, f / max(1, frames - 1), **kw)
                im.save(seq / f"{f:04d}.png")
            inputs += ["-framerate", str(FPS), "-i", str(seq / "%04d.png")]
            n = idx + 1
            filt.append(
                f"[{n}:v]setpts=PTS-STARTPTS+{start}/TB[c{idx}]")
            filt.append(
                f"[{last}][c{idx}]overlay=0:0:enable='between(t,{start},{start + dur})'"
                f"[o{idx}]")
            last = f"o{idx}"
            print(f"  rendered {frames:>3} frames  {name}")

        inputs += ["-i", str(wav)]
        audio_idx = len(cue_list) + 1

        # Mix the effects UNDER the clip's own audio rather than replacing
        # it. The first version mapped only the bed, which silently dropped
        # the engine - and the whole question this demo exists to answer is
        # whether the effects read against the engine.
        if has_audio(ff, a.clip) and a.source_gain > 0:
            filt.append(f"[0:a]volume={a.source_gain},pan=mono|c0=.5*c0+.5*c1[srca]")
            filt.append(f"[{audio_idx}:a]volume={a.sfx_gain}[sfxa]")
            if not a.duck:
                filt.append("[srca][sfxa]amix=inputs=2:duration=first:normalize=0,"
                            "alimiter=limit=0.85[aout]")
                duck = "flat"
            else:
                # Duck the engine under each hit. Without this the effects
                # measured only +0.8 dB over the engine across every cue -
                # present in the file, inaudible to a listener.
                filt.append("[sfxa]asplit=2[sfxmix][sfxkey]")
                filt.append("[srca][sfxkey]sidechaincompress="
                            "threshold=0.03:ratio=8:attack=5:release=220[ducked]")
                filt.append("[ducked][sfxmix]amix=inputs=2:duration=first:"
                            "normalize=0,alimiter=limit=0.85[aout]")
                duck = "ducked"
            amap = ["-map", "[aout]"]
            print(f"  audio: clip x{a.source_gain:.2f} ({duck}) "
                  f"+ effects x{a.sfx_gain:.2f}")
        else:
            amap = ["-map", f"{audio_idx}:a"]
            print("  audio: effects only (clip has no audio track)")

        cmd = [ff, "-y"] + inputs + [
            "-filter_complex", ";".join(filt),
            "-map", f"[{last}]"] + amap + [
            "-t", f"{end}",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", a.out, "-loglevel", "error"]
        print("\n  encoding ...")
        subprocess.run(cmd, check=True)
        print(f"  wrote {a.out}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
