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
  hook: string;
  handle: string;
  phrases: Phrase[];
  endCard: string;
  endCardAt: number;
  showProgress: boolean;
};

export const Reel: React.FC<ReelProps> = ({
  src, hook, handle, phrases, endCard, endCardAt, showProgress,
}) => {
  const { durationInFrames, fps } = useVideoConfig();
  const words = toWords(phrases);
  const endAt = endCardAt > 0 ? endCardAt : durationInFrames / fps - 3;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <OffthreadVideo
        src={src.startsWith("http") ? src : staticFile(src)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      {/* Gradient scrims. Text over moving footage is unreadable about half the
          time; these buy contrast without dimming the whole frame. */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 26%," +
            " rgba(0,0,0,0) 58%, rgba(0,0,0,.62) 100%)",
          pointerEvents: "none",
        }}
      />

      <Handle handle={handle} />
      <Hook text={hook} />
      <Captions words={words} />
      <EndCard line={endCard} startSeconds={endAt} />
      {showProgress ? <ProgressBar /> : null}
    </AbsoluteFill>
  );
};
