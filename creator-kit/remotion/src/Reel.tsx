import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, useVideoConfig, useCurrentFrame, interpolate, Easing } from "remotion";
import { loadFonts } from "./fonts";
import { Captions } from "./components/Captions";
import { Hook } from "./components/Hook";
import { ProgressBar } from "./components/ProgressBar";
import { Handle } from "./components/Handle";
import { EndCard } from "./components/EndCard";
import { SpecCard, type Card } from "./components/SpecCard";
import { AnimatedOverlay, type OverlaySpec } from "./components/AnimatedOverlay";
import { toWords, type Phrase, type Word } from "./data/captions";

loadFonts();

export type ReelProps = {
  src: string;
  phrases: Phrase[];
  /** Word-level timings (from a transcription tool) win over `phrases`. */
  words?: Word[];
  /** Sizes the composition; see calculateMetadata in Root.tsx. */
  durationSeconds?: number;
  /**
   * Overlays are off by default. The reference edit is footage plus captions
   * and nothing else - no hook card, no watermark, no progress bar, no end
   * card. Turn these on only for a deliberately branded variant.
   */
  hook?: string;
  handle?: string;
  endCard?: string;
  endCardAt?: number;
  showProgress?: boolean;
  /** The reference has no scrim; the grade already carries the contrast. */
  scrim?: boolean;
  /**
   * Punch-ins: a quick scale-up of the footage on a beat (a name, a reveal),
   * held, then eased back. `at` in seconds, `hold` in seconds, `scale`
   * defaults to 1.12. Reads as a zoom cut, which the reference edit uses
   * sparingly; two or three per minute is plenty.
   */
  punches?: { at: number; hold?: number; scale?: number }[];
  /**
   * Render only the graphics on a transparent background (prores 4444),
   * so they can be composited over the master in one ffmpeg pass instead
   * of re-encoding the footage through the browser. Punch-ins are then
   * applied to the footage in that pass, not here.
   */
  overlayOnly?: boolean;
  /** Spec cards over held frames; written by assemble_reel.py from freeze segments. */
  cards?: Card[];
  /** Overlay PNGs from the packs, animated in and out. */
  overlays?: OverlaySpec[];
};

const punchScale = (t: number, punches: ReelProps["punches"]) => {
  let s = 1;
  for (const p of punches ?? []) {
    const hold = p.hold ?? 1.2, target = p.scale ?? 1.12;
    if (t < p.at || t > p.at + hold + 0.35) continue;
    const up = interpolate(t, [p.at, p.at + 0.12], [1, target], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
    });
    const down = interpolate(t, [p.at + hold, p.at + hold + 0.35], [target, 1], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
    });
    s = t < p.at + hold ? up : down;
  }
  return s;
};

export const Reel: React.FC<ReelProps> = ({
  src, phrases, words: given, hook, handle, endCard, endCardAt = 0, showProgress = false, scrim = false, punches, overlayOnly = false, cards, overlays,
}) => {
  const { durationInFrames, fps } = useVideoConfig();
  const zoom = punchScale(useCurrentFrame() / fps, punches);
  const words = given && given.length ? given : toWords(phrases);

  return (
    <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
      {overlayOnly ? null : (
        <OffthreadVideo
          src={src.startsWith("http") ? src : staticFile(src)}
          style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})` }}
        />
      )}

      {scrim ? (
        <AbsoluteFill
          style={{
            background:
              "linear-gradient(to bottom, rgba(0,0,0,.5) 0%, rgba(0,0,0,0) 25%," +
              " rgba(0,0,0,0) 60%, rgba(0,0,0,.55) 100%)",
            pointerEvents: "none",
          }}
        />
      ) : null}

      {handle ? <Handle handle={handle} /> : null}
      {(overlays ?? []).map((o, i) => <AnimatedOverlay key={i} spec={o} />)}
      {(cards ?? []).map((c, i) => <SpecCard key={i} card={c} />)}
      {hook ? <Hook text={hook} /> : null}
      <Captions words={words} />
      {endCard ? (
        <EndCard line={endCard} startSeconds={endCardAt || durationInFrames / fps - 3} />
      ) : null}
      {showProgress ? <ProgressBar /> : null}
    </AbsoluteFill>
  );
};
