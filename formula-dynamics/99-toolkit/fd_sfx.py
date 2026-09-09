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
}

# Layers that make no sound: they are always on screen, or they are scrim.
SILENT = ("bug", "title scrim", "safe")


def _family(layer):
    for key in LAYER_SFX:
        if layer.startswith(key):
            return key
    return None


def hits_for(cues, motion_meta=None):
    """Expand a cue sheet into (time, sound, gain, essential) hits."""
    hits = []
    for c in cues:
        layer = c["layer"]
        if any(layer.startswith(s) for s in SILENT):
            continue
        fam = _family(layer)
        if not fam:
            continue
        for name, off, gain, essential in LAYER_SFX[fam]:
            if off == -1.0:
                # "at the lock" - scramble resolves at 80% of its window.
                at = c["start"] + (c["end"] - c["start"]) * 0.80
            else:
                at = c["start"] + off
            hits.append((max(0.0, at), name, gain, essential))

    # Per-character clicks for a typed line, and per-chip ticks for a panel.
    for meta in (motion_meta or []):
        if meta["kind"] == "type-on":
            n = len(meta["text"])
            step = (meta["end"] - meta["start"]) * 0.85 / max(1, n)
            for i in range(n):
                if meta["text"][i] == " ":
                    continue
                hits.append((meta["start"] + 0.05 + i * step,
                             f"key-click-{1 + i % 3}", 1.0, True))
        elif meta["kind"] == "panel-rise":
            dur = meta["end"] - meta["start"]
            for i in range(len(meta["chips"])):
                hits.append((meta["start"] + (0.35 + i * 0.12) * dur,
                             f"ui-tick-{1 + i % 3}", 0.85, True))
            last = meta["start"] + (0.35 + (len(meta["chips"]) - 1) * 0.12) * dur
            hits.append((last, "impact-soft", 0.55, False))
    return sorted(hits)


def build_bed(cues, duration, motion_meta=None, verbose=True):
    """Mix the hits into one mono track. Returns (samples, report)."""
    hits = hits_for(cues, motion_meta)
    density = len(hits) / max(1e-6, duration)
    dropped = 0
    if density > DENSITY_CAP:
        keep = [h for h in hits if h[3]]
        dropped = len(hits) - len(keep)
        hits = keep
        density = len(hits) / duration

    bed = np.zeros(int(SR * (duration + 1.0)), dtype=np.float32)
    missing = set()
    for at, name, gain, _ in hits:
        p = SFX / f"{name}.wav"
        if not p.exists():
            missing.add(name)
            continue
        with wave.open(str(p)) as w:
            a = np.frombuffer(w.readframes(w.getnframes()),
                              dtype=np.int16).astype(np.float32) / 32768
        i = int(at * SR)
        n = min(len(a), len(bed) - i)
        if n > 0:
            bed[i:i + n] += a[:n] * gain
    peak = np.abs(bed).max()
    if peak > 0.89:
        bed *= 0.89 / peak

    report = {"hits": len(hits), "density": density, "dropped": dropped,
              "missing": sorted(missing)}
    return bed, report


def write_bed(path, bed):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(bed, -1, 1) * 32767).astype(np.int16).tobytes())
    return path
