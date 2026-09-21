import React from "react";
import type { LowerThirdSpec } from "../../Motion";
import type { BrandLowerThirdFields } from "../types";
import { captionTop, type FdPhrase } from "./FdCaptions";
import { C, HZ, L, SHADOW, SPACE, ScaleRule, T, TypeOn, easeIn, fitSize, font, hazeAround, Haze, linear, ramp, ts, tw, up, useClock, withSize } from "./kit";

export type FdLowerThirdSpec = LowerThirdSpec & BrandLowerThirdFields;

const LT = L.lowerThird;
const TITLE = ts(T.lowerThirdTitle, 0);
const SUB = ts(T.lowerThirdSub, 0.1);
const KIND = ts(T.lowerThirdKind, 0.24);
const KEY = ts(T.cellKey, 0.16);
const VALUE = ts(T.cellValue, 0.08);

/**
 * Collision rule with captions: both sit in the same band (lower third 2536-2912, captions up to 2624-2960). When any
 * caption phrase overlaps the lower third's window, the lower third sits 90 px above the tallest such caption block for
 * its whole hold, so speech stays captioned and nothing jumps.
 */
export const fdLowerThirdBottom = (l: { at: number; hold: number }, phrases: FdPhrase[]): number => {
  const t0 = l.at, t1 = l.at + l.hold + 0.4;
  let top = Infinity;
  for (const p of phrases) if (p.start < t1 && p.end > t0) top = Math.min(top, captionTop(p));
  return top === Infinity ? LT.bottom : Math.min(LT.bottom, top - LT.aboveCaptions);
};

/**
 * Collision rule with the title card (same band): a lower third that would start before title.until + 0.2 s starts
 * then instead, keeping its end, and holds at least 2.4 s.
 */
export const deferPastTitle = <X extends { at: number; hold: number }>(l: X, until: number | null): X => {
  if (until == null) return l;
  const gate = until + LT.afterTitle;
  if (l.at >= gate) return l;
  return { ...l, at: gate, hold: Math.max(l.at + l.hold - gate, LT.minHold) };
};

/**
 * Lower third (restyled): section tab (rotated `kind` label, default "JOB", grey, with a red foot), 232 px title, rule with
 * its red first third, then the key/value row (Precision Workshop graft, Bebas only: key 64 px .16em grey + value 90 px
 * .08em, cells 64 px apart, e.g. CAR MASERATI MC20) or, without `cells`, the 90 px grey sub line as written. Haze with the
 * graph grid behind. In: haze 8 f, foot grows 8 f, title clips bottom-up 12 f, rule 14 f, sub types 1 f per character.
 * Out: clips right to left over 10 f.
 */
export const FdLowerThird: React.FC<{ l: FdLowerThirdSpec; bottom: number }> = ({ l, bottom }) => {
  const { frame, fps, s } = useClock();
  if (s < l.at || s > l.at + l.hold + 0.4) return null;
  const atF = Math.round(l.at * fps);
  const f0 = frame - atF;
  const endF = Math.round((l.at + l.hold) * fps) - atF;
  const outK = ramp(f0, endF, endF + 10, easeIn);
  if (outK >= 1) return null;

  const maxBody = SPACE.rail - SPACE.side - LT.tabW - LT.tabGap;
  const title = up(l.title);
  const titleSt = fitSize([title], TITLE, maxBody, 150);
  const cells = (l.cells ?? []).filter((c) => c && (c.k || c.v)).map((c) => ({ k: up(c.k), v: up(c.v) }));
  const sub = cells.length ? "" : up(l.sub);
  const cellsW = (k: typeof KEY, v: typeof VALUE) => cells.reduce((a, c, i) => a + (i ? LT.cellGap : 0) + (c.k ? tw(c.k, k) + LT.cellKeyGap : 0) + tw(c.v, v), 0);
  let keySt = KEY, valSt = VALUE;
  if (cells.length) {
    const full = cellsW(KEY, VALUE);
    if (full > maxBody) {
      const f = Math.max(0.6, maxBody / full);
      keySt = withSize(KEY, +(KEY.size * f).toFixed(2));
      valSt = withSize(VALUE, +(VALUE.size * f).toFixed(2));
    }
  }
  const subSt = sub ? fitSize([sub], SUB, maxBody, 56) : SUB;
  const rowW = cells.length ? cellsW(keySt, valSt) : sub ? tw(sub, subSt) : 0;
  const rowH = cells.length ? valSt.size : sub ? subSt.size : 0;
  const bodyW = Math.ceil(Math.max(tw(title, titleSt), rowW));
  const h = titleSt.size * 0.82 + LT.ruleGap + LT.ruleH + (rowH ? LT.subGap + rowH : 0);
  const top = bottom - h;
  const kind = up(l.kind ?? "JOB");
  const kindSt = fitSize([kind], KIND, Math.max(60, h - LT.kindInset), 44);

  const hazeK = ramp(f0, 0, 8);
  const footK = ramp(f0, 2, 10);
  const kindK = ramp(f0, 6, 14);
  const titleK = ramp(f0, 4, 16);
  const ruleK = ramp(f0, 10, 24);
  const chars = cells.length ? cells.reduce((a, c) => a + [...c.k].length + [...c.v].length, 0) : [...sub].length;
  const rowK = ramp(f0, 16, 16 + Math.max(1, chars), linear);
  // type the key/value row cell by cell
  let used = 0;
  const cellK = (text: string) => {
    const n = [...text].length, start = used;
    used += n;
    return n ? Math.min(1, Math.max(0, (rowK * chars - start) / n)) : 1;
  };
  const hz = hazeAround(LT.left, top, LT.tabW + LT.tabGap + bodyW, h, LT.haze);

  return (
    <>
      <Haze {...hz} alpha={HZ.panel} grid opacity={hazeK * (1 - outK)} />
      <div style={{ position: "absolute", left: LT.left, top, height: h, display: "flex", alignItems: "stretch", whiteSpace: "nowrap",
                    clipPath: outK > 0 ? `inset(-60px ${outK * 100}% -60px -60px)` : undefined }}>
        <div style={{ position: "relative", width: LT.tabW, flex: "none", marginRight: LT.tabGap }}>
          <div style={{ position: "absolute", left: 0, top: 0, width: LT.tabW, height: Math.max(0, h - LT.kindInset), writingMode: "vertical-rl", transform: "rotate(180deg)",
                        ...font(kindSt), lineHeight: `${LT.tabW}px`, textAlign: "right", color: C.sub, opacity: kindK }}>{kind}</div>
          <div style={{ position: "absolute", left: LT.footLeft, bottom: 0, width: LT.footW, height: LT.footH, background: C.red, transformOrigin: "50% 100%", transform: `scaleY(${footK})` }} />
        </div>
        <div style={{ width: bodyW }}>
          <div style={{ ...font(titleSt), lineHeight: 0.82, textShadow: SHADOW,
                        clipPath: titleK >= 1 ? undefined : `inset(${(1 - titleK) * 100}% -4% -30% -4%)` }}>{title}</div>
          <ScaleRule w={bodyW} h={LT.ruleH} minor={LT.minor} red={1 / 3} draw={ruleK} style={{ marginTop: LT.ruleGap }} />
          {cells.length ? (
            <div style={{ display: "flex", alignItems: "baseline", gap: LT.cellGap, marginTop: LT.subGap, lineHeight: 1, height: rowH, textShadow: SHADOW }}>
              {cells.map((c, i) => {
                const kk = cellK(c.k), vk = cellK(c.v);
                return (
                  <span key={i} style={font(valSt)}>
                    {c.k ? <span style={{ ...font(keySt), color: C.sub, marginRight: LT.cellKeyGap }}><TypeOn text={c.k} k={kk} /></span> : null}
                    <TypeOn text={c.v} k={vk} />
                  </span>
                );
              })}
            </div>
          ) : sub ? (
            <div style={{ ...font(subSt), color: C.sub, marginTop: LT.subGap, lineHeight: 1, textShadow: SHADOW }}><TypeOn text={sub} k={rowK} /></div>
          ) : null}
        </div>
      </div>
    </>
  );
};
