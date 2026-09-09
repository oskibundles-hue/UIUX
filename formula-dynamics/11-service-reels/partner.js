/* Partner URL motion graphic.
 *
 * A lower-third that puts the exhaust manufacturer's name and their own public
 * URL on screen, for use ONLY on a video where that exhaust actually appears.
 * If the cut doesn't feature the product, the bar doesn't belong on it.
 *
 * Facts come from PARTNERS.md, which was taken off the manufacturers' own
 * sites. Nothing here is inferred — a partner with no verified URL has no
 * entry, and that is on purpose.
 *
 * Uses type, never a partner logo: their marks are third-party IP and are not
 * generated in this kit.
 *
 * Usage in a scene:
 *
 *   <script src="../partner.js"></script>
 *   ...
 *   mountPartner('ryft');                       // once, in build()
 *   partnerUrl(t, 6.4, 10.2);                   // every frame, in frame(t)
 */

const PARTNERS = {
  ryft: {
    name: 'RYFT',
    url: 'ryft.co',
    line: '100% titanium · handmade',
  },
  ipe: {
    name: 'iPE',
    url: 'ipeofficial.com',
    line: 'Valvetronic · on / off / auto',
  },
  opus: {
    name: 'Opus',
    url: 'opusinnovations.com',
    line: 'Inconel · equal-length headers',
  },
  larini: {
    name: 'Larini',
    url: 'larinisystems.com',
    line: 'Valve control · factory rev-load behaviour',
  },
};

/** Build the bar once and park it off-frame. Call from scene build(). */
function mountPartner(key, opts = {}) {
  const pd = PARTNERS[key];
  if (!pd) throw new Error(
    `partner.js: no verified entry for "${key}". ` +
    `Add it to PARTNERS.md with a source first.`);

  const el = document.createElement('div');
  el.className = 'purl';
  el.id = 'purl';
  el.style.left = (opts.left ?? 54) + 'px';
  el.style.bottom = (opts.bottom ?? 470) + 'px';
  el.innerHTML =
    '<i class="pbar"></i>' +
    '<div class="pin">' +
      '<div class="pname">' + pd.name + '</div>' +
      '<div class="purlrow">' +
        '<span class="plink" id="purlText">' + pd.url + '</span>' +
      '</div>' +
      '<div class="pline">' + pd.line + '</div>' +
    '</div>';
  document.querySelector('.stage').appendChild(el);
  el.dataset.url = pd.url;
  el.style.opacity = 0;
  return el;
}

/**
 * Animate it across [at, out].
 *
 * The bar wipes down, the panel wipes open from the left, the URL types
 * character by character — a URL that assembles reads as an address rather
 * than as decoration — then the whole thing lifts away.
 */
function partnerUrl(t, at, out) {
  const el = document.querySelector('#purl');
  if (!el) return 0;

  const inU  = p(t, at, at + 0.55);
  const outU = p(t, out - 0.40, out, E.in);
  const vis  = inU * (1 - outU);
  if (vis <= 0) { el.style.opacity = 0; return 0; }

  el.style.opacity = vis;
  el.style.transform = `translate3d(${lerp(-38, 0, inU)}px, ${lerp(0, -22, outU)}px, 0)`;

  const bar = el.querySelector('.pbar');
  bar.style.transform = `scaleY(${p(t, at, at + 0.34)})`;

  const pin = el.querySelector('.pin');
  const w = p(t, at + 0.16, at + 0.62);
  pin.style.clipPath = `inset(0 ${(1 - w) * 100}% 0 0)`;

  // type the address on, then hold it complete
  const link = el.querySelector('#purlText');
  const full = el.dataset.url;
  const ty = p(t, at + 0.46, at + 1.06, E.linear);
  link.textContent = full.slice(0, Math.round(full.length * ty));

  // caret blinks only while typing
  link.classList.toggle('caret', ty > 0 && ty < 1);
  return vis;
}

window.PARTNERS = PARTNERS;
window.mountPartner = mountPartner;
window.partnerUrl = partnerUrl;
