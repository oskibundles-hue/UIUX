/**
 * Helpers shared by the brand packs. Pure functions, no side effects.
 *
 * toPhrases and pathAt are VERBATIM copies of the Motion.tsx helpers (2026-09-14),
 * so brand code never imports from Motion.tsx (no runtime cycle) and a change to
 * either copy can never move legacy pixels. check_legacy_tokens.mjs verifies the
 * copies still match the originals.
 */
import type { Word } from "../data/captions";

/** Design sources are drawn on the 2160x3840 canvas. */
export const CANVAS_4K = { w: 2160, h: 3840 } as const;

/** A 4K px length on the current canvas (Motion4K is 2160x3840, so k = 1 there). */
export const px4k = (v: number, height: number) => (v * height) / CANVAS_4K.h;

/** Scale every "<number>px" inside a CSS value (shadows, paddings) by k. */
export const scaleCss = (css: string, k: number) =>
  k === 1 ? css : css.replace(/(-?\d*\.?\d+)px/g, (_, n: string) => `${+(parseFloat(n) * k).toFixed(3)}px`);

export const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

export type CalloutPathPoint = { t: number; x: number; y: number };

/* ---- verbatim copy: Motion.tsx toPhrases ---- */
export const toPhrases = (words: Word[], breaks: number[]) => {
  const out: Word[][] = []; let cur: Word[] = [];
  for (const w of words) {
    const prev = cur[cur.length - 1];
    const crossesCut = prev ? breaks.some((b) => b > prev.start && b <= w.start) : false;
    if (cur.length && (w.start - prev.end > 0.7 || cur.length >= 5 || crossesCut)) { out.push(cur); cur = []; }
    cur.push(w);
  }
  if (cur.length) out.push(cur);
  return out;
};

/* ---- verbatim copy: Motion.tsx pathAt ---- */
export const pathAt = (path: CalloutPathPoint[], s: number): { x: number; y: number } => {
  const p = [...path].sort((a, b) => a.t - b.t);
  if (s <= p[0].t) return { x: p[0].x, y: p[0].y };
  const last = p[p.length - 1];
  if (s >= last.t) return { x: last.x, y: last.y };
  let i = 1; while (p[i].t < s) i++;
  const a = p[i - 1], b = p[i], k = b.t > a.t ? (s - a.t) / (b.t - a.t) : 1;
  return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k };
};

/** First cut strictly after 0 s (cuts usually start with 0.0 = the reel start), or 0 when there is none. */
export const firstCutAfterStart = (cuts: { at: number }[] | undefined) =>
  (cuts ?? []).map((c) => c.at).filter((t) => t > 0).sort((a, b) => a - b)[0] ?? 0;
