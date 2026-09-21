import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

/**
 * The chapter card: a short on-screen label ("CAR 2 — RANGE ROVER", "JOB 3 — BRAKE PADS") that pops in when the
 * transcript detects one of Omarie's real structural phrases (story/chapter_markers.py: "next one", "now we're
 * on the...", a labels.json car/job change) and holds briefly before fading. Same pill language as EndCard, at
 * theme.chapterY so it never competes with the Hook (0.22) or the caption line (0.726).
 *
 * Fits all three story templates (A/B/C): they all run in clock order after the open, so a chapter change is
 * always a real, later moment in the reel, never frame one. `holdSeconds` and the hookGuard below still enforce
 * that in the component itself -- belt and braces, not just a scheduling convention upstream.
 */
export type ChapterMark = { at: number; label: string };

export const Chapter: React.FC<{
  chapters: ChapterMark[];
  holdSeconds?: number;
  /** No chapter card renders before this time, however it is scheduled: the hard guard against stacking with
   * the Hook at frame one. Matches Hook's own default holdSeconds. */
  hookGuardSeconds?: number;
}> = ({ chapters, holdSeconds = 2.2, hookGuardSeconds = 2.6 }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;

  const marks = [...chapters]
    .filter((c) => c.at >= hookGuardSeconds - 1e-6)
    .sort((a, b) => a.at - b.at);
  const active = [...marks].reverse().find((c) => t >= c.at && t < c.at + holdSeconds);
  if (!active) return null;

  const start = Math.round(active.at * fps);
  const s = spring({ frame: frame - start, fps, config: { damping: 18, stiffness: 210 }, durationInFrames: 12 });
  const out = interpolate(t, [active.at + holdSeconds - 0.35, active.at + holdSeconds], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const vis = s * out;
  if (vis <= 0) return null;

  const fontSize = Math.round(height * 0.0195);

  return (
    <div
      style={{
        position: "absolute",
        left: `${theme.safe.left * 100}%`,
        right: `${theme.safe.right * 100}%`,
        top: theme.chapterY * height,
        opacity: vis,
        transform: `translateY(${(1 - s) * -16}px)`,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "inline-block",
          maxWidth: "100%",
          background: "rgba(10,10,10,0.72)",
          borderLeft: `${Math.max(2, Math.round(fontSize * 0.22))}px solid ${theme.accent}`,
          color: theme.ink,
          fontFamily: "Archivo, Helvetica, sans-serif",
          fontWeight: 700,
          fontSize,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          padding: `${fontSize * 0.5}px ${fontSize * 0.75}px`,
          borderRadius: `0 ${fontSize * 0.18}px ${fontSize * 0.18}px 0`,
          boxShadow: "0 8px 28px rgba(0,0,0,.45)",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {active.label}
      </div>
    </div>
  );
};
