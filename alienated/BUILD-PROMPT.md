# ALIENATED — Website Build Prompt

> Paste everything below the line into an AI website builder (v0, Lovable, Bolt) or an
> LLM (Claude, etc.). Trim sections you don't need. It's written to regenerate or
> extend the ALIENATED store.

---

**ROLE:** You are a senior front-end designer-developer. Build a complete, production-ready, fully responsive e-commerce website for an independent streetwear label called **ALIENATED**. It should feel like a real funded fashion label — cinematic, editorial, and a little unsettling — not a generic template. Single-page app feel with client-side view switching (Home, Shop, Product, Reviews, World, Info). Output clean, accessible HTML/CSS/JS (or React if asked); no heavy frameworks required.

## Brand concept
ALIENATED is "a uniform for the unreachable." The whole brand is built on one metaphor: being out of reach on purpose — the missed call, the message left on read, the voicemail that fills up. Collection 001 is codenamed **"Static" (SS25)**. Core lines/taglines to use:
- **"Sorry I was high. Leave a message."** (primary)
- **"For the ones who never call back."**
- **"A uniform for the unreachable."**
- Product names follow the phone motif: **Dead Air**, **Dial Tone**, **Voicemail**.

Tone of voice: terse, calm, deadpan, lowercase-friendly, confident. No corporate fluff, no exclamation marks. A little cold and cryptic.

## Visual identity
- **Mood:** dark, brutal-luxury, shot under raw light in a poured-concrete hall. Studded leather, distressed blackletter, antique-silver hardware, film grain, subtle static/scanline texture.
- **Colors:** ink black `#0a0a0b` (background), bone/off-white `#e9e5d9` (text), muted bone `#a8a49a` (secondary text), **toxic-green accent `#3fe07a`** (CTAs, highlights), plus colorway accents venom pink and sterling silver. Hairlines `rgba(233,229,217,.18)`. A chrome/silver gradient for the wordmark and emblem.
- **Type:** **Anton** for big display headings (uppercase, tight), **Inter** for body, **Pirata One** (blackletter) for the logo wordmark and gothic accents, **Space Mono** for eyebrows/labels/UI chrome (uppercase, wide letter-spacing). All from Google Fonts.
- **Emblem/logo mark:** a chrome dagger-cross with a small hypnotic-spiral medallion at its center. Use a crisp inline SVG.
- **Texture:** faint film grain + occasional scanline/“static” overlay; generous negative space; thin 1px frames; smooth scroll-reveal fade/translate animations; a horizontal marquee strip.

## Pages / sections to build
1. **Entry gate** (first-load overlay): full-screen, plays a moody background video/image, big blackletter "Alienated" wordmark, line "Collection 001 — enter your email to step inside & take 10% off," an email field, and code **ALIEN10** revealed on submit. **Must be dismissible** — a "Skip ✕" button and a "Just let me look around →" link, plus Esc to close. Don't hard-trap the visitor.
2. **Home:** full-bleed hero (background film) with huge "ALIENATED" headline + tagline and a scroll cue; a "Cast in concrete" campaign split (image + copy + CTA); a "The Collection" 3-category teaser (Full Set / Tops / Bottoms); a centered manifesto line ("For the ones who never call back."); a "Transmission 002 — the signal returns" waitlist email capture; an "as seen in" press strip (Hypebeast, Vogue, Highsnobiety, Dazed, i-D).
3. **Shop:** grid of 3 products with real-feel imagery, color-swatch selectors, a 4.x star rating, a "Numbered drop · Edition of 200" badge, price, View + Add to Bag buttons, and filter chips (Full Set / Tops / Bottoms).
4. **Product (PDP):** sticky full-height image stage with scroll-driven shots and dot navigation; colorway + size selectors; a **sticky bottom buy-bar** (name + price + Add to Bag) that appears on scroll; details/fit accordion; cross-sell.
5. **Reviews:** big average score (e.g. 4.7), rating bars, filter chips, and review cards with an "✓ Early access" badge (do **not** label them "Verified buyers" unless they truly are). Keep them honest — no claims that contradict the no-restock policy.
6. **World / About:** big "Leave A Message." headline; origin manifesto; "The Codes" (The Spiral, Blackletter, The Hardware, The Number); a "Made small. Made to keep." production section; closing "For the ones who never call back." CTA.
7. **Info:** Shipping, Returns & Exchanges, Care, Sizing & Fit, an FAQ accordion, and Contact (hello@alienated.studio).
8. **Cart drawer** (slide-in) and a detailed **Size Guide modal** (body + garment-flat measurement tables, XS–XL).
9. **Help chatbot ("Operator"):** a floating "Ask" launcher bottom-right that opens a small dark chat panel with the brand emblem, quick-reply chips (Shipping, Sizing, Returns, The drop, Care, Contact), a typing indicator, and a knowledge base built from the policies below; graceful "leave a message → email" fallback.

## Products (Collection 001 — three colorways: Toxic Green, Venom Pink, Sterling)
- **Dead Air — Full Set** (hoodie + skirt) — **$410**
- **Dial Tone Zip-Hoodie** — **$230**
- **Voicemail Stud Skirt** — **$195**
Every piece is **1 of 200**, numbered on a woven tag. Real antique-silver metal pyramid studs, stitched appliqué graphics (not printed), heavyweight washed fabric, hardware applied by hand. Cropped, low-rise, close to the body; runs small — size up if between sizes. Made in **XS–XL**.

## Policies (use as real content + chatbot knowledge)
- **The drop:** numbered run of 200 per style; once a size sells through it's gone — **no restocks, no second pressings.** Waitlist on home for 002.
- **Shipping:** packed 1–3 business days, tracked link emailed on dispatch. US 2–4 business days; international 5–10 (customs/duties are the buyer's responsibility). Worldwide, fully tracked. Free over $250.
- **Returns:** unworn, within 14 days, tags + numbered tag attached; size exchanges ship free; refunds to original payment; final-sale marked at checkout.
- **Care:** real metal + appliqué — machine wash cold gentle or hand wash, wash darks separately first, hang/lay flat to dry (never tumble — loosens studs), cool iron inside out, no bleach.
- **Payment:** USD — VISA, Mastercard, AMEX, PayPal, Apple Pay, Klarna, Afterpay. Discount **ALIEN10** = 10% off first order.

## Quality bar (must-haves)
- Fully **responsive** (great on mobile — single-column stacking) and **accessible** (semantic HTML, focus-visible states, ARIA labels on modals/forms, `prefers-reduced-motion` respected).
- **Performance:** optimized images (WebP/AVIF), lazy-loading, lightweight JS; target a fast first paint.
- **SEO/social:** title, meta description, Open Graph + Twitter Card tags, a branded `og:image`, favicon/app icons from the emblem, `robots.txt` + `sitemap.xml`, JSON-LD `Product` + `Organization` structured data.
- A branded **404 page** ("Dead Air — this line is dead").
- Demo-mode friendly: email forms and checkout should be easy to wire to a real endpoint later (Formspree/Klaviyo + Stripe/Wix), but degrade gracefully if not connected.

## Avoid
Generic "AI slop" aesthetics — no Inter-on-white minimalism, no purple gradients, no rounded SaaS cards, no stock-photo smiles. This is dark, studded, cinematic, and editorial. Be distinctive and consistent.
