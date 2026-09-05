# Logo Files — which one, when

> **Before adding the logo to anything new — an overlay, an ad, a graphic —
> use these files.** They are traced from
> `../01-brand-core/logo-source/fd-primary-horizontal_master.png`, the supplied
> master artwork. Do not re-trace the logo out of the brand-guide raster and do
> not redraw the mark: both produce the soft, round-cornered version this kit
> shipped with originally. See `FIXED-OVERLAYS.md` at the kit root.

## Pick by background, then by shape

**Step 1 — what is behind the logo?**

| Background | Use variant | Example filename |
|---|---|---|
| Dark footage / black | `--white` | `fd-primary-horizontal--white.svg` |
| Light footage / white | `--black` | `fd-primary-horizontal--black.svg` |
| Busy, mixed, or moving | `--mono-white` or `--mono-black` | single colour, no red — maximum legibility |

`--white` and `--black` are the full-colour logo; only the wordmark changes.
The red "PERFORMANCE" and the racing stripe stay branded in both.

**Step 2 — what shape do you need?**

| Lockup | Shape | Use for |
|---|---|---|
| `fd-primary-horizontal` | wide | The default. Corner bugs, end cards, wide layouts. |
| `fd-stacked` | near-square | Tight/vertical space, centred end cards, profile art. |
| `fd-icon` | small, with stripe | Compact mark where the name is already known. |
| `fd-icon-mark-only` | bare FD monogram | Tiny watermarks, favicons, profile pictures, app icons. |

---

## Which file format

```
svg-vector/         ← use this whenever you can
png-transparent/    ← use in CapCut and anything that won't take SVG
png-on-black/       ← flat background, when transparency misbehaves
png-on-white/
```

- **SVG** is true vector — sharp at any size, from a favicon to a billboard.
  Works in Figma, Illustrator, Canva, After Effects, and web.
- **PNG** ships at three widths: `_1000w`, `_2000w`, `_4000w`.
  - `_1000w` — overlays on 1080p video
  - `_2000w` — 4K video, print, safe default
  - `_4000w` — large format, heavy scaling

**For CapCut, use PNG.** CapCut doesn't import SVG. Better still, use the
pre-positioned bugs in `../03-overlays/corner-logo-bugs/` — the logo is already
placed on a full-size transparent frame, so it needs no scaling at all.

---

## Sizing the logo yourself

Minimum digital width is **120 px** (brand guide section 7). On a 1080-wide
frame that's 11%. Practical range for a corner bug is **22–32% of frame width**.

Always scale with the aspect ratio locked. In CapCut, drag a **corner** handle —
dragging an edge handle stretches the logo, which the brand guide prohibits.

Keep clear space equal to one FD-icon height on every side.

---

## Where these files came from

The vectors were traced from the official brand guide raster
(`../01-brand-core/brand-guide-master.png`), with every pixel snapped to an
exact brand hex. They are clean, scalable, and colour-accurate.

They are still a *reproduction* of a raster source. **If your designer has the
original vector artwork (`.ai`, `.eps`, or master `.svg`), that is the better
master.** To swap it in, drop the originals into `svg-vector/` using the same
filenames and re-run `99-toolkit/build_all.py` — every PNG, bug, and end card
downstream will regenerate from the new artwork automatically.
