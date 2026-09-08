/* Formula Dynamics reel engine.
 *
 * Everything is a pure function of time: seek(t) fully rebuilds the frame's
 * styles, so frame N looks identical no matter what order frames render in.
 * That is what makes offline capture safe.
 */

// ---- easing ---------------------------------------------------------------
const E = {
  linear: t => t,
  out:    t => 1 - Math.pow(1 - t, 3),
  outQ:   t => 1 - Math.pow(1 - t, 4),
  in:     t => t * t * t,
  inOut:  t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  // slight overshoot — the "pop" the caption style uses
  pop:    t => {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
  // mechanical snap, good for spec rows and bars
  snap:   t => (t < 0.6 ? E.out(t / 0.6) * 1.04 : 1.04 - 0.04 * E.out((t - 0.6) / 0.4)),
};

// normalised progress of t through [a, b], eased
function p(t, a, b, ease = E.out) {
  if (b <= a) return t >= b ? 1 : 0;
  const x = Math.min(1, Math.max(0, (t - a) / (b - a)));
  return ease(x);
}

// 1 while t is inside [a,b], with fade in/out shoulders
function band(t, a, b, fin = 0.35, fout = 0.35) {
  if (t < a || t > b) return 0;
  const up = p(t, a, a + fin);
  const dn = 1 - p(t, b - fout, b, E.in);
  return Math.min(up, dn);
}

const lerp = (a, b, u) => a + (b - a) * u;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

// ---- element helpers ------------------------------------------------------
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

/** Set opacity + a transform built from parts. */
function set(el, { o = 1, x = 0, y = 0, s = 1, rot = 0, sx = null, blur = 0, clip = null } = {}) {
  if (!el) return;
  el.style.opacity = o;
  let tr = `translate3d(${x}px, ${y}px, 0)`;
  if (s !== 1) tr += ` scale(${s})`;
  if (sx !== null) tr += ` scaleX(${sx})`;
  if (rot) tr += ` rotate(${rot}deg)`;
  el.style.transform = tr;
  el.style.filter = blur ? `blur(${blur}px)` : '';
  if (clip !== null) el.style.clipPath = clip;
}

/** Slide + fade up into place — the workhorse entrance. */
function riseIn(el, t, at, dur = 0.5, dist = 46, ease = E.out) {
  const u = p(t, at, at + dur, ease);
  set(el, { o: u, y: lerp(dist, 0, u) });
  return u;
}

/** Wipe a block in from the left (used for bars and rules). */
function wipeIn(el, t, at, dur = 0.45, ease = E.out) {
  const u = p(t, at, at + dur, ease);
  if (el) { el.style.opacity = 1; el.style.clipPath = `inset(0 ${(1 - u) * 100}% 0 0)`; }
  return u;
}

/** Type-on: reveal the first n characters of the element's stored text. */
function typeOn(el, t, at, dur, ease = E.linear) {
  if (!el) return 0;
  if (!el.dataset.full) el.dataset.full = el.textContent;
  const full = el.dataset.full;
  const u = p(t, at, at + dur, ease);
  el.textContent = full.slice(0, Math.round(full.length * u));
  el.style.opacity = u > 0 ? 1 : 0;
  return u;
}

/** Count a number up, formatted. */
function countTo(el, t, at, dur, to, fmt = v => Math.round(v)) {
  if (!el) return 0;
  const u = p(t, at, at + dur, E.outQ);
  el.textContent = fmt(to * u);
  return u;
}

// ---- registration ---------------------------------------------------------
let SCENE = null;
function defineScene(scene) {
  SCENE = scene;
  window.SCENE_DURATION = scene.duration;
  if (scene.build) scene.build();
  window.seek = t => scene.frame(t);
  window.__ready = true;
  scene.frame(0);
}

window.E = E; window.p = p; window.band = band; window.lerp = lerp; window.clamp = clamp;
window.$ = $; window.$$ = $$; window.set = set;
window.riseIn = riseIn; window.wipeIn = wipeIn; window.typeOn = typeOn; window.countTo = countTo;
window.defineScene = defineScene;
