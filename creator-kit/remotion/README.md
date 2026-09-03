# Reel Studio — Remotion templates

Programmatic Reels. You write the words and the timings; the template renders
the hook, the captions, the watermark, the progress bar and the end card,
identically every time.

The point is not that it beats CapCut at any one edit. It's that **every Reel
comes out looking like the same channel** — same caption face, same accent,
same safe areas — without you rebuilding it each time. That consistency is
what makes a grid recognisable before anyone reads the handle.

## Run it

```bash
npm install

# interactive editor, live preview, scrub the timeline
npm run studio

# render
npx remotion render src/index.ts Reel out/reel.mp4
```

Headless environments need an explicit browser:

```bash
npx remotion render src/index.ts Reel out/reel.mp4 \
  --browser-executable=/path/to/headless_shell
```

## Two-stage output

Remotion writes the **master**; `../scripts/ig_export.sh` writes the
**delivery** file:

```bash
npx remotion render src/index.ts Reel out/reel.mp4          # master, ~16 Mbps
../scripts/ig_export.sh out/reel.mp4 -m fill -b 9M \
  --crf 20 --sharpen 0 -o out/reel_IG.mp4                    # delivery
```

Sharpening is off in the second stage on purpose: the footage was already
sharpened before Remotion, and sharpening rendered text puts ringing on the
glyph edges.

## Making your own Reel

Everything is props. Edit `defaultProps` in `src/Root.tsx`, or pass
`--props=my-reel.json`:

```json
{
  "src": "clip.mp4",
  "hook": "This building was empty 30 days ago",
  "handle": "@nq.young",
  "endCard": "Send this to whoever you'd bring on the first drive",
  "endCardAt": 20,
  "showProgress": true,
  "phrases": [
    { "text": "This is the whole space", "start": 3.0, "end": 5.2 },
    { "text": "Nothing was in here", "start": 6.6, "end": 8.6 }
  ]
}
```

Put your video in `public/` and reference it by filename.

### Captions without a transcription service

You write **phrases** with a start and end in seconds. `toWords` in
`src/data/captions.ts` splits each phrase into words and distributes the time
**by word length**, because long words take longer to say — that tracks real
speech much better than dividing a phrase evenly, and it looks hand-timed.

If you do have word-level timings from a transcription tool, skip `toWords`
and pass the words straight through.

## What's in the template

| Component | Job |
|---|---|
| `Hook` | Opening text, on screen at frame one. Words land in sequence so the eye is pulled across the line. |
| `Captions` | Word-by-word, active word in the accent colour. Most people watch muted — this is the primary channel, not an extra. |
| `ProgressBar` | Thin line at the top. "Nearly over" is a reason to stay, and finishing feeds the watch-time signal. |
| `Handle` | Small permanent watermark. The only thing that survives a repost or screen-record. |
| `EndCard` | One CTA, aimed at **sends** — DM shares are weighted far above likes for reaching non-followers. |

## Safe areas

`src/theme.ts` holds the bounds. Instagram covers the bottom of a Reel with
the username, caption and audio strip, and the right edge with the action
rail. Text outside `theme.safe` gets covered:

```
top    260px    status bar
bottom 470px    username + caption + audio
left    72px
right  190px    like / comment / share
```

Change the accent in `theme.ts` and the whole system follows.

## Two things that will bite you

**Fonts must be TrueType, not woff2.** Some headless Chromium builds ship
without a working woff2 decoder: the `@font-face` is accepted, `document.fonts`
reports success, and your text silently paints in a fallback with no error
anywhere. `src/fonts.ts` loads local TTFs from `public/fonts/` and throws if a
family fails to register. It also means renders don't depend on the network.

**Set the colour space.** Remotion defaults to `yuvj420p` tagged `bt470bg` —
full range, wrong primaries. Instagram expects limited-range Rec.709, and a
mistagged file plays washed out on some phones and oversaturated on others.
`remotion.config.ts` sets `bt709` and `yuv420p`.
