# Studio carousel: the layout rules

Omarie approved this layout twice on 13 Oct 2026, once on a carousel built from product cutouts and studio renders
and once on a carousel built only from shop photos. Use it for any product or service carousel, in the
workstream's own colour and font. `generate.py` builds it, and `qa.py` checks the rules it can measure.

## The look

- **Backdrop.** A light grey seamless studio, bright in the centre and darker at the top and the edges.
- **Ghost type.** Huge outlined words with a 2 px stroke in light grey, with a faint filled word behind them.
  A word that runs down the side is turned 90°.
- **Headlines.** The brand colour, each with a blurred echo of the same word above and to the right. The echo must
  never touch a photo frame or the canvas edge.
- **Labels.** Small, widely letter-spaced, in ink colour.
- **Parts.** Cut out with rembg (`isnet-general-use`) and floated with a soft floor shadow. Fit each part inside a
  fixed box on a clear grid (`"box": [w, h]`), never by width alone. Sizing by width is what made one early slide
  look uneven.
- **Shop photos.** When a cutout would come out rough (lifts, clutter, people), use a clean framed photo on the
  studio grey instead: the `panel` element.

## The five slides

1. **Hook.** The subject, as a render or a framed photo, with the vertical ghost word up the side and the model
   name as the headline.
2. **The part.** One large clean cutout and a one-line headline.
3. **The detail.** Either the parts in tidy boxes, or a 2x2 grid of numbered steps ("01", "02" and so on, each with
   two or three words): the `steps` element.
4. **The subject, or a spread.** In the cutout build, slides 4 and 5 are one 2160 px spread split at the seam. In
   the photo build, slide 4 is one large framed photo. Don't repeat slide 1's headline here.
5. **Call to action.** One line that asks a question, one line that says how to book, then the name and the
   handle. Keep any cutout clear of the ghost words.

## Margins

- **40 px all round.** Every headline, label and photo frame stays at least 40 px inside its slide.
- **40 px more on the cover's sides.** The profile grid crops a 4:5 cover to 3:4, which takes about 34 px off each
  side. So the words on slide 1 stay 80 px in from the left and right.
- Type behind everything (ghost words, faint fills and the vertical word) may run off the frame. Parts may too.
  A headline or label only does when its element says `"bleed": true`.

## Photos

- **Cover every plate.** List each plate's box under the photo's `redact`. The box is collapsed to a 6x3 colour
  field with a feathered edge, because letters stay readable through a plain blur.
- **No faces.** Crop them out with the photo's `crop`.
- Every photo in the spec carries a `redact` list, `[]` when it has no plate, so nobody skips the look.
- **The engine finds them, a person approves them.** Omarie, 13 Oct 2026: "Find the plates for me", and "we can
  just do it after it makes the carousel". `engine.py` covers the plates and faces it finds and builds straight
  through; the look happens once, on the finished contact sheet, where each cover is outlined. Nothing is posted
  or delivered until that look is done and `engine.py --approve` has been run. The finder misses plates
  (README.md has the measured rate), so "none found" still needs the look.
- **No generating.** Omarie, 13 Oct 2026: "use what we have". Use only the photos supplied, rembg and Pillow.

## Words

Words on the slides come only from approved or existing copy: no figures, prices or brand names unless they are
sourced. Each one goes on the spec's `allowed_words`.

## Checks before delivery

1. `python3 qa.py spec.json out/` prints `all clear`.
2. One nq-check on one contact sheet (`sheet.py`), never slide by slide.
3. Anything with figures or claims then goes through nq-facts and nq-second.

## What qa.py measures

| Rule | Check |
|---|---|
| 40 px margin | Headlines, labels and photo frames at least 40 px from every edge of their slide |
| Cover clears the grid crop | Slide 1's headlines and labels at least 80 px from each side |
| Echo stays clear | A headline's echo doesn't touch a photo frame or run off the canvas |
| Plates looked for | Every photo has a `redact` list |
| Approved words only | Every word drawn is on `allowed_words` |

These it can't measure, so look for them on the contact sheet: a face left in a photo, a plate nobody listed,
words inside the photos, a cutout over the ghost words on slide 5, and slide 4 repeating slide 1's headline.
