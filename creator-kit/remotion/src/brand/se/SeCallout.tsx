import React from "react";
import { Easing, interpolate, spring } from "remotion";
import type { Callout } from "../../Motion";
import type { BrandCalloutFields } from "../types";
import { textWidth } from "../measure";
import { pathAt } from "../shared";
import { C, H4, L, LABEL, LINING, SAFE, T, W4, bracket, clampX, easeIn, fitSize, fitTracking, font, panel, ramp, ts, useClock } from "./kit";

export type SeCalloutSpec = Callout & BrandCalloutFields;

const CO = L.callout;
const VAL = ts(T.calloutValue, 800, -0.03, true);
const UNIT = ts(T.calloutUnit, 500, -0.01);
const TXT = ts(T.calloutText, 700, -0.025);
const SUB = ts(T.calloutSub, 500, -0.01);
/** "2h 37m", "2.9 s", "986 HP": number + short unit pairs get the value styling. */
const UNITS_ONLY = /^\s*(?:\d+(?:[.,]\d+)?\s*[A-Za-z%°]{1,3}\s*)+$/;
type Item = { num: string; unit: string };
const unitItems = (text: string): Item[] => [...text.matchAll(/(\d+(?:[.,]\d+)?)\s*([A-Za-z%°]{1,3})/g)].map((m) => ({ num: m[1], unit: m[2] }));
const rowWidth = (items: Item[]) => {
  let sum = 0, n = 0;
  items.forEach((it, i) => {
    sum += textWidth(it.num, VAL); n++;
    if (it.unit) { sum += textWidth(it.unit, UNIT); n++; if (i < items.length - 1) sum += CO.pairGap; }
  });
  return sum + Math.max(0, n - 1) * CO.unitGap;
};

/**
 * Callout (restyled CalloutView): glass box with a bracket label (white 84% text between orange brackets: all-orange
 * label type measured 2.5:1 on glass over bright sky at phone size), a 176 px value (units 92 px,
 * white 72%) or a 120 px text line, optional sub line; a double-stroke leader (16 px black 45%
 * under 6 px white, tokens) from the box edge at 62% of its height, 80 px straight out, then to the dot;
 * the dot is an orange-ring target (halo r70 orange 20%, ring r34, white core r15).
 *
 * Box side: `side` "right" (legacy default) puts the box right of the dot, right-aligned to the
 * safe line x 1780; "left" puts it at the left margin x 145. When the preferred side leaves no
 * room between elbow and dot the other side is used. Box top: `boxY` (0-1) or derived from the dot.
 * Path contract kept: with `path`, the dot follows pathAt(path, s); box and elbow stay on x/y. A tracked callout
 * moves over busy footage, so (as in FdCallout) its target is scaled to ring r46 and its leader is 9 px over 26 px.
 * Timing as legacy: dot, leader 4-18 f, box from 10 f, count-up 14-40 f, out 0.35 s after hold.
 */
export const SeCallout: React.FC<{ c: SeCalloutSpec }> = ({ c }) => {
  const { frame, fps, s } = useClock();
  if (s < c.at || s > c.at + c.hold + 0.4) return null;
  const f0 = frame - Math.round(c.at * fps);
  const dotK = Math.max(0, spring({ frame: f0, fps, config: { damping: 11, stiffness: 260 }, durationInFrames: 12 }));
  const line = ramp(f0, 4, 18);
  const boxK = Math.max(0, spring({ frame: f0 - 10, fps, config: { damping: 16, stiffness: 150 }, durationInFrames: 18 }));
  const out = 1 - ramp(s, c.at + c.hold, c.at + c.hold + 0.35, easeIn);

  const maxInner = SAFE.right - SAFE.left - 2 * CO.padX;
  const labelText = bracket(c.label);
  const labelSt = fitTracking(labelText, LABEL, maxInner, 0.14);
  const isText = c.text != null;
  const val = c.value ?? 0;
  const count = f0 >= 40 ? val : interpolate(f0, [14, 40], [0, val], { ...clampX, easing: Easing.out(Easing.exp) });
  const fmt = (v: number) => (val >= 100 ? String(Math.round(v)) : v.toFixed(1));
  const suffix = (c.suffix ?? "").trim();
  const finalItems: Item[] | null = isText ? (UNITS_ONLY.test(c.text ?? "") ? unitItems(c.text ?? "") : null) : [{ num: fmt(val), unit: suffix }];
  const liveItems: Item[] | null = isText ? finalItems : [{ num: fmt(count), unit: suffix }];
  const txtSt = isText && !finalItems ? fitSize([c.text ?? ""], TXT, maxInner, 72) : TXT;
  const rowW = finalItems ? rowWidth(finalItems) : textWidth(c.text ?? "", txtSt);
  const rowH = finalItems ? VAL.size * 0.9 : txtSt.size * 1.05;
  const subSt = c.sub ? fitSize([c.sub], SUB, maxInner, T.floorStrict) : SUB;
  const bw = Math.min(SAFE.right - SAFE.left, Math.ceil(Math.max(textWidth(labelText, labelSt), rowW, c.sub ? textWidth(c.sub, subSt) : 0) + 2 * CO.padX + 12));
  const bh = CO.padT + labelSt.size + CO.labelGap + rowH + (c.sub ? CO.subGap + subSt.size * 1.1 : 0) + CO.padB;

  const ax = c.x * W4, ay = c.y * H4;
  const top = c.boxY != null ? c.boxY * H4 : Math.min(SAFE.bottom - bh, Math.max(CO.minTop, ay - bh * 0.62 - 610));
  const roomRight = SAFE.right - bw - CO.reach - ax;     // elbow-to-dot room with the box on the right
  const roomLeft = ax - (SAFE.left + bw + CO.reach);     // ... with the box at the left margin
  const onRight = (c.side ?? "right") === "right"
    ? roomRight >= CO.clear || roomRight >= roomLeft
    : !(roomLeft >= CO.clear || roomLeft >= roomRight);
  const bx = onRight ? SAFE.right - bw : SAFE.left;
  const sx = onRight ? bx : bx + bw, sy = top + bh * 0.62;
  const ex = onRight ? sx - CO.reach : sx + CO.reach, ey = sy;
  const pt = c.path?.length ? pathAt(c.path, s) : null;
  const dx = pt ? pt.x * W4 : ax, dy = pt ? pt.y * H4 : ay;
  const rs = pt ? CO.trackedRing / CO.ring : 1;   // tracked target scale (same rule as FdCallout)
  const vx = dx - ex, vy = dy - ey, len = Math.hypot(vx, vy), stop = CO.ring * rs + 10;
  const tx = len > stop ? dx - (vx / len) * stop : ex, ty = len > stop ? dy - (vy / len) * stop : ey;
  const total = Math.hypot(tx - ex, ty - ey) + Math.abs(ex - sx);
  const d = `M${tx} ${ty} L${ex} ${ey} L${sx} ${sy}`;   // drawn from the dot back to the box
  const dash = { strokeDasharray: `${total} ${total + 40}`, strokeDashoffset: total * (1 - line) };

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, opacity: out }}>
      <svg width={W4} height={H4} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
        {line > 0.001 ? (
          <>
            <path d={d} fill="none" stroke={`rgba(0,0,0,${CO.leaderUnderAlpha})`} strokeWidth={pt ? CO.trackedLeaderUnder : CO.leaderUnder} strokeLinecap="round" strokeLinejoin="round" {...dash} />
            <path d={d} fill="none" stroke="#fff" strokeWidth={pt ? CO.trackedLeader : CO.leader} strokeLinecap="round" strokeLinejoin="round" {...dash} />
          </>
        ) : null}
        <circle cx={dx} cy={dy} r={CO.halo * rs * dotK * (1 + 0.08 * Math.sin(f0 / 5))} fill={C.accent} fillOpacity={0.2} />
        <circle cx={dx} cy={dy} r={CO.ring * rs * dotK} fill="rgba(15,16,20,.45)" stroke={C.accent} strokeWidth={8 * rs * Math.min(1, dotK)} />
        <circle cx={dx} cy={dy} r={CO.core * rs * dotK} fill="#fff" />
      </svg>
      <div style={{ position: "absolute", left: bx, top, width: bw, height: bh, boxSizing: "border-box", padding: `${CO.padT}px ${CO.padX}px ${CO.padB}px`, whiteSpace: "nowrap",
                    ...panel(false, CO.radius), opacity: Math.min(1, boxK * 1.2),
                    transform: `translateX(${(1 - Math.min(1, boxK)) * (onRight ? 36 : -36)}px) scale(${0.96 + 0.04 * boxK})`, transformOrigin: onRight ? "left center" : "right center" }}>
        <div style={{ ...font(labelSt), lineHeight: 1, color: C.ink84 }}><span style={{ color: C.accent }}>[</span>{labelText.slice(1, -1)}<span style={{ color: C.accent }}>]</span></div>
        {liveItems ? (
          <div style={{ display: "flex", alignItems: "baseline", gap: CO.unitGap, marginTop: CO.labelGap, height: rowH, lineHeight: 0.9 }}>
            {liveItems.map((it, i) => (
              <React.Fragment key={i}>
                <span style={font(VAL)}>
                  {it.num.split(/(\d+)/).filter(Boolean).map((part, k) => (
                    <React.Fragment key={k}>{/\d/.test(part) ? part : <span style={LINING}>{part}</span>}</React.Fragment>
                  ))}
                </span>
                {it.unit ? <span style={{ ...font(UNIT), color: C.ink72, marginRight: i < liveItems.length - 1 ? CO.pairGap : 0 }}>{it.unit}</span> : null}
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div style={{ ...font(txtSt), lineHeight: 1.05, marginTop: CO.labelGap }}>{c.text}</div>
        )}
        {c.sub ? <div style={{ ...font(subSt), lineHeight: 1.1, marginTop: CO.subGap, color: C.ink84 }}>{c.sub}</div> : null}
      </div>
    </div>
  );
};
