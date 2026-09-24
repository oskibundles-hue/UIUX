import React from "react";
import type { Word } from "../../data/captions";
import { textWidth } from "../measure";
import { toPhrases } from "../shared";
import { C, H4, L, T, easeIn, font, panel, ramp, ts, useClock, withSize } from "./kit";

/**
 * Captions (new): his words on a solid panel, Overused Grotesk 104 px, sentence case as transcribed.
 * Words already said are white, the spoken word sits in a WHITE CHIP with ground-coloured ink
 * (graft from Wordmark Monochrome: padding 10 / margin -4 on every word so nothing reflows),
 * words still to come are white 36%. Orange is not used here -- EXCEPT for words carrying a `speaker`
 * (see SPK below): another person's lines are drawn in the website orange with a small tag over the panel,
 * so a viewer can tell who is talking. Props with no `speaker` anywhere render exactly as before.
 *
 * Pages: phrases come from a verbatim toPhrases copy (<= 5 words, split on 0.7 s gaps and on cuts). A phrase that ends
 * on the first word of the next sentence ("... here. I") hands that word to the following phrase when the two are
 * contiguous (<= 0.7 s apart, no cut between), so a page never ends on a dim lone word that reads as a text cursor;
 * two phrases that were split only by the 5-word cap share a page: one line when both fit the panel,
 * otherwise one line each, as in the design. Measures text, so call it only once brand fonts are ready.
 * A page shows from its first word to 0.45 s after its last (legacy tail), or until the next page starts.
 * The panel's bottom edge sits on the Instagram-safe line (y 2899) and grows upward.
 */
export type CapPage = { lines: Word[][]; start: number; lastEnd: number; tailEnd: number; prevJoin: boolean; nextJoin: boolean;
  /** "" = him (default look). Any other value = another speaker, drawn in the speaker look with a tag. */
  speaker: string };

const CAP = L.captions;
const TAIL = 0.45;
const WORD = ts(T.caption, 700, -0.01);

const SENTENCE_END = /[.!?…]["'”’)\]]*$/;

/** Another speaker's words: the website orange instead of white, plus a small tag over the panel.
 *  Words with no `speaker` (the default) are unaffected, so a props file that doesn't use it renders as before. */
const SPK = { ink: C.accent, ink36: "rgba(255,79,22,.36)", chip: C.accent, chipInk: C.chipInk,
              tagSize: 44, tagGap: 14, tagPadX: 18, tagPadY: 8, tagPlate: "rgba(10,10,10,.78)" };
const speakerOf = (w: Word) => w.speaker ?? "";
/** Times where the speaker changes, fed in with the cuts so no phrase, group or page mixes two speakers. */
const speakerBreaks = (words: Word[]): number[] =>
  words.flatMap((w, i) => (i > 0 && speakerOf(w) !== speakerOf(words[i - 1]) ? [w.start] : []));

/** Hand a trailing one-word start of the next sentence to the following phrase (see the header). */
const carrySentenceStarts = (phrases: Word[][], breaks: number[]): Word[][] => {
  const out = phrases.map((p) => [...p]);
  for (let i = 0; i + 1 < out.length; i++) {
    const a = out[i], b = out[i + 1];
    if (a.length < 2) continue;
    const last = a[a.length - 1];
    if (!SENTENCE_END.test(a[a.length - 2].text) || SENTENCE_END.test(last.text)) continue;
    if (b[0].start - last.end > 0.7 || breaks.some((t) => t > last.start && t <= b[0].start)) continue;
    a.pop();
    b.unshift(last);
  }
  return out;
};

export const captionPages = (words: Word[], cuts: number[], after: number): CapPage[] => {
  const shown = words.filter((w) => w.start >= after);
  const breaks = [...cuts, ...speakerBreaks(shown)];
  const phrases = carrySentenceStarts(toPhrases(shown, breaks), breaks);
  const groups: Word[][][] = [];
  for (let i = 0; i < phrases.length;) {
    const a = phrases[i], b = phrases[i + 1];
    const aLast = a[a.length - 1];
    const join = !!b && b[0].start - aLast.end <= 0.7 && !breaks.some((t) => t > aLast.start && t <= b[0].start);
    groups.push(join ? [a, b] : [a]);
    i += join ? 2 : 1;
  }
  const inner = CAP.maxWidth - 2 * CAP.padX;
  const pages: CapPage[] = groups.map((group) => {
    const flat = group.flat();
    return { lines: layoutLines(flat, inner, group[0].length), start: flat[0].start, lastEnd: flat[flat.length - 1].end, tailEnd: 0, prevJoin: false, nextJoin: false, speaker: speakerOf(flat[0]) };
  });
  pages.forEach((p, i) => {
    const next = pages[i + 1];
    p.tailEnd = next ? Math.min(p.lastEnd + TAIL, next.start) : p.lastEnd + TAIL;
    p.nextJoin = !!next && p.lastEnd + TAIL >= next.start;
    if (next) next.prevJoin = p.nextJoin;
  });
  return pages;
};

/** Canvas y of the caption panel's top edge for a page of `lines` lines at full size. */
export const captionTop = (lines: number) => CAP.bottom - (CAP.padT + CAP.padB + lines * T.caption * CAP.lineHeight);

const lineWidth = (line: Word[], size: number) => {
  const t = withSize(WORD, size);
  return line.reduce((a, w) => a + textWidth(w.text, t), 0) + (line.length - 1) * textWidth(" ", t) + line.length * 2 * (CAP.chipPadX - CAP.chipOverlap);
};

/**
 * One line when the page fits the panel. Otherwise two lines, broken at the phrase boundary unless
 * that leaves a line under half the other's width (e.g. a one-word orphan), in which case the break
 * that gives the narrowest widest line is used. A page still too wide shrinks its size in SeCaptions.
 */
const layoutLines = (flat: Word[], inner: number, boundary: number): Word[][] => {
  if (flat.length < 2 || lineWidth(flat, T.caption) <= inner) return [flat];
  const split = (k: number) => [lineWidth(flat.slice(0, k), T.caption), lineWidth(flat.slice(k), T.caption)];
  if (boundary > 0 && boundary < flat.length) {
    const [a, b] = split(boundary);
    if (Math.min(a, b) >= 0.5 * Math.max(a, b)) return [flat.slice(0, boundary), flat.slice(boundary)];
  }
  let best = 1, bestW = Infinity;
  for (let k = 1; k < flat.length; k++) {
    const w = Math.max(...split(k));
    if (w < bestW - 0.5) { best = k; bestW = w; }
  }
  return [flat.slice(0, best), flat.slice(best)];
};

export const SeCaptions: React.FC<{ pages: CapPage[]; until: number; yields: [number, number][] }> = ({ pages, until, yields }) => {
  const { fps, s } = useClock();
  if (s >= until) return null;
  const pi = pages.findIndex((p) => s >= p.start && s < p.tailEnd);
  if (pi < 0) return null;
  const pg = pages[pi];
  const aIn = pg.prevJoin ? 1 : ramp(s, pg.start, pg.start + 6 / fps);
  const aOut = pg.nextJoin ? 1 : 1 - ramp(s, pg.tailEnd - 0.25, pg.tailEnd, easeIn);
  let hidden = 0;   // captions yield to a booking CTA
  for (const [a, b] of yields) hidden = Math.max(hidden, Math.min(ramp(s, a, a + 6 / fps), 1 - ramp(s, b - 6 / fps, b)));
  const opacity = Math.min(aIn, aOut) * (1 - hidden);
  if (opacity <= 0) return null;

  const inner = CAP.maxWidth - 2 * CAP.padX;
  const widest = Math.max(...pg.lines.map((l) => lineWidth(l, T.caption)));
  const size = widest <= inner ? T.caption : Math.max(T.captionMin, (T.caption * inner) / widest);
  const flat = pg.lines.flat();
  let now = -1;
  flat.forEach((w, j) => { if (w.start <= s) now = j; });
  const cw = now >= 0 ? flat[now] : null;
  const nx = now >= 0 ? flat[now + 1] : undefined;
  const chipOn = !!cw && (s < cw.end + 0.3 || (!!nx && nx.start - cw.end <= 0.3));
  const chipK = cw ? ramp(s, cw.start, cw.start + 3 / fps) : 0;

  const other = pg.speaker !== "";   // another speaker: orange ink + a tag over the panel; his own pages are untouched
  const inkNow = other ? SPK.ink : C.ink, inkNext = other ? SPK.ink36 : C.ink36;
  const chipBg = other ? SPK.chip : C.chip, chipInk = other ? SPK.chipInk : C.chipInk;

  let offset = 0;
  return (
    <div style={{ position: "absolute", left: CAP.left, bottom: H4 - CAP.bottom, maxWidth: CAP.maxWidth, boxSizing: "border-box", padding: `${CAP.padT}px ${CAP.padX}px ${CAP.padB}px`,
                  ...panel(true, CAP.radius), opacity, transform: `translateY(${(1 - aIn) * 24}px)` }}>
      {other ? (
        <div style={{ position: "absolute", left: 0, bottom: "100%", marginBottom: SPK.tagGap, ...font(ts(SPK.tagSize, 800, 0.12)),
                      color: SPK.ink, background: SPK.tagPlate, borderRadius: 10, padding: `${SPK.tagPadY}px ${SPK.tagPadX}px`,
                      whiteSpace: "nowrap", textTransform: "uppercase" }}>
          {pg.speaker}
        </div>
      ) : null}
      {pg.lines.map((line, li) => {
        const base = offset;
        offset += line.length;
        return (
          <div key={li} style={{ ...font(withSize(WORD, size)), lineHeight: CAP.lineHeight, whiteSpace: "nowrap" }}>
            {line.map((w, wi) => {
              const j = base + wi;
              const isChip = j === now && chipOn;
              const color = isChip ? chipInk : j <= now ? inkNow : inkNext;
              return (
                <React.Fragment key={wi}>
                  {wi > 0 ? " " : null}
                  <span style={{ position: "relative", padding: `0 ${CAP.chipPadX}px`, margin: `0 -${CAP.chipOverlap}px` }}>
                    {isChip ? <span style={{ position: "absolute", left: 0, right: 0, top: "0.07em", bottom: "-0.03em", background: chipBg, borderRadius: CAP.chipRadius,
                                             transform: `scale(${0.9 + 0.1 * chipK})` }} /> : null}
                    <span style={{ position: "relative", color }}>{w.text}</span>
                  </span>
                </React.Fragment>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};
