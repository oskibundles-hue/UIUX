import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fitText } from "@remotion/layout-utils";
import cue from "./cue.json";

// ---------------------------------------------------------------------------
// Brand constants — mirrored from 99-toolkit/fd_brand.py
// ---------------------------------------------------------------------------
const RED = "#FE0F13";
const WHITE = "#FFFFFF";
const ACCENT_STRIPE: [string, number][] = [
  [RED, 0.367],
  ["#000000", 0.214],
  [WHITE, 0.194],
  ["#1DB14B", 0.17],
  ["#FFDE00", 0.055],
];

const W = cue.width;
const H = cue.height;
const X0 = Math.round(W * cue.layout.marginLeftFrac);
const X1 = Math.round(W * (1 - cue.layout.marginRightFrac));
const BAND_TOP = Math.round(H * cue.layout.bandTopFrac);

// Bebas Neue cap height is 0.723em. Pillow crops text to its inked pixels, so
// a paste at y puts the cap top exactly at y. CSS positions the line box
// instead, so every text block is offset by this much to put the cap top on
// the same pixel row as the Python renderer.
const CAP = 0.723;
const capOffset = (size: number) => -size * 0.208;

// ---------------------------------------------------------------------------
// timing — same beats, same easing as build_ad.py
// ---------------------------------------------------------------------------
const easeOut = (x: number) => {
  const c = Math.max(0, Math.min(1, x));
  return 1 - Math.pow(1 - c, 3);
};
const easeInOut = (x: number) => {
  const c = Math.max(0, Math.min(1, x));
  return 3 * c * c - 2 * c * c * c;
};

type Beat = keyof typeof cue.beats;

const useBeat = (name: Beat, fadeIn = 0.45, fadeOut = 0.4) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const [start, end] = cue.beats[name] as [number, number];
  if (t < start || t > end) return { o: 0, p: 0, t };
  const p = fadeIn ? easeOut((t - start) / fadeIn) : 1;
  let o = p;
  if (fadeOut && t > end - fadeOut) {
    o *= 1 - easeInOut((t - (end - fadeOut)) / fadeOut);
  }
  return { o, p, t };
};

// ---------------------------------------------------------------------------
// pieces
// ---------------------------------------------------------------------------

const AccentStripe: React.FC<{ width: number; height: number }> = ({
  width,
  height,
}) => (
  <div style={{ display: "flex", width, height }}>
    {ACCENT_STRIPE.map(([c, share], i) => (
      <div key={i} style={{ background: c, width: width * share, height }} />
    ))}
  </div>
);

/** Soft band behind the mid-band type. Mirrors fd_hud._scrim. */
const MidScrim: React.FC = () => {
  const hook = useBeat("hook");
  const build = useBeat("build");
  const o = Math.max(hook.o, build.o);
  if (o <= 0) return null;
  const top = H * 0.355;
  const height = H * 0.31;
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top,
        width: W,
        height,
        opacity: o,
        background:
          "linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.55) 22%, rgba(0,0,0,0.80) 50%, rgba(0,0,0,0.55) 78%, rgba(0,0,0,0) 100%)",
      }}
    />
  );
};

/** fd_hud.title_block — bracket, FD monogram, name, subline, accent stripe. */
const TitleBlock: React.FC = () => {
  const { o, p } = useBeat("title", 0.55, 0.55);
  if (o <= 0) return null;
  const top = Math.round(H * 0.665);
  const bw = 78;
  const lw = 3;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity: o,
        transform: `translateX(${(1 - p) * -30}px)`,
      }}
    >
      {/* scrim under the plate */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: H * 0.63,
          width: W,
          height: H * 0.16,
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.51) 50%, rgba(0,0,0,0) 100%)",
        }}
      />
      {/* bracket */}
      <div
        style={{
          position: "absolute",
          left: X0,
          top,
          width: bw,
          height: lw,
          background: WHITE,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: X0,
          top,
          width: lw,
          height: bw,
          background: WHITE,
        }}
      />
      <Img
        src={staticFile("fd-mark-white.png")}
        style={{ position: "absolute", left: X0 + 14, top: top + 16, width: 58 }}
      />
      <div
        style={{
          position: "absolute",
          left: X0 + 108,
          top: top - 6 + capOffset(84),
          fontFamily: "Bebas",
          fontSize: 84,
          lineHeight: 1,
          color: WHITE,
          letterSpacing: 84 * 0.02,
        }}
      >
        {cue.car}
      </div>
      <div
        style={{
          position: "absolute",
          left: X0 + 108,
          top: top - 6 + 84 * CAP + 12 + capOffset(38),
          display: "flex",
          alignItems: "flex-end",
          gap: 24,
        }}
      >
        <div
          style={{
            fontFamily: "Bebas",
            fontSize: 38,
            lineHeight: 1,
            color: WHITE,
            letterSpacing: 38 * 0.14,
          }}
        >
          {cue.build}
        </div>
        <div style={{ paddingBottom: 6 }}>
          <AccentStripe width={Math.round(W * 0.3)} height={9} />
        </div>
      </div>
    </div>
  );
};

/** fd_hud.ticker — segments split by red slashes. */
const Ticker: React.FC = () => {
  const { o } = useBeat("ticker", 0.55, 0.55);
  if (o <= 0) return null;
  const y = Math.round(H * 0.775);
  const size = 30;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: o }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: y - H * 0.037,
          width: W,
          height: H * 0.075,
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.47) 50%, rgba(0,0,0,0) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: y,
          width: W,
          transform: "translateY(-50%)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 22,
          fontFamily: "Bebas",
          fontSize: size,
          lineHeight: 1,
          color: WHITE,
          letterSpacing: size * 0.12,
        }}
      >
        {cue.ticker.map((seg, i) => (
          <React.Fragment key={seg}>
            {i > 0 ? (
              <span style={{ color: RED, letterSpacing: size * 0.02 }}>/////</span>
            ) : null}
            <span>{seg}</span>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

const SHADOW = "0 3px 14px rgba(0,0,0,0.75)";

const Hook: React.FC = () => {
  const { o, t } = useBeat("hook");
  if (o <= 0) return null;
  const start = (cue.beats.hook as [number, number])[0];
  // Solved against the same 826px type column as fd_render.fit_text, so the
  // hook fits the column instead of overflowing it on CSS letter-spacing.
  const maxCap = Math.round(H * 0.1);
  const lines: [string, number][] = cue.hook.map((text) => {
    const { fontSize } = fitText({
      text,
      withinWidth: X1 - X0,
      fontFamily: "Bebas",
      letterSpacing: "0.02em",
      textTransform: "none",
    });
    return [text, Math.min(fontSize, maxCap / CAP)] as [string, number];
  });
  // fd_render.with_shadow pads each layer before pasting, so the Pillow
  // renderer's real ink lands 32px below BAND_TOP and lines advance by their
  // padded height. Measured off its output and matched here rather than
  // re-deriving CSS text metrics: cap top 800, 21px between cap boxes.
  let y = BAND_TOP + 32;
  const out: React.ReactNode[] = [];
  lines.forEach(([text, size], i) => {
    const lp = easeOut((t - start - i * 0.14) / 0.6);
    const top = y;
    y += size * CAP + 21;
    if (lp <= 0) return;
    out.push(
      <div
        key={text}
        style={{
          position: "absolute",
          left: X0,
          top: top + capOffset(size) - (1 - lp) * 36,
          fontFamily: "Bebas",
          fontSize: size,
          lineHeight: 1,
          color: WHITE,
          letterSpacing: size * 0.02,
          marginRight: -size * 0.02,
          opacity: o * lp,
          textShadow: SHADOW,
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    );
  });
  return <div style={{ position: "absolute", inset: 0 }}>{out}</div>;
};

const BuildList: React.FC = () => {
  const { o, t } = useBeat("build");
  if (o <= 0) return null;
  const start = (cue.beats.build as [number, number])[0];
  const top = BAND_TOP;
  const rowH = Math.round(H * 0.052);
  const stripeW = Math.round((X1 - X0) * easeOut((t - start) / 0.7));
  return (
    <div style={{ position: "absolute", inset: 0, opacity: o }}>
      <div
        style={{
          position: "absolute",
          left: X0,
          top: top - 20 + capOffset(34),
          fontFamily: "Bebas",
          fontSize: 34,
          lineHeight: 1,
          color: RED,
          letterSpacing: 34 * 0.16,
          textShadow: SHADOW,
        }}
      >
        {cue.buildHeading}
      </div>
      {stripeW > 2 ? (
        <div style={{ position: "absolute", left: X0, top: top + 54 }}>
          <AccentStripe width={stripeW} height={8} />
        </div>
      ) : null}
      {cue.buildRows.map((row, i) => {
        const [idx, label, sub] = row as [string, string, string];
        const rp = easeOut((t - start - 0.16 - i * 0.15) / 0.6);
        if (rp <= 0) return null;
        const y = top + Math.round(H * 0.048) + i * rowH + (1 - rp) * 20;
        return (
          <div key={idx} style={{ opacity: rp }}>
            <div
              style={{
                position: "absolute",
                left: X0,
                top: y + 16 + capOffset(28),
                fontFamily: "Bebas",
                fontSize: 28,
                lineHeight: 1,
                color: RED,
                letterSpacing: 28 * 0.14,
                textShadow: SHADOW,
              }}
            >
              {idx}
            </div>
            <div
              style={{
                position: "absolute",
                left: X0 + 66,
                top: y - 12 + capOffset(62),
                fontFamily: "Bebas",
                fontSize: 62,
                lineHeight: 1,
                color: WHITE,
                letterSpacing: 62 * 0.03,
                textShadow: SHADOW,
              }}
            >
              {label}
            </div>
            <div
              style={{
                position: "absolute",
                left: 0,
                width: X1,
                textAlign: "right",
                top: y + 18 + capOffset(27),
                fontFamily: "Bebas",
                fontSize: 27,
                lineHeight: 1,
                color: WHITE,
                opacity: 0.72,
                letterSpacing: 27 * 0.12,
                textShadow: SHADOW,
              }}
            >
              {sub}
            </div>
            <div
              style={{
                position: "absolute",
                left: X0,
                top: y + rowH - 14,
                width: X1 - X0,
                height: 2,
                background: "rgba(255,255,255,0.23)",
              }}
            />
          </div>
        );
      })}
    </div>
  );
};

const Cta: React.FC = () => {
  const { o } = useBeat("cta", 0.4, 0.35);
  if (o <= 0) return null;
  return (
    <AbsoluteFill style={{ opacity: o }}>
      <Img src={staticFile("cta.png")} style={{ width: W, height: H }} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------

export const AventadorAd: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const endStart = (cue.beats.end as [number, number])[0];

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <AbsoluteFill>
        <OffthreadVideo
          src={staticFile("plate.mp4")}
          style={{
            width: W,
            height: H,
            objectFit: "cover",
            // matches the ffmpeg eq= grade in cue.json
            filter: "contrast(1.04) saturate(0.96)",
          }}
        />
      </AbsoluteFill>

      {/* vignette — stands in for ffmpeg's vignette filter */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 72% 58% at 50% 50%, rgba(0,0,0,0) 32%, rgba(0,0,0,0.30) 68%, rgba(0,0,0,0.62) 100%)",
        }}
      />

      <MidScrim />
      <TitleBlock />
      <Ticker />
      <Hook />
      <BuildList />
      <Cta />

      {/* end card — hard cut, no fade */}
      {t >= endStart ? (
        <AbsoluteFill>
          <Img src={staticFile("endcard.png")} style={{ width: W, height: H }} />
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
