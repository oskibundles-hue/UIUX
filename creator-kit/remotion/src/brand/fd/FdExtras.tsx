import React from "react";
import { Img, spring, staticFile } from "remotion";
import type { FollowSpec, Stamp } from "../../Motion";
import { C, H4, HZ, L, Lamp, SHADOW, SPACE, ScaleRule, T, TM, TypeOn, W4, easeIn, fitSize, font, hazeAround, Haze, linear, ramp, ts, tw, up, useClock } from "./kit";

/**
 * Chapter transition (replaces Wipes, only with `wipes`): one 8 px FD red scan line crossing the frame top to bottom over
 * 6 frame steps CENTRED on each chapter change after the first: frames cut-3 .. cut+3, y = 0 .. 3840, mid-frame on the cut.
 */
export const FdScanline: React.FC<{ ats: number[] }> = ({ ats }) => {
  const { frame, fps } = useClock();
  const half = TM.scanHalfFrames;
  const cf = ats.map((t) => Math.round(t * fps)).find((c) => frame >= c - half && frame <= c + half);
  if (cf == null) return null;
  const y = ((frame - (cf - half)) / (2 * half)) * H4;
  return <div style={{ position: "absolute", left: 0, top: y - L.scan.h / 2, width: W4, height: L.scan.h, background: C.red, boxShadow: L.scan.glow }} />;
};

const SK = L.stamp;
const STAMP = ts(T.stamp, 0.04);

/** Stamp fallback: Bebas 120 px on haze with the grid, a rule with its red first third, no rotation. Left 144, centred on y 1805. */
export const FdStamp: React.FC<{ st: Stamp }> = ({ st }) => {
  const { frame, fps, s } = useClock();
  if (s < st.at || s > st.at + st.hold + 0.3) return null;
  const f0 = frame - Math.round(st.at * fps);
  const out = ramp(s, st.at + st.hold, st.at + st.hold + 0.3, easeIn);
  if (out >= 1) return null;
  const text = up(st.text);
  const tSt = fitSize([text], STAMP, SPACE.rail - SPACE.side, 72);
  const w = Math.ceil(tw(text, tSt));
  const h = tSt.size * 0.82 + SK.ruleGap + SK.ruleH;
  const top = SK.centerY - h / 2;
  const k = ramp(f0, 0, 8);
  const hz = hazeAround(SK.left, top, w, h, SK.haze);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", opacity: 1 - out }}>
      <Haze {...hz} alpha={HZ.panel} grid opacity={ramp(f0, 0, 6)} />
      <div style={{ position: "absolute", left: SK.left, top, width: w, whiteSpace: "nowrap" }}>
        <div style={{ ...font(tSt), lineHeight: 0.82, textShadow: SHADOW, clipPath: k >= 1 ? undefined : `inset(-20% ${(1 - k) * 100}% -40% -4%)` }}>{text}</div>
        <ScaleRule w={w} h={SK.ruleH} minor={SK.minor} red={1 / 3} draw={ramp(f0, 6, 16)} style={{ marginTop: SK.ruleGap }} />
      </div>
    </div>
  );
};

const FL = L.follow;
const NAME = ts(T.followName, 0.02);
const SUB = ts(T.followSub, 0.1);
const BTN = ts(T.followButton, 0.16);

/**
 * Follow card (restyled FollowCard): haze with the grid, square avatar tile, name 120 px, handle and followers 64 px grey,
 * then the follow action: red lamp (blinking 2 Hz until the tap) + "FOLLOW" in white 76 px; tapped at 1.6 s it presses
 * and turns into "FOLLOWING" with a steady lamp. Data from props as today. Left 144, top y (default 0.235).
 */
export const FdFollow: React.FC<{ f: FollowSpec }> = ({ f }) => {
  const { frame, fps, s } = useClock();
  if (s < f.at || s > f.at + f.hold + 0.5) return null;
  const f0 = frame - Math.round(f.at * fps);
  const out = ramp(s, f.at + f.hold, f.at + f.hold + 0.45, easeIn);
  if (out >= 1) return null;
  const ig = f.platform === "instagram";
  const name = up(f.name);
  const sub = up([f.handle, f.followers].filter(Boolean).join(" · "));
  const tapAt = Math.round(fps * 1.6);
  const done = f0 >= tapAt + 4;
  const btn = done ? (ig ? "FOLLOWING" : "SUBSCRIBED") : ig ? "FOLLOW" : "SUBSCRIBE";
  const A = FL.avatar;
  const maxCol = SPACE.rail - SPACE.side - A - FL.gap;
  const nameSt = fitSize([name], NAME, maxCol, 72);
  const subSt = fitSize([sub], SUB, maxCol, 44);
  const colW = Math.ceil(Math.max(tw(name, nameSt), tw(sub, subSt), 30 + FL.lampGap + tw(ig ? "FOLLOWING" : "SUBSCRIBED", BTN)));
  const top = f.y != null ? f.y * H4 : FL.top;
  const press = ramp(f0, tapAt, tapAt + 3) - ramp(f0, tapAt + 3, tapAt + 8);
  const lampOn = done || Math.floor((Math.max(0, f0) * 4) / fps) % 2 === 0;
  const avK = Math.max(0, spring({ frame: f0 - 2, fps, config: { damping: 16, stiffness: 180 }, durationInFrames: 12 }));
  const hz = hazeAround(FL.left, top, A + FL.gap + colW, A, FL.haze);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", opacity: 1 - out, transform: `translateX(${-out * 40}px)` }}>
      <Haze {...hz} alpha={HZ.panel} grid opacity={ramp(f0, 0, 8)} />
      <div style={{ position: "absolute", left: FL.left, top, height: A, display: "flex", alignItems: "center", gap: FL.gap, whiteSpace: "nowrap" }}>
        <div style={{ width: A, height: A, flex: "none", overflow: "hidden", clipPath: avK >= 1 ? undefined : `inset(0 ${(1 - avK) * 100}% 0 0)` }}>
          <Img src={staticFile(f.avatarSrc)} style={{ display: "block", width: A, height: A, objectFit: "cover" }} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", textShadow: SHADOW }}>
          <div style={{ ...font(nameSt), lineHeight: 0.86 }}><TypeOn text={name} k={ramp(f0, 4, 4 + [...name].length, linear)} /></div>
          <div style={{ ...font(subSt), lineHeight: 1, marginTop: FL.nameGap, color: C.sub }}><TypeOn text={sub} k={ramp(f0, 8, 8 + Math.ceil([...sub].length / 2), linear)} /></div>
          <div style={{ display: "flex", alignItems: "center", gap: FL.lampGap, marginTop: FL.subGap, ...font(BTN), lineHeight: 1, opacity: ramp(f0, 10, 16),
                        transform: `scale(${1 - 0.08 * press})`, transformOrigin: "left center" }}>
            <Lamp on={lampOn} /><span>{btn}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
