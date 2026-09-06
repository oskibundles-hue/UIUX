import React from "react";
import { Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

/**
 * Animates any full-frame overlay PNG from the packs (handle bugs, FD lower
 * thirds, CTA bars, SE cards): slides in from the given edge with a fade,
 * holds, slides out. The PNGs are authored at 1080x1920 and stretch to the
 * composition, so the same asset serves 1080 and 4K.
 */
export type OverlaySpec = {
  src: string;              // path under public/, e.g. "handles/handle_9x16_all-stacked_white.png"
  at: number;               // seconds in
  hold?: number;            // seconds on screen after the entrance (default to end)
  from?: "left" | "right" | "bottom" | "top" | "fade";
  distance?: number;        // fraction of frame width/height travelled (default 0.06)
};

export const AnimatedOverlay: React.FC<{ spec: OverlaySpec }> = ({ spec }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const start = Math.round(spec.at * fps);
  const end = spec.hold == null ? durationInFrames : start + Math.round(spec.hold * fps);
  if (frame < start || frame > end + 12) return null;
  const inS = spring({ frame: frame - start, fps, config: { damping: 200, stiffness: 160 }, durationInFrames: 14 });
  const outS = interpolate(frame, [end, end + 12], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const k = Math.min(inS, outS);
  const d = spec.distance ?? 0.06;
  const from = spec.from ?? "left";
  const dx = from === "left" ? -width * d : from === "right" ? width * d : 0;
  const dy = from === "bottom" ? height * d : from === "top" ? -height * d : 0;
  return (
    <Img
      src={staticFile(spec.src)}
      style={{ position: "absolute", left: 0, top: 0, width, height, opacity: k,
               transform: `translate(${dx * (1 - k)}px, ${dy * (1 - k)}px)`, pointerEvents: "none" }}
    />
  );
};
