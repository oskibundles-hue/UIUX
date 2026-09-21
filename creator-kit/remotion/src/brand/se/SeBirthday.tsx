import React from "react";
import { Img, spring, staticFile } from "remotion";
import type { BrandBirthday } from "../types";
import { textWidth } from "../measure";
import { C, L, LABEL, LINING, LOGOS, Mask, SAFE, TABULAR, W4, bracket, easeIn, easeInOut, fitSize, font, panel, ramp, ts, useClock, withSize } from "./kit";

/**
 * Birthday opener (props `birthday`, se-booking only). Three looks for one open, picked per vlog:
 *   A "The 27"        bracket label, the age rolls up like an odometer, orange ordinal, hairline + date.
 *   B "Virgo"         the Virgo constellation draws star by star behind the age and "Happy birthday", twinkles once, fades;
 *                     Virgo glyph (drawn as a path, never the emoji code point) in the label row. Orange = Spica's ring.
 *   C "Boarding pass" glass ticket slides in (route, passenger, flight, seat, group, sign, date), then a HAPPY 27TH stamp lands.
 * Runs from `at` (default 0) for `hold` s (default BIRTHDAY_HOLD), out over the last 0.4 s with a lift.
 * Everything sits in the title zone (y 780..~1560), below the corner bug and chapter row (y 560..710) and far above the
 * caption panel (top >= 2555), so his captions stay readable. SeMotion starts the chapter bar when the opener ends.
 */
export const BIRTHDAY_HOLD = 4.3;
export const birthdayEnd = (b: BrandBirthday) => (b.at ?? 0) + (b.hold ?? BIRTHDAY_HOLD);

const LEFT = L.title.left;
const TOP = L.title.top;
const MAXW = SAFE.right - SAFE.left;

const ordinal = (n: number) => {
  const t = n % 100;
  if (t >= 11 && t <= 13) return "th";
  return ["th", "st", "nd", "rd"][n % 10] ?? "th";
};

/** Local clock for the opener window. */
const useWindow = (b: BrandBirthday) => {
  const { frame, fps, s } = useClock();
  const at = b.at ?? 0;
  const hold = b.hold ?? BIRTHDAY_HOLD;
  const ls = s - at;
  const lf = frame - Math.round(at * fps);
  const live = ls >= 0 && ls <= hold + 0.05;
  const out = ramp(ls, hold - 0.4, hold, easeIn);
  return { fps, ls, lf, hold, live, out };
};

/** Soft top scrim (lighter than the title's: the open is usually a dark indoor shot). Under the chapter bar and bug. */
export const SeBirthdayScrim: React.FC<{ b: BrandBirthday }> = ({ b }) => {
  const { fps, ls, hold, live } = useWindow(b);
  if (!live) return null;
  const a = ramp(ls, 0, 6 / fps) * (1 - ramp(ls, hold - 0.4, hold + 0.05, easeIn));
  if (a <= 0) return null;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: 2200, opacity: a,
                  background: "linear-gradient(180deg,rgba(15,16,20,.34) 0px,rgba(15,16,20,.62) 640px,rgba(15,16,20,.62) 1480px,rgba(15,16,20,0) 2200px)" }} />
  );
};

export const SeBirthday: React.FC<{ b: BrandBirthday }> = ({ b }) => {
  const w = useWindow(b);
  if (!w.live || w.out >= 1) return null;
  const body = b.variant === "B" ? <Virgo b={b} w={w} /> : b.variant === "C" ? <Pass b={b} w={w} /> : <The27 b={b} w={w} />;
  return <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: "100%", opacity: 1 - w.out, transform: `translateY(${-w.out * 40}px)` }}>{body}</div>;
};

type Win = ReturnType<typeof useWindow>;

/* ------------------------------------------------------------------ A: The 27 */
const A_NUM = ts(660, 700, -0.045, true);
const A_ORD = ts(150, 600, -0.01);
const A_DATE = ts(62, 600, 0.22);

const The27: React.FC<{ b: BrandBirthday; w: Win }> = ({ b, w }) => {
  const { ls, fps, lf } = w;
  const age = Math.max(0, Math.round(b.age));
  const num = fitSize([String(age)], A_NUM, MAXW - 300, 300);
  const k = ramp(ls, 0.2, 1.3, (x) => 1 - (1 - x) ** 2);   // ticks slow into the age
  const v = k >= 1 ? age : Math.min(age, Math.floor(age * k));
  const len = String(age).length;
  const shown = String(v).padStart(len, "0");
  const lead = len - String(v).length;           // leading zeros sit at white 36%
  const rise = spring({ frame: lf - 2, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 24 });
  const st: React.CSSProperties = { ...font(num), letterSpacing: 0, color: C.ink, ...TABULAR };
  const label = bracket(b.label ?? "Happy birthday");
  const eye = ramp(lf, 0, 14);
  const ord = spring({ frame: lf - Math.round(1.2 * fps), fps, config: { damping: 16, stiffness: 160 }, durationInFrames: 18 });
  const rule = ramp(ls, 1.25, 1.7);
  const date = ramp(ls, 1.4, 1.85);
  return (
    <div style={{ position: "absolute", left: LEFT, top: TOP, whiteSpace: "nowrap" }}>
      <div style={{ ...font(LABEL), lineHeight: 1, color: C.ink84, clipPath: `inset(-20% ${(1 - eye) * 100}% -20% 0)` }}>{label}</div>
      <div style={{ display: "flex", alignItems: "flex-start", marginTop: -Math.round(num.size * 0.05), marginLeft: -Math.round(num.size * 0.04) }}>
        <Mask k={rise} size={num.size} gapTop={34}>
          <div style={{ ...st, lineHeight: 0.9 }}>{shown.split("").map((d, i) => <span key={i} style={{ color: i < lead ? C.ink36 : C.ink }}>{d}</span>)}</div>
        </Mask>
        <div style={{ ...font(A_ORD), lineHeight: 1, color: C.accent, marginLeft: 14, marginTop: Math.round(num.size * 0.2),
                      opacity: Math.min(1, ord * 1.5), transform: `translateY(${(1 - ord) * 40}px)` }}>{ordinal(age)}</div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 34, marginTop: 72 - Math.round(num.size * 0.07) }}>
        <span style={{ display: "block", width: 220, height: 4, background: C.ink56, transformOrigin: "left center", transform: `scaleX(${rule})` }} />
        <span style={{ ...font(A_DATE), lineHeight: 1, color: C.ink84, ...LINING, clipPath: `inset(-20% ${(1 - date) * 100}% -20% 0)` }}>{(b.date ?? "").toUpperCase()}</span>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ B: Virgo */
const B_NUM = ts(500, 700, -0.045);
const B_LINE = ts(186, 300, -0.035);

/** Virgo's main stars (J2000 RA/Dec in degrees, visual magnitude). Stick figure edges below. */
const STARS: { id: string; ra: number; dec: number; mag: number }[] = [
  { id: "beta", ra: 177.67, dec: 1.76, mag: 3.6 },
  { id: "eta", ra: 184.98, dec: -0.67, mag: 3.9 },
  { id: "gamma", ra: 190.42, dec: -1.45, mag: 2.7 },
  { id: "delta", ra: 193.9, dec: 3.4, mag: 3.4 },
  { id: "epsilon", ra: 195.54, dec: 10.96, mag: 2.8 },
  { id: "theta", ra: 197.49, dec: -5.54, mag: 4.4 },
  { id: "alpha", ra: 201.3, dec: -11.16, mag: 1.0 },
  { id: "zeta", ra: 203.67, dec: -0.6, mag: 3.4 },
  { id: "tau", ra: 210.41, dec: 1.54, mag: 4.3 },
  { id: "109", ra: 221.56, dec: 1.89, mag: 3.7 },
  { id: "iota", ra: 214.0, dec: -6.0, mag: 4.1 },
  { id: "mu", ra: 220.77, dec: -5.66, mag: 3.9 },
];
/** [from, to] in draw order: each star appears when the edge reaching it completes; extra edges draw with their later star. */
const EDGES: [string, string][] = [
  ["beta", "eta"], ["eta", "gamma"], ["gamma", "delta"], ["delta", "epsilon"], ["gamma", "theta"], ["theta", "alpha"],
  ["alpha", "zeta"], ["delta", "zeta"], ["zeta", "tau"], ["tau", "109"], ["zeta", "iota"], ["iota", "mu"],
];
const SKY = { x: 760, y: 770, w: 1140, raMin: 177.67, raMax: 221.56, decMax: 10.96, decMin: -11.16 };
const STEP = 0.13, FIRST = 0.15;

/** Virgo glyph, 24-unit strokes (drawn, so no emoji font can substitute a colour glyph). */
const VirgoGlyph: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.1} strokeLinecap="round" strokeLinejoin="round" style={{ display: "block", flex: "none" }}>
    <path d="M3.5 6.5V18M3.5 9c0-2.2 1.2-3.3 2.7-3.3S9 6.8 9 9v9M9 9c0-2.2 1.2-3.3 2.7-3.3S14.5 6.8 14.5 9v7.2c0 2.6 1.3 4.3 3.3 4.3" />
    <path d="M14.5 13.2c.9-2.3 2.4-3.3 3.9-3.3 1.6 0 2.6 1.2 2.6 2.9 0 3-2.8 5.4-7.6 7.7" />
  </svg>
);

const Virgo: React.FC<{ b: BrandBirthday; w: Win }> = ({ b, w }) => {
  const { ls, lf, fps } = w;
  const hSky = (SKY.w * (SKY.decMax - SKY.decMin)) / (SKY.raMax - SKY.raMin);
  const pos = (id: string) => {
    const st = STARS.find((x) => x.id === id)!;
    return { x: SKY.x + ((SKY.raMax - st.ra) / (SKY.raMax - SKY.raMin)) * SKY.w, y: SKY.y + ((SKY.decMax - st.dec) / (SKY.decMax - SKY.decMin)) * hSky };
  };
  // appearance time per star: first star at FIRST, then each edge that reaches a new star adds STEP
  const appear: Record<string, number> = { beta: FIRST };
  const edgeT: { a: string; z: string; t0: number; t1: number }[] = [];
  let t = FIRST;
  for (const [a, z] of EDGES) {
    if (appear[z] === undefined) { appear[z] = t + STEP; edgeT.push({ a, z, t0: t, t1: t + STEP }); t += STEP; }
    else edgeT.push({ a, z, t0: appear[z] - STEP, t1: appear[z] });
  }
  const skyFade = 1 - ramp(ls, 2.75, 3.35, easeIn);
  const label = `${(b.sign ?? "Virgo").toUpperCase()}${b.date ? `  ·  ${b.date.toUpperCase()}` : ""}`;
  const eye = ramp(ls, 0.25, 0.7);
  const l1 = spring({ frame: lf - Math.round(0.45 * fps), fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 24 });
  const l2 = spring({ frame: lf - Math.round(0.62 * fps), fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 24 });
  const line2 = b.label ?? "Happy birthday";
  const size2 = fitSize([line2], B_LINE, MAXW, 120).size;
  return (
    <>
      {skyFade > 0 ? (
        <svg width={W4} height={3840} viewBox={`0 0 ${W4} 3840`} style={{ position: "absolute", left: 0, top: 0, opacity: skyFade }}>
          {edgeT.map((e, i) => {
            const A = pos(e.a), Z = pos(e.z);
            const k = ramp(ls, e.t0, e.t1, easeInOut);
            if (k <= 0) return null;
            return <line key={i} x1={A.x} y1={A.y} x2={A.x + (Z.x - A.x) * k} y2={A.y + (Z.y - A.y) * k} stroke="rgba(255,255,255,.34)" strokeWidth={4} strokeLinecap="round" />;
          })}
          {STARS.map((st, i) => {
            const p = pos(st.id);
            const t0 = appear[st.id];
            const pop = spring({ frame: lf - Math.round(t0 * fps), fps, config: { damping: 11, stiffness: 200 }, durationInFrames: 16 });
            if (ls < t0) return null;
            const r = st.mag < 2 ? 17 : st.mag < 3 ? 12 : st.mag < 3.8 ? 10 : 8;
            const tw0 = 1.95 + i * 0.035;                                   // one twinkle, rippling along the figure
            const tw = ramp(ls, tw0, tw0 + 0.16) * (1 - ramp(ls, tw0 + 0.16, tw0 + 0.42, easeInOut));
            const rr = r * pop * (1 + 0.55 * tw);
            const glint = r * (3.2 + 2.2 * tw);
            return (
              <g key={st.id}>
                <circle cx={p.x} cy={p.y} r={rr * 3.2} fill="rgba(255,255,255,.10)" />
                {tw > 0.02 ? (
                  <g stroke={`rgba(255,255,255,${0.75 * tw})`} strokeWidth={3} strokeLinecap="round">
                    <line x1={p.x - glint} y1={p.y} x2={p.x + glint} y2={p.y} />
                    <line x1={p.x} y1={p.y - glint} x2={p.x} y2={p.y + glint} />
                  </g>
                ) : null}
                {st.id === "alpha" ? <circle cx={p.x} cy={p.y} r={(r + 22) * pop} fill="none" stroke={C.accent} strokeWidth={6} /> : null}
                <circle cx={p.x} cy={p.y} r={rr} fill="#fff" />
              </g>
            );
          })}
        </svg>
      ) : null}
      <div style={{ position: "absolute", left: LEFT, top: TOP, whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 24, clipPath: `inset(-30% ${(1 - eye) * 100}% -30% 0)` }}>
          <VirgoGlyph size={66} color={C.ink84} />
          <span style={{ ...font(LABEL), lineHeight: 1, color: C.ink84, ...LINING }}>{label}</span>
        </div>
        <Mask k={l1} size={B_NUM.size} gapTop={34}>
          <div style={{ ...font(B_NUM), lineHeight: 0.9, ...LINING, marginLeft: -Math.round(B_NUM.size * 0.035) }}>{Math.round(b.age)}</div>
        </Mask>
        <Mask k={l2} size={size2}>
          <div style={{ ...font(withSize(B_LINE, size2)), lineHeight: 0.98, color: C.ink84 }}>{line2}</div>
        </Mask>
      </div>
    </>
  );
};

/* ------------------------------------------------------------------ C: Boarding pass */
const P_HEAD = ts(54, 700, 0.2);
const P_CODE = ts(150, 700, -0.02);
const P_KEY = ts(48, 600, 0.2);
const P_VAL = ts(80, 700, -0.005);
const P_STAMP = ts(96, 800, 0.03);
const CARD = { left: 145, top: 780, width: 1635, padT: 50, padX: 60, padB: 56, gap: 36 };

const Pass: React.FC<{ b: BrandBirthday; w: Win }> = ({ b, w }) => {
  const { ls, lf, fps } = w;
  const age = Math.round(b.age);
  const inner = CARD.width - 2 * CARD.padX;
  const slide = spring({ frame: lf, fps, config: { damping: 20, stiffness: 110 }, durationInFrames: 30 });
  const seq = (t0: number) => ramp(ls, t0, t0 + 0.35);
  const route = (b.route ?? []).filter(Boolean).slice(0, 2).map((r) => r.toUpperCase());
  const code = route.length === 2 ? fitSize(route, P_CODE, (inner - 360) / 2, 100) : P_CODE;
  const lineK = ramp(ls, 0.6, 1.05, easeInOut);
  const cells: { k: string; v: string; span?: number }[] = [
    ...(b.passenger ? [{ k: "Passenger", v: b.passenger, span: 4 }] : []),
    { k: "Flight", v: b.flight ?? `BDAY${age}` },
    ...(b.seat ? [{ k: "Seat", v: b.seat }] : []),
    ...(b.group ? [{ k: "Group", v: b.group }] : []),
    { k: "Sign", v: b.sign ?? "Virgo" },
  ];
  const colW = (inner - 3 * 44) / 4;
  const stampK = spring({ frame: lf - Math.round(1.75 * fps), fps, config: { damping: 11, stiffness: 260 }, durationInFrames: 16 });
  const stampOn = ls >= 1.75;
  const hit = stampOn ? Math.max(0, 1 - (ls - 1.75) / 0.18) : 0;     // card gives a little under the stamp
  const stampText = (b.stamp ?? `Happy ${age}${ordinal(age)}`).toUpperCase();
  const stampSt = fitSize([stampText], P_STAMP, 760, 64);
  return (
    <div style={{ position: "absolute", left: CARD.left, top: CARD.top, width: CARD.width, boxSizing: "border-box", padding: `${CARD.padT}px ${CARD.padX}px ${CARD.padB}px`,
                  ...panel(false, 32), whiteSpace: "nowrap",
                  transform: `translateX(${(1 - slide) * -(CARD.width + CARD.left + 80)}px) translateY(${hit * 8}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 28, height: 64, opacity: seq(0.3) }}>
        <Img src={staticFile(LOGOS.marque)} style={{ height: 58, width: 58 * LOGOS.marqueAspect, display: "block" }} />
        <span style={{ ...font(P_HEAD), lineHeight: 1, color: C.ink }}>BOARDING PASS</span>
        {b.date ? <span style={{ ...font(P_HEAD), lineHeight: 1, color: C.ink72, marginLeft: "auto", ...LINING }}>{b.date.toUpperCase()}</span> : null}
      </div>
      <div style={{ height: 2, background: C.hair, margin: `${CARD.gap}px 0`, transformOrigin: "left center", transform: `scaleX(${seq(0.35)})` }} />
      {route.length === 2 ? (
        <div style={{ display: "flex", alignItems: "center", gap: 36, height: Math.round(code.size * 0.82), ...font(code), lineHeight: 1, ...LINING }}>
          <span style={{ opacity: seq(0.45) }}>{route[0]}</span>
          <span style={{ display: "block", flex: "none", width: 26, height: 26, borderRadius: 13, background: C.accent, transform: `scale(${seq(0.55)})` }} />
          <span style={{ display: "block", flex: 1, height: 5, background: `linear-gradient(90deg,${C.accent},rgba(255,255,255,.8))`, transformOrigin: "left center", transform: `scaleX(${lineK})` }} />
          <span style={{ display: "block", flex: "none", width: 30, height: 30, boxSizing: "border-box", borderRadius: 15, border: "5px solid #fff", transform: `scale(${ramp(ls, 1.0, 1.15)})` }} />
          <span style={{ opacity: seq(1.0) }}>{route[1]}</span>
        </div>
      ) : null}
      <div style={{ height: 0, borderTop: "4px dashed rgba(255,255,255,.30)", margin: `${CARD.gap + 4}px 0 ${CARD.gap}px`, opacity: seq(0.6) }} />
      <div style={{ display: "grid", gridTemplateColumns: `repeat(4, ${colW}px)`, columnGap: 44, rowGap: 34 }}>
        {cells.map((c, i) => {
          const k = seq(0.8 + i * 0.07);
          const v = fitSize([c.v.toUpperCase()], P_VAL, (c.span ?? 1) * colW + ((c.span ?? 1) - 1) * 44, 52);
          return (
            <div key={i} style={{ gridColumn: c.span ? `span ${c.span}` : undefined, opacity: k, transform: `translateY(${(1 - k) * 18}px)` }}>
              <div style={{ ...font(P_KEY), lineHeight: 1, color: C.ink56 }}>{c.k.toUpperCase()}</div>
              <div style={{ ...font(v), lineHeight: 1, marginTop: 16, color: C.ink, ...LINING }}>{c.v.toUpperCase()}</div>
            </div>
          );
        })}
      </div>
      {stampOn ? (
        <div style={{ position: "absolute", right: 150, top: 350, transform: `rotate(-4deg) scale(${1.9 - 0.9 * stampK})`, transformOrigin: "center center",
                      opacity: Math.min(0.94, ramp(ls, 1.75, 1.75 + 3 / fps) * 0.94) }}>
          <div style={{ border: `7px solid ${C.accent}`, borderRadius: 20, padding: 8 }}>
            <div style={{ border: `3px solid ${C.accent}`, borderRadius: 12, padding: "22px 40px 24px", ...font(stampSt), lineHeight: 1, color: C.accent, ...LINING }}>{stampText}</div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
