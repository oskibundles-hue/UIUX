import React from "react";
import { spring } from "remotion";
import type { BrandTitleFields } from "../types";
import { textWidth } from "../measure";
import { C, L, LABEL, Mask, SAFE, T, W4, bracket, easeIn, fitSize, fitTracking, font, ramp, ts, useClock, withSize } from "./kit";

export type SeTitleSpec = { eyebrow: string; line1: string; line2: string; until: number } & BrandTitleFields;

const TL = L.title;
const H1 = ts(T.titleLine, 700, -0.035);
const H2 = ts(T.titleLine, 300, -0.035);
const ROUTE = ts(T.route, 600, 0.22);

/** Top scrim (#0F1014 40% -> 82% at 560-1500 -> 0 at 2300). Drawn under the chapter bar and the bug. */
export const SeTitleScrim: React.FC<{ t: SeTitleSpec }> = ({ t }) => {
  const { fps, s } = useClock();
  if (s > t.until + 0.5) return null;
  const a = ramp(s, 0, 6 / fps) * (1 - ramp(s, t.until - 0.4, t.until + 0.1, easeIn));
  if (a <= 0) return null;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: TL.scrim, opacity: a,
                  background: "linear-gradient(180deg,rgba(15,16,20,.40) 0px,rgba(15,16,20,.82) 560px,rgba(15,16,20,.82) 1500px,rgba(15,16,20,0) 2300px)" }} />
  );
};

/**
 * Title card (restyled TitleReveal): orange bracket label from `eyebrow`, line 1 at 260 px 700,
 * line 2 at 260 px 300 white 84% (both shrink together to the safe width), optional route row
 * (orange dot, city, orange-to-white line, white ring, city). Copy is shown as written: author
 * sentence case for this pack. Lines rise out of masks; out over 0.4 s before `until` with a lift.
 */
export const SeTitle: React.FC<{ t: SeTitleSpec }> = ({ t }) => {
  const { frame, fps, s } = useClock();
  if (s > t.until + 0.5) return null;
  const out = ramp(s, t.until - 0.4, t.until, easeIn);
  if (out >= 1) return null;
  const maxW = SAFE.right - SAFE.left;
  const labelText = t.eyebrow ? bracket(t.eyebrow) : "";
  const labelSt = fitTracking(labelText, LABEL, maxW, 0.12);
  const size = Math.min(fitSize([t.line1], H1, maxW, 120).size, t.line2 ? fitSize([t.line2], H2, maxW, 120).size : T.titleLine);
  const eye = ramp(frame, 0, 14);
  const l1 = spring({ frame: frame - 2, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 24 });
  const l2 = spring({ frame: frame - 8, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 24 });

  const route = (t.route ?? []).filter(Boolean).map((r) => r.toUpperCase());
  const links = Math.max(0, route.length - 1);
  const cityW = route.reduce((a, r) => a + textWidth(r, ROUTE), 0);
  const gaps = Math.max(0, 1 + 3 * links) * TL.routeItemGap;
  const lineLen = links ? Math.max(TL.routeLineMin, Math.min(TL.routeLine, (maxW - cityW - TL.dot - links * TL.ring - gaps) / links)) : 0;

  return (
    <div style={{ position: "absolute", left: TL.left, top: TL.top, opacity: 1 - out, transform: `translateY(${-out * 40}px)`, whiteSpace: "nowrap" }}>
      {labelText ? <div style={{ ...font(labelSt), lineHeight: 1, color: C.accent, clipPath: `inset(-20% ${(1 - eye) * 100}% -20% 0)` }}>{labelText}</div> : null}
      <Mask k={l1} size={size} gapTop={labelText ? TL.labelGap : 0}>
        <div style={{ ...font(withSize(H1, size)), lineHeight: 0.92 }}>{t.line1}</div>
      </Mask>
      {t.line2 ? (
        <Mask k={l2} size={size}>
          <div style={{ ...font(withSize(H2, size)), lineHeight: 0.98, color: C.ink84 }}>{t.line2}</div>
        </Mask>
      ) : null}
      {route.length ? (
        <div style={{ display: "flex", alignItems: "center", gap: TL.routeItemGap, marginTop: TL.routeGap, ...font(ROUTE), lineHeight: 1 }}>
          {route.map((city, i) => {
            const d = 14 + i * 12;
            const pop = ramp(frame, d, d + 6);
            return (
              <React.Fragment key={i}>
                {i > 0 ? <span style={{ display: "block", flex: "none", width: lineLen, height: 4, background: `linear-gradient(90deg,${C.accent},rgba(255,255,255,.8))`,
                                        transformOrigin: "left center", transform: `scaleX(${ramp(frame, d - 8, d + 2)})` }} /> : null}
                {i === 0
                  ? <span style={{ display: "block", flex: "none", width: TL.dot, height: TL.dot, borderRadius: TL.dot / 2, background: C.accent, transform: `scale(${pop})` }} />
                  : <span style={{ display: "block", flex: "none", width: TL.ring, height: TL.ring, boxSizing: "border-box", borderRadius: TL.ring / 2, border: `${TL.ringStroke}px solid #fff`, transform: `scale(${pop})` }} />}
                <span style={{ display: "inline-block", opacity: ramp(frame, d + 2, d + 10) }}>{city}</span>
              </React.Fragment>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};
