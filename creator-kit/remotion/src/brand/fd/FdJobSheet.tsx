import React from "react";
import type { BrandTitleFields } from "../types";
import { C, HZ, L, Lamp, SHADOW, SPACE, ScaleRule, Stripe, T, TM, TypeOn, W4, easeIn, fitSize, font, hazeAround, Haze, linear, ramp, ts, tw, up, useClock, withSize } from "./kit";

export type FdTitleSpec = { eyebrow: string; line1: string; line2: string; until: number } & BrandTitleFields;

const TL = L.title;
const KICK = ts(T.titleKicker, 0.16);
const LINE = ts(T.titleLine, 0.01);
const IDX = ts(T.rowIndex, 0.04);
const CAR = ts(T.rowCar, 0.03);
const JOB = ts(T.rowJob, 0.1);

/** Split line 2 into [before, red, after]. Default red part: the last word, plus the word before it when the last is a number (3+ words). */
export const redSplit = (line2: string, redWord?: string): [string, string, string] => {
  const l2 = up(line2);
  if (redWord === "") return [l2, "", ""];
  if (redWord) {
    const r = up(redWord), i = l2.lastIndexOf(r);
    return i < 0 ? [l2, "", ""] : [l2.slice(0, i), r, l2.slice(i + r.length)];
  }
  const parts = l2.trim().split(/\s+/).filter(Boolean);
  if (parts.length < 2) return [l2, "", ""];            // never the whole line
  const n = /^\d+$/.test(parts[parts.length - 1]) && parts.length >= 3 ? 2 : 1;
  const red = parts.slice(-n).join(" ");
  const i = l2.lastIndexOf(red);
  return [l2.slice(0, i), red, l2.slice(i + red.length)];
};

/**
 * Title card = job sheet (restyled TitleReveal; Precision Workshop graft, Bebas only). Bottom-anchored at y 2890, left 144:
 * kicker (red lamp + `eyebrow`, 80 px .16em), line 1 at 300 px, the five-part FD stripe directly under line 1 (420 x 14, logo
 * proportions), then EITHER numbered job rows from `rows` (index 80 px, 01 red and the rest grey, car 120 px white, job 80 px
 * .10em grey at the right, 3 px hairlines) OR line 2 at 300 px with one red part (`redWord`), and a closing rule with its red
 * first third. Lines shrink together to the sheet width (180 px min).
 * Width: the rail (x 1770), or `maxRight` (0-1 of the frame width) for a shot with his face right of centre. When a car / job
 * row would need more than a 15% shrink on one line, the job stacks under the car (rows 220 px, index column 110 px).
 * Haze: behind line 2 / rows and the rule (title alpha), plus a light one (0.25) behind the kicker and line 1 with a short right
 * bleed so it stays off the face.
 * Motion: lamp blink + kicker types 10 f, line 1 clips up 10 f, stripe grows 8 f, line 2 / rows (4 f stagger) 10 f, rule 16 f;
 * holds to `until`, out over the 8 f before it with a 20 px lift.
 */
export const FdJobSheet: React.FC<{ t: FdTitleSpec }> = ({ t }) => {
  const { frame, fps, s } = useClock();
  if (s > t.until + 0.5) return null;
  const untilF = Math.round(t.until * fps);
  const out = ramp(frame, untilF - TM.outFrames, untilF, easeIn);
  if (out >= 1) return null;

  const railW = SPACE.rail - SPACE.side;
  const capW = t.maxRight != null && Number.isFinite(t.maxRight) ? Math.floor(t.maxRight * W4) - TL.left : railW;
  const maxW = Math.max(TL.minWidth, Math.min(railW, capW));
  const kicker = up(t.eyebrow);
  const line1 = up(t.line1);
  const rows = (t.rows ?? []).filter((r) => r && (r.car || r.job)).map((r) => ({ car: up(r.car), job: up(r.job) }));
  const [a, red, b] = rows.length ? ["", "", ""] : redSplit(t.line2 ?? "", t.redWord);
  const line2 = a + red + b;
  const lineSt = fitSize([line1, ...(line2.trim() ? [line2] : [])], LINE, maxW, TL.lineMin);
  const kickSt = fitSize([kicker], KICK, maxW - 30 - TL.lampGap, 48);
  // rows: car and job on one line; when that needs more than a 15% shrink, the job stacks under the car
  const inlineNeed = rows.map((r) => TL.rowIdxW + tw(r.car, CAR) + 60 + tw(r.job, JOB));
  const inlineF = rows.length ? Math.min(1, maxW / Math.max(...inlineNeed)) : 1;
  const stacked = rows.length > 0 && inlineF < TL.stackBelow;
  const idxW = stacked ? TL.stackIdxW : TL.rowIdxW;
  const carF = !rows.length ? 1 : stacked ? Math.min(1, (maxW - idxW) / Math.max(...rows.map((r) => tw(r.car, CAR)))) : inlineF;
  const rowF = Math.max(TL.rowMinF, carF);
  const carSt = withSize(CAR, +(CAR.size * rowF).toFixed(2));
  const jobSt = stacked ? fitSize(rows.map((r) => r.job), JOB, maxW - idxW, 56) : withSize(JOB, +(JOB.size * rowF).toFixed(2));
  const rowH = stacked ? TL.stackRowH : TL.rowH;
  const rowsW = stacked ? rows.map((r) => idxW + Math.max(tw(r.car, carSt), tw(r.job, jobSt))) : inlineNeed.map((n) => n * rowF);
  const sheetW = Math.ceil(Math.min(maxW, Math.max(TL.ruleW, tw(line1, lineSt), line2.trim() ? tw(line2, lineSt) : 0, ...rowsW)));
  const lineH = lineSt.size * 0.82;
  const topH = T.titleKicker + TL.line1Gap + lineH;
  const lower = rows.length ? TL.rowsGap + TL.hair + rows.length * rowH : line2.trim() ? TL.line2Gap + lineH : 0;
  const h = topH + TL.stripeGap + TL.stripeH + lower + TL.ruleGap + TL.ruleH;
  const top = TL.bottom - h;
  const lowerTop = top + topH + TL.stripeGap + TL.stripeH + (rows.length ? TL.rowsGap : lower ? TL.line2Gap : 0);

  const kickK = ramp(frame, 0, 10, linear);
  const lampOn = !(frame >= 5 && frame < 9);
  const l1K = ramp(frame, 4, 14);
  const stripeK = ramp(frame, 12, 20);
  const l2K = ramp(frame, 16, 26);
  const ruleK = ramp(frame, 20, 36);
  const hazeK = ramp(frame, 10, 18);
  const reveal = (k: number): React.CSSProperties => (k >= 1 ? {} : { clipPath: `inset(${(1 - k) * 100}% -4% -30% -4%)`, transform: `translateY(${(1 - k) * 36}px)` });
  const topW = Math.ceil(Math.min(sheetW, Math.max(30 + TL.lampGap + tw(kicker, kickSt), tw(line1, lineSt))));
  const hzTop = hazeAround(TL.left, top, topW, topH, TL.hazeTop);
  const hz = hazeAround(TL.left, lowerTop, sheetW, TL.bottom - lowerTop, TL.haze);

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", opacity: 1 - out, transform: `translateY(${-out * 20}px)` }}>
      <Haze {...hzTop} alpha={HZ.titleTop} opacity={ramp(frame, 0, 8)} />
      <Haze {...hz} alpha={HZ.title} opacity={hazeK} />
      <div style={{ position: "absolute", left: TL.left, top, width: sheetW, whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: TL.lampGap, height: T.titleKicker, ...font(kickSt), lineHeight: 1, textShadow: SHADOW }}>
          <Lamp on={lampOn} /><span><TypeOn text={kicker} k={kickK} /></span>
        </div>
        <div style={{ ...font(lineSt), lineHeight: 0.82, marginTop: TL.line1Gap, textShadow: SHADOW, ...reveal(l1K) }}>{line1}</div>
        <Stripe w={TL.stripeW} h={TL.stripeH} k={stripeK} style={{ marginTop: TL.stripeGap }} />
        {rows.length ? (
          <div style={{ marginTop: TL.rowsGap, borderTop: `${TL.hair}px solid ${C.hair}`, width: sheetW }}>
            {rows.map((r, i) => {
              const k = ramp(frame, 16 + 4 * i, 26 + 4 * i);
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", height: rowH, boxSizing: "border-box", borderBottom: `${TL.hair}px solid rgba(255,255,255,.26)`,
                                      textShadow: SHADOW, lineHeight: 1, ...reveal(k) }}>
                  <span style={{ ...font(IDX), width: idxW, flex: "none", color: i === 0 ? C.red : C.grey }}>{String(i + 1).padStart(2, "0")}</span>
                  {stacked ? (
                    <span style={{ display: "flex", flexDirection: "column", gap: TL.stackGap, minWidth: 0 }}>
                      <span style={{ ...font(carSt), lineHeight: 0.82, paddingTop: 8 }}>{r.car}</span>
                      <span style={{ ...font(jobSt), lineHeight: 0.82, color: C.sub }}>{r.job}</span>
                    </span>
                  ) : (
                    <>
                      <span style={{ ...font(carSt), flex: 1, minWidth: 0, lineHeight: 0.82, paddingTop: 8 }}>{r.car}</span>
                      <span style={{ ...font(jobSt), color: C.sub, paddingLeft: 60 }}>{r.job}</span>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        ) : line2.trim() ? (
          <div style={{ ...font(lineSt), lineHeight: 0.82, marginTop: TL.line2Gap, textShadow: SHADOW, ...reveal(l2K) }}>
            {a}{red ? <span style={{ color: C.red }}>{red}</span> : null}{b}
          </div>
        ) : null}
        <ScaleRule w={sheetW} h={TL.ruleH} minor={TL.minor} red={1 / 3} draw={ruleK} style={{ marginTop: TL.ruleGap }} />
      </div>
    </div>
  );
};
