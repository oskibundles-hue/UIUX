import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

/**
 * A thin progress line at the very top.
 *
 * It tells the viewer how little is left, which is a retention device: "nearly
 * over" is a reason to stay, and finishing feeds the watch-time signal that
 * ranks Reels. Kept to 6px so it reads as chrome, not decoration.
 */
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pct = Math.min(1, frame / Math.max(1, durationInFrames - 1));

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: 6,
        background: "rgba(255,255,255,0.16)",
      }}
    >
      <div
        style={{
          width: `${pct * 100}%`,
          height: "100%",
          background: theme.accent,
        }}
      />
    </div>
  );
};
