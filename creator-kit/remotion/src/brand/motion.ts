/**
 * Lock-On: the shared motion grammar.
 *
 * The grammar owns TIME, DISTANCE, EASING and ORDER. It owns no colour, no face and no surface, so the
 * two sealed packs keep their own identity (SE: glass panel, orange ring, Overused Grotesk; FD: reticle,
 * haze grid, ScaleRule, Bebas Neue, red as the live signal) while moving to the same clock. The numbers
 * themselves live per pack in tokens.ts as `SE.motion` / `FD.motion`; this file is only the maths that
 * reads them, so a phase means the same thing in both packs.
 *
 * Five signatures, in order:
 *   ACQUIRE  the target lands before the readout exists, and visibly locks on
 *   DRAW     leaders, rules and labels arrive by drawing or typing, never by fading in
 *   READ     label -> value -> sub, staggered, numbers counting
 *   TRACK    the core sits exactly on the tracked point every frame
 *   RELEASE  each element reverses its own entrance: the leader lets go of the readout and withdraws
 *            into the target, the target collapses, the readout slides back the way it came
 *
 * The two that change delivered pixels are switches, per render (BrandProps.calloutExit / calloutEntry)
 * and per callout (`exit` / `entry`), with a default here: RELEASE via DEFAULT_EXIT, and the ACQUIRE +
 * DRAW polish via DEFAULT_ENTRY. Both are built so that once their window is over they hand back EXACTLY
 * the values of the shipped look -- held frames stay byte-identical, which is what lets a framemd5
 * regression prove a change is confined to the entrance or the exit.
 *
 * Hard constraint every exit obeys: it must be finished by `motion.unmount` seconds after the hold ends,
 * and `unmount` must stay <= story/sync_props.py CALLOUT_GAP (0.35 s end-before-cut). SE release is 10 f
 * (0.334 s) and FD release is 8 f (0.267 s) at 29.97 fps, so both land inside it.
 *
 * Type-only + pure arrow functions: nothing here runs at import time
 * (work/brand_build/tools/check_brand_side_effects.mjs).
 */

/** A frame window, read from a `motion` token block. Inclusive of `from`, complete at `to`. */
export type Range = { readonly from: number; readonly to: number };

/** How a callout leaves. "fade" is the whole-layer opacity ramp; "retract" reverses each element's entrance. */
export type ExitKind = "fade" | "retract";

/**
 * How a callout arrives. "classic" is the entrance approved 2026-09-14. "lock" adds the ACQUIRE + DRAW
 * polish: the halo closes onto the ring as it springs out, the core lands last with its own overshoot,
 * the FD arms square up as they slide in, and a live tip rides the front of the leader while it draws.
 */
export type EntryKind = "classic" | "lock";

/** A point on the 2160x3840 canvas. */
export type Pt = readonly [number, number];

/** Linear 0 -> 1 across a frame window, clamped at both ends. A zero-width window snaps at `to`. */
export const spanK = (f: number, r: Range): number =>
  r.to <= r.from ? (f >= r.to ? 1 : 0) : Math.max(0, Math.min(1, (f - r.from) / (r.to - r.from)));

/** Eased 0 -> 1 across a frame window. `ease` is the pack's own curve, so neither pack imports the other's. */
export const spanE = (f: number, r: Range, ease: (t: number) => number): number => ease(spanK(f, r));

/**
 * Frames since the hold ended: negative while the callout is still holding, 0 on the first exit frame.
 * `f0` is frames since `at`; `endF` is the hold end in the same units.
 */
export const sinceEnd = (f0: number, endF: number): number => f0 - endF;

/**
 * Whether RELEASE applies. Per-callout `exit` wins over the render-wide `calloutExit`, which wins over
 * DEFAULT_EXIT.
 *
 * DEFAULT_EXIT was "fade" (the 2026-09-14 approved look) until 2026-09-23, when the A/B over the real
 * m10A master put "retract" ahead on both counts that matter: the graphic leaves the way it arrived
 * instead of dissolving at full size, and it is clear of the frame by f+8 rather than f+10, which widens
 * the margin against the 0.35 s end-before-cut rule. Proof sheet: p10A_se_exit_c1/c2.
 *
 * To go back to the old exit everywhere, set this to "fade" -- one word, no other change. To keep the new
 * exit but pin one callout, set that callout's `exit` in its props.
 */
export const DEFAULT_EXIT: ExitKind = "retract";

export const exitKind = (perCallout: ExitKind | undefined, perRender: ExitKind | undefined): ExitKind =>
  perCallout ?? perRender ?? DEFAULT_EXIT;

/**
 * Entrance default. Per-callout `entry` wins over the render-wide `calloutEntry`, which wins over this.
 *
 * "lock" since 2026-09-23, from an entry A/B (story/proof_sheet.py --mode entry-ab) on p2L_fd over its real
 * m2L master and p7l_se on a neutral plate. ACQUIRE is the clear win: classic grows the whole target out
 * of a point, lock opens a wide halo that closes as the hollow ring springs out and lands the core last
 * (SE), or squares the arms up as they slide in (FD) -- the target reads as acquired, in about four frames.
 * The DRAW tip is subtler (roughly a 2 px bead on a phone for ~0.2 s) but on-dialect -- round for SE,
 * square for FD -- and it is absent at rest, after the hold, and on stub leaders under draw.minLen.
 *
 * Set to "classic" to go back to the 2026-09-14 entrance everywhere -- one word, no other change.
 */
export const DEFAULT_ENTRY: EntryKind = "lock";

export const entryKind = (perCallout: EntryKind | undefined, perRender: EntryKind | undefined): EntryKind =>
  perCallout ?? perRender ?? DEFAULT_ENTRY;

/**
 * The point `dist` px along a polyline, measured from its first point. Clamped to the ends. Used to put
 * the DRAW tip exactly on the growing end of a dash-offset leader, which reveals from its first point.
 */
export const pointAlong = (pts: readonly Pt[], dist: number): Pt => {
  let left = Math.max(0, dist);
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    const seg = Math.hypot(x1 - x0, y1 - y0);
    if (left <= seg) {
      const t = seg > 0 ? left / seg : 0;
      return [x0 + (x1 - x0) * t, y0 + (y1 - y0) * t];
    }
    left -= seg;
  }
  return pts[pts.length - 1];
};

/**
 * Opacity of the DRAW tip at draw progress k (0-1): fades in over the first `fadeIn` of the stroke and out
 * over the last `fadeOut`, so it never pops on or sits as a bead where the leader meets the readout.
 * Exactly 0 at rest (k = 0 or k = 1), so a settled callout draws no tip at all.
 */
export const tipK = (k: number, fadeIn: number, fadeOut: number): number =>
  k <= 0 || k >= 1 ? 0 : Math.min(1, k / fadeIn, (1 - k) / fadeOut);
