# Motion graphics & sound effects

Built from the reference screen recording you sent (a motion piece with UI
elements landing on a dense bed of sound effects). Everything here is
original: what was taken from the reference is the **behaviour** — how
elements move, how many sounds per second, how bright they are — measured
off the file, not copied from it.

Nothing from the reference is reproduced. No artwork, no wordmark, no
colour, no audio. Every component is drawn from `fd_brand.py` and set in
Bebas Neue; every sound is synthesised from oscillators and filtered noise
by `99-toolkit/build_sfx.py`.

---

## What was measured

An onset detector over the reference's 21.7 s of audio found **100 hits**,
clustered at roughly **9.5 per second** through its busiest stretch. Sorting
them by spectral centroid and decay gave four families:

| Family | Centroid | Decay | Spacing | What it marks |
|---|---|---|---|---|
| Key click | 6–9 kHz | ~0 | 0.08 s in runs | A character being typed |
| UI tick | 3–5 kHz | 0.3–0.8 | 0.10–0.22 s | An element landing |
| Riser / tail | 6–9 kHz | 2.4–7.6 | one per reveal | A lead-in |
| Impact | 3–5 kHz | 0.35–0.55 | every 1.5–2.5 s | A section change |

Plus a low thump at 60–190 Hz under the biggest reveals.

The single most transferable finding: **one sound per visible event**. The
reference does not play a music bed with occasional accents. Every element
that appears has its own hit, which is why it feels engineered rather than
decorated.

---

## The components

`99-toolkit/fd_motion.py`. Each takes a progress value `p` from 0 to 1 and
returns a full-canvas RGBA frame, so they render to a PNG sequence and
overlay like any other clip.

| Component | What it does | Pair with |
|---|---|---|
| `glow_burst` | Red bloom opens behind the FD monogram, which scales in | `riser-short` → `impact-hard` + `sub-thump` |
| `type_on` | Text typed a character at a time, block cursor in brand red | `key-click-1..3` at the character rate |
| `scramble` | Letters resolve out of random glyphs, left to right | `scramble` under it, `ui-tick` on the lock |
| `panel_rise` | Card slides up, chips land in sequence | `whoosh-in` + `sub-drop`, then a tick per chip |

**Timing is shared, not guessed.** `panel_rise` lands chip *i* at progress
`0.35 + i × 0.12`. Its sound has to be placed at that same fraction of the
cue's duration. The first version of the demo used fixed offsets and every
tick fired about half a second before its chip appeared — it is the easiest
mistake to make here and the hardest to un-see once you notice it.

---

## The sounds

`10-motion-sfx/sfx/` — 17 files, 48 kHz mono WAV, plus `_audition-all.wav`
which plays every one in order. See `sfx/MANIFEST.md` for the full list.

Rebuild with `python3 99-toolkit/build_sfx.py`. The random seed is fixed, so
a rebuild is identical.

### Mixing against engine audio

The demo mixes the effects **under the clip's own sound**, not instead of it.
The first version mapped only the effects bed, which silently dropped the
engine — and whether the effects read against an engine is the whole question
the demo exists to answer.

Measured against the Roma clip's own audio, per cue:

| Cue | Effects over engine |
|---|---|
| Glow burst | +4.0 dB |
| Typing | +3.0 dB |
| Scramble | +2.9 / +2.1 dB |
| Panel rise | +2.1 dB |

At the original `--sfx-gain 0.85` every cue landed at **+0.6 to +0.9 dB** —
present in the file, inaudible to a listener. The default is now 1.6.

**Ducking is off by default, because it measured worse.** Sidechain-compressing
the engine under the effects gave +0.7 dB on the typing where a flat mix gave
+2.7: the duck pulls the engine down, then the summed bus hits the limiter and
the effects lose more than the duck gained. `--duck` is still there for footage
with dialogue, where protecting the voice matters more than the effect level.

### One known difference from the reference

In the reference, the typing run measures **158% of the RMS of its biggest
impact** — the typing is genuinely louder than the impacts. In the demo it
measures **18%**. That gap is not a mixing mistake: a 75 ms transient
normalised to an unclipped peak cannot carry that much energy. The reference
is getting there by layering several clicks per keystroke, or by
compressing the whole bus.

Worth deciding when you watch it: if the typing feels thin against engine
audio, the fix is to double the click layer or compress the effects bus, not
to raise the gain.

---

## The demo

```bash
python3 99-toolkit/build_motion_demo.py CLIP.mov -o demo.mp4
python3 99-toolkit/build_motion_demo.py CLIP.mov --dry-run   # cue sheet only
```

`--dry-run` prints the beat sheet without rendering. The cue list at the top
of that file is meant to be edited — each entry carries its component, its
window, and its sounds with offsets relative to its own start, so moving a
beat moves its audio with it.

The current demo runs 11.3 s over the Roma clip: glow burst, typed hook, two
scrambles, and the spec panel. 39 sound effects, 3.5 per second — deliberately
less dense than the reference's 9.5, because the reference is a silent screen
recording and yours has an engine in it.

---

## Not yet done

These are animated overlays with their own render path. They are **not** wired
into `build_edit.py` yet, so a normal cut does not use them. That is the next
step, and it should happen after you have watched the demo and said which of
the four earn their place.
