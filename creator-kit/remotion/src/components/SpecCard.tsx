import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

/**
 * Spec card over a held frame: the car or the job, and three or four facts.
 * Dark panel so it reads over any footage, gold rule and title in the caption
 * accent so it belongs to the same system as the captions.
 */
export type Card = { at: number; hold: number; title: string; lines: string[] };

export const SpecCard: React.FC<{ card: Card }> = ({ card }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  if (t < card.at || t > card.at + card.hold) return null;
  const s = spring({ frame: frame - Math.round(card.at * fps), fps, config: { damping: 200, stiffness: 170 }, durationInFrames: 12 });
  const out = interpolate(t, [card.at + card.hold - 0.3, card.at + card.hold], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const title = Math.round(height * 0.03);
  const line = Math.round(height * 0.0165);
  return (
    <div style={{ position: "absolute", left: "6.7%", right: "17.6%", top: height * 0.40, opacity: Math.min(s, out),
                  transform: `translateY(${(1 - s) * 30}px)` }}>
      <div style={{ background: "rgba(8,8,8,0.78)", borderLeft: `${Math.max(4, title * 0.18)}px solid ${theme.accent}`,
                    padding: `${title * 0.6}px ${title * 0.8}px`, borderRadius: title * 0.2, boxShadow: "0 12px 50px rgba(0,0,0,.55)" }}>
        <div style={{ fontFamily: "Anton, Impact, sans-serif", fontSize: title, lineHeight: 1.05, textTransform: "uppercase",
                      color: theme.accent, letterSpacing: "0.01em", marginBottom: title * 0.35 }}>{card.title}</div>
        {card.lines.map((l, i) => (
          <div key={i} style={{ fontFamily: "Archivo, Helvetica, sans-serif", fontWeight: 600, fontSize: line, lineHeight: 1.5,
                                color: "#FFFFFF", letterSpacing: "0.02em" }}>{l}</div>
        ))}
      </div>
    </div>
  );
};
