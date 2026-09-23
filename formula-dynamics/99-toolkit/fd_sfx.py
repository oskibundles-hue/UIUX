#!/usr/bin/env python3
"""
Formula Dynamics - turn a cue sheet into a sound-effect bed.

build_edit.py already knows exactly when every element is on screen. This
maps each of those layers to a sound, so the effects are derived from the
edit rather than placed by hand against it - move a beat and its sound
moves with it.

Density is adapted per clip rather than fixed. The reference piece ran
about 9.5 hits a second, but it is a silent screen recording; a car video
has an engine under it and the same density turns to mush. If the natural
mapping comes out busier than DENSITY_CAP, the doubling sounds (the sub
and the tight impact that sit under a main hit) are dropped first, because
they are the ones carrying the least information.
"""

import re
import subprocess
import wave

import numpy as np

import fd_brand as B

SR = 48000
SFX = B.KIT / "10-motion-sfx" / "sfx"
DENSITY_CAP = 4.5          # hits per second, averaged over the clip

# (sound, offset from the cue's start, gain, essential)
# Anything not marked essential is dropped first when a cut is too busy.
LAYER_SFX = {
    "title":       [("riser-short", -0.34, 0.65, True),
                    ("impact-hard", 0.00, 1.00, True),
                    ("sub-thump", 0.00, 0.55, False)],
    "lower-third": [("whoosh-in", 0.00, 0.70, True),
                    ("ui-tick-1", 0.14, 0.65, False)],
    "spec":        [("ui-tick-2", 0.00, 0.85, True),
                    ("impact-tight", 0.00, 0.35, False)],
    "callout":     [("ui-tick-3", 0.00, 0.90, True),
                    ("impact-tight", 0.00, 0.30, False)],
    "title block": [("whoosh-in", 0.00, 0.55, True),
                    ("sub-drop", 0.06, 0.45, False)],
    "ticker":      [("ui-tick-soft", 0.00, 0.45, False)],
    "badge":       [("ui-tick-1", 0.00, 0.80, True)],
    "cta":         [("riser-short", -0.30, 0.60, True),
                    ("impact-hard", 0.00, 1.00, True),
                    ("sub-thump", 0.00, 0.55, False)],
    "endcard":     [("impact-soft", 0.00, 0.75, True),
                    ("sub-drop", 0.00, 0.65, True)],
    # Animated components.
    "glow-burst":  [("riser-short", 0.00, 0.60, True),
                    ("impact-hard", 0.38, 1.00, True),
                    ("sub-thump", 0.38, 0.60, False)],
    "scramble":    [("scramble", 0.00, 0.50, True),
                    ("ui-tick-2", -1.0, 0.85, True)],       # -1.0 = at the lock
    "panel-rise":  [("whoosh-in", 0.00, 0.70, True),
                    ("sub-drop", 0.10, 0.55, False)],
    # One tick per word, placed at the swap rather than at the cue start -
    # hits_for handles that below, the same way scramble lands on its lock.
    "swap-in-place": [("ui-tick-2", 0.00, 0.70, True)],
    "scale-pop":   [("impact-tight", 0.00, 0.85, True),
                    ("sub-thump", 0.00, 0.45, False)],
}

# Layers that make no sound: they are always on screen, or they are scrim.
SILENT = ("bug", "title scrim", "safe")

# --------------------------------------------------------------------------
# Variation
#
# LAYER_SFX above is one fixed voicing per layer, so every ad the shop has ever
# cut opens on riser-short into impact-hard and closes the same way. Eleven ads
# that sound identical read as one ad run eleven times.
#
# ALTERNATES gives a layer more than one way to speak. A kit picks between
# them, so the character is chosen rather than rolled: "signature" is exactly
# what the approved ads already use and re-renders them unchanged, and the rest
# are real alternatives built from sounds already in the kit. No new assets.
#
# Pitch does the rest of the work. Seventeen wavs is not much, but a hit
# resampled a couple of semitones is a different hit, so the same kit does not
# repeat itself across a cut.
# --------------------------------------------------------------------------
ALTERNATES = {
    "title": {
        "signature": [("riser-short", -0.34, 0.65, True),
                      ("impact-hard", 0.00, 1.00, True),
                      ("sub-thump", 0.00, 0.55, False)],
        "deep":      [("riser-long", -0.55, 0.50, True),
                      ("impact-hard", 0.00, 0.95, True),
                      ("sub-drop", 0.02, 0.70, False)],
        "tight":     [("whoosh-in", -0.18, 0.60, True),
                      ("impact-tight", 0.00, 1.00, True),
                      ("key-click-1", 0.09, 0.40, False)],
        "minimal":   [("impact-soft", 0.00, 0.80, True)],
    },
    "cta": {
        "signature": [("riser-short", -0.30, 0.60, True),
                      ("impact-hard", 0.00, 1.00, True),
                      ("sub-thump", 0.00, 0.55, False)],
        "deep":      [("riser-long", -0.50, 0.48, True),
                      ("sub-drop", 0.00, 0.80, True),
                      ("impact-soft", 0.02, 0.70, False)],
        "tight":     [("whoosh-in", -0.16, 0.62, True),
                      ("impact-tight", 0.00, 0.95, True)],
        "minimal":   [("impact-soft", 0.00, 0.75, True)],
    },
    "title block": {
        "signature": [("whoosh-in", 0.00, 0.55, True),
                      ("sub-drop", 0.06, 0.45, False)],
        "deep":      [("sub-drop", 0.00, 0.60, True),
                      ("ui-tick-soft", 0.10, 0.35, False)],
        "tight":     [("whoosh-out", 0.00, 0.50, True),
                      ("key-click-2", 0.08, 0.45, False)],
        "minimal":   [("ui-tick-soft", 0.00, 0.50, True)],
    },
    "endcard": {
        "signature": [("impact-soft", 0.00, 0.75, True),
                      ("sub-drop", 0.00, 0.65, True)],
        "deep":      [("sub-drop", 0.00, 0.80, True),
                      ("riser-long", -0.40, 0.35, False)],
        "tight":     [("impact-tight", 0.00, 0.70, True),
                      ("sub-thump", 0.00, 0.55, True)],
        "minimal":   [("impact-soft", 0.00, 0.60, True)],
    },
    "spec": {
        "signature": [("ui-tick-2", 0.00, 0.85, True),
                      ("impact-tight", 0.00, 0.35, False)],
        "deep":      [("ui-tick-soft", 0.00, 0.80, True),
                      ("sub-thump", 0.00, 0.30, False)],
        "tight":     [("key-click-2", 0.00, 0.90, True),
                      ("impact-tight", 0.00, 0.30, False)],
        "minimal":   [("key-click-3", 0.00, 0.70, True)],
    },
    "lower-third": {
        "signature": [("whoosh-in", 0.00, 0.70, True),
                      ("ui-tick-1", 0.14, 0.65, False)],
        "deep":      [("whoosh-in", 0.00, 0.62, True),
                      ("sub-thump", 0.12, 0.40, False)],
        "tight":     [("whoosh-out", 0.00, 0.66, True),
                      ("key-click-1", 0.12, 0.60, False)],
        "minimal":   [("whoosh-in", 0.00, 0.55, True)],
    },
}

# Two more kits, built on the 21 sounds lifted out of the shop's own reference
# clips (rights confirmed 23 Sept). "street" is the TikTok vocabulary the shop
# is actually scrolling past - a hard transition hit and a sub under it.
# "cut" is the dry version: a tick on, a whoosh off, nothing sustained.
ALTERNATES["title"]["street"] = [("tk-whoosh-out-1", -0.42, 0.55, True),
                                 ("tk-impact-hard-1", 0.00, 1.00, True),
                                 ("tk-sub-drop-1", 0.02, 0.70, False)]
ALTERNATES["title"]["cut"] = [("tk-tick-bright-1", -0.10, 0.60, True),
                              ("tk-impact-hard-6", 0.00, 0.95, True)]
ALTERNATES["cta"]["street"] = [("tk-whoosh-out-2", -0.34, 0.58, True),
                               ("tk-impact-hard-2", 0.00, 1.00, True),
                               ("tk-sub-rumble-2", 0.02, 0.60, False)]
ALTERNATES["cta"]["cut"] = [("tk-tick-bright-2", -0.08, 0.60, True),
                            ("tk-impact-hard-4", 0.00, 0.95, True)]
ALTERNATES["title block"]["street"] = [("tk-whoosh-out-3", 0.00, 0.55, True),
                                       ("tk-sub-thump-1", 0.08, 0.45, False)]
ALTERNATES["title block"]["cut"] = [("tk-tick-soft-1", 0.00, 0.55, True)]
ALTERNATES["endcard"]["street"] = [("tk-impact-soft-1", 0.00, 0.75, True),
                                   ("tk-sub-rumble-1", 0.00, 0.60, True)]
ALTERNATES["endcard"]["cut"] = [("tk-impact-hard-5", 0.00, 0.70, True),
                                ("tk-sub-thump-3", 0.00, 0.50, True)]
ALTERNATES["spec"]["street"] = [("tk-tick-bright-2", 0.00, 0.85, True),
                                ("tk-sub-thump-3", 0.00, 0.30, False)]
ALTERNATES["spec"]["cut"] = [("tk-tick-soft-2", 0.00, 0.80, True)]
ALTERNATES["lower-third"]["street"] = [("tk-whoosh-out-3", 0.00, 0.68, True),
                                       ("tk-tick-soft-2", 0.12, 0.55, False)]
ALTERNATES["lower-third"]["cut"] = [("tk-whoosh-out-2", 0.00, 0.60, True)]

KITS = ("signature", "deep", "tight", "minimal", "street", "cut")

# Semitones of resampling jitter per hit, by kit. "signature" is deliberately
# zero so an approved ad re-renders byte-for-byte as before.
KIT_JITTER = {"signature": 0.0, "deep": 1.2, "tight": 1.6, "minimal": 0.8,
              "street": 1.4, "cut": 1.0}


# The typing sound. key-click-1..3 sit at 6.8-7.3 kHz with a 5 ms decay -
# bright and brittle, and the thing the shop heard as "weird". tk-tick-soft-2
# is from the shop's own reference material at 5 kHz and 91 ms, which has the
# attack without the glass.
TYPE_CLICK = "tk-tick-soft-2"


def sound_seconds(name):
    """Length of a kit sound, read off the file rather than assumed."""
    p = SFX / f"{name}.wav"
    if not p.exists():
        return 0.08
    with wave.open(str(p)) as w:
        return w.getnframes() / float(w.getframerate())


def _rng(seed, *parts):
    """A deterministic generator per hit, so a render is repeatable."""
    h = hash((seed, *parts)) & 0xFFFFFFFF
    return np.random.default_rng(h)


def resample_semitones(a, semis):
    """Shift a short hit by resampling. Changes length as well as pitch,
    which is right for percussive material and wrong for anything tonal -
    every sound in this kit is percussive."""
    if abs(semis) < 0.01:
        return a
    ratio = 2.0 ** (semis / 12.0)
    n = max(1, int(len(a) / ratio))
    return np.interp(np.linspace(0, len(a) - 1, n),
                     np.arange(len(a)), a).astype(np.float32)


def _family(layer):
    for key in LAYER_SFX:
        if layer.startswith(key):
            return key
    return None


def voicing_for(fam, kit):
    """The sound list a layer speaks with under this kit.

    Falls back to LAYER_SFX whenever a layer has no alternate written for it,
    so a kit is a partial override rather than a second table to keep in sync.
    """
    if kit != "signature" and fam in ALTERNATES:
        return ALTERNATES[fam].get(kit, LAYER_SFX[fam])
    return LAYER_SFX[fam]


def hits_for(cues, motion_meta=None, kit="signature"):
    """Expand a cue sheet into (time, sound, gain, essential) hits."""
    hits = []
    for c in cues:
        layer = c["layer"]
        if any(layer.startswith(s) for s in SILENT):
            continue
        fam = _family(layer)
        if not fam:
            continue
        for name, off, gain, essential in voicing_for(fam, kit):
            if off == -1.0:
                # "at the lock" - scramble resolves at 80% of its window.
                at = c["start"] + (c["end"] - c["start"]) * 0.80
            else:
                at = c["start"] + off
            hits.append((max(0.0, at), name, gain, essential))

    # Per-character clicks for a typed line, and per-chip ticks for a panel.
    for meta in (motion_meta or []):
        if meta["kind"] == "type-on":
            # One click per character was 23.5 a second on a 25-character hook
            # in a 1.25 s window. key-click is 75 ms long, so consecutive
            # clicks overlapped by 44% and the run read as a buzz rather than
            # as typing - and being marked essential, the density cap could
            # never thin them: 21 of the 33 hits in the cut were this.
            #
            # The stride now comes from the sound's own length instead of a
            # number: clicks are spaced at least 1.4x the sample so they never
            # run into each other. Only the first is essential.
            n = len(meta["text"])
            span = (meta["end"] - meta["start"]) * 0.85
            step = span / max(1, n)
            floor = sound_seconds(TYPE_CLICK) * 1.4
            stride = max(1, int(round(floor / max(1e-6, step))))
            first = True
            for i in range(0, n, stride):
                if meta["text"][i] == " ":
                    continue
                hits.append((meta["start"] + 0.05 + i * step,
                             TYPE_CLICK, 0.85, first))
                first = False
        elif meta["kind"] == "swap-in-place":
            # A hit on each swap, not one at the cue start. The slot holds for
            # 88% of each turn, so the sound marks the change and then gets out
            # of the way - the alternative is a tick under a word that is not
            # moving.
            n = max(1, len(meta["chips"]))
            span = meta["end"] - meta["start"]
            for i in range(n):
                hits.append((meta["start"] + span * i / n,
                             f"ui-tick-{1 + i % 3}", 0.72, i == 0))
        elif meta["kind"] == "panel-rise":
            dur = meta["end"] - meta["start"]
            for i in range(len(meta["chips"])):
                hits.append((meta["start"] + (0.35 + i * 0.12) * dur,
                             f"ui-tick-{1 + i % 3}", 0.85, True))
            last = meta["start"] + (0.35 + (len(meta["chips"]) - 1) * 0.12) * dur
            hits.append((last, "impact-soft", 0.55, False))
    return sorted(hits)


def build_bed(cues, duration, motion_meta=None, verbose=True, cap=None,
              kit="signature", seed=0):
    """Mix the hits into one mono track. Returns (samples, report).

    `cap` overrides DENSITY_CAP for one clip. The default of 4.5 was set
    against 20-30 second cuts and in practice never fires: measured across the
    eleven approved SFX ads the audible onset rate runs 0.64-1.15 per second.
    A short cut carries nearly the same cue count in half the time, so the same
    mapping lands well outside that band while staying under the cap. Rather
    than retune a constant every past render depends on, the caller can hand a
    tighter one down for the clip in front of it.
    """
    hits = hits_for(cues, motion_meta, kit)
    density = len(hits) / max(1e-6, duration)
    dropped = 0
    if density > (DENSITY_CAP if cap is None else cap):
        keep = [h for h in hits if h[3]]
        dropped = len(hits) - len(keep)
        hits = keep
        density = len(hits) / duration

    bed = np.zeros(int(SR * (duration + 1.0)), dtype=np.float32)
    missing = set()
    jitter = KIT_JITTER.get(kit, 0.0)
    for k, (at, name, gain, _) in enumerate(hits):
        p = SFX / f"{name}.wav"
        if not p.exists():
            missing.add(name)
            continue
        with wave.open(str(p)) as w:
            a = np.frombuffer(w.readframes(w.getnframes()),
                              dtype=np.int16).astype(np.float32) / 32768
        if jitter:
            # Per hit, not per sound: the point is that the third ui-tick in a
            # run does not land on the same note as the first.
            r = _rng(seed, kit, name, k)
            a = resample_semitones(a, r.uniform(-jitter, jitter))
            gain = gain * float(r.uniform(0.92, 1.08))
            at = at + float(r.uniform(-0.012, 0.012))
        i = max(0, int(at * SR))
        n = min(len(a), len(bed) - i)
        if n > 0:
            bed[i:i + n] += a[:n] * gain
    peak = np.abs(bed).max()
    if peak > 0.89:
        bed *= 0.89 / peak

    report = {"hits": len(hits), "density": density, "dropped": dropped,
              "cap": DENSITY_CAP if cap is None else cap,
              "kit": kit, "seed": seed,
              "missing": sorted(missing)}
    return bed, report


def source_rms(ffmpeg, path):
    """Linear RMS of a clip's own audio, or None if it has none.

    Read with ffmpeg's volumedetect rather than decoding the whole track.
    """
    out = subprocess.run(
        [ffmpeg, "-i", str(path), "-map", "0:a?", "-af", "volumedetect",
         "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out)
    return 10 ** (float(m.group(1)) / 20) if m else None


def auto_gain(src_rms, bed, target_lift_db=4.0, lo=0.3, hi=4.0):
    """Pick an effects gain from the clip's own loudness.

    A fixed gain does not survive different footage. At 1.6 the same pack
    measured +1.1 dB over the SF90's audio and +14.2 dB over the GT3 RS's -
    inaudible on one clip and jarring on the other - because the clips are
    mastered at different levels. This sets the gain so the effects land at
    roughly the same lift over whatever the clip is doing.
    """
    if not src_rms:
        return 1.0
    active = bed[np.abs(bed) > 0.005]
    if active.size < 100:
        return 1.0
    bed_rms = float(np.sqrt((active ** 2).mean()))
    want = (10 ** (target_lift_db / 10) - 1) ** 0.5      # effects/source ratio
    return float(min(hi, max(lo, want * src_rms / bed_rms)))


def write_bed(path, bed):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(bed, -1, 1) * 32767).astype(np.int16).tobytes())
    return path
