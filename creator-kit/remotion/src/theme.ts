/**
 * One place for every visual decision, so a Reel looks like the last one.
 * Consistency across posts is a growth lever: people should recognise your
 * grid from the thumbnail before they read the handle.
 */
export const theme = {
  // Sampled off the shop floor tile in graded footage, so the graphics carry
  // the same colour as the room rather than a generic "creator yellow".
  accent: "#E75522",        // tile red
  accentDeep: "#B23A13",
  accentAlt: "#F8CC2E",     // tile yellow
  ink: "#FFFFFF",
  inkShadow: "rgba(0,0,0,0.72)",

  // Instagram overlays its own UI on the Reel. Text outside these bounds gets
  // covered by the caption block, the action rail, or the status bar.
  safe: {
    top: 260,
    bottom: 470,           // username + caption + audio strip
    left: 72,
    right: 190,            // like / comment / share / audio rail
  },

  captionBaselineY: 1240,   // clear of the bottom UI, still in the eyeline
  hookY: 430,
} as const;

export type Theme = typeof theme;
