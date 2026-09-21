/**
 * Supercar Experience "se-booking" pack: stage, clock, text styles, surfaces and small parts.
 *
 * Every length is px on the 2160x3840 design canvas (work/se_redesign/designs/booking-luxury,
 * tokens.css); SeStage scales the layer when the composition is not 4K. Colours, sizes, layout
 * and copy come from SE in ../tokens.ts. Text widths come from ../measure.ts, so these
 * components are rendered only after useBrandFonts() reports the face ready (BrandMotion).
 * No side effects at import.
 */
import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SE } from "../tokens";
import { textWidth, type TextStyle } from "../measure";
import type { BrandCopyOverride } from "../types";

export const W4 = 2160;
export const H4 = 3840;
export const C = SE.color;
export const T = SE.type;
export const L = SE.layout;
export const SAFE = SE.space.safe;
export const FONT = SE.font.text;
export const LOGOS = SE.logos;

export const clampX = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const easeOut = Easing.out(Easing.cubic);
export const easeIn = Easing.in(Easing.cubic);
export const easeInOut = Easing.inOut(Easing.cubic);

export const useClock = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  return { frame, fps, s: frame / fps, duration: durationInFrames / fps };
};

/** 0 -> 1 as x goes from a to b, clamped (seconds or frames). */
export const ramp = (x: number, a: number, b: number, easing: (t: number) => number = easeOut): number =>
  b <= a ? (x >= a ? 1 : 0) : interpolate(x, [a, b], [0, 1], { ...clampX, easing });

/** 2160x3840 layer; children use design px directly. */
export const SeStage: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { height } = useVideoConfig();
  const k = height / H4;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: H4, transformOrigin: "0 0", transform: k === 1 ? undefined : `scale(${k})`,
                  fontFamily: FONT, color: C.ink, WebkitFontSmoothing: "antialiased", textRendering: "geometricPrecision", pointerEvents: "none" }}>
      {children}
    </div>
  );
};

/* ---------- type ---------- */
export const ts = (size: number, weight: number, tracking = 0, tabular = false): TextStyle => ({ size, weight, tracking, tabular, family: FONT });
export const withSize = (t: TextStyle, size: number): TextStyle => ({ ...t, size });
export const font = (t: TextStyle): React.CSSProperties => ({
  fontFamily: t.family, fontSize: t.size, fontWeight: t.weight,
  letterSpacing: t.tracking ? `${t.tracking}em` : undefined,
  fontVariantNumeric: t.tabular ? "tabular-nums lining-nums" : undefined,
});

/** Largest size <= t.size (and >= min) at which every text fits max. */
export const fitSize = (texts: string[], t: TextStyle, max: number, min: number): TextStyle => {
  const widest = Math.max(1, ...texts.map((x) => textWidth(x, t)));
  return widest <= max ? t : withSize(t, Math.max(min, +((t.size * max) / widest).toFixed(2)));
};

/** Tighten tracking (not below minTracking), then shrink the size (not below minSize) until text fits max. */
export const fitTracking = (text: string, t: TextStyle, max: number, minTracking: number, minSize: number = T.floor): TextStyle => {
  const full = textWidth(text, t);
  if (full <= max) return t;
  const n = Math.max(1, [...text].length);
  const base = full - n * (t.tracking ?? 0) * t.size;
  const tracking = Math.min(t.tracking ?? 0, Math.max(minTracking, (max - base) / (n * t.size)));
  return fitSize([text], { ...t, tracking: +tracking.toFixed(4) }, max, minSize);
};

/** Site habit: [ How It Works ], set in caps. */
export const bracket = (text: string) => `[ ${text.replace(/^\s*\[\s*/, "").replace(/\s*\]\s*$/, "").toUpperCase()} ]`;
export const LABEL = ts(T.label, 700, 0.2);
export const LABEL_MUTED = ts(T.label, 600, 0.2);
/** Counting numbers only: Overused Grotesk's tnum also widens "." and "-", so running text uses LINING. */
export const TABULAR: React.CSSProperties = { fontVariantNumeric: "tabular-nums lining-nums" };
export const LINING: React.CSSProperties = { fontVariantNumeric: "lining-nums" };

/** "**bold**" spans inside a line. */
export const rich = (s: string) =>
  s.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((p) => (p.length > 4 && p.startsWith("**") && p.endsWith("**") ? { bold: true, text: p.slice(2, -2) } : { bold: false, text: p }));
export const plain = (s: string) => rich(s).map((p) => p.text).join("");

/* ---------- surfaces ---------- */
/** glass = rails and callouts (footage reads through a little); solid = words and booking actions. */
export const panel = (solid: boolean, radius: number): React.CSSProperties => ({
  background: solid ? SE.surface.solid : SE.surface.glass, borderRadius: radius, boxShadow: SE.surface.shadow,
});

/** Line that rises out of its own mask. Padding keeps ascenders and descenders unclipped. */
export const Mask: React.FC<{ k: number; size: number; gapTop?: number; children?: React.ReactNode }> = ({ k, size, gapTop = 0, children }) => {
  const padT = size * 0.14, padB = size * 0.3;
  return (
    <div style={{ overflow: "hidden", paddingTop: padT, paddingBottom: padB, marginTop: gapTop - padT, marginBottom: -padB }}>
      <div style={{ transform: `translateY(${(1 - Math.min(1, Math.max(0, k))) * 160}%)` }}>{children}</div>
    </div>
  );
};

/* ---------- icons (24-unit strokes from the design's build.py) ---------- */
type Icon = React.FC<{ size: number; color: string }>;
export const ArrowRight: Icon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
    <path d="M4.5 12h15M13.5 6l6 6-6 6" />
  </svg>
);
export const ArrowUpRight: Icon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
    <path d="M6.5 17.5l11-11M8.5 6.5h9v9" />
  </svg>
);
export const InstagramGlyph: Icon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} style={{ display: "block", flex: "none" }}>
    <rect x="3" y="3" width="18" height="18" rx="5.2" /><circle cx="12" cy="12" r="4.1" /><circle cx="17.4" cy="6.6" r="1.15" fill={color} stroke="none" />
  </svg>
);
export const YoutubeGlyph: Icon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" style={{ display: "block", flex: "none" }}>
    <rect x="2.5" y="5.5" width="19" height="13" rx="3.6" stroke={color} strokeWidth={2} /><path d="M10.2 9.2v5.6l4.8-2.8z" fill={color} />
  </svg>
);
export const Check: Icon = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" style={{ display: "block", flex: "none" }}>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </svg>
);

/* ---------- parts ---------- */
export const AgeChip: React.FC<{ text: string; size: number }> = ({ text, size }) => (
  <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", flex: "none", boxSizing: "border-box", height: Math.round(size * 1.58),
                 padding: `0 ${Math.round(size * 0.42)}px`, borderRadius: 14, border: `4px solid ${C.accent}`, color: C.accent, fontSize: size, fontWeight: 800,
                 letterSpacing: "0.02em", lineHeight: 1, whiteSpace: "nowrap", ...TABULAR }}>{text}</span>
);

/** Light pill with the orange arrow disc (site "Book" button). */
export const BookButton: React.FC<{ text: string; h: number; size: number; padL: number; padR: number; gap: number; disc: number; icon: number; discK?: number }> = ({ text, h, size, padL, padR, gap, disc, icon, discK = 1 }) => (
  <div style={{ display: "inline-flex", alignItems: "center", gap, height: h, boxSizing: "border-box", borderRadius: h / 2, padding: `0 ${padR}px 0 ${padL}px`,
                background: C.light, color: C.ground, ...font(ts(size, 700, -0.01)), lineHeight: 1, whiteSpace: "nowrap", flex: "none" }}>
    <span>{text}</span>
    <span style={{ width: disc, height: disc, borderRadius: disc / 2, background: C.accent, display: "flex", alignItems: "center", justifyContent: "center", flex: "none",
                   transform: `scale(${0.6 + 0.4 * discK})` }}>
      <ArrowRight size={icon} color={C.ground} />
    </span>
  </div>
);

/* ---------- copy ---------- */
export type SeCopy = {
  site: string; phone: string; handle: string; ageRule: string; ageChip: string; ageDetail: string;
  cta: string; bookLabel: string; textUs: string; questions: string; locationsLabel: string;
  tagline: [string, string]; locations: [string, string][]; soon: string | null;
};
const normLoc = (l: string | readonly string[]): [string, string] => {
  if (typeof l !== "string") return [l[0] ?? "", l[1] ?? ""];
  const i = l.lastIndexOf(",");
  return i < 0 ? [l.trim(), ""] : [l.slice(0, i).trim(), l.slice(i + 1).trim()];
};
/** Brand copy from tokens with the props `brandCopy` overrides applied. */
export const seCopy = (o: BrandCopyOverride | undefined): SeCopy => {
  const d = SE.copy;
  const locs: readonly (string | readonly string[])[] = o?.locations ?? d.locations;
  return {
    site: o?.site ?? d.site, phone: o?.phone ?? d.phone, handle: o?.handle ?? d.handle,
    ageRule: o?.ageRule ?? d.ageRule, ageChip: o?.ageChip ?? d.ageChip, ageDetail: o?.ageDetail ?? d.ageDetail,
    cta: o?.cta ?? d.cta, bookLabel: o?.bookLabel ?? d.bookLabel, textUs: o?.textUs ?? d.textUs, questions: o?.questions ?? d.questions,
    locationsLabel: o?.locationsLabel ?? d.locationsLabel,
    tagline: o?.tagline ? [o.tagline[0] ?? "", o.tagline[1] ?? ""] : [d.tagline[0], d.tagline[1]],
    locations: locs.map(normLoc),
    soon: o?.soon !== undefined ? o.soon : d.soon,
  };
};
