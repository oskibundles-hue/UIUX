import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate, random } from "remotion";
import { IntroCut } from "./IntroCut";

/**
 * Glitch intro (opt-in; idea 27, reference e76 sam.john.creates; approved by
 * Omarie on 2026-10-27). The default intro (IntroCut) is unchanged.
 * About 1 s of glitch over the reel's opening (pixel squares from the edges,
 * 3 inverted frames, RGB split, sliced bands, white flash), then IntroCut's
 * title and light leak over a blurred, darkened bed, a short glitch out at
 * 5.33 s, and the reel runs on clear to the end (7.5 s by default).
 * The timings are in frames at 30 fps; render it at 30 fps.
 * Sound: scripts/glitch_intro_sound.py (Celina's pack only).
 */
export type GlitchIntroProps = { small: string; big: string; tag?: string; src?: string; durationSeconds?: number };

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
const GLITCH_END = 30;          // frames: the glitch second
const TITLE_FROM = 30;          // IntroCut starts here (its own clock starts at 0)
const OUT_A = 160, OUT_B = 167; // title glitches out over these frames (5.33 to 5.57 s)
const INVERT = new Set([9, 10, 22]);
const CELL = 54;

// RGB split as an SVG filter: red pushed one way, blue the other.
const RgbSplit: React.FC<{ id: string; dx: number; dy?: number }> = ({ id, dx, dy = 0 }) => (
  <svg width={0} height={0} style={{ position: "absolute" }}>
    <filter id={id} x="-5%" y="-5%" width="110%" height="110%" colorInterpolationFilters="sRGB">
      <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
      <feOffset in="r" dx={dx} dy={dy} result="r2" />
      <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
      <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
      <feOffset in="b" dx={-dx} dy={-dy} result="b2" />
      <feBlend in="r2" in2="g" mode="screen" result="rg" />
      <feBlend in="rg" in2="b2" mode="screen" />
    </filter>
  </svg>
);

// How far the channels split on each frame (0 = none).
const splitAt = (f: number) => {
  if (f >= 4 && f <= 7) return 10;
  if (f >= 16 && f <= 28) return 18 + Math.round(random(`dx${f}`) * 26);
  if (f >= OUT_A && f <= OUT_B) return 22;
  return 0;
};

// Pixel squares. Burst A: amber and white, creeping in from both side edges.
// Burst B: mixed colours in a band across the middle, like e76 at 1.3 to 1.5 s.
const Squares: React.FC<{ f: number; W: number; H: number }> = ({ f, W, H }) => {
  const cols = Math.ceil(W / CELL), rows = Math.ceil(H / CELL);
  const out: React.ReactNode[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const k = `${r}-${c}`;
      // Burst A: frames 1 to 14, depth from the nearest side edge.
      const edge = Math.min(c, cols - 1 - c) / (cols / 2);
      const bornA = 1 + edge * 9 + random(`a${k}`) * 4;
      const lifeA = 2 + random(`la${k}`) * 4;
      const inA = f >= bornA && f < bornA + lifeA && f <= 14 && edge < 0.6 && random(`sa${k}`) < 0.8 - edge * 0.9;
      // Burst B: frames 15 to 28, a band around 40 to 62 % of the height.
      const yFrac = r / rows;
      const band = Math.abs(yFrac - 0.51) < 0.11 + random(`bw${c}`) * 0.05;
      const bornB = 15 + random(`b${k}`) * 10;
      const inB = band && f >= bornB && f < bornB + 2 + random(`lb${k}`) * 3 && f <= 28 && random(`sb${k}`) < 0.5;
      if (!inA && !inB) continue;
      const pick = random(`col${k}${f >> 1}`);
      const color = inA
        ? pick < 0.45 ? "#FFD27A" : pick < 0.8 ? "#FBD101" : "#FFFFFF"
        : pick < 0.25 ? "#3DF2FF" : pick < 0.5 ? "#FF3DAE" : pick < 0.75 ? "#FBD101" : "#FFFFFF";
      const s = CELL * (random(`sz${k}`) < 0.3 ? 2 : 1);
      out.push(
        <div key={k} style={{ position: "absolute", left: c * CELL, top: r * CELL, width: s - 4, height: s - 4,
          background: color, opacity: 0.55 + random(`o${k}${f}`) * 0.45, boxShadow: `0 0 ${CELL * 0.5}px ${color}` }} />
      );
    }
  }
  return <AbsoluteFill style={{ mixBlendMode: "screen" }}>{out}</AbsoluteFill>;
};

// Horizontal bands of the frame pushed sideways (frames 18 to 27).
const Slices: React.FC<{ f: number; src: string }> = ({ f, src }) => {
  if (f < 18 || f > 27 || f % 2 === 1) return null;
  const bands = [0, 1, 2].map((i) => {
    const y = random(`sy${f}${i}`) * 0.8 + 0.1, h = 0.03 + random(`sh${f}${i}`) * 0.07;
    const x = (random(`sx${f}${i}`) - 0.5) * 220;
    return { y, h, x };
  });
  return (
    <>
      {bands.map((b, i) => (
        <AbsoluteFill key={i} style={{ clipPath: `inset(${b.y * 100}% 0 ${Math.max(0, 100 - (b.y + b.h) * 100)}% 0)`, transform: `translateX(${b.x}px)` }}>
          <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%" }} />
        </AbsoluteFill>
      ))}
    </>
  );
};

export const GlitchIntro: React.FC<GlitchIntroProps> = ({ small, big, tag, src = "reel.mp4" }) => {
  const f = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const dx = splitAt(f);
  // Title bed: blur and darken the reel while the title is up.
  const bed = interpolate(f, [GLITCH_END, GLITCH_END + 5, OUT_A, OUT_B + 4], [0, 1, 1, 0], clamp);
  const baseFilter = [
    dx ? `url(#split${f})` : "",
    INVERT.has(f) ? "invert(1) contrast(1.2)" : "",
    bed > 0 ? `blur(${bed * 30}px) brightness(${1 - bed * 0.58})` : "",
  ].filter(Boolean).join(" ") || "none";
  const flash = interpolate(f, [27, 29, 33], [0, 1, 0], clamp);
  const titleOpacity = interpolate(f, [OUT_A + 2, OUT_B], [1, 0], clamp);
  const jitter = f >= OUT_A && f <= OUT_B ? (random(`j${f}`) - 0.5) * 60 : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {dx ? <RgbSplit id={`split${f}`} dx={dx} /> : null}
      <AbsoluteFill style={{ filter: baseFilter }}>
        <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%" }} />
        <Slices f={f} src={src} />
      </AbsoluteFill>
      {f <= 28 ? <Squares f={f} W={W} H={H} /> : null}
      {flash > 0 ? <AbsoluteFill style={{ background: "#fff", opacity: flash }} /> : null}
      <AbsoluteFill style={{ opacity: titleOpacity, transform: `translateX(${jitter}px)`, filter: f >= OUT_A && f <= OUT_B ? `url(#split${f})` : "none" }}>
        <Sequence from={TITLE_FROM} layout="none">
          <IntroCut small={small} big={big} tag={tag} montageEnd={99} overlayOnly tagEarly />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
