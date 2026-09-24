/**
 * Brand layer types. Type-only module: nothing here runs at import time.
 *
 * Motion.tsx intersects `BrandProps` into `MotionProps`, so new brand fields are
 * added HERE and Motion.tsx never needs another edit.
 */

import type { ExitKind } from "./motion";

/** A brand pack drawn by src/brand/BrandMotion.tsx. */
export type BrandKey = "se-booking" | "fd-telemetry";
/** Every entry of the token table. "legacy" = today's Motion4K look. */
export type TokenKey = "legacy" | BrandKey;

/** Optional props fields for brand renders. Absent `brand` = today's look, untouched code path. */
export type BrandProps = {
  /**
   * Brand pack. Absent or null: the legacy Motion4K code path, exactly as before.
   * "legacy": runs through BrandMotion with the legacy tokens (same pixels, no in-kit logo);
   * useful to prove the brand path. Any other value throws and fails the render.
   *
   * RESERVED KEY: a top-level `brand` in Motion4K props is this pack key and nothing else. The story engine's
   * story/defaults.json has packs.*.brand = "FORMULA DYNAMICS" / "SUPERCAR EXPERIENCE" (display labels); copying such a
   * label (or "") to the top level of a props file fails every render with "unknown brand". Map it to a pack key instead.
   */
  brand?: TokenKey | null;
  /**
   * Draw the in-kit corner logo (default true). Only brands whose tokens define a
   * `bug` have one; legacy has none because its logo is the compose --logo PNG.
   * Brand overlays must be composed WITHOUT --logo, or the logo appears twice.
   */
  logo?: boolean;
  /** Chapter bar visibility: "always" (se-booking default) or seconds shown from each chapter change (fd-telemetry default 3.5). */
  chapterShow?: "always" | number;
  /** Mid-roll booking cards. Captions yield while one holds (fd-telemetry: the chapter bar yields too). */
  ctas?: BrandCta[];
  /** Overrides for the brand copy table in tokens.ts (site, phone, handle, age rule, tagline, locations ...). */
  brandCopy?: BrandCopyOverride;
  /**
   * fd-telemetry: haze alpha behind caption phrases, precomputed from the graded master by
   * work/brand_build/tools/fd_caption_haze.py. Step function: a phrase uses the last entry with
   * `at` <= phrase start + 0.05 s; before the first entry (or with no list) the token default (0.22).
   */
  captionHaze?: BrandCaptionHaze[];
  /** se-booking only: birthday opener over the first shot (src/brand/se/SeBirthday.tsx). Absent = nothing changes. */
  birthday?: BrandBirthday;
  /**
   * Lock-On RELEASE, render-wide default for every callout: "fade" (shipped, the default) or "retract"
   * (the entry played backwards -- SE 10 f, FD 8 f, both inside the 0.35 s end-before-cut rule).
   * A callout's own `exit` overrides this. Absent = "fade" = the pixels approved on 2026-09-14.
   */
  calloutExit?: ExitKind;
};

/**
 * Birthday opener (se-booking). `variant`: "A" the age rolls up, "B" Virgo constellation, "C" boarding pass + stamp.
 * `at` (default 0) and `hold` (default 4.3) in reel seconds; the chapter bar waits until at + hold. Copy is shown as written:
 * `date` (e.g. "SEP 12"), `sign` (default "Virgo"), `label` (A/B line, default "Happy birthday").
 * C only: `passenger`, `flight` (default BDAY<age>), `seat`, `group`, `route` (two codes, e.g. ["LAS", "PHX"]), `stamp` (default HAPPY <age>TH).
 * Use it instead of `title` at the open (both draw in the title zone).
 */
export type BrandBirthday = {
  variant: "A" | "B" | "C"; at?: number; hold?: number; age: number; sign?: string; date?: string; label?: string;
  passenger?: string; flight?: string; seat?: string; group?: string; route?: string[]; stamp?: string;
};

/**
 * `y` = bottom edge of the card as 0-1 of the frame height (se-booking default 2896/3840, fd-telemetry 2940/3840).
 * `haze` (fd-telemetry) = haze alpha behind the card, from work/brand_build/tools/fd_element_haze.py (default 0.55, max 0.8).
 */
export type BrandCta = { at: number; hold: number; y?: number; haze?: number };

/** One caption-haze entry: from reel second `at`, phrases get haze alpha `a` (clamped to 0-0.6). */
export type BrandCaptionHaze = { at: number; a: number };

export type BrandCopyOverride = Partial<{
  site: string; phone: string; handle: string;
  ageRule: string; ageChip: string;
  /** se-booking end card: detail line under the age rule. Off ("") by default until the policy text is confirmed. */
  ageDetail: string;
  cta: string; bookLabel: string; textUs: string; questions: string; locationsLabel: string;
  tagline: [string, string];
  /** "City, ST" strings or [city, state] pairs. */
  locations: (string | [string, string])[];
  /** Extra end-card line under the locations; null hides it. */
  soon: string | null;
  /** fd-telemetry: how-to line under the CTA ("DM US YOUR MODEL") and the CTA kicker (the brand name; FD takes no bookings). fd-telemetry joins a tagline pair with a space. */
  how: string;
  kicker: string;
}>;

/*
 * Optional per-element fields read by brand packs. They are not intersected into
 * Motion.tsx's element types (legacy ignores them); packs cast to these.
 */
/**
 * Callout extras. se-booking: `sub` = line under the value; `boxY` = box top as 0-1 of height (default follows the dot).
 * fd-telemetry: `context` = grey text at the right of the label row (e.g. "FERRARI F8 SPIDER"); `sub` = second
 * line under a text readout; `boxY` = readout top as 0-1 of height (default: above the dot, or below it near the top);
 * `haze` = readout haze alpha from work/brand_build/tools/fd_element_haze.py (default 0.55, max 0.8).
 */
export type BrandCalloutFields = { sub?: string; boxY?: number; context?: string; haze?: number; exit?: ExitKind };
/**
 * Lower-third extras (se-booking). `variant` sets the defaults: "fleet" -> label "In the fleet", book "Reserve";
 * "city" -> label "Pick-up", book "Book". `meta` items render with orange dots between them; wrap bold parts
 * in **double asterisks**. `meta` falls back to [sub]. `book: false` drops the Reserve/Book block.
 */
export type BrandLowerThirdFields = {
  variant?: "fleet" | "city";
  label?: string;
  kicker?: string;
  meta?: string[];
  book?: { k?: string; v?: string } | false;
  /**
   * fd-telemetry: `kind` = the rotated tab label (default "JOB"); `cells` = the key/value row under the rule
   * (e.g. [{k: "CAR", v: "MASERATI MC20"}, {k: "STAGE", v: "2"}]), shown instead of `sub`. Without cells, `sub` is shown as written.
   */
  kind?: string;
  cells?: { k: string; v: string }[];
};
/**
 * Title extras. se-booking: `route` = cities for the route row under the two lines (dot, city, line, ring, city ...).
 * fd-telemetry job sheet: `rows` = numbered car / job rows under line 1 and its stripe (shown instead of line2);
 * `redWord` = the part of line2 set in FD red (default: its last word, plus the word before when the last is a number; "" = none);
 * `maxRight` = the sheet's right edge as 0-1 of the frame width (e.g. 0.55 when his face is right of centre): lines shrink
 * to it and rows stack the job under the car when they no longer fit on one line.
 */
export type BrandTitleFields = { route?: string[]; rows?: { car: string; job: string }[]; redWord?: string; maxRight?: number };

/** One self-hosted face. `file` is relative to public/ (staticFile). */
export type FontFaceSpec = { family: string; file: string; weight: string; style?: "normal" | "italic" };

export type BrandFonts = {
  /** CSS font-family stack for headlines / numbers. */
  display: string;
  /** CSS font-family stack for running text. */
  text: string;
  /**
   * "kit": faces are loaded by src/fonts.ts at import (legacy; listed here for reference only).
   * "brand": faces are loaded by useBrandFonts() inside BrandMotion, with a loud failure.
   */
  loader: "kit" | "brand";
  faces: readonly FontFaceSpec[];
};

/**
 * Corner logo bug drawn inside Motion4K. All lengths are px on the 2160x3840 canvas
 * (scaled by height / 3840 at render time).
 */
export type BugSpec = {
  /** Logo file under public/. */
  src: string;
  /** Logo width, and its width:height aspect from the SVG viewBox. */
  logoWidth: number;
  logoAspect: number;
  /** Plate position from the top-right corner. `width` omitted = hugs the logo plus padX. */
  right: number;
  top: number;
  height: number;
  width?: number;
  padX?: number;
  /** Plate look. `shadow` px values are scaled with the canvas. */
  plate: { background: string; radius: number; shadow?: string };
  /** Fade in over `frames`, starting at frame 0 or at the first cut after 0 s. */
  enter: { after: "start" | "firstCut"; frames: number };
  /** Fade out over this many frames before round(outro.at * fps); gone from that frame on. No outro = stays to the end. */
  exitFrames: number;
};

/** The part of a token entry the shared brand code (loader, bug, dispatcher) reads. */
export type BaseTokens = {
  key: TokenKey;
  name: string;
  font: BrandFonts;
  bug: BugSpec | null;
};
