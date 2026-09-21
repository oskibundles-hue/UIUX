import { useEffect, useState } from "react";
import { cancelRender, continueRender, delayRender, staticFile } from "remotion";
import type { FontFaceSpec } from "./types";

/**
 * Brand font loader. Separate from src/fonts.ts on purpose: a brand font problem fails only brand renders.
 *
 * Import graph: Motion.tsx imports BrandMotion statically, so this module (like every file under src/brand) is
 * LOADED on legacy renders too. That is safe only because nothing here, or anywhere under src/brand, runs at import
 * time: the work happens inside useBrandFonts(), which only brand renders call.
 * work/brand_build/tools/check_brand_side_effects.mjs fails when a src/brand file gains a top-level call.
 *
 * Same injection route as src/fonts.ts (@font-face + document.fonts.load, TTF only), plus proofs that fail the
 * render instead of painting a fallback:
 * - load: a missing or unreadable file fails with the family and file named (Chrome's own error is only
 *   "A network error occurred.");
 * - width proof: the probe line must measure differently from monospace;
 * - weight proof (weight ranges, e.g. Overused Grotesk "300 900"): the lightest
 *   and heaviest weight must measure differently, so the variable axis is live.
 *
 * useBrandFonts() returns `ready`. The render is held (delayRender) until the faces
 * pass and React has committed with ready = true, so components that measure text
 * (src/brand/measure.ts) never lay out with fallback metrics.
 */
const PROBE = "Hamburgefonstiv 0123456789 BOOK YOUR BUILD";
const loading = new Map<string, Promise<void>>();
const loaded = new Set<string>();

const faceId = (f: FontFaceSpec) => `${f.family}|${f.file}|${f.weight}|${f.style ?? "normal"}`;

const measure = (font: string) => {
  const ctx = document.createElement("canvas").getContext("2d");
  if (!ctx) return null;
  ctx.font = font;
  return ctx.measureText(PROBE).width;
};

const loadFace = (f: FontFaceSpec): Promise<void> => {
  const style = f.style ?? "normal";
  const id = faceId(f);
  const known = loading.get(id);
  if (known) return known;
  const p = (async () => {
    const tag = document.createElement("style");
    tag.setAttribute("data-brand-font", id);
    tag.textContent = `@font-face{font-family:'${f.family}';src:url('${staticFile(f.file)}') format('truetype');` +
      `font-weight:${f.weight};font-style:${style};font-display:block;}`;
    document.head.appendChild(tag);
    const load = async (spec: string) => {
      try {
        return await document.fonts.load(spec);
      } catch (err) {
        throw new Error(`brand font failed to load: ${f.family} (${f.file}): ${err instanceof Error ? err.message : String(err)}`);
      }
    };
    const [lo, hi = lo] = f.weight.trim().split(/\s+/);
    const slant = style === "italic" ? "italic " : "";
    const faces = await load(`${slant}${lo} 100px '${f.family}'`);
    if (!faces.length) throw new Error(`brand font not registered: ${f.family} (${f.file})`);
    if (hi !== lo) await load(`${slant}${hi} 100px '${f.family}'`);
    const mono = measure(`${slant}${lo} 100px monospace`);
    const light = measure(`${slant}${lo} 100px '${f.family}', monospace`);
    const heavy = measure(`${slant}${hi} 100px '${f.family}', monospace`);
    if (mono === null || light === null || heavy === null) return;
    if (Math.abs(light - mono) < 0.5) throw new Error(`brand font painted the fallback: ${f.family} (${f.file})`);
    if (hi !== lo && Math.abs(heavy - light) < 0.5) throw new Error(`brand font weight axis not applied: ${f.family} ${f.weight}`);
    console.log(`[brand-fonts] ${f.family} ok: probe ${light.toFixed(1)}px @${lo}` + (hi !== lo ? `, ${heavy.toFixed(1)}px @${hi}` : "") + `, monospace ${mono.toFixed(1)}px`);
  })().then(() => { loaded.add(id); });
  loading.set(id, p);
  return p;
};

/**
 * Holds the render until every face is usable and returns true from then on; any failure
 * cancels the render with the reason. An empty face list is ready at once (no delayRender).
 */
export const useBrandFonts = (faces: readonly FontFaceSpec[]): boolean => {
  const [ready, setReady] = useState(() => faces.every((f) => loaded.has(faceId(f))));
  const [handle] = useState(() => (ready ? null : delayRender(`Loading brand fonts: ${faces.map((f) => f.family).join(", ")}`)));
  useEffect(() => {
    if (handle === null) return;
    Promise.all(faces.map(loadFace))
      .then(() => document.fonts.ready)
      .then(() => setReady(true))
      .catch((err) => cancelRender(err));
    // faces come from a constant token entry, so the handle is the only dependency
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handle]);
  // release the frame only after React has committed the ready tree
  useEffect(() => {
    if (ready && handle !== null) continueRender(handle);
  }, [ready, handle]);
  return ready;
};
