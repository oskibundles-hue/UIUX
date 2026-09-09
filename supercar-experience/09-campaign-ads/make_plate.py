"""
Build a 1080x1920 plate from an Osmo D-Log M raw, then measure it.

    python3 make_plate.py --raw gt3.mov --car porsche-gt3rs --start 41.0 [--dur 15] [--look golden]

Output: <car>/source/plate-1080x1920.mp4 (30 fps, H.264, no audio) and a
zone report - mean / min / max luminance under the logo-bug band, the
mid band (title + build sheet) and the CTA band, sampled across the whole
plate. Pick tones from the report, not from a thumbnail. This is the
"measure the footage, then choose" step from the FD record.
"""
import argparse, os, subprocess, sys, json
from pathlib import Path
from PIL import Image, ImageStat

HERE = Path(__file__).resolve().parent
LUTS = HERE / "_grade" / "luts"
LOOKS = {"rescue": ["AK_DLogM_Rescue"], "golden": ["AK_DLogM_Rescue", "AK_Golden_Vlog"],
         "signature": ["AK_DLogM_Rescue", "AK_NQ_Signature"], "dark": ["AK_DLogM_Rescue", "AK_Garage_Dark"],
         # "none" is for footage that is already graded - the site's own car reels,
         # or any delivered master. Applying a D-Log rescue to those double-grades.
         "none": []}

def run(cmd): subprocess.run(cmd, check=True)

def build(raw, car, start, dur, look, fps=30, crop=None):
    """crop is an ffmpeg crop spec (w:h:x:y) applied before the scale - use it to
    pull a 9:16 window out of a square/ultra-wide source."""
    out = HERE / car / "source" / "plate-1080x1920.mp4"; out.parent.mkdir(parents=True, exist_ok=True)
    steps = [f"lut3d={(LUTS / (n + '.cube')).as_posix()}" for n in LOOKS[look]]
    if crop: steps.insert(0, f"crop={crop}")
    steps += ["scale=1080:1920:flags=lanczos", f"fps={fps}", "format=yuv420p"]
    vf = ",".join(steps)
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", str(raw),
         "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", "-movflags", "+faststart", str(out)])
    return out

def measure(plate, samples=24):
    """Luminance under each graphic band, across the clip."""
    tmp = HERE / ".measure"; tmp.mkdir(exist_ok=True)
    for f in tmp.glob("*.jpg"): f.unlink()
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(plate)]))
    run(["ffmpeg", "-v", "error", "-y", "-i", str(plate), "-vf", f"fps={samples/dur},scale=270:480", "-q:v", "3", str(tmp / "s_%03d.jpg")])
    zones = {"bug (top 11-19%)": (0.05, 0.11, 0.60, 0.19), "mid band (40-60%)": (0.075, 0.40, 0.84, 0.60),
             "cta band (62-72%)": (0.10, 0.62, 0.90, 0.72), "lower third (66-80%)": (0.06, 0.66, 0.70, 0.80)}
    report = {}
    frames = sorted(tmp.glob("s_*.jpg"))
    for name, (x0, y0, x1, y1) in zones.items():
        means = []
        for f in frames:
            im = Image.open(f).convert("L"); w, h = im.size
            means.append(ImageStat.Stat(im.crop((int(w*x0), int(h*y0), int(w*x1), int(h*y1)))).mean[0])
        report[name] = dict(mean=round(sum(means)/len(means)), min=round(min(means)), max=round(max(means)))
    return report, len(frames), dur

def decide(r):
    out = {}
    for zone, v in r.items():
        # white type needs a dark-enough zone; black needs bright. Wide range = neither.
        if v["max"] < 150: out[zone] = "WHITE type / white logo"
        elif v["min"] > 120: out[zone] = "BLACK type / black logo"
        elif v["mean"] < 110 and v["max"] - v["min"] < 130: out[zone] = "white, with shadow"
        else: out[zone] = "range too wide - scrim or move the element"
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", help="source clip; not needed with --measure-only"); ap.add_argument("--car", required=True)
    ap.add_argument("--start", type=float, default=0.0); ap.add_argument("--dur", type=float, default=15.0)
    ap.add_argument("--look", choices=LOOKS, default="golden"); ap.add_argument("--measure-only", action="store_true")
    ap.add_argument("--crop", help="ffmpeg crop spec w:h:x:y, applied before the scale")
    a = ap.parse_args()
    plate = HERE / a.car / "source" / "plate-1080x1920.mp4"
    if not a.measure_only and not a.raw:
        ap.error("--raw is required unless --measure-only")
    if not a.measure_only:
        plate = build(a.raw, a.car, a.start, a.dur, a.look, crop=a.crop); print("plate:", plate, f"({plate.stat().st_size/1048576:.1f} MB)")
    r, n, dur = measure(plate)
    print(f"measured {n} frames over {dur:.2f}s")
    d = decide(r)
    for z in r: print(f"  {z:<24} mean {r[z]['mean']:>3}  range {r[z]['min']:>3}-{r[z]['max']:<3}  -> {d[z]}")
    (HERE / a.car / "source" / "zones.json").write_text(json.dumps({"zones": r, "decision": d, "start": a.start, "dur": a.dur, "look": a.look, "crop": a.crop, "raw": a.raw}, indent=1))
