import React from "react";
import type { Word } from "../../data/captions";
import type { BrandCaptionHaze } from "../types";
import { toPhrases } from "../shared";
import { C, HZ, L, T, TM, Haze, easeIn, easeOut, font, hazeAround, ramp, ts, tw, up, useClock } from "./kit";

/**
 * Captions (new): his words one at a time, Bebas 168 px .02em, white with a soft shadow, no box, no stroke.
 * Phrases come from the verbatim toPhrases copy (<= 5 words, split on 0.7 s gaps and on cuts), laid out on at most
 * two lines (left 144, max width 1626 so the block ends at the x 1770 rail, bottom-anchored at 2960; a phrase that
 * needs three lines shrinks, 120 px min). A word appears at word.start (3 f fade + 12 px rise). One 14 px red cursor
 * sits under the spoken word: it glides from the previous word on the same line and resizes to the new width over
 * min(3 f, the word's time) with an ease-out, and snaps straight to a word that lasts under 5 frames, so it never
 * trails the speech; at a new line it grows in place over the same time. Word positions are measured with the Bebas
 * face (../measure.ts), never read from the DOM, so every frame renders the same. A phrase fades out over 6 f from
 * 0.35 s after its last word, or ends when the next one starts.
 *
 * Judge fix: a subtle feathered haze behind the phrase block. Its alpha comes from props.captionHaze (per phrase,
 * computed from the graded master by work/brand_build/tools/fd_caption_haze.py) or the token default 0.22. When a
 * phrase replaces one that was still showing, the haze stays up and its alpha crossfades over 4 f (no one-frame blink).
 * Captions yield to CTAs (8 f) and stop at outro.at.
 */
const CAP = L.captions;

export type FdPhrase = { words: Word[]; start: number; lastEnd: number; end: number };
type Line = { idx: number[]; x: number[]; w: number[]; width: number };
export type PhraseLayout = { size: number; lines: Line[]; width: number; height: number };

export const captionPhrases = (words: Word[], breaks: number[], after: number, fps: number): FdPhrase[] => {
  const ph = toPhrases(words.filter((w) => w.start >= after), breaks);
  return ph.map((p, i) => {
    const next = ph[i + 1];
    const lastEnd = p[p.length - 1].end;
    const natural = lastEnd + TM.captionTail + TM.captionOutFrames / fps;
    return { words: p, start: p[0].start, lastEnd, end: next ? Math.min(natural, next[0].start) : natural };
  });
};

/** Greedy word wrap at 168 px; more than two lines shrinks the phrase (not below 120 px). */
export const layoutPhrase = (words: Word[]): PhraseLayout => {
  let size: number = T.caption;
  for (;;) {
    const st = ts(size, CAP.tracking);
    const gap = CAP.wordGap * size;
    const lines: Line[] = [];
    let cur: Line = { idx: [], x: [], w: [], width: 0 };
    words.forEach((wd, i) => {
      const w = tw(up(wd.text), st);
      if (cur.idx.length && cur.width + gap + w > CAP.maxWidth) { lines.push(cur); cur = { idx: [], x: [], w: [], width: 0 }; }
      const x = cur.idx.length ? cur.width + gap : 0;
      cur.idx.push(i); cur.x.push(x); cur.w.push(w); cur.width = x + w;
    });
    if (cur.idx.length) lines.push(cur);
    if (lines.length <= CAP.maxLines || size <= CAP.minSize) {
      return { size, lines, width: Math.max(0, ...lines.map((l) => l.width)), height: lines.length * size * CAP.lineHeight };
    }
    size = Math.max(CAP.minSize, Math.floor(size * 0.94));
  }
};

/** Canvas y of the caption text block's top edge for a phrase. */
export const captionTop = (p: FdPhrase) => CAP.bottom - layoutPhrase(p.words).height;

/** Haze alpha for a phrase starting at `start` (step function over props.captionHaze). */
export const captionHazeAlpha = (list: BrandCaptionHaze[] | undefined, start: number): number => {
  let a: number = HZ.captions;
  let best = -Infinity;
  for (const e of list ?? []) {
    if (e && Number.isFinite(e.at) && Number.isFinite(e.a) && e.at <= start + 0.05 && e.at >= best) { best = e.at; a = e.a; }
  }
  return Math.min(HZ.captionsMax, Math.max(0, a));
};

export const FdCaptions: React.FC<{ phrases: FdPhrase[]; until: number; yields: [number, number][]; haze?: BrandCaptionHaze[] }> = ({ phrases, until, yields, haze }) => {
  const { frame, fps, s } = useClock();
  if (s >= until) return null;
  const pi = phrases.findIndex((p) => s >= p.start && s < p.end);
  if (pi < 0) return null;
  const ph = phrases[pi];
  const outStart = ph.lastEnd + TM.captionTail;
  const aOut = 1 - ramp(s, outStart, outStart + TM.captionOutFrames / fps, easeIn);
  let hidden = 0;   // captions yield to a booking CTA
  for (const [a, b] of yields) hidden = Math.max(hidden, Math.min(ramp(s, a, a + 8 / fps), 1 - ramp(s, b - 8 / fps, b)));
  const vis = aOut * (1 - hidden);
  if (vis <= 0) return null;

  const lay = layoutPhrase(ph.words);
  const st = ts(lay.size, CAP.tracking);
  const lh = lay.size * CAP.lineHeight;
  const top = CAP.bottom - lay.height;
  let now = -1;
  ph.words.forEach((w, i) => { if (w.start <= s) now = i; });
  const where = (i: number) => {
    for (let li = 0; li < lay.lines.length; li++) {
      const j = lay.lines[li].idx.indexOf(i);
      if (j >= 0) return { li, x: lay.lines[li].x[j], w: lay.lines[li].w[j] };
    }
    return null;
  };

  let cursor: React.ReactNode = null;
  const at = now >= 0 ? where(now) : null;
  if (at) {
    const wd = ph.words[now];
    const f = Math.round(wd.start * fps);
    const nextW = ph.words[now + 1];
    const holdF = ((nextW ? nextW.start : wd.end) - wd.start) * fps;   // frames until the cursor moves on
    const glide = Math.max(1, Math.min(CAP.cursorGlide, Math.floor(holdF)));
    const k = holdF < CAP.cursorSnapBelow ? 1 : ramp(frame, f, f + glide, easeOut);
    const prev = now > 0 ? where(now - 1) : null;
    const same = !!prev && prev.li === at.li;
    const x = same && prev ? prev.x + (at.x - prev.x) * k : at.x;
    const w = same && prev ? prev.w + (at.w - prev.w) * k : at.w * Math.min(1, Math.max(0, k));
    cursor = (
      <div style={{ position: "absolute", left: CAP.left + x, top: top + at.li * lh + lh - CAP.cursorLift - CAP.cursorH, width: Math.max(0, w), height: CAP.cursorH,
                    background: C.red, boxShadow: "0 4px 16px rgba(0,0,0,.45)" }} />
    );
  }
  const hz = hazeAround(CAP.left, top, lay.width, lay.height, CAP.haze);
  // haze handover: the previous phrase was still fully up when this one started (cut short, not faded out)
  const prevPh = pi > 0 ? phrases[pi - 1] : null;
  const handover = !!prevPh && prevPh.end >= ph.start - 0.5 / fps && prevPh.lastEnd + TM.captionTail >= ph.start - 2 / fps;
  const mix = ramp(s, ph.start, ph.start + 4 / fps);
  const aNow = captionHazeAlpha(haze, ph.start);
  const hazeAlpha = handover && prevPh ? captionHazeAlpha(haze, prevPh.start) * (1 - mix) + aNow * mix : aNow;

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", opacity: vis }}>
      <Haze {...hz} alpha={hazeAlpha} opacity={handover ? 1 : mix} />
      {lay.lines.map((line, li) => line.idx.map((i, j) => {
        const wd = ph.words[i];
        const f = Math.round(wd.start * fps);
        const k = ramp(frame, f, f + 3);
        if (k <= 0) return null;
        return (
          <span key={`${li}-${i}`} style={{ position: "absolute", left: CAP.left + line.x[j], top: top + li * lh, height: lh, lineHeight: `${lh}px`, whiteSpace: "nowrap",
                                            ...font(st), textShadow: CAP.shadow, opacity: k, transform: `translateY(${(1 - k) * 12}px)` }}>{up(wd.text)}</span>
        );
      }))}
      {cursor}
    </div>
  );
};
