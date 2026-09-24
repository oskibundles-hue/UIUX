import React from "react";
import type { BrandCta } from "../types";
import { C, H4, L, Lamp, SHADOW, SPACE, ScaleRule, T, TM, TypeOn, easeIn, elementHaze, fitSize, font, hazeAround, Haze, linear, ramp, ts, tw, up, useClock, type FdCopy } from "./kit";

const CT = L.cta;
const KICK = ts(T.ctaKicker, 0.18);
const ACT = ts(T.ctaAction, 0);
const HOW = ts(T.ctaHow, 0.06);
const HANDLE = ts(T.ctaHandle, 0.1);

/**
 * Website CTA (mid-roll): kicker (brand name) in white 80% behind a red live lamp blinking at 2 Hz (red stays on the lamp,
 * the live signal: red kicker type measured ~2:1 on bright plates), the action "VISIT THE SITE" at 250 px, a rule with its
 * red first third, "DM US YOUR MODEL" 110 px, then the SITE in white 76 px and the handle 76 px grey; haze with the graph
 * grid (alpha: props `haze` from tools/fd_element_haze.py, else the panel default). Default slot = the lower-third slot,
 * bottom edge at y 2940 (or `y`, 0-1). Captions and the chapter bar yield for 8 f around it (FdMotion). Motion: haze 8 f,
 * kicker types 10 f, action clips in 12 f, rule 14 f, how, site and handle type in that order; out 8 f fade.
 *
 * 2026-09-23: this was a BOOKING CTA ("NOW BOOKING" / "BOOK YOUR BUILD", handle only, no site). Formula Dynamics does not
 * take bookings -- the ask is the website, so the site line is drawn here and the booking words are gone. See FD.copy.
 */
export const FdCta: React.FC<{ c: BrandCta; copy: FdCopy }> = ({ c, copy }) => {
  const { frame, fps, s } = useClock();
  if (s < c.at || s > c.at + c.hold + 0.4) return null;
  const atF = Math.round(c.at * fps);
  const f0 = frame - atF;
  const endF = Math.round((c.at + c.hold) * fps) - atF;
  const out = ramp(f0, endF, endF + TM.outFrames, easeIn);
  if (out >= 1) return null;

  const maxW = SPACE.rail - SPACE.side;
  const kick = up(copy.kicker), act = up(copy.cta), how = up(copy.how), site = up(copy.site), handle = up(copy.handle);
  const kickSt = fitSize([kick], KICK, maxW - 30 - CT.lampGap, 48);
  const actSt = fitSize([act], ACT, maxW, 150);
  const howSt = fitSize([how], HOW, maxW, 64);
  const webSt = fitSize([site, handle], HANDLE, maxW, 48);
  const w = Math.ceil(Math.max(30 + CT.lampGap + tw(kick, kickSt), tw(act, actSt), tw(how, howSt), tw(site, webSt), tw(handle, webSt)));
  const h = T.ctaKicker + CT.actGap + actSt.size * 0.82 + CT.ruleGap + CT.ruleH + CT.howGap + howSt.size
          + CT.handleGap + webSt.size + CT.handleGap * 0.5 + webSt.size;
  const bottom = (c.y ?? CT.bottom / H4) * H4;
  const top = bottom - h;
  const lampOn = Math.floor((Math.max(0, f0) * 4) / fps) % 2 === 0;   // 2 Hz

  const hazeK = ramp(f0, 0, 8);
  const kickK = ramp(f0, 0, 10, linear);
  const actK = ramp(f0, 4, 16);
  const ruleK = ramp(f0, 12, 26);
  const howK = ramp(f0, 18, 18 + Math.max(1, [...how].length), linear);
  const siteK = ramp(f0, 22, 22 + Math.ceil([...site].length / 2), linear);
  const handleK = ramp(f0, 26, 26 + Math.ceil([...handle].length / 2), linear);
  const hz = hazeAround(CT.left, top, w, h, CT.haze);

  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", opacity: 1 - out }}>
      <Haze {...hz} alpha={elementHaze(c.haze)} grid opacity={hazeK} />
      <div style={{ position: "absolute", left: CT.left, top, width: w, whiteSpace: "nowrap", textShadow: SHADOW }}>
        <div style={{ display: "flex", alignItems: "center", gap: CT.lampGap, height: T.ctaKicker, ...font(kickSt), lineHeight: 1, color: C.kicker }}>
          <Lamp on={lampOn} /><span><TypeOn text={kick} k={kickK} /></span>
        </div>
        <div style={{ ...font(actSt), lineHeight: 0.82, marginTop: CT.actGap, clipPath: actK >= 1 ? undefined : `inset(-20% ${(1 - actK) * 100}% -40% -4%)` }}>{act}</div>
        <ScaleRule w={w} h={CT.ruleH} minor={CT.minor} red={1 / 3} draw={ruleK} style={{ marginTop: CT.ruleGap }} />
        <div style={{ ...font(howSt), lineHeight: 1, marginTop: CT.howGap }}><TypeOn text={how} k={howK} /></div>
        <div style={{ ...font(webSt), lineHeight: 1, marginTop: CT.handleGap, color: C.white }}><TypeOn text={site} k={siteK} /></div>
        <div style={{ ...font(webSt), lineHeight: 1, marginTop: CT.handleGap * 0.5, color: C.sub }}><TypeOn text={handle} k={handleK} /></div>
      </div>
    </div>
  );
};
