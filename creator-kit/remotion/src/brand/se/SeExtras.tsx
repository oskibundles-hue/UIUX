import React from "react";
import { interpolate, spring } from "remotion";
import type { Stamp } from "../../Motion";
import { C, L, SAFE, T, W4, clampX, easeIn, easeInOut, fitSize, font, panel, ramp, ts, useClock } from "./kit";

const TR = L.transition;
const STAMP = ts(T.stamp, 700, -0.02);

/**
 * Chapter transition (only with `wipes`; not in the design, a proposal): a soft ground band (#0F1014 up to 62%,
 * feathered trailing edge, 900 px) led by a 6 px white 60% edge sweeps left to right over 11 frames CENTRED on each
 * chapter change after the first. Chapter times are the first frame of the new shot (props snapped to the master's
 * picture cuts by work/brand_build/tools/snap_cuts.py), so the band is mid-frame on that frame, with 5 frames on the
 * outgoing shot and 5 on the incoming one. No orange (orange stays a small signal); SeMotion draws it under the chapter
 * bar and the corner bug, so the brand chrome never dims.
 */
export const SeTransition: React.FC<{ ats: number[] }> = ({ ats }) => {
  const { frame, fps } = useClock();
  const cf = ats.map((t) => Math.round(t * fps)).find((c) => frame >= c - TR.halfFrames && frame <= c + TR.halfFrames);
  if (cf == null) return null;
  const p = (frame - (cf - TR.halfFrames)) / (2 * TR.halfFrames);
  const lead = interpolate(p, [0, 1], [0, W4 + TR.band], { ...clampX, easing: easeInOut });
  const band = `rgba(15,16,20,${TR.alpha})`;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W4, height: "100%", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: lead - TR.band, width: TR.band,
                    background: `linear-gradient(90deg,rgba(15,16,20,0) 0%,${band} 55%,${band} 100%)` }} />
      <div style={{ position: "absolute", top: 0, bottom: 0, left: lead - TR.edge, width: TR.edge, background: TR.edgeColor }} />
    </div>
  );
};

/** Stamp fallback: solid panel with a small orange dot, no rotation, scales in from 1.08. */
export const SeStamp: React.FC<{ st: Stamp }> = ({ st }) => {
  const { frame, fps, s } = useClock();
  if (s < st.at || s > st.at + st.hold + 0.3) return null;
  const f0 = frame - Math.round(st.at * fps);
  const k = spring({ frame: f0, fps, config: { damping: 14, stiffness: 220 }, durationInFrames: 14 });
  const out = ramp(s, st.at + st.hold, st.at + st.hold + 0.3, easeIn);
  const tSt = fitSize([st.text], STAMP, SAFE.right - SAFE.left - 128 - 44, 72);
  return (
    <div style={{ position: "absolute", left: 0, width: W4, top: (st.y ?? 0.47) * 3840, display: "flex", justifyContent: "center" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 28, padding: "40px 64px 46px", ...panel(true, 32), ...font(tSt), lineHeight: 1, whiteSpace: "nowrap",
                    opacity: Math.min(1, k * 1.4) * (1 - out), transform: `translateY(-50%) scale(${1.08 - 0.08 * Math.min(1, k)})` }}>
        <i style={{ display: "block", width: 16, height: 16, borderRadius: 8, background: C.accent, flex: "none" }} />
        <span>{st.text}</span>
      </div>
    </div>
  );
};
