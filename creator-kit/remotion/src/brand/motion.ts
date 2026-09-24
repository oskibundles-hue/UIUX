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
 *   ACQUIRE  the target lands before the readout exists
 *   DRAW     leaders, rules and labels arrive by drawing or typing, never by fading in
 *   READ     label -> value -> sub, staggered, numbers counting
 *   TRACK    the core sits exactly on the tracked point every frame
 *   RELEASE  the exit is the entry played backwards
 *
 * RELEASE is the one that changes delivered pixels, so it is opt-in per render (BrandProps.calloutExit)
 * and per callout (`exit`), defaulting to the shipped fade.
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

/** How a callout leaves. "fade" is the shipped whole-layer opacity ramp; "retract" plays the entry backwards. */
export type ExitKind = "fade" | "retract";

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
