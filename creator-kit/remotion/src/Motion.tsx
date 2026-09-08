import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { loadFonts } from "./fonts";
import { theme } from "./theme";
import type { Word } from "./data/captions";

loadFonts();

/**
 * Motion-graphics variant of the reel overlay. Everything animates: the
 * title is a kinetic reveal, captions are laid out per phrase with a key
 * word set large, spec callouts draw a leader line and roll their numbers
 * up, the lower third is a skewed bar with a light sweep, and the outro
 * cascades the CTA letter by letter under the end card.
 */
export type Callout = { at: number; hold: number; x: number; y: number; label: string; value: number; suffix?: string; side?: "left" | "right" };
export type MotionProps = {
  src: string; words: Word[]; durationSeconds?: number; overlayOnly?: boolean;
  title?: { eyebrow: string; line1: string; line2: string; until: number };
  callouts?: Callout[];
  lowerThird?: { at: number; hold: number; title: string; sub: string };
  chapters?: { at: number; label: string }[];
  outro?: { at: number; cta: string; endCardSrc?: string };
  emphasis?: string[];
  /** Timeline positions of the edit's cuts; a caption phrase never spans one. */
  cuts?: { at: number }[];
};

const RED = theme.accentAlt, GOLD = theme.accent;
const ANTON = "Anton, Impact, sans-serif", ARCHIVO = "Archivo, Helvetica, sans-serif";
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

/* ---------- Title: masked line reveals, sweeping bar, slide-out ---------- */
const TitleReveal: React.FC<{ t: { eyebrow: string; line1: string; line2: string; until: number } }> = ({ t }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  if (s > t.until + 0.5) return null;
  const l1 = spring({ frame: frame - 2, fps, config: { damping: 16, stiffness: 120 }, durationInFrames: 22 });
  const l2 = spring({ frame: frame - 8, fps, config: { damping: 16, stiffness: 120 }, durationInFrames: 22 });
  const bar = spring({ frame: frame - 14, fps, config: { damping: 20, stiffness: 140 }, durationInFrames: 18 });
  const eye = interpolate(frame, [0, 16], [0, 1], clamp);
  const out = interpolate(s, [t.until - 0.4, t.until], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const big = H * 0.155, small = H * 0.07;
  return (
    <div style={{ position: "absolute", left: W * 0.067, top: H * 0.20, right: W * 0.09, opacity: 1 - out, transform: `translateY(${-out * H * 0.06}px)` }}>
      <div style={{ fontFamily: ARCHIVO, fontWeight: 600, fontSize: H * 0.0125, letterSpacing: "0.2em", textTransform: "uppercase", color: "#fff",
                    clipPath: `inset(0 ${(1 - eye) * 100}% 0 0)`, textShadow: "0 2px 12px rgba(0,0,0,.8)", marginBottom: H * 0.012 }}>{t.eyebrow}</div>
      <div style={{ overflow: "hidden", height: big * 1.02 }}>
        <div style={{ fontFamily: ANTON, fontSize: big, lineHeight: 1, color: "#fff", textTransform: "uppercase", letterSpacing: "-0.01em",
                      transform: `translateY(${(1 - l1) * 110}%)`, WebkitTextStroke: `${big * 0.02}px rgba(0,0,0,.9)`, paintOrder: "stroke fill",
                      textShadow: "0 12px 40px rgba(0,0,0,.6)" }}>{t.line1}</div>
      </div>
      <div style={{ overflow: "hidden", height: small * 1.08 }}>
        <div style={{ fontFamily: ANTON, fontSize: small, lineHeight: 1, color: GOLD, textTransform: "uppercase", letterSpacing: "0.06em",
                      transform: `translateY(${(1 - l2) * 110}%)`, WebkitTextStroke: `${small * 0.02}px rgba(0,0,0,.9)`, paintOrder: "stroke fill" }}>{t.line2}</div>
      </div>
      <div style={{ height: H * 0.006, width: W * 0.42, background: RED, marginTop: H * 0.012, transformOrigin: "left", transform: `scaleX(${bar})` }} />
    </div>
  );
};

/* ---------- Kinetic captions: per-phrase layout with one key word set large ---------- */
const toPhrases = (words: Word[], breaks: number[]) => {
  const out: Word[][] = []; let cur: Word[] = [];
  for (const w of words) {
    const prev = cur[cur.length - 1];
    const crossesCut = prev ? breaks.some((b) => b > prev.start && b <= w.start) : false;
    if (cur.length && (w.start - prev.end > 0.7 || cur.length >= 5 || crossesCut)) { out.push(cur); cur = []; }
    cur.push(w);
  }
  if (cur.length) out.push(cur);
  return out;
};
const KineticCaptions: React.FC<{ words: Word[]; emphasis: string[]; after: number; breaks: number[] }> = ({ words, emphasis, after, breaks }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  const phrases = toPhrases(words.filter((w) => w.start >= after), breaks);
  const ph = phrases.find((p) => s >= p[0].start && s < p[p.length - 1].end + 0.45);
  if (!ph) return null;
  const clean = (x: string) => x.replace(/[^a-z0-9]/gi, "").toUpperCase();
  let key = ph.reduce((a, b) => (clean(b.text).length > clean(a.text).length ? b : a));
  const emph = ph.find((w) => emphasis.includes(clean(w.text))); if (emph) key = emph;
  const end = ph[ph.length - 1].end;
  const out = interpolate(s, [end + 0.15, end + 0.45], [0, 1], { ...clamp, easing: Easing.in(Easing.quad) });
  const small = H * 0.026, bigF = H * 0.082;
  return (
    <div style={{ position: "absolute", left: W * 0.067, right: W * 0.09, top: H * 0.62, display: "flex", flexWrap: "wrap", alignItems: "baseline",
                  gap: `${H * 0.006}px ${W * 0.018}px`, opacity: 1 - out, transform: `translateY(${-out * H * 0.05}px)` }}>
      {ph.map((w, i) => {
        const isKey = w === key;
        const inS = spring({ frame: frame - Math.round(w.start * fps), fps, config: { damping: 12, stiffness: 240, mass: 0.7 }, durationInFrames: 12 });
        const active = s >= w.start && s < w.end;
        const under = active ? interpolate(s, [w.start, Math.max(w.start + 0.12, w.end)], [0, 1], clamp) : s >= w.end ? 1 : 0;
        return (
          <span key={i} style={{ position: "relative", display: "inline-block", opacity: inS, transform: `translateY(${(1 - inS) * H * 0.02}px) scale(${0.7 + 0.3 * inS}) rotate(${isKey ? -2.5 : 0}deg)`, transformOrigin: "left bottom",
                                 fontFamily: isKey ? ANTON : ARCHIVO, fontWeight: isKey ? 400 : 800, fontSize: isKey ? bigF : small, lineHeight: 1,
                                 textTransform: "uppercase", color: isKey ? GOLD : "#fff", letterSpacing: isKey ? "0.01em" : "0.04em",
                                 WebkitTextStroke: `${(isKey ? bigF : small) * 0.05}px rgba(0,0,0,.92)`, paintOrder: "stroke fill", textShadow: "0 6px 24px rgba(0,0,0,.6)" }}>
            {w.text}
            {!isKey ? <span style={{ position: "absolute", left: 0, right: 0, bottom: -small * 0.18, height: small * 0.12, background: RED, transformOrigin: "left", transform: `scaleX(${under})` }} /> : null}
          </span>
        );
      })}
    </div>
  );
};

/* ---------- Callout: pulsing dot, drawn leader line, rolling counter ---------- */
const CalloutView: React.FC<{ c: Callout }> = ({ c }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  if (s < c.at || s > c.at + c.hold + 0.4) return null;
  const f0 = frame - Math.round(c.at * fps);
  const dot = spring({ frame: f0, fps, config: { damping: 10, stiffness: 300 }, durationInFrames: 10 });
  const line = interpolate(f0, [4, 18], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const box = spring({ frame: f0 - 12, fps, config: { damping: 14, stiffness: 160 }, durationInFrames: 16 });
  const count = f0 >= 40 ? c.value : interpolate(f0, [14, 40], [0, c.value], { ...clamp, easing: Easing.out(Easing.exp) });
  const out = interpolate(s, [c.at + c.hold, c.at + c.hold + 0.35], [1, 0], clamp);
  const pulse = 1 + 0.25 * Math.sin(f0 / 4);
  const x = c.x * W, y = c.y * H, right = (c.side ?? "right") === "right";
  const dx = right ? W * 0.16 : -W * 0.16, dy = -H * 0.07;
  const bx = x + dx * line, by = y + dy * line;
  const r = H * 0.006, lab = H * 0.012, num = H * 0.05;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: out, pointerEvents: "none" }}>
      <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0 }}>
        <circle cx={x} cy={y} r={r * 2.6 * pulse} fill="none" stroke={GOLD} strokeWidth={r * 0.35} opacity={0.6 * dot} />
        <circle cx={x} cy={y} r={r * dot} fill={GOLD} />
        <line x1={x} y1={y} x2={bx} y2={by} stroke="#fff" strokeWidth={r * 0.45} strokeLinecap="round" />
        <line x1={bx} y1={by} x2={bx + (right ? W * 0.05 : -W * 0.05) * line} y2={by} stroke="#fff" strokeWidth={r * 0.45} strokeLinecap="round" />
      </svg>
      <div style={{ position: "absolute", left: right ? bx + W * 0.055 : undefined, right: right ? undefined : W - bx + W * 0.055, top: by - num * 0.9,
                    transform: `scale(${0.85 + 0.15 * box})`, transformOrigin: right ? "left center" : "right center", opacity: box,
                    background: "rgba(10,10,10,.78)", borderLeft: right ? `${r}px solid ${GOLD}` : undefined, borderRight: right ? undefined : `${r}px solid ${GOLD}`,
                    padding: `${num * 0.18}px ${num * 0.35}px`, borderRadius: r, boxShadow: "0 10px 40px rgba(0,0,0,.5)" }}>
        <div style={{ fontFamily: ARCHIVO, fontWeight: 600, fontSize: lab, letterSpacing: "0.16em", textTransform: "uppercase", color: "#cfcfcf" }}>{c.label}</div>
        <div style={{ fontFamily: ANTON, fontSize: num, lineHeight: 1.05, color: "#fff", fontVariantNumeric: "tabular-nums" }}>
          {c.value >= 100 ? Math.round(count) : count.toFixed(1)}<span style={{ color: GOLD, fontSize: num * 0.55, marginLeft: num * 0.1 }}>{c.suffix ?? ""}</span>
        </div>
      </div>
    </div>
  );
};

/* ---------- Lower third: skewed red bar with a light sweep ---------- */
const LowerThird: React.FC<{ l: { at: number; hold: number; title: string; sub: string } }> = ({ l }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  if (s < l.at || s > l.at + l.hold + 0.5) return null;
  const f0 = frame - Math.round(l.at * fps);
  const inS = spring({ frame: f0, fps, config: { damping: 15, stiffness: 130 }, durationInFrames: 20 });
  const sub = spring({ frame: f0 - 8, fps, config: { damping: 15, stiffness: 130 }, durationInFrames: 20 });
  const out = interpolate(s, [l.at + l.hold, l.at + l.hold + 0.4], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const sweep = ((f0 * 3) % 140) / 100;
  const tf = H * 0.03, sf = H * 0.014;
  return (
    <div style={{ position: "absolute", left: 0, top: H * 0.755, transform: `translateX(${(-1 + inS + out * -1) * 100}%)` }}>
      <div style={{ position: "relative", background: RED, transform: "skewX(-12deg)", transformOrigin: "left bottom", marginLeft: -W * 0.02,
                    padding: `${tf * 0.35}px ${W * 0.06}px ${tf * 0.35}px ${W * 0.09}px`, overflow: "hidden", boxShadow: "0 12px 40px rgba(0,0,0,.45)" }}>
        <div style={{ position: "absolute", top: 0, bottom: 0, width: W * 0.05, left: `${sweep * 100}%`, background: "linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.35),rgba(255,255,255,0))" }} />
        <div style={{ transform: "skewX(12deg)", fontFamily: ANTON, fontSize: tf, lineHeight: 1, color: "#fff", textTransform: "uppercase", letterSpacing: "0.02em" }}>{l.title}</div>
      </div>
      <div style={{ background: "rgba(12,12,12,.85)", transform: `skewX(-12deg) translateX(${(1 - sub) * -40}%)`, transformOrigin: "left top", marginLeft: -W * 0.02, opacity: sub,
                    padding: `${sf * 0.5}px ${W * 0.05}px ${sf * 0.5}px ${W * 0.09}px`, display: "inline-block" }}>
        <div style={{ transform: "skewX(12deg)", fontFamily: ARCHIVO, fontWeight: 600, fontSize: sf, letterSpacing: "0.16em", textTransform: "uppercase", color: GOLD }}>{l.sub}</div>
      </div>
    </div>
  );
};

/* ---------- Chapter bar: three ticks, a marker that rides the timeline ---------- */
const ChapterBar: React.FC<{ chapters: { at: number; label: string }[] }> = ({ chapters }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W, durationInFrames } = useVideoConfig(); const s = frame / fps; const total = durationInFrames / fps;
  const p = s / total; const cur = [...chapters].reverse().find((c) => s >= c.at);
  const inS = interpolate(frame, [0, 20], [0, 1], clamp);
  const left = W * 0.2, width = W * 0.6, top = H * 0.145, h = H * 0.0035;
  return (
    <div style={{ position: "absolute", left, top, width, opacity: inS }}>
      <div style={{ position: "relative", height: h, background: "rgba(255,255,255,.28)", borderRadius: h }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${p * 100}%`, background: GOLD, borderRadius: h }} />
        {chapters.map((c, i) => <div key={i} style={{ position: "absolute", left: `${(c.at / total) * 100}%`, top: -h, width: h * 0.8, height: h * 3, background: "#fff", borderRadius: 1 }} />)}
        <div style={{ position: "absolute", left: `${p * 100}%`, top: -h * 2, width: h * 5, height: h * 5, marginLeft: -h * 2.5, borderRadius: "50%", background: "#fff", boxShadow: "0 0 12px rgba(0,0,0,.6)" }} />
      </div>
      <div style={{ marginTop: h * 3, fontFamily: ARCHIVO, fontWeight: 600, fontSize: H * 0.011, letterSpacing: "0.18em", textTransform: "uppercase", color: "#fff", textShadow: "0 2px 10px rgba(0,0,0,.8)", textAlign: "center" }}>{cur?.label ?? ""}</div>
    </div>
  );
};

/* ---------- Outro: end card fades up, CTA cascades letter by letter ---------- */
const Outro: React.FC<{ o: { at: number; cta: string; endCardSrc?: string } }> = ({ o }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  if (s < o.at) return null;
  const f0 = frame - Math.round(o.at * fps);
  const card = interpolate(f0, [0, 18], [0, 1], clamp);
  const fs = H * 0.034; const letters = o.cta.split(""); const g0 = o.cta.indexOf("SF90");
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {o.endCardSrc ? <Img src={staticFile(o.endCardSrc)} style={{ position: "absolute", inset: 0, width: W, height: H, opacity: card }} /> : null}
      <div style={{ position: "absolute", left: W * 0.067, right: W * 0.09, top: H * 0.70, fontFamily: ANTON, fontSize: fs, justifyContent: "center", textAlign: "center", lineHeight: 1.05, textTransform: "uppercase", color: "#fff",
                    WebkitTextStroke: `${fs * 0.04}px rgba(0,0,0,.9)`, paintOrder: "stroke fill", textShadow: "0 8px 30px rgba(0,0,0,.7)", display: "flex", flexWrap: "wrap" }}>
        {letters.map((ch, i) => {
          const k = spring({ frame: f0 - 6 - i * 1.2, fps, config: { damping: 12, stiffness: 260 }, durationInFrames: 10 });
          return <span key={i} style={{ display: "inline-block", whiteSpace: "pre", opacity: k, transform: `translateY(${(1 - k) * fs * 0.6}px)`, color: g0 >= 0 && i >= g0 && i < g0 + 4 ? GOLD : undefined }}>{ch}</span>;
        })}
      </div>
    </div>
  );
};

export const Motion: React.FC<MotionProps> = ({ src, words, overlayOnly = false, title, callouts, lowerThird, chapters, outro, emphasis = [], cuts = [] }) => (
  <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
    {overlayOnly ? null : <OffthreadVideo src={src.startsWith("http") ? src : staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
    {chapters?.length ? <ChapterBar chapters={chapters} /> : null}
    {title ? <TitleReveal t={title} /> : null}
    <KineticCaptions words={words} emphasis={emphasis} after={title?.until ?? 0} breaks={cuts.map((c) => c.at)} />
    {(callouts ?? []).map((c, i) => <CalloutView key={i} c={c} />)}
    {lowerThird ? <LowerThird l={lowerThird} /> : null}
    {outro ? <Outro o={outro} /> : null}
  </AbsoluteFill>
);
