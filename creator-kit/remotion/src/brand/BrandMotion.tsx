import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import type { MotionProps } from "../Motion";
import { CornerBug } from "./CornerBug";
import { FdMotion, type FdMotionProps } from "./fd/FdMotion";
import { useBrandFonts } from "./fonts";
import { SeMotion, type SeMotionProps } from "./se/SeMotion";
import { resolveTokens } from "./tokens";

export type { BrandProps } from "./types";

/** The legacy Motion4K renderer, handed in by Motion.tsx (this module never imports Motion.tsx at runtime). */
export type LegacyRenderer = React.ComponentType<MotionProps>;

const NO_FACES = [] as const;

/**
 * Brand renders (props.brand set). Motion.tsx sends every props object with a
 * `brand` here; without one, Motion.tsx renders the legacy look itself and this
 * component never renders. The module, and everything under src/brand, is still
 * IMPORTED on legacy renders (Motion.tsx imports it statically), so no brand file may
 * run anything at import time (work/brand_build/tools/check_brand_side_effects.mjs).
 *
 * Layer order, bottom to top:
 *   ground / video > title scrim > chapter bar > corner bug > title > captions > callouts >
 *   lower thirds > CTA > follow > stamps > transition > end card
 *   (se-booking draws its transition under the chapter bar, so the brand chrome never dims)
 *
 * - "se-booking": the Booking-first Luxury pack (src/brand/se/SeMotion.tsx).
 * - "fd-telemetry": the Telemetry pack (src/brand/fd/FdMotion.tsx).
 *   Both are drawn only once the brand font is ready, because their layouts measure text.
 * - "legacy": the legacy renderer draws every element with today's look (overlayOnly forced so it
 *   adds no ground or video of its own) and no bug (proves the brand path adds nothing).
 * Any other value throws in resolveTokens.
 */
export const BrandMotion: React.FC<MotionProps & { Legacy: LegacyRenderer }> = ({ Legacy, ...props }) => {
  const tokens = resolveTokens(props.brand);   // throws on an unknown brand key
  const fontsReady = useBrandFonts(tokens.font.loader === "brand" ? tokens.font.faces : NO_FACES);
  const { src, overlayOnly = false, logo = true, outro, cuts } = props;
  const bug = logo && tokens.bug ? <CornerBug bug={tokens.bug} outroAt={outro?.at} cuts={cuts} /> : null;
  const video = overlayOnly ? null : <OffthreadVideo src={src.startsWith("http") ? src : staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />;
  if (tokens.key === "se-booking") {
    return (
      <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
        {video}
        {fontsReady ? <SeMotion p={props as SeMotionProps} bug={bug} /> : null}
      </AbsoluteFill>
    );
  }
  if (tokens.key === "fd-telemetry") {
    return (
      <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
        {video}
        {fontsReady ? <FdMotion p={props as FdMotionProps} bug={bug} /> : null}
      </AbsoluteFill>
    );
  }
  const legacyProps: MotionProps = { ...props, brand: undefined, overlayOnly: true };
  return (
    <AbsoluteFill style={{ backgroundColor: overlayOnly ? "transparent" : "#000" }}>
      {video}
      {bug}
      <Legacy {...legacyProps} />
    </AbsoluteFill>
  );
};
