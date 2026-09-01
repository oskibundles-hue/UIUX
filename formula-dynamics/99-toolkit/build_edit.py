#!/usr/bin/env python3
"""
Formula Dynamics Performance - burn the overlay set into a video.

Takes your footage and renders a finished, on-brand cut: title card in,
logo bug for the body of the video, service name plate, feature badge, one
call to action, end card. Timing follows the edit rules in the kit - the CTA
sits on the payoff rather than the last frame, and never overlaps the end
card, because two asks is zero asks.

    # See the cue sheet without rendering
    python3 build_edit.py clip.mp4 --template reveal --dry-run

    # Render it
    python3 build_edit.py clip.mp4 --template reveal -o out.mp4

Templates map to the seven shot formulas in 06-video-system/SHOT-LISTS.md.
Any element can be overridden: --title, --service, --badge, --cta, --none cta

Requires ffmpeg. If it is not on PATH, `pip install imageio-ffmpeg` supplies one.
"""

import argparse
import json
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

import fd_brand as B


# --------------------------------------------------------------------------
# Templates - which asset fills each slot, per video format
# --------------------------------------------------------------------------
TEMPLATES = {
    "reveal": dict(title="body-kits", service="body-kits", badge="body-kits",
                   cta="book-your-build",
                   about="Body-kit / aero reveal. Peak desire, so ask for the build."),
    "sound-check": dict(title="sound-check", service="exhaust", badge="exhaust",
                        cta="dm-for-pricing",
                        about="Exhaust. The note is the hook - they want the price."),
    "fitment": dict(title="wheels", service="wheels", badge="wheels",
                    cta="see-what-fits",
                    about="Wheels. Fitment is the exact worry, so answer it."),
    "dyno": dict(title="dyno-results", service="tuning", badge="tuning",
                 cta="book-now",
                 about="Dyno / tune. Hard proof earns a hard ask."),
    "before-after": dict(title="before-after", service=None, badge=None,
                         cta="what-would-you-fit",
                         about="Before & after. Comment bait - built for reach."),
    "install-day": dict(title="install-day", service=None, badge=None,
                        cta="now-booking",
                        about="Install timelapse. Shows capacity is real."),
    "service": dict(title=None, service="service", badge="service",
                    cta="we-service-what-we-build",
                    about="Maintenance. Trust, not sale."),
}


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found. Install it, or: pip install imageio-ffmpeg")


def ffprobe_bin():
    exe = shutil.which("ffprobe")
    return exe or ffmpeg_bin().replace("ffmpeg", "ffprobe")


def probe(path):
    """Duration, size and fps of the source clip."""
    exe = shutil.which("ffprobe")
    if exe:
        out = subprocess.run(
            [exe, "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate:format=duration",
             "-of", "json", str(path)],
            capture_output=True, text=True, check=True).stdout
        d = json.loads(out)
        s = d["streams"][0]
        num, den = s["r_frame_rate"].split("/")
        return (float(d["format"]["duration"]), int(s["width"]),
                int(s["height"]), round(float(num) / float(den), 3))

    # No ffprobe: parse ffmpeg's own stderr banner instead.
    out = subprocess.run([ffmpeg_bin(), "-i", str(path)],
                         capture_output=True, text=True).stderr
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = re.search(r"(\d{2,5})x(\d{2,5})", out)
    w, h = int(m.group(1)), int(m.group(2))
    m = re.search(r"([\d.]+) fps", out)
    return dur, w, h, float(m.group(1)) if m else 30.0


def canvas_for(w, h):
    """Pick the overlay canvas that matches the footage's aspect ratio."""
    ratio = w / h
    best, diff = "9x16", 1e9
    for key, (cw, ch) in B.CANVASES.items():
        d = abs(ratio - cw / ch)
        if d < diff:
            best, diff = key, d
    return best


# --------------------------------------------------------------------------
# The edit
# --------------------------------------------------------------------------
def plan(duration, canvas, tone, cfg, bug_position="top-left"):  # noqa: C901
    """Build the cue sheet.

    Beats are proportional with absolute clamps, so a 15 s clip and a 45 s
    clip both come out paced correctly rather than one of them running the
    title card for a sixth of its length.
    """
    ov = B.OVERLAYS
    # Real footage is rarely uniformly bright or dark: on this GT3 RS the
    # top of frame is sky (bright) while mid and lower frame is road and
    # shadow. So each element carries its own tone rather than inheriting
    # one global setting.
    t_title = cfg.get("title_tone") or tone
    t_badge = cfg.get("badge_tone") or tone
    t_end = cfg.get("endcard_tone") or tone
    bug_tone = cfg.get("bug_tone") or tone
    logo_tone = "white" if bug_tone == "dark" else "black"
    cues = []

    def add(layer, path, start, end, anim, note, place="full"):
        if path and Path(path).exists() and end > start + 0.15:
            cues.append(dict(layer=layer, path=str(path), start=round(start, 2),
                             end=round(end, 2), anim=anim, note=note,
                             place=place))

    # End card owns the last beat; everything else is laid out against it.
    end_len = min(3.0, max(2.0, duration * 0.10))
    end_start = duration - end_len

    # 1. Title card - the hook. Always ~2.5 s, never a sixth of the video.
    t_start = 0.4
    t_len = min(2.6, max(1.4, duration * 0.16))
    if cfg.get("title_scrim"):
        add("title scrim", cfg["title_scrim"], t_start, t_start + t_len, "fade",
            "Keeps the title legible as the shots change underneath it.")
    if cfg.get("title_custom"):
        add("title", cfg["title_custom"], t_start, t_start + t_len, "fade",
            "Hook. Names the car - the thing people search for.")
    elif cfg.get("title"):
        add("title", ov / "title-cards" /
            f"title_{canvas}_{cfg['title']}_{t_title}.png",
            t_start, t_start + t_len, "fade",
            "Hook. Over your strongest opening frame.")

    # 2. Logo bug - runs the body of the video, off before the end card so it
    #    does not sit on top of the logo that is already on that card.
    add("bug", ov / "corner-logo-bugs" /
        f"bug_{canvas}_{bug_position}_logo-{logo_tone}.png",
        0.6, end_start, "fade-in", "Branding. Same position on every video.")

    # 3. Service name plate.
    lt_start = max(t_start + t_len + 0.6, duration * 0.14)
    lt_len = min(4.0, max(2.5, duration * 0.22))
    if cfg.get("partner"):
        add("lower-third", ov / "lower-thirds" /
            f"lt_{canvas}_partner_{cfg['partner']}.png",
            lt_start, lt_start + lt_len, "slide",
            "Partner plate. Earns the reshare and adds third-party credibility.")
    elif cfg.get("service"):
        add("lower-third", ov / "lower-thirds" /
            f"lt_{canvas}_service_{cfg['service']}.png",
            lt_start, lt_start + lt_len, "slide",
            "Names the service while they are still watching.")

    # 4. Feature badge on the payoff shot.
    b_start = duration * 0.46
    b_len = min(3.0, max(2.0, duration * 0.16))
    if cfg.get("badge"):
        # Badges are loose chips, not frame-size, so they need placing:
        # centred, above the CTA band and clear of the bottom keep-out zone.
        add("badge", ov / "service-badges" / f"badge_{cfg['badge']}_{t_badge}.png",
            b_start, b_start + b_len, "fade", "Feature callout on the money shot.",
            place="centre-0.60")

    # 4b. Spec run - a multi-service build earns a rundown rather than one
    #     badge. Chips are spaced across the body of the video so each lands
    #     on its own shot instead of stacking up.
    specs = cfg.get("specs") or []
    cta_len_pre = min(4.0, max(2.5, duration * 0.22))
    spec_from = max(lt_start + lt_len + 0.8, duration * 0.30)
    spec_to = end_start - cta_len_pre - 2.2
    if specs and spec_to > spec_from + 1.5:
        slot = (spec_to - spec_from) / len(specs)
        hold = min(2.8, max(1.6, slot * 0.78))
        for i, (text, path) in enumerate(specs):
            st = spec_from + i * slot
            add(f"spec {i + 1}", path, st, st + hold, "fade",
                f"Spec: {text}", place="centre-0.585")

    # 5. One call to action, on the payoff - not the last frame, because most
    #    viewers leave before the end. Gap before the end card is deliberate:
    #    a CTA and an end card on screen together is two asks.
    cta_len = min(4.0, max(2.5, duration * 0.22))
    cta_start = end_start - cta_len - 1.0
    if cfg.get("cta") and cta_start > lt_start + lt_len + 0.4:
        add("cta", ov / "cta-captions" /
            f"cta_{canvas}_{cfg['cta_group']}_{cfg['cta']}_{cfg['cta_style']}.png",
            cta_start, cta_start + cta_len, "fade",
            "The ask. Lands on the payoff, clear of the end card.")

    # 6. End card - hard cut in, no fade. It is the last shot, not a graphic.
    add("endcard", ov / "end-cards" / f"endcard_{canvas}_{t_end}.png",
        end_start, duration + 0.05, "cut", "Contact details. Hold to the end.")

    return sorted(cues, key=lambda c: c["start"])


def cue_sheet(cues, duration, source):
    lines = [
        "",
        f"  CUE SHEET  ·  {Path(source).name}  ·  {duration:.1f}s",
        "  " + "-" * 74,
        f"  {'IN':>6}  {'OUT':>6}  {'LAYER':<12} {'ANIM':<9} ELEMENT",
        "  " + "-" * 74,
    ]
    for c in cues:
        lines.append(f"  {c['start']:>6.2f}  {c['end']:>6.2f}  {c['layer']:<12} "
                     f"{c['anim']:<9} {Path(c['path']).name}")
        lines.append(f"  {'':>14}  {'':<12} {'':<9} \033[2m{c['note']}\033[0m"
                     if sys.stdout.isatty() else
                     f"  {'':>14}  {'':<12} {'':<9} {c['note']}")
    lines.append("  " + "-" * 74)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------
FADE = 0.3


def filter_graph(cues, width, height):
    """Compose the overlay chain. Each cue is one input, faded and gated."""
    parts, last = [], "0:v"
    for i, c in enumerate(cues, start=1):
        tag = f"o{i}"
        s, e = c["start"], c["end"]
        dur = e - s
        f = [f"[{i}:v]format=rgba"]

        if c["anim"] == "cut":
            pass
        elif c["anim"] == "fade-in":
            f.append(f"fade=t=in:st={s:.2f}:d={FADE}:alpha=1")
        else:
            fo = min(FADE, dur / 3)
            f.append(f"fade=t=in:st={s:.2f}:d={min(FADE, dur / 3):.2f}:alpha=1")
            f.append(f"fade=t=out:st={e - fo:.2f}:d={fo:.2f}:alpha=1")
        parts.append(",".join(f) + f"[{tag}]")

        place = c.get("place", "full")
        if place.startswith("centre-"):
            base_x, y = "(W-w)/2", f"{float(place.split('-')[1]):.3f}*H"
        else:
            base_x, y = "0", "0"

        # A short slide sharpens the entrance on name plates.
        if c["anim"] == "slide":
            d = round(width * 0.11)
            x = (f"{base_x}+if(lt(t,{s + 0.3:.2f}),"
                 f"-{d}+(t-{s:.2f})/0.3*{d},0)")
        else:
            x = base_x

        out = f"v{i}"
        parts.append(f"[{last}][{tag}]overlay=x='{x}':y='{y}':"
                     f"enable='between(t,{s:.2f},{e:.2f})':format=auto[{out}]")
        last = out
    return ";".join(parts), last


def render(source, out, cues, width, height, fps, duration, bitrate="20M"):
    cmd = [ffmpeg_bin(), "-y", "-i", str(source)]
    for c in cues:
        # Each overlay is looped across the full timeline. A still PNG is a
        # single frame at PTS 0, so a fade with st>0 never reaches its start
        # on that input's own clock and the frame stays fully transparent -
        # the overlay silently never appears. Looping gives it real
        # timestamps that line up with the main video.
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{duration:.3f}",
                "-i", c["path"]]

    graph, last = filter_graph(cues, width, height)
    cmd += ["-filter_complex", graph, "-map", f"[{last}]"]
    cmd += ["-map", "0:a?", "-c:a", "aac", "-b:a", "320k"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-b:v", bitrate,
            "-maxrate", bitrate, "-bufsize", "40M", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-movflags", "+faststart", str(out)]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stderr[-3000:])
        sys.exit(f"\nffmpeg failed ({res.returncode})")
    return out


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Burn the Formula Dynamics overlay set into a video.")
    ap.add_argument("source", help="input video")
    ap.add_argument("-t", "--template", default="reveal", choices=TEMPLATES,
                    help="which shot formula this clip is")
    ap.add_argument("-o", "--output", help="output file")
    ap.add_argument("--tone", choices=["dark", "light"], default="dark",
                    help="dark = white graphics for dark footage (default)")
    ap.add_argument("--bug", default="top-left",
                    choices=["top-left", "top-center", "top-right", "bottom-left"])
    ap.add_argument("--cta-style", choices=["bar", "panel"], default="bar",
                    help="panel reads better over red cars")
    ap.add_argument("--title"), ap.add_argument("--service")
    ap.add_argument("--badge"), ap.add_argument("--cta")
    ap.add_argument("--partner", help="use a partner plate as the lower third")
    ap.add_argument("--title-text", metavar="'LINE1|LINE2'",
                    help="custom two-line title, e.g. 'GT3 RS|BUILD'")
    ap.add_argument("--spec", action="append", default=[], metavar="TEXT",
                    help="spec chip, repeatable: --spec 'STAGE 2 TUNE'")
    ap.add_argument("--spec-scale", type=float, default=1.3,
                    help="size multiplier for spec chips (default 1.3 - the "
                         "stock chip is sized for a static poster, not a phone)")
    ap.add_argument("--title-scrim", action="store_true",
                    help="soft band behind the title; use on fast-cut footage "
                         "where the background changes under it")
    for slot in ("title", "badge", "bug", "endcard"):
        ap.add_argument(f"--{slot}-tone", choices=["dark", "light"],
                        help=f"override tone for the {slot}")
    ap.add_argument("--none", action="append", default=[], metavar="LAYER",
                    help="drop a slot, e.g. --none badge")
    ap.add_argument("--bitrate", default="20M")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the cue sheet without rendering")
    a = ap.parse_args()

    src = Path(a.source)
    if not src.exists():
        sys.exit(f"No such file: {src}")

    duration, w, h, fps = probe(src)
    canvas = canvas_for(w, h)

    cfg = dict(TEMPLATES[a.template])
    for slot in ("title", "service", "badge", "cta"):
        if getattr(a, slot):
            cfg[slot] = getattr(a, slot)
    for slot in a.none:
        cfg[slot] = None

    for slot in ("title", "badge", "bug", "endcard"):
        cfg[f"{slot}_tone"] = getattr(a, f"{slot}_tone")
    if a.partner:
        cfg["partner"] = a.partner

    # Custom title and spec chips are rendered on demand from the same
    # builders the kit uses, so they stay on-brand without being baked in.
    tmp = Path(tempfile.mkdtemp(prefix="fd-edit-"))
    if a.title_scrim:
        import build_overlays as BO
        cfg["title_scrim"] = tmp / "title-scrim.png"
        BO.title_scrim(canvas).save(cfg["title_scrim"])
    if a.title_text:
        import build_overlays as BO
        l1, _, l2 = a.title_text.partition("|")
        card = BO.title_card(canvas, l1.strip(), (l2 or "").strip(),
                             cfg.get("title_tone") or a.tone)
        cfg["title_custom"] = tmp / "title-custom.png"
        card.save(cfg["title_custom"])
    if a.spec:
        import build_overlays as BO
        cfg["specs"] = []
        for i, text in enumerate(a.spec):
            chip = BO.badge(text, cfg.get("badge_tone") or a.tone)
            if a.spec_scale != 1.0:
                chip = chip.resize(
                    (round(chip.width * a.spec_scale),
                     round(chip.height * a.spec_scale)), Image.LANCZOS)
            path = tmp / f"spec-{i}.png"
            chip.save(path)
            cfg["specs"].append((text, path))

    groups = {slug: g for slug, _, _, g in B.CTA_CAPTIONS}
    cfg["cta_group"] = groups.get(cfg.get("cta"), "booking")
    cfg["cta_style"] = a.cta_style

    cues = plan(duration, canvas, a.tone, cfg, a.bug)

    print(f"\n  {a.template.upper()}  ·  {TEMPLATES[a.template]['about']}")
    print(f"  Source: {w}x{h} @ {fps}fps  ->  canvas {canvas}")
    print(cue_sheet(cues, duration, src))

    if a.dry_run:
        return

    out = Path(a.output) if a.output else src.with_name(src.stem + "_FD.mp4")
    print(f"  Rendering -> {out} ...")
    render(src, out, cues, w, h, fps, duration, a.bitrate)
    mb = out.stat().st_size / 1_048_576
    print(f"  Done. {out}  ({mb:.1f} MB)\n")


if __name__ == "__main__":
    main()
