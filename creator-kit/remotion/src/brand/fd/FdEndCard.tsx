import React from "react";
import { Img, staticFile } from "remotion";
import { C, L, LOGOS, ScaleRule, T, TypeOn, W4, H4, fitSize, font, linear, ramp, ts, up, useClock, type FdCopy } from "./kit";

const EC = L.endCard;
const TAG = ts(T.endTagline, 0.22);
const CTA = ts(T.endCta, 0);
const HOW = ts(T.endHow, 0.08);
const WEB = ts(T.endWeb, 0.12);

/**
 * End card (new, replaces Outro; outro.endCardSrc and outro.cta are ignored): hard cut to a 100% opaque #08080A ground at
 * outro.at, masked 120/480 px graph grid (10 f), stacked FD logo 760 wide at y 640 (12 f), tagline 86 px .22em at y 1550
 * (types over 30 f). Judge fix: no dyno curve; the CTA block moves up into its place: "BOOK YOUR BUILD" 190 px at y 1850,
 * a 720 px rule with its red first third, "DM US YOUR MODEL" 92 px, then site and handle 84 px .12em in white (the card's
 * act-on lines; they were 68 px grey). Every centred line fits 1380 px, so it stays inside x 390..1770, left of Instagram's
 * action column. Everything ends above y 2960. The corner bug and chapter bar are already gone from outro.at.
 */
export const FdEndCard: React.FC<{ at: number; copy: FdCopy }> = ({ at, copy }) => {
  const { frame, fps } = useClock();
  const f0 = frame - Math.round(at * fps);
  if (f0 < 0) return null;
  const tag = up(copy.tagline), cta = up(copy.cta), how = up(copy.how), site = up(copy.site), handle = up(copy.handle);
  const tagSt = fitSize([tag], TAG, EC.maxW, 56);
  const ctaSt = fitSize([cta], CTA, EC.maxW, 110);
  const howSt = fitSize([how], HOW, EC.maxW, 60);
  const webSt = fitSize([site, handle], WEB, EC.maxW, 56);
  const logoH = EC.logoW / LOGOS.stackedAspect;
  const centered = (t: { tracking?: number }): React.CSSProperties => ({
    position: "absolute", left: 0, width: W4, textAlign: "center", whiteSpace: "nowrap", boxSizing: "border-box",
    paddingLeft: t.tracking ? `${t.tracking}em` : undefined,   // balance the tracking after the last letter
  });
  const up24 = (a: number, b: number): React.CSSProperties => {
    const v = ramp(f0, a, b);
    return { opacity: v, transform: `translateY(${(1 - v) * 24}px)` };
  };
  const grid = "rgba(255,255,255,.085)", fine = "rgba(255,255,255,.035)";
  const mask = "radial-gradient(ellipse 80% 60% at 50% 46%, #000 30%, transparent 100%)";

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, background: C.ink }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, opacity: ramp(f0, 0, 10),
                    backgroundImage: `linear-gradient(${grid} 2px, transparent 2px), linear-gradient(90deg, ${grid} 2px, transparent 2px), linear-gradient(${fine} 2px, transparent 2px), linear-gradient(90deg, ${fine} 2px, transparent 2px)`,
                    backgroundSize: "480px 480px, 480px 480px, 120px 120px, 120px 120px", backgroundPosition: "120px 0, 120px 0, 120px 0, 120px 0",
                    WebkitMaskImage: mask, maskImage: mask }} />
      <Img src={staticFile(LOGOS.stacked)} style={{ position: "absolute", left: (W4 - EC.logoW) / 2, top: EC.logoTop, width: EC.logoW, height: logoH, opacity: ramp(f0, 2, 14) }} />
      <div style={{ ...centered(tagSt), top: EC.tagTop, ...font(tagSt), lineHeight: 1 }}><TypeOn text={tag} k={ramp(f0, 10, 40, linear)} /></div>
      <div style={{ ...centered(ctaSt), top: EC.ctaTop, ...font(ctaSt), lineHeight: 0.82, ...up24(28, 38) }}>{cta}</div>
      <div style={{ position: "absolute", left: (W4 - EC.ruleW) / 2, top: EC.ruleTop }}>
        <ScaleRule w={EC.ruleW} h={EC.ruleH} minor={24} red={1 / 3} draw={ramp(f0, 32, 44)} />
      </div>
      <div style={{ ...centered(howSt), top: EC.howTop, ...font(howSt), lineHeight: 1, ...up24(36, 46) }}>{how}</div>
      <div style={{ ...centered(webSt), top: EC.webTop, ...font(webSt), lineHeight: EC.webLine, color: C.white, ...up24(42, 50) }}>{site}<br />{handle}</div>
    </div>
  );
};
