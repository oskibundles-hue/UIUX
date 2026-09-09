# Service posters

Static 1080×1920 posters, one per approved service. Frames come from the
approved ads themselves, so a poster and its video read as the same campaign
rather than two things about the same subject.

| File | Service | Source |
|---|---|---|
| `annual.png` | Annual service package, $3,999 | SF90 |
| `fullppf.png` | Full car PPF, ceramic included | Roma |
| `windshield.png` | Windshield PPF $899, headlights free | GT3 RS |
| `freetune.png` | Free ECU tune | Roma |

```bash
python3 build_stills.py            # all four
python3 build_stills.py annual     # one
```

## The layout is the rejected video, in the right medium

This is the detail grid from `13-experimental` — hero picture, a strip of three
detail panes, a vertical section tab, a header bar, a caption on its own plate.

It was **thrown away as a video**: the strip cut the hero in half for the whole
runtime and the eye had nowhere to rest while the picture moved underneath it.

As a **still** that is precisely what you want. A poster is read in one look, so
showing the hero and three supporting details simultaneously is the point rather
than a fight. The components were never wrong — the medium was.

## Rules it inherits

Same as the ads: no model names, the caption sits on ground rather than over
picture, conditions are stated, and the five-segment accent stripe signs off
bottom-right. See `../12-service-ads-footage/COPY-RULES.md`.

Frames are chosen the same way too — read the source at one-second resolution
first. The first pass put a blurred hand in a detail pane and a blurred interior
as a hero, because the timestamps were picked from memory rather than looked at.
