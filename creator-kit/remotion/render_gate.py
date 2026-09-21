#!/usr/bin/env python3
"""Reel Studio render-finish quality gate (item 4) -- the Remotion creator-kit's equivalent of the story
engine's audit.py/rules.py gate: a checklist that runs after every Remotion render and blocks delivery on FAIL.

  G1  every font file the composition can load (src/fonts.ts + src/brand/tokens.ts's `file:` entries) exists on
      disk and is a real TrueType/OTF (checked by file signature, not just that a file with that name exists).
      This is a pre-render, fast-feedback complement to the runtime proof already in fonts.ts/brand/fonts.ts
      (document.fonts.load width/weight-axis measurement, which fails the render itself on a silent fallback --
      see those files' own docstrings). Not a replacement for it.                                        FAIL
  G2  the rendered output is tagged Rec.709 (bt709) and yuv420p, read from the file itself (ffmpeg -i), not
      assumed from the render command.                                                                    FAIL
  G3  every fixed-position text/graphic component (Hook, Captions, EndCard, Chapter) stays inside theme.safe,
      computed from the render props the same way each component computes its own position -- a change to
      theme.ts or a component's own formula that pushes it outside safe is caught here before a render, not
      after Omarie sees it cropped by Instagram's UI.                                                      FAIL
  G4  the ProgressBar component's own formula (frame / (durationInFrames - 1), clamped) guarantees 100% at the
      final frame by construction; checked as a static source-code assertion, not a runtime measurement,
      because the guarantee is in the formula, not any particular render's numbers.                        FAIL
  G5  end-card content fits inside the actual runtime: endCardAt plus a minimum readable hold does not run past
      durationSeconds (a config a caption sync or a length-fallback trim could otherwise silently violate).  FAIL
  G6  captions don't overlap a detected face -- item 5's caption_faces.py output for this props file: FAIL if
      any line is still `unresolved` (a face too large for either caption band, needing a human call) or if
      caption_faces.py was never run for this props file at all (WARN, not FAIL: it's an optional pass, but a
      silent skip should be visible, not invisible).                                              FAIL/WARN

usage: nice -n 19 python3 render_gate.py --props PROPS.json [--video OUTPUT.mp4] [--caption-positions POS.json]
         [--json OUT.json]
exit: 0 PASS (WARNs allowed) | 1 any FAIL | 2 bad input
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
PUBLIC = os.path.join(HERE, "public")
FF = os.path.expanduser("~/.local/vlogtools/bin/ffmpeg")

# theme.ts, kept in sync by hand (small, stable file). See theme.ts itself for the source of truth.
CAPTION_CENTRE_Y = 0.726
CAPTION_FONT_FRAC = 0.03365
HOOK_Y = 0.22
END_CARD_Y = 0.60
CHAPTER_Y = 0.16
SAFE = {"top": 0.135, "bottom": 0.245, "left": 0.067, "right": 0.176}

# TTF: 'true' (Mac), 0x00010000 (Windows/most), 'ttcf' (TrueType collection). OTF (CFF-flavoured): 'OTTO'.
FONT_MAGIC = (b"\x00\x01\x00\x00", b"true", b"ttcf", b"OTTO")


def check_fonts():
    """G1: every `file: "fonts/X.ttf"` reference in fonts.ts / brand/tokens.ts resolves to a real font file."""
    bad, files = [], set()
    for src in (os.path.join(SRC, "fonts.ts"), os.path.join(SRC, "brand", "tokens.ts")):
        if not os.path.exists(src):
            bad.append(f"G1: source file missing: {src}")
            continue
        text = open(src).read()
        for m in re.finditer(r'file:\s*"(fonts/[^"]+\.(?:ttf|otf))"', text):
            files.add(m.group(1))
    if not files:
        bad.append("G1: no font file references found in fonts.ts/brand/tokens.ts (parser out of date, or the "
                   "kit stopped self-hosting fonts -- check by hand)")
    for f in sorted(files):
        p = os.path.join(PUBLIC, f)
        if not os.path.exists(p):
            bad.append(f"G1: referenced font file missing on disk: {f}")
            continue
        with open(p, "rb") as fh:
            head = fh.read(4)
        if head not in FONT_MAGIC:
            bad.append(f"G1: {f} does not look like a real TrueType/OTF file (header {head!r}): "
                      f"a system-font fallback or a corrupt/placeholder file would silently render wrong")
        if os.path.getsize(p) < 1024:
            bad.append(f"G1: {f} is under 1 KB ({os.path.getsize(p)} bytes): almost certainly not a real font")
    return bad, sorted(files)


def check_color(video_path):
    """G2: the rendered file is yuv420p and tagged bt709, read from the file itself."""
    if not video_path:
        return None, "no --video given: G2 skipped"
    if not os.path.exists(video_path):
        return [f"G2: video not found: {video_path}"], None
    if not os.path.exists(FF):
        return [f"G2: ffmpeg not found at {FF}: cannot inspect the render"], None
    r = subprocess.run(["nice", "-n", "19", FF, "-hide_banner", "-i", video_path], capture_output=True, text=True)
    info = r.stderr
    vline = next((ln for ln in info.splitlines() if "Video:" in ln), "")
    bad = []
    if "yuv420p" not in vline:
        bad.append(f"G2: output is not yuv420p (Instagram/most players expect it): {vline.strip() or 'no video stream found'}")
    if "bt709" not in vline and "709" not in vline:
        bad.append(f"G2: output has no bt709/Rec.709 color tag (untagged or another primary can wash out on "
                  f"Instagram's player): {vline.strip()}")
    return bad, vline.strip()


def _clamped(y, half=0.0):
    return SAFE["top"] <= y - half and y + half <= 1 - SAFE["bottom"]


def check_safe_area(props, height_frac_only=True):
    """G3: replicate each fixed-position component's own formula against theme.safe. Horizontal placement
    (left/right margins) is asserted by construction in every component (hardcoded to safe.left/right or a
    fraction of width derived from it) and is not re-derived here; this checks the vertical placements, which
    are the ones that vary per composition (hook/endCard/chapter Y are theme constants, captions move with
    caption_faces.py overrides, callouts carry their own y in the props already)."""
    bad = []
    if props.get("hook") and not _clamped(HOOK_Y):
        bad.append(f"G3: Hook sits at y={HOOK_Y}, outside theme.safe ({SAFE['top']}-{1 - SAFE['bottom']})")
    if props.get("endCard") and not _clamped(END_CARD_Y):
        bad.append(f"G3: EndCard sits at y={END_CARD_Y}, outside theme.safe")
    if props.get("chapters") and not _clamped(CHAPTER_Y):
        bad.append(f"G3: Chapter sits at y={CHAPTER_Y}, outside theme.safe")
    cap_half = CAPTION_FONT_FRAC * 0.72        # Captions.tsx: top = centreY*H - fontSize*0.72 (the block's own top edge)
    if props.get("words") and not (SAFE["top"] <= CAPTION_CENTRE_Y - cap_half):
        bad.append(f"G3: default caption position (y={CAPTION_CENTRE_Y}) top edge sits above theme.safe.top")
    for pos in props.get("captionPositions") or []:
        y = float(pos.get("y", CAPTION_CENTRE_Y))
        if not (SAFE["top"] <= y - cap_half and y + cap_half <= 1 - SAFE["bottom"]):
            bad.append(f"G3: a caption position override (y={y}, {pos.get('start')}-{pos.get('end')}) sits "
                      f"outside theme.safe")
    for c in props.get("callouts") or []:
        y = float(c.get("y", 0))
        if not (SAFE["top"] <= y <= 1 - SAFE["bottom"]):
            bad.append(f"G3: callout '{c.get('label')}' at y={y} sits outside theme.safe")
    return bad


def check_progress_bar():
    """G4: ProgressBar.tsx's own formula guarantees 100% at the final frame -- verified as source text, not a
    runtime measurement, because a render of any one duration can't prove the formula for every duration."""
    p = os.path.join(SRC, "components", "ProgressBar.tsx")
    if not os.path.exists(p):
        return ["G4: components/ProgressBar.tsx not found"]
    text = open(p).read()
    if re.search(r"durationInFrames\s*-\s*1", text) is None:
        return ["G4: ProgressBar.tsx no longer divides by (durationInFrames - 1): the 100%-at-final-frame "
              "guarantee may have been changed or removed -- re-derive this check by hand before trusting it"]
    if "Math.min(1" not in text and "Math.min(1," not in text:
        return ["G4: ProgressBar.tsx no longer clamps to 1 (100%): check by hand"]
    return []


def check_end_card_runtime(props):
    """G5: endCardAt plus a minimum readable hold does not run past the actual duration."""
    if not props.get("endCard"):
        return []
    dur = props.get("durationSeconds")
    at = props.get("endCardAt")
    if dur is None:
        return ["G5: props has an endCard but no durationSeconds: cannot check it fits the runtime"]
    MIN_HOLD = 1.5
    end_at = at if at else max(0.0, float(dur) - 3.0)     # EndCard.tsx default: durationInFrames/fps - 3
    if end_at + MIN_HOLD > float(dur) + 1e-6:
        return [f"G5: end card starts at {end_at:.2f}s but the reel is only {dur:.2f}s long "
              f"(less than {MIN_HOLD}s to read it)"]
    return []


def check_caption_faces(caption_positions_path):
    """G6: item 5's caption_faces.py output for this props file -- FAIL on any unresolved line, WARN if the
    check was never run at all."""
    if not caption_positions_path:
        return [], ["G6: no --caption-positions given: face-aware caption placement was not checked for this "
                    "render (run story/caption_faces.py first if the footage is handheld/chest-mounted)"]
    if not os.path.exists(caption_positions_path):
        return [f"G6: --caption-positions given but file not found: {caption_positions_path}"], []
    doc = json.load(open(caption_positions_path))
    if doc.get("unresolved"):
        return [f"G6: {len(doc['unresolved'])} caption line(s) have a face overlapping BOTH caption bands, "
              f"unresolved by caption_faces.py, needing a human call: "
              + "; ".join(u["words"] for u in doc["unresolved"])], []
    return [], []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--props", required=True, help="the Reel.tsx render-props JSON for this variant")
    ap.add_argument("--video", help="the rendered output file (mp4/mov)")
    ap.add_argument("--caption-positions", help="story/caption_faces.py output for this props file")
    ap.add_argument("--json", help="write the full report here")
    a = ap.parse_args()
    if not os.path.exists(a.props):
        print(f"props not found: {a.props}")
        return 2
    props = json.load(open(a.props))

    checks = []

    def add(rid, level, detail):
        checks.append({"id": rid, "level": level, "detail": detail})

    font_bad, font_files = check_fonts()
    add("G1", "FAIL" if font_bad else "PASS", "; ".join(font_bad) if font_bad else
        f"{len(font_files)} referenced font file(s), all real TrueType/OTF on disk: {', '.join(font_files)}")

    color_bad, vline = check_color(a.video)
    if color_bad is None:
        add("G2", "WARN", vline)
    else:
        add("G2", "FAIL" if color_bad else "PASS", "; ".join(color_bad) if color_bad else vline)

    safe_bad = check_safe_area(props)
    add("G3", "FAIL" if safe_bad else "PASS", "; ".join(safe_bad) if safe_bad else
        "Hook/EndCard/Chapter/Captions/callouts all clamp inside theme.safe")

    pbar_bad = check_progress_bar()
    add("G4", "FAIL" if pbar_bad else "PASS", "; ".join(pbar_bad) if pbar_bad else
        "ProgressBar's frame/(durationInFrames-1) formula guarantees 100% at the final frame")

    ec_bad = check_end_card_runtime(props)
    add("G5", "FAIL" if ec_bad else "PASS", "; ".join(ec_bad) if ec_bad else
        "no end card, or it fits inside the reel's actual runtime")

    cf_bad, cf_warn = check_caption_faces(a.caption_positions)
    if cf_bad:
        add("G6", "FAIL", "; ".join(cf_bad))
    elif cf_warn:
        add("G6", "WARN", "; ".join(cf_warn))
    else:
        add("G6", "PASS", "no caption line has an unresolved face overlap")

    fails = [c for c in checks if c["level"] == "FAIL"]
    warns = [c for c in checks if c["level"] == "WARN"]
    result = "FAIL" if fails else "PASS"
    lines = [f"{c['id']:<4} {c['level']:<4} {c['detail']}" for c in checks]
    lines.append(f"-- render_gate {os.path.basename(a.props)}: {result} ({len(fails)} fail, {len(warns)} warn)")
    print("\n".join(lines))
    doc = {"props": os.path.abspath(a.props), "video": a.video, "result": result,
          "fails": [f"{c['id']}: {c['detail']}" for c in fails], "warns": [f"{c['id']}: {c['detail']}" for c in warns],
          "checks": checks}
    if a.json:
        json.dump(doc, open(a.json, "w"), indent=1)
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
