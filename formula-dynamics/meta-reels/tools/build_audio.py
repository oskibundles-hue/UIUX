#!/usr/bin/env python3
"""Build a sound-design bed for each reel from the existing FD SFX pack and
mux it into the rendered MP4.

Cues are placed against the same beat times the scenes animate to, so the
audio lands exactly on the motion. Music is deliberately NOT added — drop a
licensed bed under this in Ads Manager or your editor.

Output is limited to -1.5 dBTP, matching the earlier deliveries.
"""
import os
import subprocess
import sys

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SFX = os.path.join(HERE, "assets", "sfx", "sfx")
REELS = os.path.join(HERE, "out", "reels")

# (sound, time, gain)
CUES = {
    "FD-R1-Exhaust-Larini": [
        ("riser_air",      0.20, 0.55),   # tach sweeps up
        ("impact_low",     1.36, 0.85),   # redline hit + red flash
        ("whoosh_short",   3.72, 0.50),
        ("hit_snap",       4.62, 0.60),   # distributor badge
        ("ui_click_hard",  5.15, 0.38), ("ui_click_hard", 5.45, 0.38),
        ("ui_click_hard",  5.75, 0.38),
        ("whoosh_short",   8.55, 0.50),
        ("ui_click_soft",  9.00, 0.35),
        ("impact_deep",   10.25, 0.95),   # the valve opens — the big moment
        ("reverse_whoosh",11.85, 0.45),
        ("impact_low",    12.22, 0.70),   # end card
        ("pop",           12.92, 0.50),   # CTA
    ],
    "FD-R2-Tuning": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("swish",          4.28, 0.45),   # factory curve draws
        ("swish",          5.08, 0.50),   # FD curve draws
        ("impact_deep",    6.08, 0.80),   # the gain area fills
        ("whoosh_short",   9.18, 0.50),
        ("ui_click_hard",  9.65, 0.38), ("ui_click_hard", 9.95, 0.38),
        ("ui_click_hard", 10.25, 0.38),
        ("reverse_whoosh",12.05, 0.45),
        ("impact_low",    12.42, 0.70),
        ("pop",           13.12, 0.50),
    ],
    "FD-R3-PPF": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("ui_click_soft",  4.22, 0.40), ("ui_click_soft", 4.56, 0.40),
        ("ui_click_soft",  4.90, 0.40), ("ui_click_soft", 5.24, 0.40),
        ("hit_snap",       6.26, 0.70),  # the scratch lands
        ("riser_tone",     7.00, 0.45),  # healing
        ("ding",           8.05, 0.55),  # healed
        ("whoosh_short",   9.38, 0.50),
        ("ui_click_hard",  9.85, 0.38), ("ui_click_hard", 10.15, 0.38),
        ("ui_click_hard", 10.45, 0.38),
        ("reverse_whoosh",12.05, 0.45),
        ("impact_low",    12.42, 0.70),
        ("pop",           13.12, 0.50),
    ],
    "FD-R4-Builds": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("shutter",        4.08, 0.55),  # the build sheet lands
        ("ui_click_soft",  4.68, 0.40), ("ui_click_soft", 5.00, 0.40),
        ("ui_click_soft",  5.32, 0.40), ("ui_click_soft", 5.64, 0.40),
        ("ui_click_soft",  5.96, 0.40),
        ("ding",           6.70, 0.60),  # the tick
        ("whoosh_short",   9.18, 0.50),
        ("ui_click_hard", 10.18, 0.38), ("ui_click_hard", 10.44, 0.38),
        ("ui_click_hard", 10.70, 0.38),
        ("reverse_whoosh",12.05, 0.45),
        ("impact_low",    12.42, 0.70),
        ("pop",           13.12, 0.50),
    ],
    "FD-R5-20-Years": [
        ("riser_tone",     0.30, 0.40),  # under the count-up
        ("tick",           0.70, 0.30), ("tick", 0.95, 0.30),
        ("tick",           1.20, 0.30),
        ("impact_low",     1.68, 0.66),  # the "+" lands
        ("whoosh_short",   3.95, 0.50),
        ("impact_deep",    4.45, 0.62),  # #1 MASERATI SPECIALISTS
        ("hit_snap",       5.55, 0.60),  # Larini badge
        ("whoosh_short",   8.78, 0.50),
        ("pop",            9.28, 0.42), ("pop", 9.50, 0.42),
        ("pop",            9.72, 0.42), ("pop", 9.94, 0.42),
        ("reverse_whoosh",12.05, 0.45),
        ("impact_low",    12.42, 0.70),
        ("pop",           13.12, 0.50),
    ],
    "FD-R6-Wheels-NVForged": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.82, 0.80),
        ("whoosh_short",   3.75, 0.50),
        ("hit_snap",       4.68, 0.60),   # NV Forged badge
        ("ui_click_hard",  5.22, 0.38), ("ui_click_hard", 5.52, 0.38),
        ("ui_click_hard",  5.82, 0.38),
        ("whoosh_short",   8.78, 0.50),
        ("impact_deep",    9.62, 0.72),   # the wheel drops into the arch
        ("ui_click_soft", 10.42, 0.40),
        ("reverse_whoosh",12.05, 0.45),
        ("impact_low",    12.42, 0.70),
        ("pop",           13.12, 0.50),
    ],
    "FD-R7-Body-Kits": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.82, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("swish",          4.12, 0.48),   # the weave wipes on
        ("swish",          4.85, 0.36),   # sheen crosses
        ("whoosh_short",   8.78, 0.50),
        ("pop",            9.30, 0.42), ("pop", 9.52, 0.42),
        ("pop",            9.74, 0.42), ("pop", 9.96, 0.42),
        ("ding",          10.35, 0.50),
        ("reverse_whoosh",12.05, 0.45),
        ("impact_low",    12.42, 0.70),
        ("pop",           13.12, 0.50),
    ],
}

DURATION = 15.0


def build(stem):
    video = os.path.join(REELS, stem + ".mp4")
    if not os.path.exists(video):
        return f"skip {stem} (no video yet)"
    cues = CUES[stem]

    cmd = [FF, "-y", "-i", video]
    for name, _, _ in cues:
        cmd += ["-i", os.path.join(SFX, name + ".wav")]

    parts, labels = [], []
    for i, (_, t, g) in enumerate(cues, start=1):
        lab = f"a{i}"
        parts.append(f"[{i}:a]adelay={int(t*1000)}:all=1,volume={g}[{lab}]")
        labels.append(f"[{lab}]")
    parts.append(
        "".join(labels)
        + f"amix=inputs={len(cues)}:normalize=0:dropout_transition=0[mx];"
        + f"[mx]alimiter=limit=0.84:level=disabled,"
        + f"apad,atrim=0:{DURATION},asetpts=N/SR/TB[aout]"
    )
    out = os.path.join(REELS, stem + "-SFX.mp4")
    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return f"FAIL {stem}: {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}"
    mb = os.path.getsize(out) / 1048576
    return f"ok   {stem}-SFX.mp4  ({mb:.1f} MB, {len(cues)} cues)"


if __name__ == "__main__":
    targets = sys.argv[1:] or list(CUES)
    for stem in targets:
        print(build(stem))
