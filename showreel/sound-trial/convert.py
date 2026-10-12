"""Showreel picture cues (showreel/audio/cues.json, written by tools/cues.mjs) -> a sound-layer cue sheet.

Every time comes from the picture's own export; nothing is typed by frame. Each synth R.sfx type maps to a
recorded sound picked with `sfx.py browse`. One family for the reel: air whooshes, a dry sub and thud low
end, clean interface ticks and clicks.

  python3 showreel/sound-trial/convert.py showreel/audio/cues.json <trial dir>/audio/cues.json
"""
import json, math, sys

src = json.load(open(sys.argv[1]))
fps = src["fps"]

# Heroes, one per ~4 s: cold open, the box unfolds, THE DROP, FINAL HIT. hit+boom, with the picture's own
# reverse swell ending on each (except the cold open, which has nothing before it).
HERO = {
    # round 2: fast-rise layers for the cold open (round 1 peaked 1.5 frames late); hits with body above the
    # score's kick for the unfold and the final hit (round 1 lifted their main band only 2.4-2.5 dB)
    0.0:    ("cold-open", "hit/fs-443494-thud2-wav-1+boom/fs-223838-expriements-bass-8-mp3-2", None),
    3.75:   ("unfold",    "hit/fs-57893-dun-wav-1+boom/fs-201748-bass-rugged-sub-2-3", None),
    7.5:    ("drop",      "hit/fs-558238-distorted-impact-short-wav-1+boom/fs-636624-deep-hit-2", "cut"),
    # round 3: a boom with body at 114 Hz, under the braam (round 2 lifted 125-250 Hz by 2.9 dB, needs 3).
    # round 5, "make the final hit hit harder": the unfold's rugged sub added as a third layer. Of six layer sets
    # tried under the braam, it is the one that lifts 125-250 Hz past 3 dB (3.5) without a new FAIL
    13.125: ("final-hit", "hit/fs-592034-braams-hit-1-1+boom/fs-636624-deep-hit-2+boom/fs-201748-bass-rugged-sub-2-3", None),
}
SUPPORT_IMPACT = {1.0: "hit/fs-443494-thud2-wav-1+thump/fs-458877-thump-1"}   # the HEAVY slam
IMPACT = "hit/fs-243375-tire-puncture-pop-hit-punch-1"      # round 2: thud2 was buried at 125-250 Hz
WHOOSH = [(0.30, "whoosh/fs-471097-knife-sword-swing-1"),     # by the picture's requested length; round 2:
          (9.99, "whoosh/fs-449988-whoosh-med-high-1")]       # brighter air, the dark swoshes were masked
REVERSE = [(0.25, "reverse/fs-503805-reverse-fx-7-wav-1"),
           (9.99, "reverse/fs-503803-reverse-fx-13-wav-1")]
SOUND = {
    "swish":   ["swish/fs-395264-sword-movement-single-3-1", "swish/fs-395263-sword-movement-single-4-1"],
    "tick":    ["tick/fs-386202-ratchet-vlc-tighten-4-3", "tick/fs-386203-ratchet-vlc-tighten-1-2"],
    "pop":     ["pop/fs-328117-pop-8-1", "pop/fs-244652-pop-4-1"],
    "blip":    ["ui/kenney-digital-high-down", "ui/kenney-digital-high-up"],
    "click":   ["click/kenney-interface-switch-001", "click/fs-399443-mouse-clicks"],
    "glitch":  ["glitch/fs-262858-blip-1-2"],                 # short row pops; longer bursts below
    "shimmer": ["shimmer/fs-452371-small-bell-2"],
    "riser":   ["riser/fs-531729-energy-riser-3-1"],
    "type":    ["key/fs-348239-mech-keyboard-01-wav-1"],
}
# round 2, per event: the sounds that were still buried in round 1
OVERRIDE = {11.25: "glitch/fs-376700-digital-madness-1", 12.0703125: "glitch/fs-376700-digital-madness-1",
            11.1328125: "pop/fs-347353-squeaky-cork-pull-1", 12.1875: "pop/fs-347353-squeaky-cork-pull-1",
            7.5: "shimmer/fs-462095-sparkling-star-01-wav-2", 8.4375: "shimmer/fs-462095-sparkling-star-01-wav-2",
            13.0078125: "riser/fs-608217-inhale-with-glass-wav-1"}
# Sounds closer than 60 ms (the QA's sync window) blur each other's peaks: keep the one that carries the action.
PRIORITY = ["impact", "pop", "blip", "click", "glitch", "tick", "type", "swish"]
# What the picture does on each sound, from the scene's own comment on the R.sfx call.
LAND = {2.34375, 2.578125, 2.8125, 2.9296875, 5.15625, 11.1328125, 12.1875, 13.59375}
CUT = {9.375, 11.25, 11.484375}
# Round 4: the score's dead stops before the drop (7.27-7.50 s) and the final hit (13.01-13.13 s). The music bed
# is rendered with `synth.py --mute hits`, which keeps the synth's own swells through them. A recorded swell
# ending there was solved against a silent bed (-41 and -46 dB, inaudible), so the score's swell plays instead.
PASSED = {7.5, 13.125}


def near(t, times):
    return next((x for x in times if abs(x - t) < 1e-4), None)


def by_len(table, d):
    return next(s for lim, s in table if d <= lim)


def semis(ratio):
    """The synth's pitch ratio as semitones around the melody's middle (C5 = 1.498), kept within a fifth,
    so the landing pops still climb F-Ab-C-F without pitching a recording by an octave."""
    return max(-7.0, min(7.0, round(12 * math.log2(ratio / 1.498), 2)))


cues, seen, n = [], {}, 0
for ev in src["sounds"]:
    typ, t = ev["type"], ev["t"]
    if typ in ("subdrop", "tapestop"):      # subdrop rides in the hero's boom; the tape-stop is in the score
        continue
    n += 1
    k = seen[typ] = seen.get(typ, -1) + 1
    cid = f"{typ}-{t:.3f}"
    if typ == "impact":
        hero = HERO.get(near(t, HERO))
        if hero:
            # round 3: the cold open starts on frame 0, since nothing plays before the first frame
            c = dict(id=hero[0], t=t, sound=hero[1], weight="hero", align="start" if t == 0 else "peak")
            if hero[2]: c["visual"] = hero[2]
        else:
            c = dict(id=cid, t=t, sound=SUPPORT_IMPACT.get(ev.get("amt"), IMPACT), align="peak", typ=typ)
            if near(t, CUT) is not None: c["visual"] = "cut"
        cues.append(c); continue
    if typ in ("whoosh", "reverse", "riser"):  # end-anchored in the picture: they land at t + dur
        end = t + ev["dur"]
        if typ != "whoosh" and near(end, PASSED) is not None:
            continue
        snd = by_len(WHOOSH, ev["dur"]) if typ == "whoosh" else by_len(REVERSE, ev["dur"]) if typ == "reverse" \
            else SOUND["riser"][0]
        # fix after round 3: OVERRIDE is keyed by time only, so it is for the riser here; a whoosh or reverse that
        # ends on a shimmer's or pop's time was picking up that sound (reverse-7.500 played the sparkling star)
        if typ == "riser": snd = OVERRIDE.get(near(end, OVERRIDE), snd)
        c = dict(id=f"{typ}-{end:.3f}", t=end, sound=snd, align="end")
        if typ == "whoosh":
            c["pan"] = -0.3 if ev.get("dir") == "down" else 0.3
        cues.append(c); continue
    if typ == "type":                       # round 2: one key on the burst's first letter; a key per 50 ms was
        cues.append(dict(id=f"key-{t:.3f}", t=t, sound=SOUND["type"][0], align="peak", typ=typ))   # buried
        continue
    pool = SOUND[typ]
    snd = OVERRIDE.get(near(t, OVERRIDE)) if typ in ("glitch", "pop", "shimmer") else None
    c = dict(id=cid, t=t, sound=snd or pool[k % len(pool)], align="start" if typ == "shimmer" else "peak")
    if ev.get("pitch") and typ in ("pop", "tick", "blip", "glitch"):
        c["pitch"] = semis(ev["pitch"])
    if typ in ("pop", "blip") and near(t, LAND) is not None:
        c["visual"] = "land"
    if typ == "glitch" and near(t, CUT) is not None:
        c["visual"] = "cut"
    c["typ"] = typ
    cues.append(c)

# round 3: support sounds qa.py measured under the score in round 2 (stand out < 1.5 dB in their own band).
# Dropped rather than pushed: the mixer caps them against the bed, and LISTEN.md lists each one.
# reverse-8.438 is back: round 2 measured it playing the wrong file (see the fix above).
QUIET = ['blip-1.875', 'blip-10.078', 'blip-11.016', 'blip-5.156', 'glitch-11.250', 'glitch-11.836', 'glitch-12.070', 'glitch-9.375', 'impact-11.484', 'pop-10.547', 'pop-11.133', 'pop-12.188', 'shimmer-13.828', 'shimmer-8.438', 'swish-11.558', 'swish-5.273', 'tick-10.195', 'tick-13.711', 'tick-4.805', 'tick-4.922', 'tick-5.039', 'tick-9.844', 'tick-9.961', 'whoosh-13.359', 'whoosh-2.344', 'whoosh-5.156']

# Thin clusters: of the support sounds peaking within 60 ms of each other (or of a hero), keep the one that
# carries the action. End-aligned swells and start-aligned shimmers peak elsewhere and stay.
quiet = [c for c in cues if c["id"] in QUIET]
print("measured quiet, dropped:", ", ".join(c["id"] for c in quiet))
cues = [c for c in cues if c not in quiet]
peaks = sorted((c for c in cues if c["align"] == "peak"), key=lambda c: (c["t"], c.get("weight") != "hero"))
dropped = []
for i, c in enumerate(peaks):
    if c.get("weight") == "hero" or c in dropped: continue
    for o in peaks:
        if o is c or o in dropped or abs(o["t"] - c["t"]) > 0.06: continue
        rank = lambda x: -1 if x.get("weight") == "hero" else PRIORITY.index(x["typ"])
        if rank(o) < rank(c) or rank(o) == rank(c) and o["t"] < c["t"]:
            dropped.append(c); break
cues = [c for c in cues if c not in dropped]
for c in cues: c.pop("typ", None)
print("thinned:", ", ".join(f"{c['id']}" for c in dropped))

sheet = {
    "fps": fps, "duration_s": src["duration"], "energy": "punchy", "lufs": -14, "kit": "audio/kit",
    "music": {"file": "audio/music.wav", "start_s": 0, "loop": False, "fade_out_s": 0.1},
    "cues": sorted(cues, key=lambda c: c.get("t", c.get("frame", 0) / fps)),
}
json.dump(sheet, open(sys.argv[2], "w"), indent=1)
print(f"{n} picture events -> {len(sheet['cues'])} cues "
      f"({sum(c.get('weight') == 'hero' for c in cues)} hero, {sum('visual' in c for c in cues)} picture-checked)")
