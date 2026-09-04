import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { toLines, type Word } from "../data/captions";

/**
 * Captions matched to the reference edit.
 *
 * White line, the word currently being spoken in gold. Sizing and position
 * come from the theme as fractions of frame height, so this renders identically
 * at 1080x1920 and 2160x3840.
 *
 * No scale or slide animation on the active word: the reference simply swaps
 * the colour, and adding movement reads as a different, busier style.
 */
export const Captions: React.FC<{ words: Word[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const lines = toLines(words, 3);
  const line = lines.find((l) => t >= l[0].start && t < l[l.length - 1].end);
  if (!line) return null;

  const fontSize = theme.captionFontFrac * height;
  const stroke = Math.max(1, Math.round(fontSize * 0.055));

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        width,
        top: theme.captionCentreY * height - fontSize * 0.72,
        display: "flex",
        justifyContent: "center",
        flexWrap: "wrap",
        // Compress the whole line, not each word. Scaling spans individually
        // shrinks each about its own centre and leaves phantom gaps between
        // them, which pushes the line wider than the reference.
        transform: `scaleX(${theme.captionScaleX})`,
        transformOrigin: "center",
        // scaleX compresses the glyphs but not the flex gap, so the gap has
        // to be pre-multiplied by it or the words drift apart.
        gap: `0 ${fontSize * 0.20}px`,
        pointerEvents: "none",
      }}
    >
      {line.map((w, i) => {
        const active = t >= w.start && t < w.end;
        return (
          <span
            key={`${w.text}-${i}`}
            style={{
              fontFamily: "Anton, Impact, sans-serif",
              fontSize,
              lineHeight: 1.05,
              textTransform: "uppercase",
              color: active ? theme.captionActive : theme.captionBase,
              // Stroke plus a tight shadow. The reference keeps a hard dark
              // edge on every glyph so the line reads over a bright floor
              // reflection as easily as over a black wall.
              WebkitTextStroke: `${stroke}px rgba(0,0,0,0.92)`,
              paintOrder: "stroke fill",
              textShadow: `0 ${Math.round(fontSize * 0.045)}px ${Math.round(
                fontSize * 0.09
              )}px rgba(0,0,0,0.65)`,
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
