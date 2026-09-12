#!/usr/bin/env python3
"""Reframe a finished 9:16 ad into the other ad-platform canvases.

Why this exists rather than a re-render: the approved ads carry their graphics
burned in. The spec panel sits at y 1074-1314 with the title block directly
under it, so going to 4:5 means losing 570px of height and going to 1:1 means
losing 840px - either crop takes the panel, the title block or the logo bug
with it. Measured, not guessed.

So the picture is never cut. The whole 1080x1920 frame is scaled to fit inside
the target canvas and the remainder is filled with a blurred, darkened copy of
the same frame. Every graphic survives at full height; the cost is how much of
the canvas is real picture:

    4x5  1080x1350  ->  picture 760px wide,  70% of the canvas
    1x1  1080x1080  ->  picture 608px wide,  56% of the canvas
    16x9 1920x1080  ->  picture 608px wide,  32% of the canvas  (too thin - see
                        README; this ratio wants a true re-render from footage)

No border on the picture edge. The shop's rule is translucent, never bordered,
and a red frame around the video would break it for the sake of a flourish.

Audio is copied through untouched - these files are already mastered to
-14 LUFS / -1.0 dBTP and re-encoding would undo that.

    python3 fd_reframe.py 4x5 in.mp4 [more.mp4 ...] -o out/
    python3 fd_reframe.py 1x1 folder/ -o out/
    python3 fd_reframe.py 4x5 in.mp4 --dry-run
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fd_brand as B  # noqa: E402

# The canvases this tool targets. 9x16 is the source shape, not a destination.
TARGETS = {k: v for k, v in B.CANVASES.items() if k != "9x16"}

# The fill has two jobs: stop the bars reading as dead black, and stay out of
# the way of the picture. sigma 28 destroys all detail at 1080 wide, and the
# brightness/saturation cut pushes it behind the real frame so the car and the
# type in the middle carry the eye.
FILL_BLUR = 28
FILL_BRIGHTNESS = -0.18
FILL_SATURATION = 0.85


def ffmpeg_bin() -> str:
    from shutil import which
    exe = which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe(path: Path) -> tuple[int, int, float]:
    """Read width, height and duration off the file itself."""
    out = subprocess.run([ffmpeg_bin(), "-i", str(path)],
                         capture_output=True, text=True).stderr
    import re
    m = re.search(r"(\d{3,5})x(\d{3,5})", out)
    if not m:
        raise SystemExit(f"could not read dimensions from {path.name}")
    w, h = int(m.group(1)), int(m.group(2))
    d = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    dur = (int(d.group(1)) * 3600 + int(d.group(2)) * 60
           + float(d.group(3))) if d else 0.0
    return w, h, dur


def picture_width(sw: int, sh: int, tw: int, th: int) -> int:
    """Width the source occupies once fitted inside the target, rounded even."""
    if sw / sh > tw / th:          # source wider than target: fit by width
        return tw
    w = round(th * sw / sh)
    return w - (w % 2)


def chain(tw: int, th: int) -> str:
    """Blurred fill behind, untouched picture in front, both centred."""
    return (
        f"[0:v]split=2[bg][fg];"
        # Cover the canvas, crop to it, then destroy the detail. Scaling first
        # and blurring after keeps the bars reading as this clip rather than as
        # generic grey.
        f"[bg]scale={tw}:{th}:force_original_aspect_ratio=increase,"
        f"crop={tw}:{th},gblur=sigma={FILL_BLUR},"
        f"eq=brightness={FILL_BRIGHTNESS}:saturation={FILL_SATURATION}[bgo];"
        # Fit the whole frame inside - nothing is cropped, so no graphic is lost.
        f"[fg]scale={tw}:{th}:force_original_aspect_ratio=decrease[fgo];"
        f"[bgo][fgo]overlay=(W-w)/2:(H-h)/2:format=auto,"
        f"format=yuv420p[v]"
    )


def reframe(src: Path, key: str, dest: Path, dry: bool) -> None:
    tw, th = TARGETS[key]
    sw, sh, dur = probe(src)
    pw = picture_width(sw, sh, tw, th)
    pct = 100.0 * pw / tw
    print(f"  {src.name}")
    print(f"    {sw}x{sh} {dur:.2f}s  ->  {tw}x{th}"
          f"   picture {pw}px ({pct:.0f}% of canvas)")
    if dry:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg_bin(), "-y", "-i", str(src),
           "-filter_complex", chain(tw, th),
           "-map", "[v]", "-map", "0:a?",
           # Audio is already mastered. Copy it; do not touch it.
           "-c:a", "copy",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           str(dest), "-loglevel", "error"]
    subprocess.run(cmd, check=True)
    print(f"    wrote {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ratio", choices=sorted(TARGETS))
    ap.add_argument("inputs", nargs="+", help="video files, or folders of them")
    ap.add_argument("-o", "--out", default=None,
                    help="output folder (default: <ratio>/ beside the input)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report the geometry without encoding")
    a = ap.parse_args()

    srcs: list[Path] = []
    for raw in a.inputs:
        p = Path(raw)
        if p.is_dir():
            srcs += sorted(q for q in p.iterdir() if q.suffix.lower() == ".mp4")
        else:
            srcs.append(p)
    if not srcs:
        raise SystemExit("no inputs found")

    tw, th = TARGETS[a.ratio]
    print(f"{a.ratio}  {tw}x{th}   {len(srcs)} file(s)")
    for s in srcs:
        out_dir = Path(a.out) if a.out else s.parent / a.ratio
        reframe(s, a.ratio, out_dir / s.name, a.dry_run)


if __name__ == "__main__":
    main()
