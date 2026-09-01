# Formula Dynamics Performance — Brand & Video Asset Kit

**Start here.** Everything needed to edit on-brand video lives in this folder,
organised so you can find a file in seconds and drag it straight onto a CapCut
timeline.

---

## The 30-second version

| I need to… | Go to |
|---|---|
| Put the logo on a video | `03-overlays/corner-logo-bugs/` — already positioned, just drag |
| Name a service on screen | `03-overlays/lower-thirds/` |
| Open with a title | `03-overlays/title-cards/` |
| Close with contact info | `03-overlays/end-cards/` |
| Use the logo somewhere else | `02-logos/` |
| Check a colour or font | `01-brand-core/BRAND-SPEC.md` |
| Write a caption | `05-copy-library/` |
| Know how to shoot / edit / export | `06-video-system/` |

Full file-by-file listing: **[`ASSET-INDEX.md`](ASSET-INDEX.md)**

---

## Folder map

```
formula-dynamics/
├── 01-brand-core/        The rules. Colours, type, logo spec, swatches.
├── 02-logos/             Every logo lockup — vector (SVG) + PNG at 3 sizes.
├── 03-overlays/          Drop-on-timeline video graphics. ← the daily driver
├── 04-templates/         Safe-zone guides + the campaign posters for reference.
├── 05-copy-library/      Hooks, captions, hashtags, CTAs, scripts.
├── 06-video-system/      How to shoot, edit, and export. CapCut workflow.
├── 07-fonts/             Bebas Neue (bundled) + notes on the accent face.
└── 99-toolkit/           Scripts that generated everything here.
```

---

## The one rule that saves the most time

**Every full-frame overlay is rendered at the exact pixel size of its canvas.**

A file named `..._9x16.png` is exactly 1080 × 1920. If your CapCut project is
set to 9:16, that overlay drops onto the timeline already in the right place at
100% scale. No resizing, no dragging, no drift between clips — so the logo sits
in *identical* position in every video you ever make.

Pick your canvas first, then only ever use files matching it:

| Suffix | Pixels | Use for |
|---|---|---|
| `9x16` | 1080 × 1920 | TikTok, Reels, Shorts — **your main format** |
| `4x5` | 1080 × 1350 | Instagram feed video |
| `1x1` | 1080 × 1080 | Square feed posts |
| `16x9` | 1920 × 1080 | YouTube, website, landing hero |

---

## What Formula Dynamics does

Upgrades **and** service. Both belong in the content mix.

**Upgrades** — body kits, exhaust, wheels, tuning (current video focus),
plus PPF, ceramic coating, paint correction, detailing, suspension.

**Service** — scheduled maintenance, fluids, brakes, diagnostics. Lower
glamour, high trust. Great for "why us" content.

**Select partners** — NV Forged (wheels), IPE (exhaust), RIFT (exhaust, blow-off
valves), Luring (springs/suspension).
See `05-copy-library/services-and-partners.md`.

---

## Regenerating everything

All assets are generated from code, so the kit stays consistent. Change a
colour, service or contact detail in `99-toolkit/fd_brand.py`, then:

```bash
cd 99-toolkit
pip install Pillow numpy potracer cairosvg
python3 build_all.py
```

Details in `99-toolkit/README.md`.
