# Auto-Edit — burning the overlays into a clip

`99-toolkit/build_edit.py` takes a cut clip and renders a finished, on-brand
video: title card, logo bug, service plate, feature badge, one CTA, end card —
timed, animated and positioned automatically.

**It does not cut your footage.** Feed it a clip you've already edited to
length. It adds the graphics layer, which is the repetitive part.

---

## Use

```bash
cd 99-toolkit
pip install imageio-ffmpeg           # only if ffmpeg isn't already installed

# See the timing without rendering anything
python3 build_edit.py clip.mp4 --template reveal --dry-run

# Render it
python3 build_edit.py clip.mp4 --template reveal -o finished.mp4
```

Aspect ratio and frame rate are read from your clip and matched automatically.

---

## Templates

One per shot formula in `SHOT-LISTS.md`. Each picks the title, service plate,
badge and CTA that suit that kind of video.

| `--template` | For | CTA it uses |
|---|---|---|
| `reveal` | Body kits / aero | BOOK YOUR BUILD |
| `sound-check` | Exhaust | DM FOR PRICING |
| `fitment` | Wheels | SEE WHAT FITS YOUR CAR |
| `dyno` | Tuning | BOOK NOW |
| `before-after` | Any service | WHAT WOULD YOU FIT NEXT? |
| `install-day` | Timelapse | NOW BOOKING |
| `service` | Maintenance | WE SERVICE WHAT WE BUILD |

---

## Options

| Flag | Does |
|---|---|
| `--tone light` | Black graphics, for bright footage (default is `dark`) |
| `--cta-style panel` | Black CTA panel instead of the red bar — **use on red cars** |
| `--bug top-right` | Move the logo bug |
| `--cta get-a-quote` | Swap any single element |
| `--title` `--service` `--badge` | Same, for the other slots |
| `--none badge` | Drop a slot entirely (repeatable) |
| `--bitrate 25M` | Override the 20 Mbps default |

```bash
# Red Ferrari, exhaust clip, quote CTA instead of the default
python3 build_edit.py ferrari.mp4 -t sound-check --cta-style panel --cta get-a-quote
```

---

## How the timing is decided

Beats are proportional to clip length with absolute limits, so a 15-second clip
and a 45-second clip both come out paced correctly.

| Element | Timing | Why |
|---|---|---|
| Title card | In at 0.4 s, ~2.5 s long | The hook. Fixed length — a hook is a hook at any duration. |
| Logo bug | 0.6 s → end card | Off before the end card, which already carries the logo. |
| Lower third | ~14% in, ~4 s | Names the service while they're still watching. |
| Badge | ~46% in, ~3 s | The payoff shot. |
| CTA | Ends 1 s before the end card | **On the payoff, not the last frame** — most viewers leave before the end. |
| End card | Last 2–3 s, hard cut | It's the closing shot, not a graphic. |

**The gap between the CTA and the end card is deliberate.** Two asks on screen
at once is zero asks. If a clip is too short to fit both cleanly, the CTA is
dropped automatically rather than crowded in.

Animation: fades throughout, a short slide-in on the lower third, and a hard
cut for the end card.

---

## Notes

- Rendering is roughly 4× realtime — a 20-second clip takes about 90 seconds.
  Every overlay is a full-frame layer, which is what makes placement exact.
- Output is H.264, 20 Mbps, `+faststart`, audio passed through as 320k AAC —
  matching `EXPORT-SPECS.md`.
- Prefer CapCut? Use `--dry-run` and read the cue sheet as your build order.
  The timings transfer directly.
