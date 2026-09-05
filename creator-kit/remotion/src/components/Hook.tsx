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
  const { fps, height } = useVideoConfig();
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
  // Sized as a fraction of frame height so 1080 and 4K renders match.
  const fontSize = Math.round(height * 0.0405);

  return (
    <div
      style={{
        position: "absolute",
        left: "6.7%",
        right: "14%",
        top: theme.hookY * height,
        opacity: exit,
        transform: `scale(${scale}) translateY(${(1 - enter) * -14}px)`,
        transformOrigin: "left center",
      }}
    >
      <div
        style={{
          width: fontSize * 0.9,
          height: Math.max(4, Math.round(fontSize * 0.08)),
          background: theme.accent,
          borderRadius: 4,
          marginBottom: fontSize * 0.25,
        }}
      />
      <div
        style={{
          fontFamily: "Anton, Impact, sans-serif",
          fontSize,
          lineHeight: 0.97,
          letterSpacing: "-0.01em",
          textTransform: "uppercase",
          color: theme.ink,
          WebkitTextStroke: `${Math.max(1, Math.round(fontSize * 0.04))}px rgba(0,0,0,0.9)`,
          paintOrder: "stroke fill",
          textShadow: `0 ${Math.round(fontSize * 0.05)}px 0 ${theme.inkShadow}, 0 0 ${fontSize * 0.4}px rgba(0,0,0,.6)`,
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
                marginRight: fontSize * 0.2,
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
