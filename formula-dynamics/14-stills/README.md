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

## The caption is glass, not a plate

The first pass laid a solid black band across the foot of the poster with a red
rule ruled edge to edge along its top. That is a border, and it was rejected for
the same reason the bordered chip was rejected in the videos: it sits *on* the
picture instead of belonging to it.

It is now the house treatment — `frost()` crops that region of the poster,
blurs it, pulls it down to a set brightness and fades its top edge in. The
photograph carries on behind the words. The only red is a short rule under the
service name, about a third of its width.

**How dark the glass goes is measured, not fixed.** A plate over dark tarmac
needs almost nothing; the same plate over sunlit concrete needs a lot, and one
fixed number is what left the red offer line unreadable on the windshield
poster. The tile is sampled and aimed at `TARGET_GLASS`.

## The hero is a whole car, and it is sharp

Two separate faults put half a blurred car on the first posters:

**Framing.** The hero filled the canvas, but only its top two thirds was ever
visible — the detail strip and the caption covered the rest, so a car sitting in
the middle of the frame got cut in half. The frame is now scaled by just enough
that lifting it by `hero_y` still reaches the bottom edge: full bleed, car in the
visible window, and real photograph behind the caption to frost.

**Choice of frame.** Every source was scanned at 2 fps for edge energy, and the
hero is the sharpest timestamp where the *whole* car is in shot — read off the
frames, never remembered. The numbers in the config are the output of that scan.

## Rules it inherits

Same as the ads: no model names, conditions are stated, no bordered anything,
and the five-segment accent stripe signs off bottom-right. See
`../12-service-ads-footage/COPY-RULES.md`.
