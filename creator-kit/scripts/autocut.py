#!/usr/bin/env python3
"""
autocut - silence-cut, grade and export a clip in one command.

Takes a raw D-Log clip and produces an upload-ready file:

  1. finds the silences and removes them, cutting only where you stop talking
  2. applies your grade LUT
  3. exports 4K 29.97fps, two-pass, hitting a target file size

The export target follows the 4K-upload method: 4K at 29.97fps, 10-35 Mbps,
file around 75 MB, then upload through Instagram's Edits app. Two-pass
encoding is what lets it hit the size on the nose rather than landing wherever
a CRF happens to put it.

Requires ffmpeg. Pure standard library otherwise.

Usage:
    python3 autocut.py source.MOV -l ../luts/AK_NQ_Signature.cube -o reel.mp4

    # keep it under 60 MB and leave a bit more air around each phrase
    python3 autocut.py source.MOV --target-mb 60 --pad 0.12

    # see the cut plan without encoding
    python3 autocut.py source.MOV --dry-run
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def ffmpeg_bin():
    b = shutil.which("ffmpeg")
    if not b:
        raise SystemExit("ffmpeg not found on PATH")
    return b


def probe(ff, path):
    """Duration, resolution and fps, read from ffmpeg's own banner."""
    out = run([ff, "-hide_banner", "-i", path]).stderr
    dur = 0.0
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if m:
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    w = h = 0
    m = re.search(r"Video:.*?[, ](\d{2,5})x(\d{2,5})", out)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
    fps = 30.0
    m = re.search(r"([\d.]+) fps", out)
    if m:
        fps = float(m.group(1))
    has_audio = "Audio:" in out
    return {"duration": dur, "width": w, "height": h, "fps": fps, "audio": has_audio}


def find_silences(ff, path, noise_db, min_len):
    """Return [(start, end)] of every detected silence, in seconds.

    -vn matters more than it looks. Without it ffmpeg decodes the video stream
    to find silence in the audio, and on a 4K60 HEVC source that is 0.84x
    realtime. Sweeping five thresholds to pick a cut rhythm then costs five full
    4K decodes to read a waveform. Audio-only turns a minutes-long sweep into
    seconds."""
    out = run([ff, "-hide_banner", "-vn", "-i", path,
               "-af", "silencedetect=noise=%ddB:d=%s" % (noise_db, min_len),
               "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    spans = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        spans.append((s, e))
    return spans


def keep_segments(silences, duration, pad, min_seg):
    """Invert the silences into the speech segments worth keeping.

    `pad` leaves a little air on each side so words are not clipped at the
    boundary; without it, cuts land hard on the first and last phoneme and the
    edit sounds clipped.
    """
    segs, cursor = [], 0.0
    for s, e in silences:
        start = cursor
        end = min(s + pad, duration)
        if end - start >= min_seg:
            segs.append((max(0.0, start), end))
        cursor = max(0.0, (e - pad) if e is not None else duration)
    if duration - cursor >= min_seg:
        segs.append((cursor, duration))

    # Merge segments separated by a gap too short to be worth a cut - a
    # 0.1s hole reads as a glitch, not an edit.
    merged = []
    for s, e in segs:
        if merged and s - merged[-1][1] < 0.25:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def build_filter(segs, lut, fps, out_w, out_h, sharpen, has_audio, lut_after_scale=False):
    """One filter_complex over a SINGLE decode of the source.

    The obvious way to assemble segments is one `-ss/-t -i` per segment plus
    concat, but that makes ffmpeg open and decode the file once per segment -
    on a 4K60 source that is ruinous. `select` with a between() expression
    keeps the same frames from a single decode pass, and setpts closes the
    gaps left behind.
    """
    expr = "+".join("between(t,%.3f,%.3f)" % (s, e) for s, e in segs)

    chain = ["[0:v]select='%s',setpts=N/FRAME_RATE/TB" % expr]
    lut_step = None
    if lut:
        esc = lut.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        lut_step = "format=gbrp16le,lut3d=file='%s':interp=tetrahedral" % esc
    scale_step = ("scale=%d:%d:flags=lanczos+accurate_rnd:force_original_aspect_ratio=increase"
                  % (out_w, out_h))
    # LUT before scale is the correct order: averaging log-encoded pixels and
    # then transforming is not the same as transforming and then averaging.
    # Scaling first runs the LUT over far fewer pixels, which roughly doubles
    # throughput on a 4K source - worth it when you are downscaling anyway.
    if lut_step and lut_after_scale:
        chain += [scale_step, "crop=%d:%d" % (out_w, out_h), lut_step]
    else:
        if lut_step:
            chain.append(lut_step)
        chain += [scale_step, "crop=%d:%d" % (out_w, out_h)]
    if sharpen and float(sharpen) > 0:
        chain.append("unsharp=5:5:%s:5:5:0" % sharpen)
    chain.append("fps=%s" % fps)
    chain.append("setsar=1,format=yuv420p[vout]")
    graph = ",".join(chain)

    if has_audio:
        graph += (";[0:a]aselect='%s',asetpts=N/SR/TB,"
                  "loudnorm=I=-14:TP=-1.5:LRA=11[aout]" % expr)
    return graph


def main():
    ap = argparse.ArgumentParser(description="Silence-cut, grade and export in one pass.")
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("-l", "--lut", default=None, help="grade LUT (.cube)")
    ap.add_argument("--noise", type=int, default=-30, help="silence threshold in dB (default -30)")
    ap.add_argument("--min-silence", type=float, default=0.35,
                    help="ignore silences shorter than this (default 0.35s)")
    ap.add_argument("--pad", type=float, default=0.08,
                    help="air kept on each side of speech (default 0.08s)")
    ap.add_argument("--min-seg", type=float, default=0.40,
                    help="drop kept segments shorter than this (default 0.40s)")
    ap.add_argument("--target-mb", type=float, default=75.0,
                    help="target output size in MB (default 75, per the 4K upload method)")
    ap.add_argument("--fps", default="30000/1001", help="output fps (default 29.97)")
    ap.add_argument("--height", type=int, default=3840, help="output height (default 3840)")
    ap.add_argument("--sharpen", default="0", help="unsharp amount, 0 disables")
    ap.add_argument("--max-mbps", type=float, default=35.0, help="bitrate ceiling (default 35)")
    ap.add_argument("--min-mbps", type=float, default=10.0, help="bitrate floor (default 10)")
    ap.add_argument("--two-pass", action="store_true",
                    help="exact file-size targeting, but twice the encode time")
    ap.add_argument("--preset", default="medium", help="x264 preset (default medium)")
    ap.add_argument("--fast", action="store_true",
                    help="scale before the LUT when downscaling. Roughly doubles "
                         "throughput; slightly less correct than transforming at "
                         "full resolution, and does nothing when output is native size")
    ap.add_argument("--dry-run", action="store_true", help="print the cut plan and stop")
    args = ap.parse_args()

    ff = ffmpeg_bin()
    if not os.path.isfile(args.input):
        raise SystemExit("input not found: %s" % args.input)
    if args.lut and not os.path.isfile(args.lut):
        raise SystemExit("LUT not found: %s" % args.lut)

    info = probe(ff, args.input)
    if info["duration"] <= 0:
        raise SystemExit("could not read a duration from %s" % args.input)
    out_h = args.height
    out_w = int(round(out_h * 9 / 16 / 2)) * 2

    print("source   : %s" % os.path.basename(args.input))
    print("           %dx%d  %.2f fps  %.1fs" % (info["width"], info["height"], info["fps"], info["duration"]))

    silences = find_silences(ff, args.input, args.noise, args.min_silence)
    segs = keep_segments(silences, info["duration"], args.pad, args.min_seg)
    if not segs:
        raise SystemExit("no speech segments found - try --noise -40 or --min-silence 0.6")

    kept = sum(e - s for s, e in segs)
    print("silences : %d found  ->  %d segments kept" % (len(silences), len(segs)))
    print("length   : %.1fs  ->  %.1fs  (removed %.1fs, %.0f%%)"
          % (info["duration"], kept, info["duration"] - kept,
             100 * (info["duration"] - kept) / info["duration"]))
    avg = kept / len(segs)
    print("shot len : %.1fs average" % avg)

    if args.dry_run:
        print("\ncut plan:")
        for i, (s, e) in enumerate(segs, 1):
            print("  %2d  %7.2f -> %7.2f   (%.2fs)" % (i, s, e, e - s))
        return

    # Bitrate to land on the target size, clamped to the method's 10-35 Mbps.
    audio_kbps = 192
    total_kbits = args.target_mb * 8 * 1024
    v_kbps = (total_kbits / kept) - audio_kbps
    wanted = v_kbps / 1000.0
    v_mbps = max(args.min_mbps, min(args.max_mbps, wanted))
    v_kbps = int(v_mbps * 1000)
    est_mb = (v_kbps + audio_kbps) * kept / 8 / 1024
    print("bitrate  : %.1f Mbps video  ->  ~%.0f MB for %.1fs" % (v_mbps, est_mb, kept))
    if wanted < args.min_mbps:
        # Quality floor wins over the size target: a 4K frame starved below
        # 10 Mbps looks worse than a slightly larger file uploads badly.
        print("           %.1f Mbps would hit %.0f MB, but that is below the %.0f Mbps"
              % (wanted, args.target_mb, args.min_mbps))
        print("           floor for 4K. Holding the floor - shorten the cut to about"
              " %.0fs, or raise --target-mb to %.0f." 
              % (args.target_mb * 8 * 1024 / (args.min_mbps * 1000 + audio_kbps), est_mb))
    print("output   : %dx%d @ %s fps\n" % (out_w, out_h, args.fps))

    out = args.output or (os.path.splitext(args.input)[0] + "_cut.mp4")
    # Pass 1 measures video complexity only. Reusing the full graph leaves the
    # loudnorm branch unconnected, which ffmpeg rejects outright.
    lut_after = args.fast and out_h < info["height"]
    graph = build_filter(segs, args.lut, args.fps, out_w, out_h, args.sharpen, info["audio"], lut_after)
    graph_v = build_filter(segs, args.lut, args.fps, out_w, out_h, args.sharpen, False, lut_after)


    maps = ["-map", "[vout]"] + (["-map", "[aout]"] if info["audio"] else [])
    common = [
        "-c:v", "libx264", "-preset", args.preset,
        "-b:v", "%dk" % v_kbps, "-maxrate", "%dk" % int(v_kbps * 1.35),
        "-bufsize", "%dk" % int(v_kbps * 2.5),
        "-profile:v", "high", "-level", "5.2", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
    ]
    audio = ["-c:a", "aac", "-b:a", "%dk" % audio_kbps, "-ar", "48000", "-ac", "2"] if info["audio"] else ["-an"]

    if not args.two_pass:
        # Single-pass ABR. Lands near the target rather than exactly on it, at
        # half the encode time - the better default for a 4K source, where the
        # LUT alone runs at 0.23x realtime.
        print("encoding (single pass) ...")
        p = run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", args.input,
                 "-filter_complex", graph] + maps + common + audio +
                ["-movflags", "+faststart", out])
        if p.returncode != 0:
            sys.stderr.write(p.stderr[-3000:])
            raise SystemExit("encode failed")
    else:
        tmp = tempfile.mkdtemp(prefix="autocut-")
        log = os.path.join(tmp, "pass")
        try:
            print("pass 1/2 ...")
            p = run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", args.input,
                     "-filter_complex", graph_v, "-map", "[vout]"] + common +
                    ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull])
            if p.returncode != 0:
                sys.stderr.write(p.stderr[-3000:])
                raise SystemExit("pass 1 failed")
            print("pass 2/2 ...")
            p = run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", args.input,
                     "-filter_complex", graph] + maps + common +
                    ["-pass", "2", "-passlogfile", log] + audio +
                    ["-movflags", "+faststart", out])
            if p.returncode != 0:
                sys.stderr.write(p.stderr[-3000:])
                raise SystemExit("pass 2 failed")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    mb = os.path.getsize(out) / 1024 / 1024
    print("\ndone: %s  (%.1f MB)" % (out, mb))
    if mb > args.target_mb * 1.15:
        print("note: over target - the clip is too long to fit %.0f MB at the 4K"
              " bitrate floor." % args.target_mb)
    print("\nUpload path: import this into Instagram's Edits app and export 4K from")
    print("there, rather than posting straight to the Reels composer.")


if __name__ == "__main__":
    main()
