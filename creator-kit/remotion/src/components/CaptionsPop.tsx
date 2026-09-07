import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { toLines, type Word } from "../data/captions";

/**
 * "Pop" captions - the second caption style in the kit.
 *
 * Same family as the measured style (Anton, compressed 0.80, white line at
 * 72.6% of frame height, gold accent) so it still reads as the same channel,
 * but the delivery is different:
 *
 *   - each line lands with a short overshoot pop (scale 0.82 -> 1.04 -> 1),
 *     which is the beat the ear expects at the start of a phrase;
 *   - the spoken word is not recoloured, it is boxed: a gold rounded pill
 *     snaps in behind it and the word turns dark, so the active word reads
 *     as a physical highlighter moving along the line;
 *   - the active word lifts by a couple of percent while it is spoken.
 *
 * Nothing fades: entrances are springs, exits are hard swaps, because the
 * classic style's hard swaps are what keeps the caption on the beat.
 */
export const CaptionsPop: React.FC<{ words: Word[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const lines = toLines(words, 3);
  const line = lines.find((l) => t >= l[0].start && t < l[l.length - 1].end);
  if (!line) return null;

  const fontSize = theme.captionFontFrac * height * 1.06;
  const stroke = Math.max(1, Math.round(fontSize * 0.05));
  const lineStart = Math.round(line[0].start * fps);
  const pop = spring({ frame: frame - lineStart, fps, config: { damping: 11, stiffness: 260, mass: 0.7 }, durationInFrames: 12 });
  const lineScale = interpolate(pop, [0, 1], [0.82, 1]);
  const lineRise = interpolate(pop, [0, 1], [fontSize * 0.25, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        width,
        top: theme.captionCentreY * height - fontSize * 0.72,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexWrap: "wrap",
        transform: `translateY(${lineRise}px) scale(${lineScale}) scaleX(${theme.captionScaleX})`,
        transformOrigin: "center",
        gap: `0 ${fontSize * 0.22}px`,
        pointerEvents: "none",
      }}
    >
      {line.map((w, i) => {
        const active = t >= w.start && t < w.end;
        const wStart = Math.round(w.start * fps);
        const pill = active
          ? spring({ frame: frame - wStart, fps, config: { damping: 12, stiffness: 320, mass: 0.6 }, durationInFrames: 9 })
          : 0;
        const pillScale = interpolate(pill, [0, 1], [0.6, 1]);
        const wordScale = active ? interpolate(pill, [0, 1], [1, 1.06]) : 1;
        const padX = fontSize * 0.16, padY = fontSize * 0.02;
        return (
          <span
            key={`${w.text}-${i}`}
            style={{
              position: "relative",
              display: "inline-block",
              padding: `${padY}px ${padX}px`,
              margin: `0 ${-padX * 0.35}px`,
              transform: `scale(${wordScale}) translateY(${active ? -fontSize * 0.03 : 0}px)`,
              transformOrigin: "center",
            }}
          >
            {active ? (
              <span
                style={{
                  position: "absolute",
                  inset: 0,
                  background: theme.captionActive,
                  borderRadius: fontSize * 0.18,
                  transform: `scale(${pillScale})`,
                  transformOrigin: "center",
                  boxShadow: `0 ${Math.round(fontSize * 0.06)}px ${Math.round(fontSize * 0.16)}px rgba(0,0,0,0.45)`,
                }}
              />
            ) : null}
            <span
              style={{
                position: "relative",
                fontFamily: "Anton, Impact, sans-serif",
                fontSize,
                lineHeight: 1.05,
                textTransform: "uppercase",
                color: active ? "#141414" : theme.captionBase,
                WebkitTextStroke: active ? "0px transparent" : `${stroke}px rgba(0,0,0,0.92)`,
                paintOrder: "stroke fill",
                textShadow: active
                  ? "none"
                  : `0 ${Math.round(fontSize * 0.045)}px ${Math.round(fontSize * 0.09)}px rgba(0,0,0,0.65)`,
              }}
            >
              {w.text}
            </span>
          </span>
        );
      })}
    </div>
  );
};
