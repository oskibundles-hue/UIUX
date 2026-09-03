import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

/**
 * Your handle, small and permanent.
 *
 * Reels get reposted and screen-recorded. A watermark is the only thing that
 * survives that trip. Kept quiet on purpose - it is a credit, not a banner.
 */
export const Handle: React.FC<{ handle: string }> = ({ handle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const o = interpolate(frame, [0, fps * 0.5], [0, 0.82], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: theme.safe.left,
        top: theme.safe.top - 96,
        display: "flex",
        alignItems: "center",
        gap: 12,
        opacity: o,
      }}
    >
      <div style={{ width: 5, height: 30, background: theme.accent, borderRadius: 3 }} />
      <span
        style={{
          fontFamily: "Archivo, Helvetica, sans-serif",
          fontWeight: 700,
          fontSize: 27,
          letterSpacing: "0.05em",
          color: theme.ink,
          textShadow: "0 2px 10px rgba(0,0,0,.7)",
        }}
      >
        {handle}
      </span>
    </div>
  );
};
