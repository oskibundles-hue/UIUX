"""
Build a 1080x1920 plate out of several clips instead of one.

    python3 make_montage.py --car fall-rally --fps 30 \
        --clip "/path/fleet.mov@1.5:3.0" \
        --clip "/path/roma.mov@6.0:3.0" ...

Each --clip is <file>@<start>:<duration>. Every segment is scaled to fill
1080x1920, trimmed, and hard-cut to the next - no dissolves, per the house
record. The result lands at <car>/source/plate-1080x1920.mp4, exactly where
build_ad.py expects a plate, so a montage and a single-take plate are
interchangeable downstream.

Measure it afterwards the same way as any other plate:

    python3 make_plate.py --car <car> --measure-only --start 0 --dur <T>

A montage cuts under the type, so expect the bands to measure wide and expect
to land on the panel layout. Read the report, do not assume.
"""
import argparse, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILL = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"


def parse_clip(spec):
    try:
        path, rest = spec.rsplit("@", 1)
        start, dur = rest.split(":")
        return Path(path), float(start), float(dur)
    except ValueError:
        sys.exit(f'bad --clip "{spec}" - want <file>@<start>:<duration>')


def segment(src, start, dur, out, fps, lut=None):
    vf = FILL + f",fps={fps},format=yuv420p"
    if lut:
        vf = f"lut3d={lut}," + vf
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur),
                    "-i", str(src), "-vf", vf, "-c:v", "libx264", "-preset", "medium",
                    "-crf", "16", "-an", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--car", required=True)
    ap.add_argument("--clip", action="append", required=True,
                    help="<file>@<start>:<duration>, repeatable, in cut order")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--lut", help="optional .cube applied to every segment")
    a = ap.parse_args()

    tmp = HERE / ".montage"
    tmp.mkdir(exist_ok=True)
    for f in tmp.glob("seg_*.mp4"):
        f.unlink()

    parts, total = [], 0.0
    for i, spec in enumerate(a.clip):
        src, start, dur = parse_clip(spec)
        if not src.exists():
            sys.exit(f"missing clip: {src}")
        out = tmp / f"seg_{i:02d}.mp4"
        segment(src, start, dur, out, a.fps, a.lut)
        parts.append(out)
        total += dur
        print(f"  {i+1}. {src.name}  {start:.1f}s +{dur:.1f}s")

    listing = tmp / "concat.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))

    plate = HERE / a.car / "source" / "plate-1080x1920.mp4"
    plate.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(listing), "-c:v", "libx264", "-preset", "slow",
                    "-crf", "18", "-an", "-movflags", "+faststart", str(plate)],
                   check=True)
    print(f"plate: {plate} ({plate.stat().st_size/1048576:.1f} MB, "
          f"{len(parts)} cuts, {total:.1f}s)")


if __name__ == "__main__":
    main()
