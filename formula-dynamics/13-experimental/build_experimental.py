#!/usr/bin/env python3
"""Two experimental cuts, built from components lifted off the dealer templates.

These are deliberately NOT the house ad. They borrow devices the reference
videos use well and test whether they survive contact with the brand:

  EXP-1  frosted glass panels   real frosted glass, not a flat plate: the panel
                                region is cropped out of the picture, blurred,
                                and put back, so the car moves behind the glass
                                exactly as it does in the reference. Plus the
                                staged build and the circular swipe affordance.

Everything is generated; nothing is traced from the templates themselves.

    python3 build_experimental.py exp1 /path/to/clip.mp4
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "99-toolkit"))

from PIL import Image, ImageDraw          # noqa: E402
import fd_brand as B                       # noqa: E402
import fd_render as R                      # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "cuts"
TMP = HERE / ".tmp"
W, H = B.CANVASES["9x16"]


def ff():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr.strip().splitlines()[-1] if r.stderr else "ffmpeg failed")


# ---------------------------------------------------------------- components

def panel_text(lines, width, height):
    """Text for one frosted panel: a red kicker, a big figure, a subline."""
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    kicker, figure, sub = lines
    pad = 34
    y = pad
    k = R.text(kicker, 26, B.RED, tracking=0.26)
    R.paste(im, k, pad, y)
    y += k.height + 18
    f = R.fit_text(figure, width - pad * 2, max_height=int(height * 0.46),
                   color=B.WHITE, tracking=0.02)
    R.paste(im, f, pad, y)
    y += f.height + 14
    s = R.text(sub, 24, B.WHITE, tracking=0.20)
    R.paste(im, s, pad, y)
    return im


def fine_print(text, width):
    im = Image.new("RGBA", (width, 60), (0, 0, 0, 0))
    t = R.text(text, 21, B.WHITE, tracking=0.10)
    R.paste(im, t, 0, 0)
    return im


def swipe_arrow(d=104):
    """The circular affordance the dealer templates put bottom-centre."""
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([2, 2, d - 3, d - 3], fill=(255, 255, 255, 235))
    cx, cy, a = d // 2, d // 2, d * 0.24
    dr.line([(cx, cy + a), (cx, cy - a)], fill=B.rgb(B.BLACK) + (255,), width=7)
    dr.line([(cx - a * 0.62, cy - a * 0.28), (cx, cy - a)],
            fill=B.rgb(B.BLACK) + (255,), width=7)
    dr.line([(cx + a * 0.62, cy - a * 0.28), (cx, cy - a)],
            fill=B.rgb(B.BLACK) + (255,), width=7)
    return im


def vertical_tab(label):
    word = R.text(label, 60, B.WHITE, tracking=0.24)
    pad = 40
    bar = Image.new("RGBA", (word.width + pad * 2, word.height + pad * 2),
                    B.rgb(B.RED) + (255,))
    R.paste(bar, word, bar.width // 2, bar.height // 2, anchor="cm")
    return bar.rotate(90, expand=True)


def header_bar(label, width=520, height=62):
    im = Image.new("RGBA", (width, height), B.rgb(B.RED) + (255,))
    t = R.text(label, 30, B.WHITE, tracking=0.22)
    R.paste(im, t, width // 2, height // 2, anchor="cm")
    return im


def name_block(name, sub):
    im = Image.new("RGBA", (W, 190), (0, 0, 0, 0))
    n = R.text(name, 62, B.WHITE, tracking=0.05)
    R.paste(im, R.with_shadow(n), 0, 0)
    s = R.text(sub, 26, B.WHITE, tracking=0.24)
    R.paste(im, s, 2, n.height + 18)
    return im


# ------------------------------------------------------------------- EXP  1

def exp1(source, out):
    """Frosted glass price panels, built up in stages."""
    TMP.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    x0 = int(W * 0.05)
    pw, ph = 400, 240
    gap = 26
    px2 = x0 + pw + gap
    py = int(H * 0.615)

    R.save(name_block("FERRARI SF90 STRADALE", "ANNUAL SERVICE  ·  FORMULA DYNAMICS"),
           TMP / "e1-name.png")
    R.save(panel_text(("PACKAGE PRICE", "$3,999", "PER YEAR"), pw, ph),
           TMP / "e1-p1.png")
    R.save(panel_text(("WHAT YOU GET", "6 VISITS", "PLUS SUSPENSION"), pw, ph),
           TMP / "e1-p2.png")
    R.save(fine_print("OIL INCLUDED  ·  PADS NOT INCLUDED  ·  10% OFF PERFORMANCE UPGRADES", W),
           TMP / "e1-fine.png")
    R.save(swipe_arrow(), TMP / "e1-arrow.png")
    R.save(header_bar("FORMULA DYNAMICS"), TMP / "e1-head.png")

    # Frosted glass: crop each panel's rectangle out of the picture, blur and
    # darken it, then put it back. The car keeps moving behind the glass.
    g = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},fps=30,setsar=1[base];"
        f"[base]split=3[b0][c1][c2];"
        f"[c1]crop={pw}:{ph}:{x0}:{py},boxblur=22:2,eq=brightness=-0.13[g1];"
        f"[c2]crop={pw}:{ph}:{px2}:{py},boxblur=22:2,eq=brightness=-0.13[g2];"
        f"[b0][g1]overlay={x0}:{py}:enable='gte(t,3.2)'[s1];"
        f"[s1][g2]overlay={px2}:{py}:enable='gte(t,4.4)'[s2];"
        f"[s2][1:v]overlay=x={x0}:y={int(H*0.505)}:"
        f"enable='gte(t,1.4)':format=auto[s3];"
        f"[s3][2:v]overlay=x={x0}:y={py}:enable='gte(t,3.2)':format=auto[s4];"
        f"[s4][3:v]overlay=x={px2}:y={py}:enable='gte(t,4.4)':format=auto[s5];"
        f"[s5][4:v]overlay=x={x0}:y={int(H*0.775)}:"
        f"enable='gte(t,5.6)':format=auto[s6];"
        f"[s6][5:v]overlay=x=(W-w)/2:y={int(H*0.845)}:"
        f"enable='gte(t,6.4)':format=auto[s7];"
        f"[s7][6:v]overlay=x={W-520-int(W*0.05)}:y={int(H*0.10)}:"
        f"enable='gte(t,0.6)':format=auto[vout]"
    )
    cmd = [ff(), "-nostdin", "-y", "-i", str(source)]
    for n in ("e1-name", "e1-p1", "e1-p2", "e1-fine", "e1-arrow", "e1-head"):
        cmd += ["-loop", "1", "-i", str(TMP / f"{n}.png")]
    cmd += ["-filter_complex", g, "-map", "[vout]", "-map", "0:a?",
            "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out)]
    run(cmd)
    print(f"ok  {out.name}")


# ------------------------------------------------------------------- EXP  2
#
# EXP-2 was a detail grid: hero picture over a strip of three sub-panes pulled
# from the same clip, with a vertical section tab and a caption plate. It was
# built, looked at, and thrown away - the strip cut the hero picture in half
# and the layout read as a brochure page rather than as a piece of film. The
# vertical tab was the one part worth keeping and it survives on its own as
# `--spec-style tab` in 99-toolkit/fd_spec.py.
#
# Not kept as dead code. If a detail grid is wanted later it should be built
# against a clip shot for it, not retrofitted onto a rolling beauty shot.


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    OUT.mkdir(exist_ok=True)
    if which in ("exp1", "both"):
        exp1(src or Path(os.environ["SF90"]), OUT / "FD-EXP1-Glass-Panels.mp4")
