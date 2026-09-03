import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { theme } from "../theme";
import { toLines, type Word } from "../data/captions";

/**
 * Word-by-word captions with the spoken word highlighted.
 *
 * Most people watch muted, so captions are not an accessibility extra here -
 * they are the primary channel. The active-word highlight is what keeps the
 * eye moving; a static block of text gets read once and then ignored.
 */
export const Captions: React.FC<{ words: Word[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const lines = toLines(words, 3);
  const line = lines.find((l) => t >= l[0].start && t < l[l.length - 1].end);
  if (!line) return null;

  const enter = spring({
    frame: frame - Math.round(line[0].start * fps),
    fps,
    config: { damping: 200, stiffness: 220 },
    durationInFrames: 8,
  });

  return (
    <div
      style={{
        position: "absolute",
        left: theme.safe.left,
        right: theme.safe.right,
        top: theme.captionBaselineY,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: "0 18px",
        transform: `translateY(${(1 - enter) * 26}px)`,
        opacity: enter,
      }}
    >
      {line.map((w, i) => {
        const active = t >= w.start && t < w.end;
        return (
          <span
            key={`${w.text}-${i}`}
            style={{
              fontFamily: "Anton, Impact, sans-serif",
              fontSize: 82,
              lineHeight: 1.06,
              letterSpacing: "0.01em",
              textTransform: "uppercase",
              color: active ? theme.accent : theme.ink,
              // A heavy shadow rather than a stroke: it survives Instagram's
              // re-encode, where a thin outline turns to mush.
              textShadow: `0 4px 0 ${theme.inkShadow}, 0 0 26px rgba(0,0,0,.55)`,
              transform: active ? "scale(1.06)" : "scale(1)",
              transformOrigin: "center bottom",
              transition: "none",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
