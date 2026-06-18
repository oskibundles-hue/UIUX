# ALIENATED — site fixes

Applied to `index.html` (your `alienated.html`, repaired and renamed for hosting as `index.html`).

## Done

1. **UTF-8 mojibake repaired** — every double-encoded character (`â`, `Â·`, etc.) is now a
   correct `—`, `·`, `→`, `✓`, `★`… across the title, marquee, reviews, product names and footer.
2. **Entry gate is no longer a hard wall** — added a `Skip ✕` button, a "Just let me look around →"
   link, and `Esc` to close. Closing unlocks the page so visitors can browse. If they leave without
   subscribing, an **exit-intent** re-offer fires once. Flip `const GATE_ON_LOAD = false;` (in the
   script) to never block on load and only show the gate on exit-intent.
3. **Reviews made honest** — "Verified buyers" → "Early-access wearers", and the per-review
   "✓ Verified" badge → "✓ Early access" (removes the false verified-purchase claim / FTC risk).
4. **Brand contradiction removed** — reviews no longer mention "restocks" / selling out "three times"
   while the brand promises *no restocks, no second pressings*.
5. **Inclusive sizing XS–XL** — product size selectors, copy ("Made in XS–XL"), and the full size
   guide (body + garment-flat tables, cm row) now include XS and XL. The size-ceiling complaint
   review was updated accordingly.
6. **Social/SEO meta** — added Open Graph + Twitter Card + `theme-color` tags.
7. **Consent line** added under the footer email signup; footer year set to 2026.
8. **Image hints** — `loading="lazy" decoding="async"` added to all `<img>` tags.
9. **Assets externalized** — all 11 inline base64 assets extracted to `/media/*` real files and the
   references rewired. **`index.html` went from 2.4 MB → ~100 KB.** Files are now cacheable, and the
   `loading="lazy"` hints actually defer off-screen transfers. Just deploy `index.html` + `media/`
   together (e.g. drag both to Netlify/Vercel/Cloudflare Pages).

## Still needs you

- **Optional: shrink `/media` further.** The extracted images are JPEG (~50–66 KB each). Converting
  to `.webp`/`.avif` and the two `.mp4`s to a smaller bitrate would cut the ~1.6 MB media folder
  roughly in half. Re-point the paths in `MEDIA = {…}` / the campaign `<video>` if you do.
- **`og:image`** — add a hosted 1200×630 share image (placeholder TODO is in `<head>`).
- **Live forms/checkout** — set `FORM_ENDPOINT`, `STORE_URL`/`CHECKOUT` to go out of demo mode.
- **Scarcity counter** (`CLAIMED`) is currently hidden by `RESTRAINT = true`; keep it honest if you
  ever switch it on.
