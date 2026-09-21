/**
 * Formula Dynamics "fd-telemetry" pack: stage, clock, type, haze, scale rule, reticle, stripe, lamp, copy.
 *
 * Every length is px on the 2160x3840 design canvas (work/fd_redesign/designs/telemetry, telemetry.css);
 * FdStage scales the layer when the composition is not 4K. Colours, sizes, layout and copy come from FD in
 * ../tokens.ts. Bebas Neue only (caps-only face: copy is upper-cased before it is measured and drawn), white
 * type with a soft shadow and no strokes, FD red #FE0F13 only as the live signal. Text widths come from
 * ../measure.ts, so these components render only after useBrandFonts() reports the face ready (BrandMotion).
 * No side effects at import.
 */
import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FD } from "../tokens";
import { textWidth, type TextStyle } from "../measure";
import type { BrandCopyOverride } from "../types";

export const W4 = 2160;
export const H4 = 3840;
export const C = FD.color;
export const T = FD.type;
export const L = FD.layout;
export const HZ = FD.haze;
export const TM = FD.timing;
export const SPACE = FD.space;
export const LOGOS = FD.logos;
export const FONT = FD.font.display;
export const SHADOW = FD.shadow.text;

export const clampX = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const easeOut = Easing.out(Easing.cubic);
export const easeIn = Easing.in(Easing.cubic);
export const linear = (t: number) => t;

export const useClock = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  return { frame, fps, s: frame / fps, duration: durationInFrames / fps };
};

/** 0 -> 1 as x goes from a to b, clamped (seconds or frames). */
export const ramp = (x: number, a: number, b: number, easing: (t: number) => number = easeOut): number =>
  b <= a ? (x >= a ? 1 : 0) : interpolate(x, [a, b], [0, 1], { ...clampX, easing });

/** 2160x3840 layer; children use design px directly. */
export const FdStage: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { height } = useVideoConfig();
  const k = height / H4;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, transformOrigin: "0 0", transform: k === 1 ? undefined : `scale(${k})`,
                  fontFamily: FONT, fontWeight: 400, color: C.white, fontVariantNumeric: "tabular-nums", WebkitFontSmoothing: "antialiased",
                  textRendering: "geometricPrecision", pointerEvents: "none" }}>
      {children}
    </div>
  );
};

/* ---------- type ---------- */
export const up = (s: string | undefined | null) => (s ?? "").toUpperCase();
export const ts = (size: number, tracking = 0): TextStyle => ({ size, weight: 400, tracking, family: FONT });
export const withSize = (t: TextStyle, size: number): TextStyle => ({ ...t, size });
export const font = (t: TextStyle): React.CSSProperties => ({
  fontFamily: t.family, fontSize: t.size, fontWeight: 400, letterSpacing: t.tracking ? `${t.tracking}em` : 0,
});
export const tw = (text: string, t: TextStyle) => textWidth(text, t);

/** Largest size <= t.size (and >= min) at which every text fits max. */
export const fitSize = (texts: string[], t: TextStyle, max: number, min: number): TextStyle => {
  const widest = Math.max(1, ...texts.map((x) => textWidth(x, t)));
  return widest <= max ? t : withSize(t, Math.max(min, +((t.size * max) / widest).toFixed(2)));
};

/** Types `text` on: the first n characters show, the rest keep their space (nothing reflows). */
export const TypeOn: React.FC<{ text: string; k: number }> = ({ text, k }) => {
  const chars = [...text];
  const n = Math.round(Math.min(1, Math.max(0, k)) * chars.length);
  if (n >= chars.length) return <>{text}</>;
  return (<><span>{chars.slice(0, n).join("")}</span><span style={{ opacity: 0 }}>{chars.slice(n).join("")}</span></>);
};

/* ---------- haze ---------- */
export type Feather = number | { l: number; r: number; t: number; b: number };
export type HazeBox = { l: number; r: number; t: number; b: number; f?: number; fl?: number; fr?: number; ft?: number; fb?: number };

/**
 * Feathered haze: rgba(8,8,10,alpha) inside two intersecting linear-gradient masks (no edge, no border, no radius),
 * optionally with the 60 px graph grid (white 7.5%) aligned to the canvas grid. x/y/w/h = the haze box in canvas px.
 */
export const Haze: React.FC<{ x: number; y: number; w: number; h: number; alpha: number; feather: Feather; grid?: boolean; opacity?: number }> = ({ x, y, w, h, alpha, feather, grid = false, opacity = 1 }) => {
  if (opacity <= 0 || alpha <= 0 || w <= 0 || h <= 0) return null;
  const f = typeof feather === "number" ? { l: feather, r: feather, t: feather, b: feather } : feather;
  const mask = `linear-gradient(to right, transparent 0px, #000 ${f.l}px, #000 ${Math.max(f.l, w - f.r)}px, transparent ${w}px), ` +
               `linear-gradient(to bottom, transparent 0px, #000 ${f.t}px, #000 ${Math.max(f.t, h - f.b)}px, transparent ${h}px)`;
  const tint = `linear-gradient(rgba(${HZ.tint},${alpha}), rgba(${HZ.tint},${alpha}))`;
  const cell = HZ.gridCell;
  const gx = -(((x % cell) + cell) % cell), gy = -(((y % cell) + cell) % cell);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, opacity,
                  backgroundImage: grid ? `linear-gradient(${HZ.grid} 2px, transparent 2px), linear-gradient(90deg, ${HZ.grid} 2px, transparent 2px), ${tint}` : tint,
                  backgroundSize: grid ? `${cell}px ${cell}px, ${cell}px ${cell}px, 100% 100%` : "100% 100%",
                  backgroundPosition: grid ? `${gx}px ${gy}px, ${gx}px ${gy}px, 0 0` : "0 0",
                  WebkitMaskImage: mask, maskImage: mask, WebkitMaskComposite: "source-in", maskComposite: "intersect" }} />
  );
};

/** Haze around a content rectangle using a token bleed box. */
export const hazeAround = (x: number, y: number, w: number, h: number, box: HazeBox) => ({
  x: x - box.l, y: y - box.t, w: w + box.l + box.r, h: h + box.t + box.b,
  feather: { l: box.fl ?? box.f ?? 100, r: box.fr ?? box.f ?? 100, t: box.ft ?? box.f ?? 100, b: box.fb ?? box.f ?? 100 },
});

/* ---------- scale rule (telemetry.js port) ---------- */
/**
 * Graduated rule: baseline 4 px white 62%, minor ticks 3 x `tick` every `minor` px (white 42%), major ticks
 * 5 x `majorH` at fractions (white, or red while flashing), elapsed part 6 px white + red needle 8 x 76 at `progress`,
 * red first part of the width (`red`, the brand's short rule) 8 px thick. `draw` reveals it from `from`.
 */
export const ScaleRule: React.FC<{
  w: number; h?: number; minor?: number; tick?: number; majorH?: number; majors?: number[]; flash?: number | null;
  progress?: number | null; red?: number | null; draw?: number; from?: "left" | "right"; style?: React.CSSProperties;
}> = ({ w, h = 36, minor = 24, tick = 16, majorH = 42, majors = [], flash = null, progress = null, red = null, draw = 1, from = "left", style }) => {
  const d = Math.min(1, Math.max(0, draw));
  const minors: number[] = [];
  for (let x = 0; x <= w + 0.5; x += minor) minors.push(Math.min(x, w - 3));
  const clip = from === "left" ? `inset(-60px ${(1 - d) * 100}% -60px -20px)` : `inset(-60px -20px -60px ${(1 - d) * 100}%)`;
  return (
    <div style={{ position: "relative", width: w, height: h, clipPath: d >= 1 ? undefined : clip, ...style }}>
      {d > 0 ? (
        <svg width={w} height={Math.max(majorH, tick) + 10} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", filter: "drop-shadow(0 2px 6px rgba(0,0,0,.45))" }}>
          {minors.map((x, i) => <rect key={`m${i}`} x={x} y={4} width={3} height={tick} fill="#fff" fillOpacity={0.42} />)}
          <rect x={0} y={0} width={w} height={4} fill="#fff" fillOpacity={0.62} />
          {progress != null ? <rect x={0} y={-1} width={w * progress} height={6} fill="#fff" /> : null}
          {majors.map((f, i) => <rect key={`M${i}`} x={Math.max(0, Math.min(w - 5, f * w - 2.5))} y={0} width={5} height={majorH} fill={flash === i ? C.red : "#fff"} />)}
          {red != null ? <rect x={0} y={-2} width={w * red} height={8} fill={C.red} /> : null}
          {progress != null ? <rect x={w * progress - 4} y={-30} width={8} height={76} fill={C.red} /> : null}
        </svg>
      ) : null}
    </div>
  );
};

/* ---------- small parts ---------- */
/** Red live square (timing-screen lamp). */
export const Lamp: React.FC<{ size?: number; on?: boolean; style?: React.CSSProperties }> = ({ size = 30, on = true, style }) => (
  <span style={{ display: "inline-block", width: size, height: size, background: C.red, flex: "none", opacity: on ? 1 : 0, ...style }} />
);

/** Five-part FD stripe in the logo's proportions (red, black, white, green, yellow). `k` grows it from the left. */
export const Stripe: React.FC<{ w: number; h: number; k?: number; style?: React.CSSProperties }> = ({ w, h, k = 1, style }) => {
  let x = 0;
  return (
    <div style={{ position: "relative", width: w, height: h, clipPath: k >= 1 ? undefined : `inset(0 ${(1 - Math.max(0, k)) * 100}% 0 0)`, ...style }}>
      {FD.stripe.map(([color, frac], i) => {
        const left = x; x += frac * w;
        return <div key={i} style={{ position: "absolute", left, top: 0, width: frac * w + (i < FD.stripe.length - 1 ? 0.5 : 0), height: h, background: color }} />;
      })}
    </div>
  );
};

/** Haze alpha for a callout or CTA: its props `haze` (tools/fd_element_haze.py) clamped to 0..elementMax, else the panel default. */
export const elementHaze = (v: number | undefined): number =>
  v != null && Number.isFinite(v) ? Math.min(HZ.elementMax, Math.max(0, v)) : HZ.panel;

/**
 * Reticle at (cx, cy) in an SVG: ring (r from `ringFrom` to `ring`, white 55%, 4 px), four 5 x 40 arms that
 * slide in from 1.5x their distance, red centre dot. k values 0-1. `scale` enlarges ring, arms, strokes and dot
 * (tracked callouts, which move over busy footage).
 */
export const Reticle: React.FC<{ cx: number; cy: number; ringK: number; armK: number; dotK: number; scale?: number }> = ({ cx, cy, ringK, armK, dotK, scale = 1 }) => {
  const R = L.callout;
  const r = (R.ringFrom + (R.ring - R.ringFrom) * ringK) * scale;
  const at = R.armAt * scale * (1.5 - 0.5 * armK);
  const arm = R.arm * scale;
  const aw = R.armW * Math.max(1, scale * 0.9);
  const hw = aw / 2;
  return (
    <g transform={`translate(${cx} ${cy})`}>
      <circle r={r} fill="none" stroke="#fff" strokeOpacity={0.55 * Math.min(1, ringK * 2)} strokeWidth={4 * Math.max(1, scale)} />
      <g opacity={armK}>
        <rect x={-hw} y={-at - arm} width={aw} height={arm} fill="#fff" />
        <rect x={-hw} y={at} width={aw} height={arm} fill="#fff" />
        <rect x={-at - arm} y={-hw} width={arm} height={aw} fill="#fff" />
        <rect x={at} y={-hw} width={arm} height={aw} fill="#fff" />
      </g>
      <circle r={R.dot * scale * Math.max(0, dotK)} fill={C.red} />
    </g>
  );
};

/* ---------- copy ---------- */
export type FdCopy = { site: string; handle: string; cta: string; how: string; kicker: string; tagline: string };
/** Brand copy from tokens with the props `brandCopy` overrides applied (a tagline pair is joined with a space). */
export const fdCopy = (o: BrandCopyOverride | undefined): FdCopy => {
  const d = FD.copy;
  return {
    site: o?.site ?? d.site, handle: o?.handle ?? d.handle, cta: o?.cta ?? d.cta, how: o?.how ?? d.how, kicker: o?.kicker ?? d.kicker,
    tagline: o?.tagline ? o.tagline.filter(Boolean).join(" ") : d.tagline,
  };
};

/** mm:ss of a reel second. */
export const clock = (s: number) => {
  const t = Math.max(0, Math.floor(s));
  return `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
};
