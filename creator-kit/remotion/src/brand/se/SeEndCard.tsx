import React from "react";
import { Img, spring, staticFile } from "remotion";
import { AgeChip, BookButton, C, H4, InstagramGlyph, L, LABEL, LABEL_MUTED, LINING, LOGOS, Mask, T, W4, bracket, easeInOut, fitSize, font, ramp, ts, useClock, withSize, type SeCopy } from "./kit";

const EC = L.endCard;
const TAG_B = ts(T.endTagline, 700, -0.028);
const TAG_L = ts(T.endTagline, 300, -0.028);
const PHONE = ts(T.endPhone, 500);
const LOC = ts(T.endLocation, 600, -0.015);
const STATE = ts(T.endState, 600, 0.26);
const SOON = ts(T.endSoon, 500);
const HANDLE = ts(T.endHandle, 600, -0.01);
const AGE = ts(T.endAge, 500);
const AGE_DETAIL = ts(T.endAgeDetail, 500);
const withStop = (x: string) => (/[.!?]$/.test(x) ? x : `${x}.`);

/**
 * End card (new, replaces Outro; outro.endCardSrc and outro.cta are ignored): the #0F1014 ground
 * fades in over 18 frames and is then 100% opaque (judge fix). Column at x 145: logo 1420 wide,
 * tagline (700 / 300 white 72%), rule, "[ Book your supercar ]" + button, "Questions? Text us"
 * + phone (62 px), rule, "[ Locations ]" with city / state columns, optional `soon` line, Instagram
 * handle (64 px), then the age chip + age rule (62 px, white 84%) and, only when copy.ageDetail is set,
 * the detail on its own line (56 px, white 72%). The corner bug and chapter bar are already gone from outro.at.
 */
export const SeEndCard: React.FC<{ at: number; copy: SeCopy }> = ({ at, copy }) => {
  const { frame, fps } = useClock();
  const f0 = frame - Math.round(at * fps);
  if (f0 < 0) return null;
  const ground = ramp(f0, 0, 18, easeInOut);
  const up = (d: number): React.CSSProperties => {
    const v = ramp(f0, d, d + 10);
    return { opacity: v, transform: `translateY(${(1 - v) * 28}px)` };
  };
  const tagSize = Math.min(fitSize([copy.tagline[0]], TAG_B, EC.width, 110).size, fitSize([copy.tagline[1]], TAG_L, EC.width, 110).size);
  const t1 = spring({ frame: f0 - 10, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 22 });
  const t2 = spring({ frame: f0 - 15, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 22 });
  const ageRule = copy.ageRule.trim() ? withStop(copy.ageRule.trim()) : "";
  const ageDetail = copy.ageDetail.trim() ? withStop(copy.ageDetail.trim()) : "";

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4 }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, background: C.endGround, opacity: ground }} />
      <div style={{ position: "absolute", left: EC.left, top: EC.top, width: EC.width }}>
        <div style={up(6)}>
          <Img src={staticFile(LOGOS.lockup)} style={{ display: "block", width: EC.logoWidth, height: EC.logoWidth / LOGOS.lockupAspect }} />
        </div>
        <div style={{ marginTop: EC.tagGap, whiteSpace: "nowrap" }}>
          <Mask k={t1} size={tagSize}><div style={{ ...font(withSize(TAG_B, tagSize)), lineHeight: 1 }}>{copy.tagline[0]}</div></Mask>
          <Mask k={t2} size={tagSize} gapTop={EC.tagLineGap}><div style={{ ...font(withSize(TAG_L, tagSize)), lineHeight: 1, color: C.ink72 }}>{copy.tagline[1]}</div></Mask>
        </div>
        <div style={{ height: 2, background: C.hair, margin: `${EC.rule1[0]}px 0 ${EC.rule1[1]}px`, transformOrigin: "left center", transform: `scaleX(${ramp(f0, 16, 30)})` }} />
        <div style={{ ...font(LABEL), lineHeight: 1, color: C.accent, whiteSpace: "nowrap", ...up(18) }}>{bracket(copy.bookLabel)}</div>
        <div style={{ marginTop: EC.gap, ...up(20) }}>
          <BookButton text={copy.site} h={156} size={T.endButton} padL={70} padR={20} gap={34} disc={118} icon={58} />
        </div>
        <div style={{ marginTop: EC.gap, ...font(PHONE), lineHeight: 1.2, color: C.ink72, whiteSpace: "nowrap", ...up(22) }}>
          {copy.questions} <b style={{ fontWeight: 600, color: C.ink, ...LINING }}>{copy.phone}</b>
        </div>
        <div style={{ height: 2, background: C.hair, margin: `${EC.rule2[0]}px 0 ${EC.rule2[1]}px`, transformOrigin: "left center", transform: `scaleX(${ramp(f0, 22, 36)})` }} />
        <div style={{ ...font(LABEL_MUTED), lineHeight: 1, color: C.ink72, whiteSpace: "nowrap", ...up(24) }}>{bracket(copy.locationsLabel)}</div>
        <div style={{ marginTop: EC.gap, display: "grid", gridTemplateColumns: `repeat(${Math.max(1, copy.locations.length)}, 1fr)`, columnGap: 20, ...up(26) }}>
          {copy.locations.map(([city, st], i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column", gap: EC.locGap }}>
              <span style={{ ...font(LOC), lineHeight: 1.1, whiteSpace: "nowrap" }}>{city}</span>
              {st ? <span style={{ ...font(STATE), lineHeight: 1.1, color: C.ink56 }}>{st.toUpperCase()}</span> : null}
            </div>
          ))}
        </div>
        {copy.soon ? <div style={{ marginTop: EC.soonGap, ...font(SOON), lineHeight: 1.2, color: C.ink56, ...up(27) }}>{copy.soon}</div> : null}
        <div style={{ marginTop: EC.footGap, display: "flex", alignItems: "center", gap: 26, ...font(HANDLE), lineHeight: 1.1, ...up(28) }}>
          <InstagramGlyph size={72} color={C.ink} /><span>{copy.handle}</span>
        </div>
        {ageRule || ageDetail ? (
          <div style={{ marginTop: EC.ageGap, ...up(30) }}>
            <div style={{ display: "flex", alignItems: "center", gap: 28, ...font(AGE), lineHeight: 1.1, color: C.ink84, whiteSpace: "nowrap" }}>
              <AgeChip text={copy.ageChip} size={T.endAge} />{ageRule ? <span>{ageRule}</span> : null}
            </div>
            {ageDetail ? (
              <div style={{ marginTop: EC.ageLineGap, maxWidth: EC.ageMaxWidth, ...font(AGE_DETAIL), lineHeight: 1.3, color: C.ink72, textWrap: "balance" } as React.CSSProperties}>{ageDetail}</div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
};
