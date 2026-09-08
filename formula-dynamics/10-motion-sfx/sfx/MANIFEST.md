# SFX manifest

Synthesised from scratch by `99-toolkit/build_sfx.py`. Nothing is
sampled from any reference - only the timing and brightness were
measured. 48 kHz mono WAV, peak-normalised to -1 dBFS.

| File | Length | Use |
|---|---|---|
| `key-click-1.wav` | 0.07 s | Typewriter / caption keystroke. Lay at 0.08 s spacing for a run. |
| `key-click-2.wav` | 0.07 s | Typewriter / caption keystroke. Lay at 0.08 s spacing for a run. |
| `key-click-3.wav` | 0.07 s | Typewriter / caption keystroke. Lay at 0.08 s spacing for a run. |
| `ui-tick-1.wav` | 0.13 s | A chip, callout or lower third landing. One per element. |
| `ui-tick-2.wav` | 0.13 s | A chip, callout or lower third landing. One per element. |
| `ui-tick-3.wav` | 0.13 s | A chip, callout or lower third landing. One per element. |
| `ui-tick-soft.wav` | 0.17 s | Quieter tick for secondary elements, so a dense run still has shape. |
| `riser-short.wav` | 0.38 s | Half-second lead-in to a callout. |
| `riser-long.wav` | 0.95 s | Lead-in to a title or end card. |
| `whoosh-in.wav` | 0.40 s | Element sliding in from off frame. |
| `whoosh-out.wav` | 0.30 s | Element leaving frame. |
| `impact-hard.wav` | 0.55 s | Section change. The biggest hit in a cut. |
| `impact-soft.wav` | 0.34 s | Smaller punctuation between beats. |
| `impact-tight.wav` | 0.22 s | Fast cut on a beat. |
| `sub-thump.wav` | 0.55 s | Weight under a title reveal. |
| `sub-drop.wav` | 0.85 s | Under the end card. |
| `scramble.wav` | 0.26 s | Under a scramble/resolve text effect. Loop or trim to the reveal. |

`_audition-all.wav` plays every sound in order, 0.45 s apart.
