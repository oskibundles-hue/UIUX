import React from "react";
import { Img, spring, staticFile } from "remotion";
import type { FollowSpec } from "../../Motion";
import { C, Check, H4, InstagramGlyph, L, LINING, T, YoutubeGlyph, easeIn, font, panel, ramp, ts, useClock } from "./kit";

const FL = L.follow;
const NAME = ts(T.followName, 700, -0.01);
const SUB = ts(T.followSub, 500);
const BTN = ts(T.followButton, 700, -0.01);

/**
 * Follow card (restyled FollowCard): glass plate, avatar in an orange ring (an .svg avatar such as
 * brand-se/se-marque-white.svg is drawn contained on the ground colour), name, platform glyph +
 * handle, follower line only when `followers` is non-empty, light "Follow" pill that is tapped at
 * 1.6 s and turns into "Following" with an orange check. Data comes from props as today.
 */
export const SeFollow: React.FC<{ f: FollowSpec }> = ({ f }) => {
  const { frame, fps, s } = useClock();
  if (s < f.at || s > f.at + f.hold + 0.5) return null;
  const f0 = frame - Math.round(f.at * fps);
  const inK = spring({ frame: f0, fps, config: { damping: 16, stiffness: 150 }, durationInFrames: 22 });
  const av = spring({ frame: f0 - 6, fps, config: { damping: 12, stiffness: 220 }, durationInFrames: 16 });
  const out = ramp(s, f.at + f.hold, f.at + f.hold + 0.45, easeIn);
  const tapAt = Math.round(fps * 1.6);
  const press = ramp(f0, tapAt, tapAt + 4) - ramp(f0, tapAt + 4, tapAt + 10);
  const done = f0 >= tapAt + 4;
  const ig = f.platform === "instagram";
  const isMark = /\.svg$/i.test(f.avatarSrc);
  const innerD = FL.avatar - 2 * 5 - 2 * 8;
  const label = done ? (ig ? "Following" : "Subscribed") : ig ? "Follow" : "Subscribe";

  return (
    <div style={{ position: "absolute", left: FL.left, top: f.y != null ? f.y * H4 : FL.top, height: FL.height, boxSizing: "border-box", display: "flex", alignItems: "center",
                  gap: FL.gap, padding: `0 ${FL.padR}px 0 ${FL.padL}px`, whiteSpace: "nowrap", ...panel(false, FL.radius),
                  opacity: Math.min(1, inK * 1.4) * (1 - out), transform: `translateX(${(1 - Math.min(1, inK)) * -80 - out * 60}px)` }}>
      <div style={{ width: FL.avatar, height: FL.avatar, flex: "none", boxSizing: "border-box", borderRadius: "50%", border: `5px solid ${C.accent}`, padding: 8, transform: `scale(${Math.max(0, av)})` }}>
        <div style={{ width: innerD, height: innerD, borderRadius: "50%", overflow: "hidden", background: C.ground, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Img src={staticFile(f.avatarSrc)} style={isMark ? { display: "block", width: innerD * 0.58, height: (innerD * 0.58) / 1.6 } : { display: "block", width: innerD, height: innerD, objectFit: "cover" }} />
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, paddingRight: 10 }}>
        <div style={{ ...font(NAME), lineHeight: 1.05 }}>{f.name}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, ...font(SUB), lineHeight: 1.1, color: C.ink72 }}>
          {ig ? <InstagramGlyph size={FL.glyph} color={C.ink72} /> : <YoutubeGlyph size={FL.glyph} color={C.ink72} />}<span>{f.handle}</span>
        </div>
        {f.followers ? <div style={{ ...font(SUB), lineHeight: 1.1, color: C.ink56, ...LINING }}>{f.followers}</div> : null}
      </div>
      <div style={{ height: FL.button, boxSizing: "border-box", borderRadius: FL.button / 2, padding: "0 48px", display: "flex", alignItems: "center", gap: 14,
                    background: done ? "rgba(255,255,255,.12)" : C.light, color: done ? C.ink : C.ground, ...font(BTN), lineHeight: 1, transform: `scale(${1 - 0.08 * press})` }}>
        {done ? <Check size={40} color={C.accent} /> : null}<span>{label}</span>
      </div>
    </div>
  );
};
