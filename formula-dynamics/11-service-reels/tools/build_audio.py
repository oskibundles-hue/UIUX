#!/usr/bin/env python3
"""Build a sound-design bed for each reel from the existing FD SFX pack and
mux it into the rendered MP4.

Cues are placed against the same beat times the scenes animate to, so the
audio lands exactly on the motion. Music is deliberately NOT added — drop a
licensed bed under this in Ads Manager or your editor.

Output is limited to -1.5 dBTP, matching the earlier deliveries.
"""
import json
import os
import subprocess
import sys

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:  # cloud sessions: the system ffmpeg
    FF = "/usr/bin/ffmpeg"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SFX = os.path.join(ROOT, "sfx-fd")
REELS = os.path.join(ROOT, "renders")

# (sound, time, gain)
CUES = {
    "FD-R1-Exhaust-Larini": [
        ("riser_tone",     0.20, 0.38),   # tach sweeps up
        ("riser_air",      0.55, 0.34),
        ("k_impact_plate",   1.36, 0.66),   # redline hit + red flash
        ("whoosh_short",   3.72, 0.50),
        ("k_impact_metal",       4.62, 0.60),   # distributor badge
        ("k_click_tight",  5.15, 0.38), ("k_click_tight", 5.45, 0.38),
        ("k_click_tight",  5.75, 0.38),
        ("whoosh_short",   8.55, 0.50),
        ("k_select",  9.00, 0.35),
        ("fd_engine_low",  8.95, 0.20),   # valve CLOSED — our own engine, held back
        ("sub_drop",      10.25, 0.50),   # the valve opens — the big moment
        ("fd_engine_peak",10.18, 0.62),   # ...carried by the real exhaust
        ("k_impact_sub",  10.25, 0.30),
        ("whoosh_reverse",11.85, 0.45),
        ("impact_low",    12.22, 0.70), ("drone_low", 12.10, 0.20),   # end card
        ("pop",           12.92, 0.50),   # CTA
    ],
    "FD-R2-Tuning": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("swish_fine",          4.28, 0.45),   # factory curve draws
        ("swish_fine",          5.08, 0.50),   # FD curve draws
        ("sub_drop",       6.08, 0.58),   # the gain area fills
        ("whoosh_short",   9.18, 0.50),
        ("k_click_tight",  9.65, 0.38), ("k_click_tight", 9.95, 0.38),
        ("k_click_tight", 10.25, 0.38),
        ("whoosh_reverse",12.05, 0.45),
        ("impact_low",    12.42, 0.70), ("drone_low", 12.30, 0.20),
        ("pop",           13.12, 0.50),
    ],
    "FD-R3-PPF": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("k_select",  4.22, 0.40), ("k_select", 4.56, 0.40),
        ("k_select",  4.90, 0.40), ("k_select", 5.24, 0.40),
        ("k_impact_metal",       6.26, 0.70),  # the scratch lands
        ("riser_tone",     7.00, 0.45),  # healing
        ("shimmer",        7.95, 0.42),  # healed
        ("k_glass",        8.10, 0.40),
        ("whoosh_short",   9.38, 0.50),
        ("k_click_tight",  9.85, 0.38), ("k_click_tight", 10.15, 0.38),
        ("k_click_tight", 10.45, 0.38),
        ("whoosh_reverse",12.05, 0.45),
        ("impact_low",    12.42, 0.70), ("drone_low", 12.30, 0.20),
        ("pop",           13.12, 0.50),
    ],
    "FD-R4-Builds": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("k_switch_heavy",        4.08, 0.55),  # the build sheet lands
        ("k_select",  4.68, 0.40), ("k_select", 5.00, 0.40),
        ("k_select",  5.32, 0.40), ("k_select", 5.64, 0.40),
        ("k_select",  5.96, 0.40),
        ("ding",           6.70, 0.55),  # the tick
        ("whoosh_short",   9.18, 0.50),
        ("k_click_tight", 10.18, 0.38), ("k_click_tight", 10.44, 0.38),
        ("k_click_tight", 10.70, 0.38),
        ("whoosh_reverse",12.05, 0.45),
        ("impact_low",    12.42, 0.70), ("drone_low", 12.30, 0.20),
        ("pop",           13.12, 0.50),
    ],
    "FD-R5-20-Years": [
        ("riser_stutter",  0.30, 0.42),  # under the count-up
        ("k_tick_metal",           0.70, 0.30), ("k_tick_metal", 0.95, 0.30),
        ("k_tick_metal",           1.20, 0.30),
        ("impact_low",     1.68, 0.66),  # the "+" lands
        ("whoosh_short",   3.95, 0.50),
        ("impact_deep",    4.45, 0.60),  # #1 MASERATI SPECIALISTS
        ("k_impact_metal",       5.55, 0.60),  # Larini badge
        ("whoosh_short",   8.78, 0.50),
        ("pop",            9.28, 0.42), ("pop", 9.50, 0.42),
        ("pop",            9.72, 0.42), ("pop", 9.94, 0.42),
        ("whoosh_reverse",12.05, 0.45),
        ("impact_low",    12.42, 0.70), ("drone_low", 12.30, 0.20),
        ("pop",           13.12, 0.50),
    ],
    "FD-R6-Wheels-NVForged": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.82, 0.80),
        ("whoosh_short",   3.75, 0.50),
        ("k_impact_metal",       4.68, 0.60),   # NV Forged badge
        ("k_click_tight",  5.22, 0.38), ("k_click_tight", 5.52, 0.38),
        ("k_click_tight",  5.82, 0.38),
        ("whoosh_short",   8.78, 0.50),
        ("impact_deep",    9.62, 0.74),   # the wheel drops into the arch
        ("ratchet",        9.95, 0.30),
        ("k_select", 10.42, 0.40),
        ("whoosh_reverse",12.05, 0.45),
        ("impact_low",    12.42, 0.70), ("drone_low", 12.30, 0.20),
        ("pop",           13.12, 0.50),
    ],
    "FD-R7-Body-Kits": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.82, 0.80),
        ("whoosh_short",   3.65, 0.50),
        ("swish_fine",          4.12, 0.48),   # the weave wipes on
        ("swish_fine",          4.85, 0.36),   # sheen crosses
        ("whoosh_short",   8.78, 0.50),
        ("pop",            9.30, 0.42), ("pop", 9.52, 0.42),
        ("pop",            9.74, 0.42), ("pop", 9.96, 0.42),
        ("chime_low",     10.35, 0.44),
        ("whoosh_reverse",12.05, 0.45),
        ("impact_low",    12.42, 0.70), ("drone_low", 12.30, 0.20),
        ("pop",           13.12, 0.50),
    ],
    "FD-R8-Annual-Package": [
        ("riser_air",      0.22, 0.55),
        ("impact_low",     0.80, 0.80),   # the hook lands
        ("whoosh_short",   3.65, 0.50),   # into the price
        # The count-up is the moment. A tone rises under the ramping number,
        # then the plate hit lands exactly as it settles on 3,999 and the
        # stripe wipes under it.
        ("riser_tone",     4.10, 0.42),
        ("k_impact_plate", 5.35, 0.66),
        ("sub_drop",       5.35, 0.45),
        ("swish_fine",     5.58, 0.40),   # "Six services. One price."
        ("whoosh_short",   7.30, 0.50),   # into the list
        # one tick per row, on the row's own entrance
        ("k_click_tight",  7.85, 0.40), ("k_click_tight", 8.37, 0.40),
        ("k_click_tight",  8.89, 0.40), ("k_click_tight", 9.41, 0.40),
        ("k_select",       9.93, 0.46),   # the 10%-off row is the payoff
        ("whoosh_reverse",12.15, 0.45),
        ("impact_low",    12.52, 0.70), ("drone_low", 12.40, 0.20),
        ("pop",           13.45, 0.50),   # CTA
    ],
}

DURATION = 15.0


# ---- P1 Opus exhaust tips carousel (scenes/p1-opus-carousel.html) ----------
# Slide cuts in the 9:16 video: 0, 3.0, 5.4, 7.8, 10.2 (moving slide), 13.4, 16.2.
# Headlines land ~0.35 s after each cut; the DM box pops ~0.65 s in.
_AIR = [("air_bed", t, 0.16) for t in (0.0, 2.9, 5.8, 8.7, 11.6, 14.5, 17.4)]
_OPUS_VIDEO = _AIR + [
    ("riser_air",       0.00, 0.40),
    ("k_impact_plate",  0.35, 0.62),   # OPUS EXHAUST TIPS lands
    ("pop",             0.68, 0.45),   # DM TO ORDER
    ("whoosh_short",    2.85, 0.50), ("k_click_tight", 3.35, 0.40),   # THE FACETS
    ("whoosh_short",    5.25, 0.50), ("k_click_tight", 5.75, 0.40),   # THE CAGE
    ("whoosh_short",    7.65, 0.50), ("k_click_tight", 8.15, 0.40),   # THE SPLIT
    ("whoosh_pass",     9.95, 0.50),
    ("fd_engine_peak", 10.30, 0.50),   # the moving slide: our own engine
    ("sub_drop",       10.50, 0.55),   # SHARP
    ("whoosh_short",   13.25, 0.50), ("k_impact_metal", 13.75, 0.50),  # NOT FOR YOUR CAR?
    ("whoosh_reverse", 15.85, 0.45),
    ("impact_low",     16.30, 0.70), ("drone_low", 16.20, 0.20),        # end card
    ("pop",            16.88, 0.50),   # DM TO ORDER
]
_OPUS_MOVING = [("air_bed", 0.0, 0.16), ("air_bed", 2.9, 0.16),
    ("fd_engine_peak", 0.10, 0.50), ("sub_drop", 0.30, 0.55), ("k_click_tight", 0.70, 0.40)]
for _c in ("Tan", "Black"):
    CUES[f"Opus-{_c}-08-video-9x16"] = _OPUS_VIDEO
    CUES[f"Opus-{_c}-05-moving"] = _OPUS_MOVING

# Per-stem length (the R reels are all 15 s) and loudness target. The Opus
# cuts are normalised to the -14 LUFS the Brembo carousel video went out at.
DURATIONS = {f"Opus-{c}-{k}": d for c in ("Tan", "Black")
             for k, d in (("08-video-9x16", 19.4), ("05-moving", 3.2))}
LUFS = {k: -14.0 for k in DURATIONS}


def _loudness(path):
    r = subprocess.run([FF, "-nostats", "-i", path, "-map", "0:a", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary"):]
    i = float(tail.split("I:")[1].split("LUFS")[0])
    tp = float(tail.split("Peak:")[1].split("dBFS")[0])
    return i, tp


def build(stem, video=None, out=None):
    """Mux the stem's cue bed into `video` (default renders/<stem>.mp4)."""
    video = video or os.path.join(REELS, stem + ".mp4")
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
        + f"apad,atrim=0:{DURATIONS.get(stem, DURATION)},asetpts=N/SR/TB[aout]"
    )
    out = out or os.path.join(REELS, stem + "-SFX.mp4")
    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return f"FAIL {stem}: {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}"
    level = ""
    if stem in LUFS:
        # Two-pass loudnorm: measure, then normalise to the target with its
        # true-peak limiter (4x oversampled), set 1.3 dB under the -1.5 dBTP ceiling because the AAC encode adds
        # overs back (measured on the Opus cuts).
        src = out + ".mix.mp4"
        os.replace(out, src)
        norm = f"loudnorm=I={LUFS[stem]}:TP=-2.8:LRA=11"
        r = subprocess.run([FF, "-nostats", "-i", src, "-map", "0:a", "-af", norm + ":print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True)
        m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
        norm += (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
                 f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        r = subprocess.run([FF, "-y", "-i", src, "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                            "-af", norm + ",aresample=48000",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                            "-movflags", "+faststart", out], capture_output=True, text=True)
        if r.returncode != 0:
            return f"FAIL {stem} loudness pass"
        os.remove(src)
        i, tp = _loudness(out)
        level = f", {i:.1f} LUFS, {tp:.1f} dBTP"
    mb = os.path.getsize(out) / 1048576
    return f"ok   {os.path.basename(out)}  ({mb:.1f} MB, {len(cues)} cues{level})"


if __name__ == "__main__":
    # stem            -> renders/<stem>.mp4 into renders/<stem>-SFX.mp4
    # stem:in.mp4:out.mp4 -> any picture master into any output path
    targets = sys.argv[1:] or [k for k in CUES if not k.startswith("Opus-")]
    for arg in targets:
        stem, *paths = arg.split(":")
        print(build(stem, *paths))
