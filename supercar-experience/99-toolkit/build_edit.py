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

import sce_brand as B
import fd_sfx
import fd_motion as FM


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


def has_audio(path):
    """True if the clip carries an audio stream."""
    out = subprocess.run([ffmpeg_bin(), "-i", str(path)],
                         capture_output=True, text=True).stderr
    return "Audio:" in out


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
    t_len = cfg.get("title_hold") or min(2.6, max(1.4, duration * 0.16))
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
    # --none bug drops it: on some footage no corner tone survives, and the
    # HUD title block carries the mark instead.
    if cfg.get("bug", "on") is not None:
        add("bug", ov / "corner-logo-bugs" /
            f"bug_{canvas}_{bug_position}_logo-{logo_tone}.png",
            0.6, end_start, "fade-in",
            "Branding. Same position on every video.")

    # 3. Service name plate.
    lt_start = max(t_start + t_len + 0.6, duration * 0.14)
    lt_len = min(4.0, max(2.5, duration * 0.22))
    if cfg.get("title_block"):
        pass          # the HUD title block is the name plate on this look
    elif cfg.get("partner"):
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
    spec_from = max(lt_start + lt_len + 0.5, duration * 0.28)
    spec_to = end_start - cta_len_pre - 1.2
    if specs and spec_to > spec_from + 1.5:
        slot = (spec_to - spec_from) / len(specs)
        # Hold must always be shorter than the slot, or chips overlap and two
        # are on screen at once. On a short clip with several specs the slot
        # gets tight, so the floor is clamped rather than applied blindly.
        hold = min(2.8, max(1.0, slot * 0.8), slot - 0.2)
        full_frame = cfg.get("spec_style", "chip") != "chip"
        place = "full" if full_frame else "centre-0.585"
        anim = "slide" if cfg.get("spec_style") == "index" else "fade"
        for i, (text, path) in enumerate(specs):
            st = spec_from + i * slot
            add(f"spec {i + 1}", path, st, st + hold, anim,
                f"Spec: {text}", place=place)

    # 4c. HUD furniture - persistent title block and ticker. Both clear the
    #     frame before the CTA appears: the CTA occupies the same lower band,
    #     and stacking them would put three things in one place.
    hud_end = None
    if cfg.get("title_block") or cfg.get("ticker"):
        cta_len_h = min(4.0, max(2.5, duration * 0.22))
        hud_end = end_start - cta_len_h - 1.6 if cfg.get("cta") else end_start
        for key, layer, note in (
            ("title_block", "title block",
             "Persistent name plate. Replaces the big title card on this look."),
            ("ticker", "ticker",
             "Bottom strip. Keeps the brand present without another logo."),
        ):
            # Start after the opening hook, not under it - both live in the
            # same frame and would otherwise be on screen together.
            hud_start = 1.2
            if cfg.get("title_custom") or cfg.get("title"):
                hud_start = max(hud_start, t_start + t_len + 0.4)
            if cfg.get(key):
                add(layer, cfg[key], hud_start, hud_end, "fade", note)

    # 4d. Indexed callouts, each pinned to a feature on a specific shot.
    for c in cfg.get("callouts") or []:
        add(f"callout {c['index']}", c["path"], c["start"], c["end"], "fade",
            f"Points at: {c['label']}")

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


def seq_cue(name, tmp, canvas, fps, start, end, fn, kwargs, note):
    """Render an animated component to a PNG sequence and return its cue."""
    d = Path(tmp) / f"seq-{name}-{start:.2f}".replace(".", "_")
    d.mkdir(parents=True, exist_ok=True)
    frames = max(2, int((end - start) * fps))
    for i in range(frames):
        fn(canvas, i / (frames - 1), **kwargs).save(d / f"{i:04d}.png")
    return dict(layer=name, path=str(d / "%04d.png"), start=round(start, 2),
                end=round(end, 2), anim="seq", note=note, place="full",
                seq=True)


def filter_graph(cues, width, height):
    """Compose the overlay chain. Each cue is one input, faded and gated."""
    parts, last = [], "0:v"
    for i, c in enumerate(cues, start=1):
        tag = f"o{i}"
        s, e = c["start"], c["end"]
        dur = e - s
        f = [f"[{i}:v]format=rgba"]

        if c.get("seq"):
            # A sequence carries its own animation, so it is not faded - it
            # is only shifted onto the timeline. Its input clock starts at
            # zero regardless of where the cue sits.
            f.append(f"setpts=PTS-STARTPTS+{s:.3f}/TB")
            parts.append(",".join(f) + f"[{tag}]")
            out = f"v{i}"
            parts.append(f"[{last}][{tag}]overlay=x=0:y=0:"
                         f"enable='between(t,{s:.2f},{e:.2f})':format=auto[{out}]")
            last = out
            continue

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


def render(source, out, cues, width, height, fps, duration, bitrate="20M",
           bed_wav=None, sfx_gain=1.6):
    cmd = [ffmpeg_bin(), "-y", "-i", str(source)]
    for c in cues:
        if c.get("seq"):
            cmd += ["-framerate", str(fps), "-i", c["path"]]
            continue
        # Each overlay is looped across the full timeline. A still PNG is a
        # single frame at PTS 0, so a fade with st>0 never reaches its start
        # on that input's own clock and the frame stays fully transparent -
        # the overlay silently never appears. Looping gives it real
        # timestamps that line up with the main video.
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{duration:.3f}",
                "-i", c["path"]]

    graph, last = filter_graph(cues, width, height)

    if bed_wav:
        cmd += ["-i", str(bed_wav)]
        bed_idx = len(cues) + 1
        has_src = has_audio(source)
        if has_src:
            # The effects sit UNDER the clip's own sound. Ducking the source
            # was tried and measured worse: the sidechain pulls the engine
            # down, then the summed bus hits the limiter and the effects lose
            # more than the duck gained.
            graph += (f";[0:a]pan=mono|c0=.5*c0+.5*c1[srca]"
                      f";[{bed_idx}:a]volume={sfx_gain}[sfxa]"
                      f";[srca][sfxa]amix=inputs=2:duration=first:normalize=0,"
                      f"alimiter=limit=0.85[aout]")
        else:
            graph += f";[{bed_idx}:a]volume={sfx_gain},alimiter=limit=0.85[aout]"
        cmd += ["-filter_complex", graph, "-map", f"[{last}]", "-map", "[aout]"]
        cmd += ["-c:a", "aac", "-b:a", "320k"]
    else:
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
    ap.add_argument("--spec-style", default="chip",
                    choices=["chip", "rule", "index", "tab"],
                    help="how a service word is set. chip is the bordered box; "
                         "rule, index and tab are full-frame type treatments "
                         "with no container - see fd_spec.py")
    ap.add_argument("--spec-scale", type=float, default=1.3,
                    help="size multiplier for spec chips (default 1.3 - the "
                         "stock chip is sized for a static poster, not a phone)")
    ap.add_argument("--title-block", metavar="'NAME|SUBLINE'",
                    help="persistent HUD name plate, e.g. 'FERRARI ROMA|2024 BUILD'")
    ap.add_argument("--ticker", metavar="'A|B|C'",
                    help="persistent bottom strip, segments split by |")
    ap.add_argument("--callout", action="append", default=[],
                    metavar="'IDX|LABEL|x,y|start|end'",
                    help="indexed leader line pinned to a feature; x,y are "
                         "fractions of the frame. Repeatable.")
    ap.add_argument("--title-hold", type=float, metavar="SECONDS",
                    help="how long the opening hook holds; shorten it to free "
                         "an early shot for a callout")
    ap.add_argument("--title-scrim", action="store_true",
                    help="soft band behind the title; use on fast-cut footage "
                         "where the background changes under it")
    for slot in ("title", "badge", "bug", "endcard"):
        ap.add_argument(f"--{slot}-tone", choices=["dark", "light"],
                        help=f"override tone for the {slot}")
    ap.add_argument("--none", action="append", default=[], metavar="LAYER",
                    help="drop a slot, e.g. --none badge")
    ap.add_argument("--sfx", action="store_true",
                    help="lay the sound-effect pack under the edit, derived "
                         "from this cue sheet - every element that appears "
                         "gets a hit")
    ap.add_argument("--sfx-gain", type=float, default=None,
                    help="level of the effects against the clip's own audio. "
                         "Left off, it is calibrated from the clip's own "
                         "loudness so the effects land at the same lift on "
                         "every clip.")
    ap.add_argument("--sfx-lift", type=float, default=4.0,
                    help="target dB the effects sit over the clip's audio "
                         "(default 4.0)")
    ap.add_argument("--motion", action="store_true",
                    help="animate the opening: a glow burst on the monogram "
                         "and the hook typed on, instead of the still title "
                         "card. Implies --sfx.")
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
    cfg["title_hold"] = a.title_hold
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
        cfg["specs"] = []
        tone = cfg.get("badge_tone") or a.tone
        if a.spec_style == "chip":
            import build_overlays as BO
            for i, text in enumerate(a.spec):
                chip = BO.badge(text, tone)
                if a.spec_scale != 1.0:
                    chip = chip.resize(
                        (round(chip.width * a.spec_scale),
                         round(chip.height * a.spec_scale)), Image.LANCZOS)
                path = tmp / f"spec-{i}.png"
                chip.save(path)
                cfg["specs"].append((text, path))
        else:
            # The type treatments are full-canvas layers: each owns its own
            # position in frame, so they composite at 0,0 and ignore
            # --spec-scale, which only ever meant "make the chip bigger".
            import fd_spec as SP
            for i, text in enumerate(a.spec):
                layer = SP.build(a.spec_style, canvas, text,
                                 n=i + 1, total=len(a.spec), tone=tone)
                path = tmp / f"spec-{i}.png"
                layer.save(path)
                cfg["specs"].append((text, path))
        cfg["spec_style"] = a.spec_style

    if a.title_block or a.ticker or a.callout:
        import fd_hud as HUD
    if a.title_block:
        name, _, sub = a.title_block.partition("|")
        cfg["title_block"] = tmp / "hud-title.png"
        HUD.title_block(canvas, name.strip(), sub.strip() or None).save(
            cfg["title_block"])
    if a.ticker:
        cfg["ticker"] = tmp / "hud-ticker.png"
        HUD.ticker(canvas, [x.strip() for x in a.ticker.split("|") if x.strip()]
                   ).save(cfg["ticker"])
    if a.callout:
        cfg["callouts"] = []
        for i, spec in enumerate(a.callout):
            bits = [x.strip() for x in spec.split("|")]
            if len(bits) < 5:
                sys.exit(f"--callout needs IDX|LABEL|x,y|start|end, got: {spec}")
            idx, label, xy, st, en = bits[:5]
            x, y = (float(v) for v in xy.split(","))
            # Point the label toward the frame centre so it never runs off the
            # edge, and route the elbow away from the lower furniture.
            side = "right" if x < 0.5 else "left"
            drop = -0.16 if y > 0.58 else 0.12
            path = tmp / f"callout-{i}.png"
            HUD.callout(canvas, idx, label, (x, y), side, drop).save(path)
            cfg["callouts"].append(dict(index=idx, label=label, path=path,
                                        start=float(st), end=float(en)))

    groups = {slug: g for slug, _, _, g in B.CTA_CAPTIONS}
    cfg["cta_group"] = groups.get(cfg.get("cta"), "booking")
    cfg["cta_style"] = a.cta_style

    if a.motion:
        a.sfx = True

    cues = plan(duration, canvas, a.tone, cfg, a.bug)
    motion_meta = []

    if a.motion:
        # Replace the still title card with the animated pair. The hook text
        # is whatever the title card would have said.
        l1, _, l2 = (a.title_text or "").partition("|")
        hook = " ".join(x for x in (l1.strip(), l2.strip()) if x) or B.BRAND_NAME
        title_cues = [c for c in cues if c["layer"] in ("title", "title scrim")]
        t_start = min((c["start"] for c in title_cues), default=0.4)
        t_end = max((c["end"] for c in title_cues), default=3.0)
        cues = [c for c in cues if c["layer"] != "title"]

        burst_end = t_start + min(1.5, (t_end - t_start) * 0.55)
        cues.append(seq_cue("glow-burst", tmp, canvas, fps, t_start, burst_end,
                            FM.glow_burst, dict(text=B.BRAND_NAME, y=0.40),
                            "Monogram opens behind a red bloom."))
        cues.append(seq_cue("type-on", tmp, canvas, fps, burst_end + 0.15, t_end,
                            FM.type_on, dict(text=hook, y=0.42),
                            f"Hook typed on: {hook}"))
        motion_meta.append(dict(kind="type-on", text=hook,
                                start=burst_end + 0.15, end=t_end))

        # A spec panel just before the ask - but only if there is a window
        # with nothing else in the lower band. On a HUD cut the title block
        # and ticker already own that band for most of the clip, and the
        # panel would stack on top of them.
        chips = [t for t, _ in cfg.get("specs", [])]
        cta = next((c for c in cues if c["layer"] == "cta"), None)
        if chips and cta:
            busy = [(c["start"], c["end"]) for c in cues
                    if c["layer"].startswith(("title block", "ticker",
                                              "callout", "lower-third",
                                              "endcard"))]
            p_end = cta["start"] - 0.5
            p_start = max(t_end + 0.5, p_end - 2.6)
            clear = all(p_end <= bs or p_start >= be for bs, be in busy)
            name = (a.title_block or "|").partition("|")[0].strip() or hook
            fits = FM.panel_fits(canvas, name, chips)
            if p_end - p_start > 1.4 and clear and fits:
                cues.append(seq_cue(
                    "panel-rise", tmp, canvas, fps, p_start, p_end,
                    FM.panel_rise, dict(title=name, chips=chips, y=0.62),
                    "Spec panel rises, chips land in sequence."))
                motion_meta.append(dict(kind="panel-rise", chips=chips,
                                        start=p_start, end=p_end))
                # The panel IS the spec display - keep the chips as well and
                # the same words appear twice.
                cues = [c for c in cues if not c["layer"].startswith("spec")]
            else:
                why = ("no clear window in the lower band" if not clear
                       else "window too short" if p_end - p_start <= 1.4
                       else f"{len(chips)} chips will not fit one row - "
                            f"keeping the chip rundown")
                print(f"  (no spec panel: {why})")
        cues.sort(key=lambda c: (c["start"], c["layer"]))

    print(f"\n  {a.template.upper()}  ·  {TEMPLATES[a.template]['about']}")
    print(f"  Source: {w}x{h} @ {fps}fps  ->  canvas {canvas}")
    print(cue_sheet(cues, duration, src))

    if a.dry_run:
        return

    bed_wav = None
    if a.sfx:
        bed, rep = fd_sfx.build_bed(cues, duration, motion_meta)
        if rep["missing"]:
            sys.exit(f"  missing sounds: {', '.join(rep['missing'])}\n"
                     f"  run: python3 99-toolkit/build_sfx.py")
        bed_wav = fd_sfx.write_bed(tmp / "sfx-bed.wav", bed)
        if a.sfx_gain is None:
            src_rms = fd_sfx.source_rms(ffmpeg_bin(), src)
            a.sfx_gain = fd_sfx.auto_gain(src_rms, bed, a.sfx_lift)
            print(f"  SFX gain: {a.sfx_gain:.2f} (calibrated for +"
                  f"{a.sfx_lift:.1f} dB over this clip)")
        note = (f"  SFX: {rep['hits']} hits, {rep['density']:.1f}/s"
                + (f" ({rep['dropped']} secondary hits dropped - over the "
                   f"{fd_sfx.DENSITY_CAP}/s cap)" if rep["dropped"] else ""))
        print(note)

    out = Path(a.output) if a.output else src.with_name(src.stem + "_FD.mp4")
    print(f"  Rendering -> {out} ...")
    render(src, out, cues, w, h, fps, duration, a.bitrate, bed_wav, a.sfx_gain)
    mb = out.stat().st_size / 1_048_576
    print(f"  Done. {out}  ({mb:.1f} MB)\n")


if __name__ == "__main__":
    main()
