import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

/**
 * The closing call to action.
 *
 * Aimed at sends, because DM shares are weighted far above likes for reaching
 * people who don't follow you - and a send is the one signal you can ask for
 * directly. It sits over the last beat rather than on black, so the video
 * never actually stops moving.
 */
export const EndCard: React.FC<{ line: string; startSeconds: number }> = ({
  line,
  startSeconds,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const start = Math.round(startSeconds * fps);
  if (frame < start) return null;

  const s = spring({
    frame: frame - start,
    fps,
    config: { damping: 200, stiffness: 190 },
    durationInFrames: 12,
  });

  return (
    <div
      style={{
        position: "absolute",
        left: "6.7%",
        right: "17.6%",
        top: theme.endCardY * height,
        opacity: s,
        transform: `translateY(${(1 - s) * 24}px)`,
      }}
    >
      <div
        style={{
          display: "inline-block",
          background: theme.accent,
          color: "#FFFFFF",
          fontFamily: "Archivo, Helvetica, sans-serif",
          fontWeight: 700,
          fontSize: 34,
          letterSpacing: "0.02em",
          padding: "18px 26px",
          borderRadius: 6,
          boxShadow: "0 10px 40px rgba(0,0,0,.5)",
          maxWidth: "100%",
        }}
      >
        {line}
      </div>
    </div>
  );
};
