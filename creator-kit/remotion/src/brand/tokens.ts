/**
 * Brand tokens: colours, fonts, spacing, type sizes, the corner logo and brand copy.
 * Data only, no imports with side effects, nothing runs at import time.
 *
 * Units
 * - LEGACY keeps Motion.tsx's own numbers: fractions of frame width (x) or height (y,
 *   type), and the literal colour strings. Motion.tsx does NOT read this entry; it is
 *   a mirror checked against the source by work/brand_build/tools/check_legacy_tokens.mjs.
 *   Edit Motion.tsx and this entry together, or not at all.
 * - SE and FD are px on the 2160x3840 canvas, as written in the design sources
 *   (work/se_redesign/designs/booking-luxury, work/fd_redesign/designs/telemetry).
 *   Scale with px4k() from ./shared.
 */
import type { BaseTokens, TokenKey } from "./types";

/* ------------------------------------------------------------------ legacy */
export const LEGACY = {
  key: "legacy",
  name: "Motion4K legacy look",
  color: {
    red: "#DE1A22",                     // Motion.tsx RED
    gold: "#FBD101",                    // Motion.tsx GOLD = theme.accent
    ink: "#fff",
    calloutLabel: "#cfcfcf",
    calloutBox: "rgba(10,10,10,.78)",
    lowerThirdSubPlate: "rgba(12,12,12,.85)",
    chapterRail: "rgba(255,255,255,.28)",
    chapterPill: "rgba(0,0,0,.45)",
    outroDim: "rgba(0,0,0,0.62)",
    outroCtaPlate: "rgba(8,8,8,.55)",
    stampPlate: "rgba(10,10,10,.35)",
    followPlate: "rgba(22,22,24,.92)",
    followSub: "#a8a8ad",
    followIg: "#3797F0",
    followYt: "#FF0000",
  },
  font: {
    display: "Anton, Impact, sans-serif",       // Motion.tsx ANTON
    text: "Archivo, Helvetica, sans-serif",     // Motion.tsx ARCHIVO
    loader: "kit",
    faces: [                                    // src/fonts.ts FACES
      { family: "Anton", file: "fonts/Anton-Regular.ttf", weight: "400" },
      { family: "Archivo", file: "fonts/Archivo.ttf", weight: "100 900" },
      { family: "Instrument Serif", file: "fonts/InstrumentSerif-Regular.ttf", weight: "400" },
      { family: "Instrument Serif", file: "fonts/InstrumentSerif-Italic.ttf", weight: "400", style: "italic" },
    ],
  },
  /** Fractions: x values of frame width, y values of frame height. */
  space: {
    left: 0.067,                 // title, captions, chapter bar, follow card, outro CTA
    right: 0.09,                 // title, captions, outro CTA
    titleTop: 0.20,
    titleFitWidth: 0.84,
    chapterTop: 0.145,
    chapterWidth: 0.46,
    captionTopKeyWord: 0.62,
    captionTopUniform: 0.705,
    lowerThirdTop: 0.585,
    calloutReachX: 0.16,
    calloutReachY: -0.07,
    stampTop: 0.47,
    followTop: 0.235,
    outroCtaTop: 0.665,
    safe: { top: 0.135, bottom: 0.245, left: 0.067, right: 0.176 },   // theme.safe
  },
  /** Font sizes as fractions of frame height. */
  type: {
    titleLine1Max: 0.155,
    titleLine2Max: 0.07,
    titleEyebrow: 0.0125,
    captionKeyWordSmall: 0.026,
    captionUniform: 0.0235,
    captionKey: 0.082,
    calloutDot: 0.006,
    calloutLabel: 0.012,
    calloutValue: 0.05,
    lowerThirdTitle: 0.03,
    lowerThirdSub: 0.014,
    chapterLabel: 0.011,
    outroCta: 0.034,
    stamp: 0.042,
    followHeight: 0.058,
  },
  /** Legacy logo is the full-frame PNG burned in by compose_reel_mac.sh --logo. */
  bug: null,
  copy: null,
} as const satisfies BaseTokens & Record<string, unknown>;

/* -------------------------------------------------------------- se-booking */
/** Supercar Experience "Booking-first Luxury" (picked 2026-09-14) + judge fixes + Wordmark Mono caption chip. */
export const SE = {
  key: "se-booking",
  name: "Supercar Experience · Booking-first Luxury",
  color: {
    ground: "#0F1014",
    graphite: "#1A1B20",
    accent: "#FF4F16",           // website orange: a small signal only (labels, index, dot ring, age chip)
    ink: "#FFFFFF",
    ink84: "rgba(255,255,255,.84)",
    ink72: "rgba(255,255,255,.72)",
    ink56: "rgba(255,255,255,.56)",
    ink36: "rgba(255,255,255,.36)",
    hair: "rgba(255,255,255,.14)",
    light: "#EEEEEF",            // button / book block
    chip: "#FFFFFF",             // spoken caption word chip (Wordmark Mono graft)
    chipInk: "#0F1014",
    endGround: "#0F1014",        // judge fix: end card ground 100% opaque
  },
  surface: {
    glass: "linear-gradient(180deg,rgba(26,27,32,.80) 0%,rgba(15,16,20,.80) 100%)",
    solid: "linear-gradient(180deg,rgba(26,27,32,1) 0%,rgba(15,16,20,1) 100%)",
    shadow: "inset 0 0 0 2px rgba(255,255,255,.07), inset 0 3px 0 rgba(255,255,255,.07), 0 28px 80px rgba(0,0,0,.30)",
  },
  font: {
    display: "'Overused Grotesk', 'Helvetica Neue', Arial, sans-serif",
    text: "'Overused Grotesk', 'Helvetica Neue', Arial, sans-serif",
    loader: "brand",
    faces: [{ family: "Overused Grotesk", file: "fonts/OverusedGrotesk-VF.ttf", weight: "300 900" }],
  },
  /** px at 2160x3840. Instagram-safe box: x 145..1780, y 518..2899. */
  space: {
    safe: { left: 145, right: 1780, top: 518, bottom: 2899 },
    radius: { plate: 28, panel: 32, cta: 36 },
    railTop: 560,
  },
  /**
   * px at 4K. Judge fix: every must-read line is at least 46-48 px (design 36-44 raised); `floor` is the
   * smallest size an auto-fit may shrink a line to. Phone-scale review (2026-09-14): 48 px at 4K is only ~8.7 pt on a
   * 390 pt phone, so lines a viewer acts on (phone number, age rule, handles, the site on buttons and book blocks) are
   * 54-66 px and bracket labels 54 px. Decorative labels (chapter name, state codes, route) stay at 46.
   * Everything else is the design size.
   */
  type: {
    floor: 44,
    floorStrict: 48,
    mustRead: 62,              // phone-scale floor for act-on lines: ~11 pt on a 390 pt phone
    label: 54,                 // [ bracket labels ] 700 .2em (design 36, judge 46)
    chapter: 46,               // 03 / 07 + name (design 40)
    caption: 104,
    captionMin: 80,            // a page whose widest line would overflow the panel shrinks to this at most
    calloutValue: 176,
    calloutUnit: 92,
    calloutText: 120,
    calloutSub: 58,
    lowerThirdKicker: 46,      // design 36
    lowerThirdTitle: 132,
    lowerThirdMeta: 54,        // design 38, judge 48
    lowerThirdBookK: 46,       // design 40
    lowerThirdBookV: 54,       // the site in the book block (design 38, judge 46)
    titleLine: 260,
    route: 46,                 // design 40
    ctaHead: 134,
    ctaButton: 66,             // the site on the pill (design 58)
    ctaAlt: 62,                // "or text us" + phone (design 44, judge 48)
    age: 62,                   // 25+ chip + "Renter must be 25+" (design 42, judge 48)
    endTagline: 150,
    endButton: 72,
    endPhone: 62,              // "Questions? Text us" + phone (design 54)
    endLocation: 64,
    endState: 46,              // design 36
    endHandle: 64,             // design 56
    endAge: 62,                // age rule (design 40, judge 48)
    endAgeDetail: 56,          // optional detail line under it, white 72% (copy.ageDetail, off by default)
    endSoon: 46,               // design 40
    followName: 58,
    followSub: 62,             // handle (design 46)
    followButton: 48,
    stamp: 120,
  },
  timing: { chapterShow: "always" },
  /**
   * Lock-On motion (SE dialect: "spring & settle"). Frames at 29.97 fps unless a field names seconds.
   * These are today's shipped numbers, lifted out of SeCallout.tsx so the next element inherits the feel
   * instead of inventing a fourth spring. Data only -- no call is made here.
   *
   * `unmount` is the seconds AFTER the hold at which the component stops rendering. It must stay <= the
   * story rule's end-before-cut gap (story/sync_props.py CALLOUT_GAP = 0.35), or a callout can still be
   * painting when the next cut lands. It was 0.4 until 2026-09-23, which was safe only because the fade
   * had already reached 0 by 0.35; any exit that actually draws in that window would have crossed the cut.
   * Every exit below therefore finishes within `unmount`.
   */
  motion: {
    unmount: 0.35,
    dot: { damping: 11, stiffness: 260, frames: 12 },
    leader: { from: 4, to: 18 },
    box: { delay: 10, damping: 16, stiffness: 150, frames: 18, slide: 36, scaleFrom: 0.96 },
    count: { from: 14, to: 40 },
    halo: { amp: 0.08, period: 5 },
    /** exit: "fade" = today's whole-layer opacity ramp, in seconds. */
    exitFade: 0.35,
    /**
     * exit: "retract", frames from the hold end, 10 f = 0.334 s. Each element reverses its own entrance: the
     * leader lets go of the box and withdraws into the dot (0-6), the ring, halo and core collapse (2-8),
     * the box slides back its 36 px and goes (4-10). Note the leader withdraws INTO THE DOT, not toward the
     * box -- the dash reveals from the dot end, so shrinking it gives up the box end first.
     */
    exitRetract: { frames: 10, leader: { from: 0, to: 6 }, target: { from: 2, to: 8 }, box: { from: 4, to: 10 } },
    /**
     * entry: "lock" -- ACQUIRE. The halo starts wide (r110) and closes onto its r70 over 0-8 f while the ring
     * springs out, so the target visibly locks instead of just growing. The white core no longer rides the
     * ring's spring: it lands last on its own, softer, bouncier spring from f3 (overshoot, then r15). From
     * `core.settle` on, both hand back exactly the classic values, so held frames do not change.
     */
    acquire: { haloFrom: 110, halo: { from: 0, to: 8 }, core: { delay: 3, damping: 8, stiffness: 400, frames: 6, settle: 12 } },
    /**
     * entry: "lock" -- DRAW. A live tip rides the growing end of the leader while it draws (4-18 f): a white
     * disc `tip` x the leader width in radius, over the leader's own black under-stroke for contrast on
     * bright sky. Fades in over the first 12% of the stroke and out over the last 20%, and is absent at rest.
     * No tip on a leader shorter than `minLen` px: it would only park at the target and fade, not travel.
     */
    draw: { tip: 1, fadeIn: 0.12, fadeOut: 0.2, minLen: 160 },
  },
  /** Element geometry, px at 4K, from booking-luxury tokens.css + src/*.html (y values are canvas y). */
  layout: {
    chapter: { left: 145, top: 560, width: 1000, height: 150, padX: 44, rowGap: 28, itemGap: 26, segGap: 12, segHeight: 10 },
    captions: { left: 145, bottom: 2899, maxWidth: 1560, padT: 44, padX: 58, padB: 50, lineHeight: 1.2, radius: 32, chipPadX: 10, chipOverlap: 4, chipRadius: 12 },
    callout: { padT: 46, padX: 60, padB: 52, labelGap: 26, subGap: 24, unitGap: 10, pairGap: 30, radius: 32, minTop: 780, reach: 80, clear: 60, halo: 70, ring: 34, core: 15,
               leader: 6, leaderUnder: 20, leaderUnderAlpha: 0.55,
               trackedRing: 46, trackedLeader: 9, trackedLeaderUnder: 26 },   // tracked (path) callouts: FD-style bigger target + heavier leader over moving footage   // was 5 px over 13 px black 34% (1.2:1 over sky at phone scale)
    lowerThird: { left: 145, bottom: 2892, radius: 32, padT: 46, padX: 60, padB: 50, eyebrowGap: 30, titleGap: 20, metaGap: 26, metaItemGap: 30, dot: 10, bookWidth: 390, bookPadX: 46, bookGap: 16, icon: 52, aboveCaptions: 40 },
    title: { left: 145, top: 800, scrim: 2300, labelGap: 40, routeGap: 60, routeItemGap: 26, routeLine: 340, routeLineMin: 120, dot: 24, ring: 28, ringStroke: 5 },
    cta: { left: 145, width: 1560, bottom: 2896, radius: 36, padT: 44, padX: 60, padB: 46, topGap: 30, marqueW: 85, headGap: 24, rowGap: 34, rowItemGap: 44, ruleGap: 34, rulePad: 30, ageGap: 28,
           button: { h: 140, padL: 62, padR: 18, gap: 34, disc: 108, icon: 54 } },
    endCard: { left: 145, top: 740, width: 1620, logoWidth: 1420, tagGap: 130, tagLineGap: 14, rule1: [100, 90], rule2: [84, 70], gap: 40, locGap: 12, soonGap: 34, footGap: 84, ageGap: 56, ageLineGap: 22, ageMaxWidth: 1240 },
    follow: { left: 145, top: 902, height: 220, radius: 36, padL: 30, padR: 44, gap: 34, avatar: 160, button: 112, glyph: 56 },
    // proposal, not in the design: soft band (#0F1014 up to 62%) led by a white 60% edge; no orange
    transition: { halfFrames: 5, band: 900, alpha: 0.62, edge: 6, edgeColor: "rgba(255,255,255,.6)" },
  },
  logos: {
    lockup: "brand-se/se-logo-white.svg",
    lockupAspect: 732.7509766 / 102.9199219,
    marque: "brand-se/se-marque-white.svg",
    marqueAspect: 161.8479004 / 101.0056152,
  },
  bug: {
    src: "brand-se/se-logo-white.svg",
    logoWidth: 606,
    logoAspect: 732.7509766 / 102.9199219,   // official viewBox, 7.12:1
    right: 145,
    top: 560,
    height: 150,
    padX: 42,
    plate: {
      background: "linear-gradient(180deg,rgba(26,27,32,.80) 0%,rgba(15,16,20,.80) 100%)",
      radius: 28,
      shadow: "inset 0 0 0 2px rgba(255,255,255,.07), inset 0 3px 0 rgba(255,255,255,.07), 0 28px 80px rgba(0,0,0,.30)",
    },
    enter: { after: "start", frames: 12 },
    exitFrames: 8,
  },
  /** Brand copy (props `brandCopy` overrides any key). Sentence case as on the site. */
  copy: {
    site: "supercarexp.vip",
    phone: "(725) 425-3583",
    handle: "@supercar_experience_",
    ageRule: "Renter must be 25+",
    ageChip: "25+",
    // End-card line under the age rule: OFF by default. The design's "Valid driver’s license and matching insurance
    // required." is not verified against SE policy (site: 21 on the home page, 25 in the FAQs); set brandCopy.ageDetail once confirmed.
    ageDetail: "",
    cta: "Book your supercar.",
    bookLabel: "Book your supercar",
    textUs: "or text us",
    questions: "Questions? Text us",
    locationsLabel: "Locations",
    tagline: ["A ride of a lifetime.", "Waiting for you."],
    locations: [["Las Vegas", "NV"], ["Scottsdale", "AZ"], ["Boise", "ID"]],
    soon: null,                  // "Coming soon: ..." line: off unless brandCopy.soon is set (unverified, and it crowds the safe area)
  },
} as const satisfies BaseTokens & Record<string, unknown>;

/* ------------------------------------------------------------ fd-telemetry */
/** Formula Dynamics "Telemetry" (picked 2026-09-14) + judge fixes + Precision Workshop grafts. */
export const FD = {
  key: "fd-telemetry",
  name: "Formula Dynamics · Telemetry",
  color: {
    red: "#FE0F13",              // live signal only. Never #DE1A22, never gold.
    white: "#FFFFFF",
    black: "#000000",
    ink: "#08080A",              // end card ground, bug tile, haze tint
    sub: "#C9C9D0",
    kicker: "rgba(255,255,255,.8)",   // CTA kicker text; red stays on its lamp
    grey: "#9A9AA2",
    hair: "rgba(255,255,255,.62)",
    tick: "rgba(255,255,255,.42)",
    grid: "rgba(255,255,255,.075)",
    green: "#1DB14B",            // stripe only
    yellow: "#FFDE00",           // stripe only
  },
  /** Five-part FD stripe, left to right, in the logo's proportions. */
  stripe: [["#FE0F13", 0.367], ["#000000", 0.214], ["#FFFFFF", 0.194], ["#1DB14B", 0.17], ["#FFDE00", 0.055]],
  shadow: { text: "0 2px 3px rgba(0,0,0,.38), 0 8px 34px rgba(0,0,0,.58)" },
  /**
   * Feathered tint: the design's backdrop blur has nothing behind it on an alpha render, so the haze is
   * rgba(8,8,10,a) under two intersecting feather masks. Alpha per use. Captions stay subtle (judge);
   * `captions` is the default when props.captionHaze has no entry, `captionsMax` caps an entry.
   * Phone-scale review (2026-09-14): chapter .40 -> .48, panel .50 -> .55, title .42 -> .50; `titleTop` = the job sheet's
   * kicker and line 1; callouts and CTAs take a per-element props `haze` (tools/fd_element_haze.py), capped at `elementMax`.
   */
  haze: { tint: "8,8,10", captions: 0.22, captionsMax: 0.6, chapter: 0.48, panel: 0.55, title: 0.5, titleTop: 0.25, elementMax: 0.8, grid: "rgba(255,255,255,.075)", gridCell: 60 },
  font: {
    display: "'Bebas Neue', Impact, sans-serif",
    text: "'Bebas Neue', Impact, sans-serif",
    loader: "brand",
    faces: [{ family: "Bebas Neue", file: "fonts/BebasNeue-Regular.ttf", weight: "400" }],
  },
  /**
   * px at 2160x3840. Every mid-frame element stays left of the IG rail and above the floor. Rail 1770 (~82% of the width,
   * where Instagram's like/comment column starts; the design's 1814 put type under it).
   */
  space: { side: 144, top: 470, floor: 2960, rail: 1770, grid: 60 },
  type: {
    chapter: 80,
    calloutLabel: 78,
    calloutContext: 70,
    calloutValue: 360,
    calloutUnit: 132,
    calloutText: 220,
    caption: 168,
    lowerThirdTitle: 232,
    lowerThirdSub: 90,
    lowerThirdKind: 66,
    cellKey: 64,
    cellValue: 90,
    titleKicker: 80,
    titleLine: 300,
    ctaKicker: 80,
    ctaAction: 250,
    ctaHow: 110,
    ctaHandle: 76,
    endTagline: 86,
    endCta: 190,
    endHow: 92,
    endWeb: 84,                  // site + handle, white (was 68 grey)
    calloutSub: 92,
    rowIndex: 80,
    rowCar: 120,
    rowJob: 80,
    followPlatform: 64,
    followName: 120,
    followSub: 64,
    followButton: 76,
    stamp: 120,
  },
  /** Seconds unless named frames. Chapter bar window per chapter change (judge: ~3.5 s, not always on). */
  timing: { chapterShow: 3.5, captionTail: 0.35, captionOutFrames: 6, outFrames: 8, scanHalfFrames: 3 },
  /**
   * Lock-On motion (FD dialect: "draw & type"). Frames at 29.97 fps unless a field names seconds.
   * Today's shipped numbers, lifted out of FdCallout.tsx. Data only -- no call is made here.
   * See SE.motion for why `unmount` is 0.35 and not 0.4.
   */
  motion: {
    unmount: 0.35,
    arms: { from: 0, to: 8 },
    ring: { from: 0, to: 10 },
    dot: { delay: 2, damping: 14, stiffness: 320, frames: 6 },
    haze: { from: 8, to: 16 },
    rule: { from: 12, to: 22 },
    label: { from: 12, to: 22 },
    context: { from: 16, to: 26 },
    text: { from: 18, to: 28 },
    subFrom: 24,
    leader: { from: 4, to: 16 },
    elbow: { from: 9, to: 11 },
    count: { from: 16, to: 40 },
    /**
     * exit: "retract", frames from the hold end, 8 f = 0.267 s. Each element reverses its own entrance: type
     * clips out right to left, the rule draws back, the leader withdraws into the reticle, the reticle
     * collapses, with a 2 f opacity tail on the panel so nothing can linger.
     */
    exitRetract: { frames: 8, leader: { from: 0, to: 6 }, target: { from: 1, to: 6 }, rule: { from: 0, to: 5 }, text: { from: 0, to: 5 } },
    /**
     * entry: "lock" -- ACQUIRE. The four arms still slide in from 1.5x, and now also square up: they arrive
     * rotated `armRotFrom` degrees and turn to true over 0-8 f, so the reticle reads as a sight settling onto
     * the part. Ring and dot are round, so only the arms turn. At rest the rotation is exactly 0.
     */
    acquire: { armRotFrom: -12, rot: { from: 0, to: 8 } },
    /**
     * entry: "lock" -- DRAW. A live tip rides the growing end of the orthogonal leader while it draws (4-16 f):
     * a white square `tip` px (tracked: the 16 px elbow size), echoing the elbow square. Contrast comes from
     * the leader layer's existing drop shadow. Fades in over 12% and out over 20%, absent at rest.
     * No tip on a leader shorter than `minLen` px. When the readout sits right on the target (p2L callout 4,
     * "COMBINED OUTPUT") the leader is a ~38 px stub hidden at the top arm, and a tip there only parks on
     * the arm and fades -- it reads as a glitch, not a pen stroke.
     */
    draw: { tip: 12, fadeIn: 0.12, fadeOut: 0.2, minLen: 160 },
  },
  /**
   * Element geometry, px at 4K, from telemetry.css / html (y values are canvas y). `haze` boxes bleed past the
   * content by l/r/t/b and feather by f (or fl/fr/ft/fb).
   */
  layout: {
    // judge: the chapter haze ends just past the ruler (ruler ends x 1444; haze solid to 1448, gone by 1488)
    chapter: { left: 144, top: 486, width: 1300, rowH: 80, gap: 28, lamp: 30, ruleGap: 34, ruleH: 44, minor: 26,
               haze: { l: 160, r: 44, t: 130, b: 120, fl: 140, fr: 40, ft: 110, fb: 110 } },
    captions: { left: 144, maxWidth: 1626, bottom: 2960, lineHeight: 1, tracking: 0.02, wordGap: 0.2, maxLines: 2, minSize: 120,
                cursorH: 14, cursorLift: 4, cursorGlide: 3, cursorSnapBelow: 5, shadow: "0 2px 3px rgba(0,0,0,.42), 0 10px 44px rgba(0,0,0,.72)",
                haze: { l: 110, r: 110, t: 84, b: 70, f: 96 } },
    callout: { width: 790, widthText: 760, textMax: 1240, textMin: 150, textFitMin: 132, head: 78, headGap: 56, ruleGap: 24, ruleH: 36, minor: 24,
               valueGap: 44, unitGap: 26, textGap: 40, subGap: 22, above: 538, below: 674, minTop: 760, maxBottom: 2520, clear: 40,
               ring: 66, ringFrom: 40, arm: 40, armAt: 72, armW: 5, dot: 15, leader: 5, elbow: 16, edgeGap: 30, trackedRing: 90, trackedLeader: 8,
               haze: { l: 124, r: 124, t: 118, b: 112, f: 116 } },
    lowerThird: { left: 144, bottom: 2912, tabW: 70, tabGap: 44, footW: 30, footH: 104, footLeft: 20, kindInset: 128,
                  ruleGap: 34, ruleH: 36, minor: 24, subGap: 26, cellGap: 64, cellKeyGap: 20, aboveCaptions: 90, afterTitle: 0.2, minHold: 2.4,
                  haze: { l: 124, r: 124, t: 112, b: 96, f: 108 } },
    title: { left: 144, bottom: 2890, lampGap: 26, line1Gap: 40, stripeGap: 30, stripeW: 420, stripeH: 14, line2Gap: 34, rowsGap: 40,
             rowH: 150, rowIdxW: 150, hair: 3, ruleGap: 44, ruleW: 1320, ruleH: 44, minor: 26, lineMin: 180,
             minWidth: 700, rowMinF: 0.7, stackBelow: 0.85, stackIdxW: 110, stackRowH: 220, stackGap: 18,
             haze: { l: 120, r: 120, t: 64, b: 96, f: 104 }, hazeTop: { l: 110, r: 60, t: 70, b: 56, fl: 100, fr: 60, ft: 70, fb: 56 } },
    cta: { left: 144, bottom: 2940, lampGap: 26, actGap: 40, ruleGap: 36, ruleH: 36, minor: 24, howGap: 30, handleGap: 22,
           haze: { l: 124, r: 124, t: 118, b: 112, f: 116 } },
    // judge: no dyno curve; the CTA block moves up into its place
    endCard: { logoW: 760, logoTop: 640, tagTop: 1550, ctaTop: 1850, ruleTop: 2062, ruleW: 720, ruleH: 36, howTop: 2132, webTop: 2300, webLine: 1.22, maxW: 1380 },   // centred lines stay inside x 390..1770 (IG rail)
    follow: { left: 144, top: 902, avatar: 288, gap: 48, nameGap: 14, subGap: 22, lampGap: 22, haze: { l: 110, r: 110, t: 100, b: 100, f: 100 } },
    stamp: { left: 144, centerY: 1805, ruleGap: 28, ruleH: 36, minor: 24, haze: { l: 110, r: 110, t: 100, b: 100, f: 100 } },
    scan: { h: 8, glow: "0 0 28px 6px rgba(254,15,19,.45)" },
  },
  logos: { stacked: "brand-fd/fd-stacked--white.svg", stackedAspect: 157 / 161, icon: "brand-fd/fd-icon-mark-only--white.svg" },
  bug: {
    src: "brand-fd/fd-icon-mark-only--white.svg",
    logoWidth: 240,
    logoAspect: 185 / 122,
    right: 144,
    top: 560,                    // was 470 (on Instagram's 12% header line); 560 as SE's railTop
    width: 330,
    height: 330,
    plate: { background: "rgba(8,8,10,.9)", radius: 0 },   // solid near-black square so the icon reads on sky
    enter: { after: "firstCut", frames: 12 },
    exitFrames: 8,
  },
  copy: {
    site: "formuladynamicsperformance.com",
    handle: "@formuladynamicsperformance",
    /**
     * Formula Dynamics does NOT take bookings (Omarie, 2026-09-23: "there is no booking for formula
     * dynamics but they can go to the website"). The CTA sends people to the site, so the site line is
     * drawn inside the CTA block as well as on the end card. Was "BOOK YOUR BUILD" / "NOW BOOKING"
     * until 2026-09-23 -- do not reintroduce booking language on FD. Supercar Experience is the brand
     * that books (SE.copy.cta "Book your supercar."), and the two never share copy.
     */
    cta: "VISIT THE SITE",
    how: "DM US YOUR MODEL",
    kicker: "FORMULA DYNAMICS",
    tagline: "PRECISION. PERFORMANCE. PASSION.",
  },
} as const satisfies BaseTokens & Record<string, unknown>;

export const BRAND_TOKENS = { legacy: LEGACY, "se-booking": SE, "fd-telemetry": FD } as const;
export type AnyTokens = (typeof BRAND_TOKENS)[TokenKey];

/** Token entry for a props `brand` value. Throws on anything not in the table (a typo must not render the legacy look under a brand name). */
export const resolveTokens = (brand: unknown): AnyTokens => {
  if (typeof brand === "string" && Object.prototype.hasOwnProperty.call(BRAND_TOKENS, brand)) {
    return BRAND_TOKENS[brand as TokenKey];
  }
  throw new Error(`Motion4K: unknown brand ${JSON.stringify(brand)}. Use one of: ${Object.keys(BRAND_TOKENS).join(", ")} (or omit "brand" for today's look).`);
};
