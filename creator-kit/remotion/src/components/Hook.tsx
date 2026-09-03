import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

/**
 * The opening text hook.
 *
 * It has to be on screen at frame one. Anything that fades up over half a
 * second has already spent the window - people decide in about a second, and
 * average Reel watch time is around eight.
 */
export const Hook: React.FC<{ text: string; holdSeconds?: number }> = ({
  text,
  holdSeconds = 2.6,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const hold = Math.round(holdSeconds * fps);

  // Starts at 0.94 rather than 0, so the first frame already reads as text.
  const enter = spring({ frame, fps, config: { damping: 200, stiffness: 180 }, durationInFrames: 10 });
  const scale = interpolate(enter, [0, 1], [0.94, 1]);
  const exit = interpolate(frame, [hold, hold + 9], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  if (exit <= 0) return null;

  const words = text.split(/\s+/);

  return (
    <div
      style={{
        position: "absolute",
        left: theme.safe.left,
        right: theme.safe.right - 90,
        top: theme.hookY,
        opacity: exit,
        transform: `scale(${scale}) translateY(${(1 - enter) * -14}px)`,
        transformOrigin: "left center",
      }}
    >
      <div
        style={{
          width: 92,
          height: 8,
          background: theme.accent,
          borderRadius: 4,
          marginBottom: 26,
        }}
      />
      <div
        style={{
          fontFamily: "Anton, Impact, sans-serif",
          fontSize: 104,
          lineHeight: 0.97,
          letterSpacing: "-0.01em",
          textTransform: "uppercase",
          color: theme.ink,
          textShadow: `0 5px 0 ${theme.inkShadow}, 0 0 40px rgba(0,0,0,.6)`,
        }}
      >
        {words.map((w, i) => {
          // Words land one after another, so the eye is pulled across the line
          // instead of hitting a wall of type.
          const s = spring({
            frame: frame - i * 2,
            fps,
            config: { damping: 200, stiffness: 200 },
            durationInFrames: 9,
          });
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                marginRight: 20,
                opacity: s,
                transform: `translateY(${(1 - s) * 18}px)`,
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
    </div>
  );
};
