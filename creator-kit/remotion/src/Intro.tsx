import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { loadFonts } from "./fonts";
import { theme } from "./theme";

loadFonts();

/**
 * Channel intro, 5 seconds. Bands sweep in, the name slams in line by line
 * with a rolling reveal, a gold rule draws under it, the handles ride in on
 * a pill with the avatar, then the bands sweep back out. Renders on black
 * as a standalone bumper, or overlay-only to sit on footage.
 */
export type IntroProps = {
  line1: string; line2: string; sub: string; handles: string[]; avatarSrc?: string;
  overlayOnly?: boolean; durationSeconds?: number;
};
const GOLD = theme.accent, RED = theme.accentAlt;
const ANTON = "Anton, Impact, sans-serif", ARCHIVO = "Archivo, Helvetica, sans-serif";
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

export const Intro: React.FC<IntroProps> = ({ line1, line2, sub, handles, avatarSrc, overlayOnly = false, durationSeconds = 5 }) => {
  const frame = useCurrentFrame(); const { fps, width: W, height: H, durationInFrames } = useVideoConfig();
  const s = frame / fps, end = durationInFrames / fps;
  // Bands: in over the first 0.7 s, out over the last 0.7 s.
  const pin = interpolate(s, [0, 0.7], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const pout = interpolate(s, [end - 0.7, end], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const bandX = (o: number) => (s < end - 0.7 ? interpolate(pin, [0, 1], [-1.6 + o, 1.6 + o]) : interpolate(pout, [0, 1], [-1.6 + o, 1.6 + o]));
  const band = (x: number, color: string, w: number) => (
    <div style={{ position: "absolute", top: -H * 0.2, height: H * 1.4, width: W * w, left: x * W, background: color, transform: "skewX(-18deg)" }} />
  );
  const big = H * 0.13, subF = H * 0.014;
  const l1 = spring({ frame: frame - Math.round(0.45 * fps), fps, config: { damping: 15, stiffness: 140 }, durationInFrames: 22 });
  const l2 = spring({ frame: frame - Math.round(0.65 * fps), fps, config: { damping: 15, stiffness: 140 }, durationInFrames: 22 });
  const rule = spring({ frame: frame - Math.round(1.0 * fps), fps, config: { damping: 20, stiffness: 120 }, durationInFrames: 24 });
  const subIn = interpolate(s, [1.25, 1.6], [0, 1], clamp);
  const pill = spring({ frame: frame - Math.round(1.7 * fps), fps, config: { damping: 13, stiffness: 150 }, durationInFrames: 22 });
  const fade = interpolate(s, [end - 0.9, end - 0.6], [1, 0], clamp);
  const ph = H * 0.05, av = ph * 0.72;
  return (
    <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#0b0b0c" }}>
      {!overlayOnly ? <AbsoluteFill style={{ background: "radial-gradient(60% 40% at 50% 45%, rgba(251,209,1,.10), rgba(0,0,0,0) 70%)" }} /> : null}
      <div style={{ position: "absolute", left: W * 0.09, right: W * 0.09, top: H * 0.34, opacity: fade }}>
        <div style={{ overflow: "hidden", height: big * 1.02 }}>
          <div style={{ fontFamily: ANTON, fontSize: big, lineHeight: 1, color: "#fff", textTransform: "uppercase", letterSpacing: "-0.01em", transform: `translateY(${(1 - l1) * 110}%)`, textShadow: "0 14px 50px rgba(0,0,0,.6)" }}>{line1}</div>
        </div>
        <div style={{ overflow: "hidden", height: big * 1.02 }}>
          <div style={{ fontFamily: ANTON, fontSize: big, lineHeight: 1, color: GOLD, textTransform: "uppercase", letterSpacing: "-0.01em", transform: `translateY(${(1 - l2) * 110}%)` }}>{line2}</div>
        </div>
        <div style={{ height: H * 0.005, width: "100%", background: RED, marginTop: H * 0.014, transformOrigin: "left", transform: `scaleX(${rule})` }} />
        <div style={{ marginTop: H * 0.014, fontFamily: ARCHIVO, fontWeight: 600, fontSize: subF, letterSpacing: "0.22em", textTransform: "uppercase", color: "#d8d8d8", opacity: subIn, transform: `translateY(${(1 - subIn) * 12}px)` }}>{sub}</div>
        <div style={{ marginTop: H * 0.03, display: "inline-flex", alignItems: "center", gap: ph * 0.3, height: ph, padding: `0 ${ph * 0.4}px 0 ${ph * 0.14}px`, borderRadius: ph / 2,
                      background: "rgba(22,22,24,.92)", boxShadow: "0 18px 60px rgba(0,0,0,.55), inset 0 0 0 1px rgba(255,255,255,.06)",
                      opacity: pill, transform: `translateX(${(1 - pill) * -W * 0.08}px)` }}>
          {avatarSrc ? <div style={{ width: av, height: av, borderRadius: "50%", padding: av * 0.05, background: "conic-gradient(from 210deg, #f9ce34, #ee2a7b, #6228d7, #f9ce34)", flex: "none" }}>
            <Img src={staticFile(avatarSrc)} style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", border: `${av * 0.04}px solid #161618`, boxSizing: "border-box" }} />
          </div> : null}
          {handles.map((h, i) => (
            <span key={i} style={{ fontFamily: ARCHIVO, fontWeight: 800, fontSize: ph * 0.3, color: i === 0 ? "#fff" : "#a8a8ad", whiteSpace: "nowrap" }}>{h}</span>
          ))}
        </div>
      </div>
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
        {band(bandX(0.16), RED, 0.5)}{band(bandX(0), GOLD, 0.34)}
      </div>
    </AbsoluteFill>
  );
};
