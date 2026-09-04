import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, useVideoConfig } from "remotion";
import { loadFonts } from "./fonts";
import { Captions } from "./components/Captions";
import { Hook } from "./components/Hook";
import { ProgressBar } from "./components/ProgressBar";
import { Handle } from "./components/Handle";
import { EndCard } from "./components/EndCard";
import { toWords, type Phrase } from "./data/captions";

loadFonts();

export type ReelProps = {
  src: string;
  phrases: Phrase[];
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
};

export const Reel: React.FC<ReelProps> = ({
  src, phrases, hook, handle, endCard, endCardAt = 0, showProgress = false, scrim = false,
}) => {
  const { durationInFrames, fps } = useVideoConfig();
  const words = toWords(phrases);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <OffthreadVideo
        src={src.startsWith("http") ? src : staticFile(src)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

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
      {hook ? <Hook text={hook} /> : null}
      <Captions words={words} />
      {endCard ? (
        <EndCard line={endCard} startSeconds={endCardAt || durationInFrames / fps - 3} />
      ) : null}
      {showProgress ? <ProgressBar /> : null}
    </AbsoluteFill>
  );
};
