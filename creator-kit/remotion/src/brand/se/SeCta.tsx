import React from "react";
import { Img, spring, staticFile } from "remotion";
import type { BrandCta } from "../types";
import { AgeChip, BookButton, C, H4, L, LABEL_MUTED, LINING, LOGOS, Mask, T, bracket, easeIn, fitSize, fitTracking, font, panel, ramp, ts, useClock, type SeCopy } from "./kit";

const CT = L.cta;
const BTN = CT.button;
const HEAD = ts(T.ctaHead, 700, -0.025);
const ALT = ts(T.ctaAlt, 500);
const AGE = ts(T.age, 500);

/**
 * Booking CTA (new, mid-roll): solid card, marque + "[ Las Vegas · Scottsdale · Boise ]",
 * "Book your supercar." 134 px, light pill button (site 66 px + orange arrow disc), "or text us" + phone 62 px,
 * hairline, then the 25+ age chip and "Renter must be 25+" at 62 px, white 84%. The act-on lines are 62-66 px
 * (phone-scale review: 48 px at 4K is ~8.7 pt on a phone). Copy from the brand table.
 * Bottom edge at 2896 (or `y`). Captions yield while it holds (SeMotion).
 */
export const SeCta: React.FC<{ c: BrandCta; copy: SeCopy }> = ({ c, copy }) => {
  const { frame, fps, s } = useClock();
  if (s < c.at || s > c.at + c.hold + 0.5) return null;
  const f0 = frame - Math.round(c.at * fps);
  const inK = spring({ frame: f0, fps, config: { damping: 18, stiffness: 140 }, durationInFrames: 20 });
  const headK = spring({ frame: f0 - 4, fps, config: { damping: 18, stiffness: 130 }, durationInFrames: 22 });
  const discK = spring({ frame: f0 - 12, fps, config: { damping: 10, stiffness: 220 }, durationInFrames: 14 });
  const rowK = ramp(f0, 9, 21);
  const ruleK = ramp(f0, 14, 26);
  const out = ramp(s, c.at + c.hold, c.at + c.hold + 0.4, easeIn);

  const inner = CT.width - 2 * CT.padX;
  const labelText = bracket(copy.locations.map((l) => l[0]).join(" · "));
  const labelSt = fitTracking(labelText, LABEL_MUTED, inner - CT.marqueW - CT.topGap, 0.12);
  const headSt = fitSize([copy.cta], HEAD, inner, 96);
  const bottom = (c.y ?? CT.bottom / H4) * H4;

  return (
    <div style={{ position: "absolute", left: CT.left, bottom: H4 - bottom, width: CT.width, boxSizing: "border-box", padding: `${CT.padT}px ${CT.padX}px ${CT.padB}px`,
                  ...panel(true, CT.radius), whiteSpace: "nowrap", opacity: Math.min(1, inK * 1.3) * (1 - out), transform: `translateY(${(1 - Math.min(1, inK)) * 60 + out * 30}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: CT.topGap }}>
        <Img src={staticFile(LOGOS.marque)} style={{ display: "block", flex: "none", width: CT.marqueW, height: CT.marqueW / LOGOS.marqueAspect }} />
        <span style={{ ...font(labelSt), lineHeight: 1, color: C.ink72 }}>{labelText}</span>
      </div>
      <Mask k={headK} size={headSt.size} gapTop={CT.headGap}>
        <div style={{ ...font(headSt), lineHeight: 1 }}>{copy.cta}</div>
      </Mask>
      <div style={{ marginTop: CT.rowGap, display: "flex", alignItems: "center", gap: CT.rowItemGap, opacity: rowK, transform: `translateY(${(1 - rowK) * 20}px)` }}>
        <BookButton text={copy.site} h={BTN.h} size={T.ctaButton} padL={BTN.padL} padR={BTN.padR} gap={BTN.gap} disc={BTN.disc} icon={BTN.icon} discK={discK} />
        <div style={{ ...font(ALT), lineHeight: 1.16, color: C.ink72 }}>
          {copy.textUs}<br /><b style={{ fontWeight: 600, color: C.ink, ...LINING }}>{copy.phone}</b>
        </div>
      </div>
      <div style={{ marginTop: CT.ruleGap, paddingTop: CT.rulePad, borderTop: `2px solid ${C.hair}`, display: "flex", alignItems: "center", gap: CT.ageGap,
                    ...font(AGE), lineHeight: 1.1, color: C.ink84, opacity: ruleK }}>
        <AgeChip text={copy.ageChip} size={T.age} />
        <span>{copy.ageRule}</span>
      </div>
    </div>
  );
};
