/**
 * Measured off the reference edit (mimic.mp4), not chosen.
 *
 * Every value below was read off real frames: caption colours sampled from
 * the pixels, position and cap height measured as a fraction of frame height
 * so the same numbers hold at 1080x1920 and 2160x3840.
 */
export const theme = {
  // Caption colours, sampled from the reference frames.
  captionBase: "#FDFDFD",
  captionActive: "#FBD101",

  accent: "#FBD101",
  accentAlt: "#E75522",
  accentDeep: "#C4801B",
  ink: "#FFFFFF",
  inkShadow: "rgba(0,0,0,0.72)",

  // Fractions of frame height/width, so one set of numbers serves any output
  // size. Multiply by width/height at render time.
  captionCentreY: 0.726,   // measured: caption centre sits at 72.6% of height

  // Anton font-size as a fraction of frame height, calibrated so its cap
  // height lands on the reference's 112px-in-3840 (2.92% of height).
  captionFontFrac: 0.03365,

  // The reference's face is narrower than any Google condensed font: its
  // width-to-cap-height ratio is 3.89 where Anton, Fjalla and Bebas all sit
  // near 4.9. That is a CapCut-proprietary face, so Anton is compressed
  // horizontally to match the measured proportions.
  captionScaleX: 0.80,
  hookY: 0.22,
  endCardY: 0.60,

  safe: { top: 0.135, bottom: 0.245, left: 0.067, right: 0.176 },
} as const;

/** Measured: Anton renders a cap height of 0.867 em. */
export const ANTON_CAP_RATIO = 0.867;
