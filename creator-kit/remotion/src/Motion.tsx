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
export type Callout = { at: number; hold: number; x: number; y: number; label: string; value?: number; text?: string; suffix?: string; side?: "left" | "right" };
export type LowerThirdSpec = { at: number; hold: number; title: string; sub: string };
export type Stamp = { at: number; hold: number; text: string };
export type MotionProps = {
  src: string; words: Word[]; durationSeconds?: number; overlayOnly?: boolean;
  title?: { eyebrow: string; line1: string; line2: string; until: number };
  callouts?: Callout[];
  lowerThird?: LowerThirdSpec;
  lowerThirds?: LowerThirdSpec[];
  /** Rubber-stamp pops: rotated double-border badge with an overshoot. */
  stamps?: Stamp[];
  /** Instagram / YouTube follow cards. */
  follows?: FollowSpec[];
  /** Diagonal wipe bands at every chapter change after the first. */
  wipes?: boolean;
  /** true (default) sets one key word large per phrase; false keeps every word the same size. */
  keyWord?: boolean;
  chapters?: { at: number; label: string }[];
  outro?: { at: number; cta?: string; endCardSrc?: string };
  emphasis?: string[];
  /** Timeline positions of the edit's cuts; a caption phrase never spans one. */
  cuts?: { at: number }[];
};

// Red is the Formula Dynamics / Rosso Corsa red that is actually in the footage, not the theme orange.
const RED = "#DE1A22", GOLD = theme.accent;
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
const KineticCaptions: React.FC<{ words: Word[]; emphasis: string[]; after: number; until: number; breaks: number[]; keyWord: boolean }> = ({ words, emphasis, after, until, breaks, keyWord }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  if (s >= until) return null;
  const phrases = toPhrases(words.filter((w) => w.start >= after), breaks);
  const ph = phrases.find((p) => s >= p[0].start && s < p[p.length - 1].end + 0.45);
  if (!ph) return null;
  const clean = (x: string) => x.replace(/[^a-z0-9]/gi, "").toUpperCase();
  let key = ph.reduce((a, b) => (clean(b.text).length > clean(a.text).length ? b : a));
  const emph = ph.find((w) => emphasis.includes(clean(w.text))); if (emph) key = emph;
  const end = ph[ph.length - 1].end;
  const out = interpolate(s, [end + 0.15, end + 0.45], [0, 1], { ...clamp, easing: Easing.in(Easing.quad) });
  // Uniform captions: smaller and lower (72.6% of frame height, his measured caption line).
  const small = keyWord ? H * 0.026 : H * 0.0235, bigF = H * 0.082;
  return (
    <div style={{ position: "absolute", left: W * 0.067, right: W * 0.09, top: keyWord ? H * 0.62 : H * 0.705, display: "flex", flexWrap: "wrap", alignItems: "baseline",
                  gap: `${H * 0.006}px ${W * 0.018}px`, opacity: 1 - out, transform: `translateY(${-out * H * 0.05}px)` }}>
      {ph.map((w, i) => {
        const isKey = keyWord && w === key;
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
  const val = c.value ?? 0;
  const count = f0 >= 40 ? val : interpolate(f0, [14, 40], [0, val], { ...clamp, easing: Easing.out(Easing.exp) });
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
        {c.text != null ? (
          <div style={{ fontFamily: ANTON, fontSize: num * 0.62, lineHeight: 1.1, color: "#fff", textTransform: "uppercase", letterSpacing: "0.02em", maxWidth: W * 0.30, textWrap: "balance" as never }}>{c.text}</div>
        ) : (
          <div style={{ fontFamily: ANTON, fontSize: num, lineHeight: 1.05, color: "#fff", fontVariantNumeric: "tabular-nums" }}>
            {val >= 100 ? Math.round(count) : count.toFixed(1)}<span style={{ color: GOLD, fontSize: num * 0.55, marginLeft: num * 0.1 }}>{c.suffix ?? ""}</span>
          </div>
        )}
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
  // Left-aligned and short enough to stay clear of the corner logo bug on the right.
  const left = W * 0.067, width = W * 0.46, top = H * 0.145, h = H * 0.0035;
  return (
    <div style={{ position: "absolute", left, top, width, opacity: inS }}>
      <div style={{ position: "relative", height: h, background: "rgba(255,255,255,.28)", borderRadius: h }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${p * 100}%`, background: GOLD, borderRadius: h }} />
        {chapters.map((c, i) => <div key={i} style={{ position: "absolute", left: `${(c.at / total) * 100}%`, top: -h, width: h * 0.8, height: h * 3, background: "#fff", borderRadius: 1 }} />)}
        <div style={{ position: "absolute", left: `${p * 100}%`, top: -h * 2, width: h * 5, height: h * 5, marginLeft: -h * 2.5, borderRadius: "50%", background: "#fff", boxShadow: "0 0 12px rgba(0,0,0,.6)" }} />
      </div>
      <div style={{ marginTop: h * 3, textAlign: "center" }}>
        <span style={{ display: "inline-block", fontFamily: ARCHIVO, fontWeight: 600, fontSize: H * 0.011, letterSpacing: "0.18em", textTransform: "uppercase", color: "#fff",
                       background: "rgba(0,0,0,.45)", padding: `${H * 0.004}px ${H * 0.01}px`, borderRadius: H * 0.01 }}>{cur?.label ?? ""}</span>
      </div>
    </div>
  );
};

/* ---------- Outro: end card fades up, CTA cascades letter by letter ---------- */
const Outro: React.FC<{ o: { at: number; cta?: string; endCardSrc?: string } }> = ({ o }) => {
  const frame = useCurrentFrame(); const { fps, height: H, width: W } = useVideoConfig(); const s = frame / fps;
  if (s < o.at) return null;
  const f0 = frame - Math.round(o.at * fps);
  const card = interpolate(f0, [0, 18], [0, 1], clamp);
  const cta = o.cta ?? ""; const fs = H * 0.034; const g0 = cta.indexOf("SF90");
  const wordsOut: { ch: string; i: number }[][] = []; let cur: { ch: string; i: number }[] = [];
  cta.split("").forEach((ch, i) => { if (ch === " ") { wordsOut.push(cur); cur = []; } else cur.push({ ch, i }); }); if (cur.length) wordsOut.push(cur);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.62)", opacity: card }} />
      {o.endCardSrc ? <Img src={staticFile(o.endCardSrc)} style={{ position: "absolute", inset: 0, width: W, height: H, opacity: card, transform: "scale(0.84)", transformOrigin: "50% 16%", WebkitMaskImage: "linear-gradient(to bottom, #000 66%, transparent 68.5%), linear-gradient(to right, transparent 0%, #000 7%, #000 93%, transparent 100%)", maskImage: "linear-gradient(to bottom, #000 66%, transparent 68.5%), linear-gradient(to right, transparent 0%, #000 7%, #000 93%, transparent 100%)", WebkitMaskComposite: "source-in", maskComposite: "intersect" }} /> : null}
      {cta ? <div style={{ position: "absolute", left: W * 0.067, right: W * 0.09, top: H * 0.665, padding: `${fs * 0.35}px ${fs * 0.5}px`, background: "rgba(8,8,8,.55)", borderLeft: `${fs * 0.16}px solid ${GOLD}`, opacity: card, fontFamily: ANTON, fontSize: fs, justifyContent: "flex-start", textAlign: "left", lineHeight: 1.05, textTransform: "uppercase", color: "#fff",
                    WebkitTextStroke: `${fs * 0.04}px rgba(0,0,0,.9)`, paintOrder: "stroke fill", textShadow: "0 8px 30px rgba(0,0,0,.7)", display: "flex", flexWrap: "wrap" }}>
        {wordsOut.map((wd, wi) => (
          <span key={wi} style={{ display: "inline-block", whiteSpace: "nowrap", marginRight: fs * 0.28 }}>
            {wd.map(({ ch, i }) => {
              const k = spring({ frame: f0 - 6 - i * 1.2, fps, config: { damping: 12, stiffness: 260 }, durationInFrames: 10 });
              return <span key={i} style={{ display: "inline-block", opacity: k, transform: `translateY(${(1 - k) * fs * 0.6}px)`, color: g0 >= 0 && i >= g0 && i < g0 + 4 ? GOLD : undefined }}>{ch}</span>;
            })}
          </span>
        ))}
      </div> : null}
    </div>
  );
};

/* ---------- Wipes: two diagonal bands sweep the frame at each chapter change ---------- */
const Wipes: React.FC<{ ats: number[] }> = ({ ats }) => {
  const frame = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig(); const s = frame / fps;
  const a = ats.find((t) => s >= t && s < t + 0.7); if (a == null) return null;
  const p = (s - a) / 0.7;
  const x1 = interpolate(p, [0, 1], [-1.4, 1.4], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const x2 = interpolate(p, [0.08, 1], [-1.4, 1.4], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const band = (x: number, color: string, w: number) => (
    <div style={{ position: "absolute", top: -H * 0.2, height: H * 1.4, width: W * w, left: x * W, background: color, transform: "skewX(-18deg)", boxShadow: "0 0 80px rgba(0,0,0,.4)" }} />
  );
  return <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>{band(x2, RED, 0.5)}{band(x1, GOLD, 0.34)}</div>;
};

/* ---------- Stamp: rotated double-border badge slammed on with an overshoot ---------- */
const StampView: React.FC<{ st: Stamp }> = ({ st }) => {
  const frame = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig(); const s = frame / fps;
  if (s < st.at || s > st.at + st.hold + 0.3) return null;
  const f0 = frame - Math.round(st.at * fps);
  const k = spring({ frame: f0, fps, config: { damping: 9, stiffness: 320, mass: 0.8 }, durationInFrames: 14 });
  const out = interpolate(s, [st.at + st.hold, st.at + st.hold + 0.3], [1, 0], clamp);
  const fs = H * 0.042, pad = fs * 0.45;
  return (
    <div style={{ position: "absolute", left: "50%", top: H * 0.47, transform: `translate(-50%,-50%) rotate(-8deg) scale(${1.9 - 0.9 * k})`, opacity: Math.min(k * 1.4, 1) * out,
                  border: `${fs * 0.12}px solid ${GOLD}`, outline: `${fs * 0.05}px solid ${GOLD}`, outlineOffset: fs * 0.12, padding: `${pad * 0.6}px ${pad}px`, borderRadius: fs * 0.15,
                  background: "rgba(10,10,10,.35)", boxShadow: "0 20px 60px rgba(0,0,0,.5)", whiteSpace: "nowrap" }}>
      <div style={{ fontFamily: ANTON, fontSize: fs, lineHeight: 1, color: GOLD, textTransform: "uppercase", letterSpacing: "0.08em", textShadow: "0 4px 18px rgba(0,0,0,.6)" }}>{st.text}</div>
    </div>
  );
};

export const Motion: React.FC<MotionProps> = ({ src, words, overlayOnly = false, title, callouts, lowerThird, lowerThirds, stamps, follows, wipes = false, keyWord = true, chapters, outro, emphasis = [], cuts = [] }) => (
  <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
    {overlayOnly ? null : <OffthreadVideo src={src.startsWith("http") ? src : staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
    {chapters?.length ? <ChapterBar chapters={chapters} /> : null}
    {title ? <TitleReveal t={title} /> : null}
    <KineticCaptions words={words} emphasis={emphasis} after={title?.until ?? 0} until={outro?.at ?? 1e9} breaks={cuts.map((c) => c.at)} keyWord={keyWord} />
    {(callouts ?? []).map((c, i) => <CalloutView key={i} c={c} />)}
    {lowerThird ? <LowerThird l={lowerThird} /> : null}
    {(lowerThirds ?? []).map((l, i) => <LowerThird key={i} l={l} />)}
    {(stamps ?? []).map((st, i) => <StampView key={i} st={st} />)}
    {(follows ?? []).map((fl, i) => <FollowCard key={i} f={fl} />)}
    {wipes && chapters ? <Wipes ats={chapters.slice(1).map((c) => c.at)} /> : null}
    {outro ? <Outro o={outro} /> : null}
  </AbsoluteFill>
);

/* ---------- Follow card: platform pill with avatar ring, handle, count, and a button that gets tapped ---------- */
export type FollowSpec = { at: number; hold: number; platform: "instagram" | "youtube"; name: string; handle: string; followers: string; avatarSrc: string; y?: number };
export const FollowCard: React.FC<{ f: FollowSpec }> = ({ f }) => {
  const frame = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig(); const s = frame / fps;
  if (s < f.at || s > f.at + f.hold + 0.5) return null;
  const f0 = frame - Math.round(f.at * fps);
  const inS = spring({ frame: f0, fps, config: { damping: 13, stiffness: 150, mass: 0.9 }, durationInFrames: 22 });
  const av = spring({ frame: f0 - 6, fps, config: { damping: 10, stiffness: 260 }, durationInFrames: 14 });
  const out = interpolate(s, [f.at + f.hold, f.at + f.hold + 0.45], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const tapAt = Math.round(fps * 1.6), tap = spring({ frame: f0 - tapAt, fps, config: { damping: 9, stiffness: 400 }, durationInFrames: 12 });
  const done = f0 >= tapAt + 6;
  const ig = f.platform === "instagram";
  const h = H * 0.058, r = h / 2, avatar = h * 0.68, nameF = h * 0.30, subF = h * 0.19, btnF = h * 0.22;
  const ring = ig ? "conic-gradient(from 210deg, #f9ce34, #ee2a7b, #6228d7, #f9ce34)" : "conic-gradient(#ff0000, #ff5a5a, #ff0000)";
  const btnBg = done ? "rgba(255,255,255,.14)" : ig ? "#3797F0" : "#FF0000";
  const btnText = done ? (ig ? "Following ✓" : "Subscribed ✓") : ig ? "Follow" : "Subscribe";
  const ringSpin = interpolate(f0, [0, 40], [0, 360], clamp);
  return (
    <div style={{ position: "absolute", left: W * 0.067, top: (f.y ?? 0.235) * H, opacity: (1 - out) * Math.min(1, inS * 1.5),
                  transform: `translateX(${(1 - inS) * -W * 0.12 - out * W * 0.12}px) scale(${0.92 + 0.08 * inS})`, transformOrigin: "left center",
                  display: "flex", alignItems: "center", gap: h * 0.28, height: h, padding: `0 ${h * 0.32}px 0 ${h * 0.16}px`, borderRadius: r,
                  background: "rgba(22,22,24,.92)", boxShadow: "0 18px 60px rgba(0,0,0,.55), inset 0 0 0 1px rgba(255,255,255,.06)" }}>
      <div style={{ width: avatar, height: avatar, borderRadius: "50%", padding: avatar * 0.045, background: ring, transform: `scale(${av}) rotate(${ringSpin}deg)`, flex: "none" }}>
        <Img src={staticFile(f.avatarSrc)} style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", transform: `rotate(${-ringSpin}deg)`, border: `${avatar * 0.035}px solid #161618`, boxSizing: "border-box" }} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", lineHeight: 1.15, minWidth: h * 2.2, paddingRight: h * 0.2 }}>
        <div style={{ fontFamily: ARCHIVO, fontWeight: 800, fontSize: nameF, color: "#fff", letterSpacing: "-0.01em", whiteSpace: "nowrap" }}>{f.name}</div>
        <div style={{ fontFamily: ARCHIVO, fontWeight: 500, fontSize: subF, color: "#a8a8ad", whiteSpace: "nowrap" }}>{f.handle}</div>
        <div style={{ fontFamily: ARCHIVO, fontWeight: 500, fontSize: subF, color: "#a8a8ad", whiteSpace: "nowrap", fontVariantNumeric: "tabular-nums" }}>{f.followers}</div>
      </div>
      <div style={{ position: "relative", background: btnBg, color: "#fff", fontFamily: ARCHIVO, fontWeight: 800, fontSize: btnF, padding: `${btnF * 0.75}px ${btnF * 1.6}px`, borderRadius: r,
                    transform: `scale(${1 - 0.12 * Math.sin(Math.min(1, Math.max(0, tap)) * Math.PI)})`, whiteSpace: "nowrap", transition: "none" }}>
        {btnText}
        {f0 >= tapAt && f0 < tapAt + 14 ? (
          <div style={{ position: "absolute", left: "50%", top: "50%", width: btnF * 1.2, height: btnF * 1.2, marginLeft: -btnF * 0.6, marginTop: -btnF * 0.6, borderRadius: "50%",
                        border: `${btnF * 0.08}px solid rgba(255,255,255,.9)`, transform: `scale(${1 + (f0 - tapAt) * 0.35})`, opacity: 1 - (f0 - tapAt) / 14 }} />
        ) : null}
      </div>
    </div>
  );
};
