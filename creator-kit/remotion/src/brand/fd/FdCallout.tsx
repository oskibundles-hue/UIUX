import React from "react";
import { Easing, interpolate, spring } from "remotion";
import type { Callout } from "../../Motion";
import type { TextStyle } from "../measure";
import type { BrandCalloutFields } from "../types";
import { pathAt } from "../shared";
import { exitKind, sinceEnd, spanE, type ExitKind } from "../motion";
import { C, H4, L, M, Reticle, SHADOW, SPACE, ScaleRule, T, TM, TypeOn, W4, clampX, easeIn, elementHaze, fitSize, font, hazeAround, Haze, linear, ramp, ts, tw, up, useClock } from "./kit";

export type FdCalloutSpec = Callout & BrandCalloutFields;

const CO = L.callout;
const LAB = ts(T.calloutLabel, 0.14);
const CTX = ts(T.calloutContext, 0.12);
const VAL = ts(T.calloutValue, 0);
const UNIT = ts(T.calloutUnit, 0.04);
const TXT = ts(T.calloutText, 0);
const SUB = ts(T.calloutSub, 0.1);
const END_PAD = 60;   // end-aligned readouts keep their type this far from the vertical leader

/**
 * Callout (restyled CalloutView) = readout + reticle. Readout: label 78 px .14em (+ optional `context` 70 px grey at the
 * right), a rule with its red first third, then a 360 px value with a 132 px unit (white 76%) or a text line (220 px,
 * fitted to 1240 px, 150 px min) with an optional `sub` line; haze with the 60 px graph grid behind. Reticle on the
 * target: ring r66, four arms, red dot r15. A tracked (`path`) callout moves over busy footage, so its ring is r90 (arms
 * and dot scaled with it) and its leader 8 px. Readout haze alpha: props `haze` (tools/fd_element_haze.py) or the panel default.
 *
 * Placement, in order (x = target x):
 * 1. `side` "right" (legacy default) = readout right of the target, right-aligned to the Instagram rail x 1814; "left" =
 *    readout at the left margin x 144. If the preferred side has no room the other side is used. Leader (5 px white,
 *    orthogonal): from the rule's end nearest the target, horizontal to the target x, 16 px white square at the elbow,
 *    then to the reticle arm.
 * 2. No room on either side: a text line shrinks (not below 132 px) until one side fits.
 * 3. Still no room: the readout is end-aligned on the target x (Telemetry still 02; the text may shrink the same way) and
 *    the leader drops straight from the rule's end; the readout prefers to sit below the target.
 * 4. Last resort: straight leader from the readout's near edge.
 * Readout top: `boxY` (0-1), else the rule sits 538 px above the target (674 px below it when that would climb past
 * y 760, or in step 3); kept within y 760-2520.
 * Path contract kept: with `path` the reticle follows pathAt(path, s); readout and elbow stay on x/y, and the last
 * leader segment runs to the moving reticle.
 * Motion: arms slide in from 1.5x (8 f), ring 40 -> 66, dot spring (6 f), leader draws from the reticle (4-16 f), rule
 * draws back from the leader (12-22 f), label types (10 f), value counts up 16-40 f (ease-out exp, tabular digits) or
 * the text clips in left to right (10 f). Out: 8 f fade after the hold, the leader retracts over 6 f.
 */
export const FdCallout: React.FC<{ c: FdCalloutSpec; exit?: ExitKind }> = ({ c, exit }) => {
  const { frame, fps, s } = useClock();
  if (s < c.at || s > c.at + c.hold + M.unmount) return null;
  const atF = Math.round(c.at * fps);
  const f0 = frame - atF;
  const endF = Math.round((c.at + c.hold) * fps) - atF;

  // RELEASE. "fade" = the shipped 8 f whole-layer ramp with the leader already retracting under it.
  // "retract" drops that ramp and reverses each element instead -- reticle collapses, rule draws back,
  // type clips out -- keeping only a 2 f opacity tail on the panel so nothing can linger past
  // M.exitRetract.frames (8 f = 0.267 s), well inside the 0.35 s end-before-cut rule.
  const retracting = exitKind(c.exit, exit) === "retract";
  const R = M.exitRetract;
  const fe = sinceEnd(f0, endF);
  const out = retracting
    ? 1 - spanE(fe, { from: R.frames - 2, to: R.frames }, easeIn)
    : 1 - ramp(f0, endF, endF + TM.outFrames, easeIn);
  if (out <= 0) return null;
  // Identical in both modes: ramp(f0, endF, endF + 6) and spanE(fe, {0, 6}) are the same window.
  const retract = 1 - spanE(fe, R.leader, easeIn);
  const targetOut = retracting ? spanE(fe, R.target, easeIn) : 0;
  const ruleOut = retracting ? spanE(fe, R.rule, easeIn) : 0;
  const textOut = retracting ? spanE(fe, R.text, easeIn) : 0;

  const label = up(c.label);
  const context = up(c.context);
  const isText = c.text != null;
  const val = c.value ?? 0;
  const fmt = (v: number) => (val >= 100 ? String(Math.round(v)) : v.toFixed(1));
  const unit = up((c.suffix ?? "").trim());
  const count = f0 >= M.count.to ? val : interpolate(f0, [M.count.from, M.count.to], [0, val], { ...clampX, easing: Easing.out(Easing.exp) });
  const text = up(c.text);
  const sub = isText ? up(c.sub) : "";
  const railW = SPACE.rail - SPACE.side;
  const subSt = sub ? fitSize([sub], SUB, railW, 60) : SUB;
  const headW = tw(label, LAB) + (context ? CO.headGap + tw(context, CTX) : 0);
  const numW = tw(fmt(val), VAL);
  const valueW = numW + (unit ? CO.unitGap + tw(unit, UNIT) : 0);
  const widthFor = (st: TextStyle) =>
    Math.ceil(Math.min(railW, Math.max(isText ? CO.widthText : CO.width, headW, isText ? Math.max(tw(text, st), sub ? tw(sub, subSt) : 0) : valueW)));

  // ---- placement
  const ax = c.x * W4, ay = c.y * H4;
  const wantRight = (c.side ?? "right") === "right";
  const roomL = ax - CO.clear - SPACE.side;      // readout at the left margin, target to its right
  const roomR = SPACE.rail - CO.clear - ax;     // readout at the rail, target to its left
  const pick = (width: number): boolean | null => {   // true = readout at the rail
    const fitsR = width <= roomR, fitsL = width <= roomL;
    if (wantRight ? fitsR : fitsL) return wantRight;
    if (wantRight ? fitsL : fitsR) return !wantRight;
    return null;
  };
  // readout at the rail (true) / left margin (false) with the target end-aligned on its rule (end mode)
  const endPick = (width: number): boolean | null => {
    const wE = width + END_PAD;
    const leftOf = ax - wE >= SPACE.side, rightOf = ax + wE <= SPACE.rail;
    return wantRight ? (rightOf ? true : leftOf ? false : null) : (leftOf ? false : rightOf ? true : null);
  };
  // shrink a text line so its readout is at most `room` wide (4 px slack against rounding)
  const shrinkTo = (room: number) => fitSize([text], TXT, Math.min(CO.textMax, Math.floor(room) - 4), CO.textFitMin);
  let txtSt = isText ? fitSize([text], TXT, CO.textMax, CO.textMin) : TXT;
  let w = widthFor(txtSt);
  let atRail = pick(w);
  if (atRail === null && isText) {
    const shrunk = shrinkTo(Math.max(roomL, roomR));
    const w2 = widthFor(shrunk);
    if (pick(w2) !== null) { txtSt = shrunk; w = w2; atRail = pick(w2); }
  }
  let mode: "elbow" | "end" | "straight" = "elbow";
  let x = 0;
  let endAt: "left" | "right" = "right";        // end mode: which end of the rule sits on the target x
  if (atRail !== null) {
    x = atRail ? SPACE.rail - w : SPACE.side;
  } else {
    let r = endPick(w);
    if (r === null && isText) {
      const shrunk = shrinkTo(Math.max(ax - SPACE.side, SPACE.rail - ax) - END_PAD);
      const w3 = widthFor(shrunk);
      if (endPick(w3) !== null) { txtSt = shrunk; w = w3; r = endPick(w3); }
    }
    if (r !== null) { mode = "end"; w = Math.min(railW, w + END_PAD); x = r ? ax : ax - w; endAt = r ? "left" : "right"; }
    else { mode = "straight"; x = wantRight ? SPACE.rail - w : SPACE.side; }
  }
  const ruleOff = CO.head + CO.ruleGap;
  const h = ruleOff + CO.ruleH + (isText ? CO.textGap + txtSt.size * 0.84 + (sub ? CO.subGap + subSt.size : 0) : CO.valueGap + VAL.size * 0.78);
  const aboveTop = ay - CO.above - ruleOff, belowTop = ay + CO.below - ruleOff;
  let top: number;
  if (c.boxY != null) top = c.boxY * H4;
  else if (mode === "end") top = belowTop + h <= CO.maxBottom ? belowTop : aboveTop;
  else top = aboveTop >= CO.minTop ? aboveTop : belowTop;
  top = Math.max(CO.minTop, Math.min(CO.maxBottom - h, top));
  const ruleY = top + ruleOff + 2;
  const padL = mode === "end" && endAt === "left" ? END_PAD : 0;
  const padR = mode === "end" && endAt === "right" ? END_PAD : 0;

  // ---- leader, drawn from the reticle back to the readout
  const pt = c.path?.length ? pathAt(c.path, s) : null;
  const dx = pt ? pt.x * W4 : ax, dy = pt ? pt.y * H4 : ay;
  const rs = pt ? CO.trackedRing / CO.ring : 1;   // tracked reticle scale
  const stop = (CO.armAt + CO.arm) * rs;
  const toward = (fx: number, fy: number): [number, number] => {
    const vx = dx - fx, vy = dy - fy, len = Math.hypot(vx, vy);
    return len > stop ? [dx - (vx / len) * stop, dy - (vy / len) * stop] : [fx, fy];
  };
  let pts: [number, number][];
  let elbow: [number, number] | null = null;
  let ruleFrom: "left" | "right" = "left";
  if (mode === "elbow") {
    const rightEnd = ax > x + w;
    ruleFrom = rightEnd ? "right" : "left";
    elbow = [ax, ruleY];
    pts = [toward(ax, ruleY), elbow, [rightEnd ? x + w : x, ruleY]];
  } else if (mode === "end") {
    ruleFrom = endAt;
    pts = [toward(ax, ruleY), [ax, ruleY]];
  } else {
    const ey = top + h / 2 < ay ? top + h + CO.edgeGap : top - CO.edgeGap;
    pts = [toward(ax, ey), [ax, ey]];
  }
  let total = 0;
  for (let i = 1; i < pts.length; i++) total += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const lineK = ramp(f0, M.leader.from, M.leader.to) * retract;
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(" ");
  const elbowK = elbow ? ramp(f0, M.elbow.from, M.elbow.to) * retract : 0;

  const collapse = 1 - targetOut;
  const armK = ramp(f0, M.arms.from, M.arms.to) * collapse;
  const ringK = ramp(f0, M.ring.from, M.ring.to) * collapse;
  const dotK = spring({ frame: f0 - M.dot.delay, fps, config: { damping: M.dot.damping, stiffness: M.dot.stiffness }, durationInFrames: M.dot.frames }) * collapse;
  const hazeK = ramp(f0, M.haze.from, M.haze.to) * (1 - ruleOut);
  const ruleK = Math.min(ramp(f0, M.rule.from, M.rule.to), 1 - ruleOut);
  const labK = ramp(f0, M.label.from, M.label.to, linear) * (1 - textOut);
  const ctxK = ramp(f0, M.context.from, M.context.to, linear) * (1 - textOut);
  const txtK = Math.min(ramp(f0, M.text.from, M.text.to), 1 - textOut);
  const subK = ramp(f0, M.subFrom, M.subFrom + Math.max(1, [...sub].length), linear) * (1 - textOut);
  const hz = hazeAround(x, top, w, h, CO.haze);
  const pad: React.CSSProperties = { paddingLeft: padL, paddingRight: padR, boxSizing: "border-box" };

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, opacity: out }}>
      <Haze {...hz} alpha={elementHaze(c.haze)} grid opacity={hazeK} />
      <svg width={W4} height={H4} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", filter: "drop-shadow(0 2px 8px rgba(0,0,0,.55))" }}>
        {lineK > 0.001 && total > 0 ? (
          <path d={d} fill="none" stroke="#fff" strokeWidth={pt ? CO.trackedLeader : CO.leader} strokeLinecap="butt" strokeLinejoin="miter"
                strokeDasharray={`${total} ${total + 40}`} strokeDashoffset={total * (1 - lineK)} />
        ) : null}
        {elbow && elbowK > 0 ? <rect x={elbow[0] - CO.elbow / 2} y={elbow[1] - CO.elbow / 2} width={CO.elbow} height={CO.elbow} fill="#fff" opacity={elbowK} /> : null}
        <Reticle cx={dx} cy={dy} ringK={ringK} armK={armK} dotK={dotK} scale={rs} />
      </svg>
      <div style={{ position: "absolute", left: x, top, width: w, whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: CO.headGap, height: CO.head, lineHeight: 1, textShadow: SHADOW, ...pad }}>
          <span style={font(LAB)}><TypeOn text={label} k={labK} /></span>
          {context ? <span style={{ ...font(CTX), color: C.sub }}><TypeOn text={context} k={ctxK} /></span> : null}
        </div>
        <ScaleRule w={w} h={CO.ruleH} minor={CO.minor} red={1 / 3} draw={ruleK} from={ruleFrom} style={{ marginTop: CO.ruleGap }} />
        {isText ? (
          <>
            <div style={{ ...font(txtSt), lineHeight: 0.84, marginTop: CO.textGap, textShadow: SHADOW, ...pad,
                          clipPath: txtK >= 1 ? undefined : `inset(-20% ${(1 - txtK) * 100}% -40% -4%)` }}>{text}</div>
            {sub ? <div style={{ ...font(subSt), lineHeight: 1, marginTop: CO.subGap, color: C.sub, textShadow: SHADOW, ...pad }}><TypeOn text={sub} k={subK} /></div> : null}
          </>
        ) : (
          <div style={{ display: "flex", alignItems: "baseline", ...font(VAL), lineHeight: 0.78, marginTop: CO.valueGap, textShadow: SHADOW, opacity: ramp(f0, 14, 18) * (1 - textOut), ...pad }}>
            <span style={{ display: "inline-block", minWidth: numW }}>{fmt(count)}</span>
            {unit ? <span style={{ ...font(UNIT), lineHeight: 1, marginLeft: CO.unitGap, color: "rgba(255,255,255,.76)" }}>{unit}</span> : null}
          </div>
        )}
      </div>
    </div>
  );
};
