# Studio carousel

Omarie, 13 Oct 2026, on the carousel generator built for the Formula Dynamics x RYFT Ferrari 812 GTS carousel: "this
carousel generator why isnt it on my os". This is that generator, made generic.

It builds a 5-slide 4:5 Instagram carousel (1080x1350 per slide) in the studio look: product parts and subject renders
on a light grey seamless backdrop, with big type behind them. Everything brand-specific (colour, font, words, images,
placements) comes from a JSON spec. This folder holds the code and a sample spec with labelled placeholder images only.
Real photos, renders, client names and words never go in this public repo.

![The sample carousel, slides 1 to 5](preview.png)

## Files

| File | What it is |
|---|---|
| `generate.py` | The generator: `python3 generate.py <spec.json> <out_dir>`. Holds the default layout |
| `qa.py` | The check to run before anything goes to nq-check (below) |
| `sheet.py` | One contact sheet of the slides: `python3 sheet.py out.jpg 1/5=01.png 2/5=02.png ...` |
| `sample/spec.json` | The sample spec. Copy it to start a new carousel |
| `sample/assets/` | Labelled placeholder parts and subjects; `sample/make_placeholders.py` redraws them |
| `preview.png` | The sample, rendered |

Needs Python 3 with numpy, Pillow and scipy (`pip install numpy pillow scipy`).

## The rules

1. **Ask which style first.** This is one look among the approved ones, so ask Omarie before building (CLAUDE.md,
   rule 1). Build it only when he picks it.
2. **Use the images we have.** Cut parts out of the product photos already supplied, and use the subject renders
   already made. Don't generate more unless Omarie asks; his words: "no more generating, use what we have".
3. **Every word is on the allowed list.** Put each word the slides may carry in the spec's `allowed_words`, taken from
   the brief or the client's own copy. `qa.py` fails on anything else. Before delivery the words go through nq-facts,
   then nq-second.
4. **One contact sheet to nq-check.** Make it with `sheet.py` and send that one image, never the slides one by one.
5. **Show it on the post mockup page** (`design-systems/post-mockup/`): the five slides in the Instagram frame beside
   the posting kit.
6. **One brand per carousel**, in that workstream's colour and font. Formula Dynamics is FD red `#FE0F13` with Bebas
   Neue; other workstreams take theirs from their brand spec.

## The design

- **Backdrop.** A light grey seamless studio: bright in the centre, darker at the top and the edges.
- **Cover (slide 1).** A huge vertical word down the left edge, white with a light outline and bleeding off the
  frame. The hero part floats large across the middle, the model name stacks bottom right in the brand colour, and
  the product name sits under it in dark ink.
- **Background type.** Ghost words (outline only) and faint filled words sit behind everything. They may bleed off
  the frame.
- **Headlines.** The brand colour, each with a blurred echo of itself above and to the right.
- **Labels.** Dark ink, widely letter-spaced.
- **Parts.** Product photos cut out with rembg (`isnet-general-use`) and never recoloured. They float with a soft
  floor shadow. One photo of several pieces can be split into its pieces (`"split": true`), largest first.
- **Subjects.** Car or product renders shot on a studio ground, blended into the backdrop by a soft mask. The mask
  comes from each pixel's distance from that row's studio tone, read off the render's own left and right edges.
  It's never a hard cutout, so render edges and reflections stay soft.
- **Slides 4 and 5** are one 2160-wide spread, with the hero view straddling the seam, so the swipe carries it across.

## Making a new one

1. Copy `sample/spec.json` into the scratchpad, with the images beside it. Never put real ones in this repo.
2. Fill in the spec:
   - `brand`: `colour` (hex), `font` (a .ttf path), and optionally `ink` and `ghost`;
   - `words`: the roles the default layout uses: `brand`, `product`, `product_word`, `cover_word`, `model`,
     `subject_name`, `feature_1` to `feature_3`, `closing_1` and `closing_2`;
   - `allowed_words`: every word the slides may show;
   - `parts`: the slots `hero`, `a`, `b`, `c` and `flat1` to `flat3`. Each is a cutout PNG path, or
     `{"file", "split": true, "piece": n, "open": k}` to take piece `n` of a photo with several pieces (`open`
     separates pieces that touch);
   - `subjects`: the slots `side`, `rear`, `front` and `three_quarter`, each a render on its studio ground;
   - `slides`: leave it empty for the default layout. To change one slide, give it its own element list under `"1"`,
     `"2"`, `"3"` or `"spread"`. The other slides keep the default.
3. Run `python3 generate.py spec.json out/`, then `python3 qa.py spec.json out/`.
4. Make the contact sheet and send it to nq-check; then nq-facts and nq-second for the words.
5. Present the slides on the post mockup page.

### Elements

A slide is a list of elements, drawn in order (later on top). Positions are in px on that canvas (the spread is
2160 wide). `anchor` is two letters: `l`/`m`/`r` then `t`/`m`/`b` (default `lt`). Text takes `{role}` words.

| `type` | Fields | Layer |
|---|---|---|
| `soft_fill` | `text`, `px`, `x`, `y`, `anchor`, `alpha`, `colour`, `spacing` | background |
| `ghost` | `text`, `px`, `x`, `y`, `anchor`, `rot`, `width`, `colour`, `spacing` | background |
| `vertical` | `text`, `px`, `x`, `y` (its bottom-left corner), `fill`, `stroke` | background |
| `echo` | `text`, `px`, `x`, `y`, `anchor`, `colour`, `spacing` | foreground |
| `label` | `text`, `px`, `x`, `y`, `anchor`, `colour`, `spacing` | foreground |
| `part` | `ref`, `cx`, `cy`, `w` or `box: [w, h]`, `rot`, `shadow` | |
| `subject` | `ref`, `cx`, `cy`, `w`, `crop` | |

Any text element takes `"bleed": true` to let it run off the frame on purpose.

## Before nq-check

```bash
python3 qa.py spec.json out/       # no arguments renders and checks the sample
```

It renders the spec and fails on any of these:

- a slide that isn't 1080x1350, or a spread that isn't 2160x1350;
- foreground text (headlines and labels) crossing the frame edge, or the seam between slides 4 and 5, unless it has
  `"bleed": true`;
- foreground text whose box sits on a part's opaque pixels for more than 2% of the box. nq-check caught this twice
  on the first carousel;
- a part's alpha box within 30 px of a subject's;
- any word, in any text element, that isn't on `allowed_words`.

Send to nq-check only when it prints `all clear`. The check covers text drawn by the generator, not words inside
the photos.

## Where it is used

- **FD x RYFT Ferrari 812 GTS carousel** (13 Oct 2026), the first build.
