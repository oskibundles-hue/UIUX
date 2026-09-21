import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { BugSpec } from "./types";
import { clamp, firstCutAfterStart, px4k, scaleCss } from "./shared";

/**
 * Corner logo drawn inside Motion4K (replaces the compose --logo PNG for brand renders).
 *
 * Visibility, in frames at the composition fps:
 * - in:  0 -> 1 over bug.enter.frames, from frame 0 ("start") or from the first cut after 0 s ("firstCut");
 * - out: 1 -> 0 over the bug.exitFrames frames before round(outro.at * fps), and not drawn from that frame on,
 *        so it is never on the end card; with no outro it stays to the last frame.
 */
export const CornerBug: React.FC<{ bug: BugSpec; outroAt?: number; cuts?: { at: number }[] }> = ({ bug, outroAt, cuts }) => {
  const frame = useCurrentFrame(); const { fps, height: H } = useVideoConfig();
  const endF = outroAt != null ? Math.round(outroAt * fps) : null;
  if (endF !== null && frame >= endF) return null;
  const inF = bug.enter.after === "firstCut" ? Math.round(firstCutAfterStart(cuts) * fps) : 0;
  const aIn = interpolate(frame, [inF, inF + bug.enter.frames], [0, 1], clamp);
  const aOut = endF === null ? 1 : interpolate(frame, [endF - bug.exitFrames, endF], [1, 0], clamp);
  const opacity = Math.min(aIn, aOut);
  if (opacity <= 0) return null;
  const k = px4k(1, H);
  const logoW = bug.logoWidth * k, logoH = logoW / bug.logoAspect;
  return (
    <div style={{ position: "absolute", right: bug.right * k, top: bug.top * k, height: bug.height * k, width: bug.width != null ? bug.width * k : undefined,
                  padding: bug.padX != null ? `0 ${bug.padX * k}px` : undefined, boxSizing: "border-box", display: "flex", alignItems: "center", justifyContent: "center",
                  background: bug.plate.background, borderRadius: bug.plate.radius * k, boxShadow: bug.plate.shadow ? scaleCss(bug.plate.shadow, k) : undefined,
                  opacity, pointerEvents: "none" }}>
      <Img src={staticFile(bug.src)} style={{ display: "block", width: logoW, height: logoH, flex: "none" }} />
    </div>
  );
};
