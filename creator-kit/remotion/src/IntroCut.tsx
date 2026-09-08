import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import { loadFonts } from "./fonts";
import { theme } from "./theme";

loadFonts();

/**
 * Cold-open intro cut from the reel's own footage. The footage underneath is
 * a montage (built by ffmpeg): ten micro-shots, then the key shot held.
 * This overlay adds what the references do on top of that:
 *   - a typewriter title: small sans line, then a big italic serif line,
 *     with a blinking cursor;
 *   - the key shot opening from a letterbox strip to full frame;
 *   - a warm light leak sweeping over the settled title;
 *   - a tag line that says what the video is.
 */
export type IntroCutProps = {
  small: string; big: string; tag?: string;
  montageEnd: number;        // seconds; where the held shot starts
  durationSeconds?: number; overlayOnly?: boolean; src?: string;
};
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
const typed = (text: string, t: number, from: number, to: number) => {
  const n = Math.round(interpolate(t, [from, to], [0, text.length], clamp)); return text.slice(0, n);
};

export const IntroCut: React.FC<IntroCutProps> = ({ small, big, tag, montageEnd, overlayOnly = true }) => {
  const frame = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig(); const t = frame / fps;
  const smallF = H * 0.0165, bigF = H * 0.074;
  const sTxt = typed(small, t, 0.15, 0.95), bTxt = typed(big, t, 1.05, 2.55);
  const bigDone = t >= 2.55;
  const cursorOn = Math.floor(t * 3) % 2 === 0 && t < 4.2;
  // Letterbox: the held shot arrives as a strip and opens up.
  const open = interpolate(t, [montageEnd, montageEnd + 0.75], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const bar = t < montageEnd ? 0 : H * 0.34 * (1 - open);
  // Light leak: one warm pass, left to right.
  const leakP = interpolate(t, [3.2, 4.3], [-0.7, 1.4], { ...clamp, easing: Easing.inOut(Easing.quad) });
  const leakOn = t > 3.2 && t < 4.3;
  const tagIn = interpolate(t, [3.5, 3.95], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
      {bar > 0 ? <>
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: bar, background: "#000" }} />
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: bar, background: "#000" }} />
      </> : null}
      {leakOn ? (
        <div style={{ position: "absolute", top: -H * 0.3, height: H * 1.6, width: W * 0.9, left: leakP * W, transform: "rotate(-14deg)", mixBlendMode: "screen", opacity: 0.7,
                      background: `linear-gradient(90deg, rgba(251,209,1,0) 0%, rgba(251,209,1,.55) 35%, rgba(231,85,34,.6) 55%, rgba(255,255,255,.25) 70%, rgba(231,85,34,0) 100%)` }} />
      ) : null}
      <div style={{ position: "absolute", left: W * 0.08, right: W * 0.08, top: H * 0.44, textAlign: "center", color: "#fff", textShadow: "0 2px 18px rgba(0,0,0,.75), 0 0 2px rgba(0,0,0,.9)" }}>
        <div style={{ fontFamily: "Archivo, Helvetica, sans-serif", fontWeight: 500, fontSize: smallF, letterSpacing: "0.04em", minHeight: smallF * 1.3 }}>
          {sTxt}{t < 1.05 && cursorOn ? <span style={{ display: "inline-block", width: 3, height: smallF, background: "#fff", verticalAlign: "-0.15em", marginLeft: 3 }} /> : null}
        </div>
        <div style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontStyle: "italic", fontSize: bigF, lineHeight: 1.05, letterSpacing: "-0.005em", minHeight: bigF * 1.1, marginTop: smallF * 0.2 }}>
          {bTxt}{t >= 1.05 && cursorOn ? <span style={{ display: "inline-block", width: 4, height: bigF * 0.8, background: "#fff", verticalAlign: "-0.08em", marginLeft: 6 }} /> : null}
        </div>
        {tag ? (
          <div style={{ marginTop: smallF * 1.1, fontFamily: "Archivo, Helvetica, sans-serif", fontWeight: 600, fontSize: smallF * 0.85, letterSpacing: "0.18em", textTransform: "uppercase", color: theme.accent, opacity: tagIn, transform: `translateY(${(1 - tagIn) * 10}px)` }}>{tag}</div>
        ) : null}
        {bigDone ? null : null}
      </div>
    </AbsoluteFill>
  );
};
