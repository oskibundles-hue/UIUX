import { continueRender, delayRender, staticFile } from "remotion";

/**
 * Self-hosted fonts.
 *
 * Remotion's Google Fonts helper fetches from fonts.gstatic.com at render
 * time, which makes every render depend on the network - and fails outright
 * behind a proxy whose certificate the headless browser doesn't trust.
 *
 * Injecting @font-face into the document and then waiting on
 * document.fonts.load() is the reliable route: constructing FontFace objects
 * directly can resolve before the face is actually usable for layout, and the
 * render then paints a fallback with no error to show for it.
 */
// TrueType, not woff2. Some headless Chromium builds ship without a working
// woff2 decoder: the @font-face is accepted, document.fonts reports success,
// and text silently paints in the fallback. TTF is larger and always works.
const FACES = [
  { family: "Anton", file: "fonts/Anton-Regular.ttf", weight: "400" },
  { family: "Archivo", file: "fonts/Archivo.ttf", weight: "100 900" },
];

let started = false;

export const loadFonts = () => {
  if (started || typeof document === "undefined") return;
  started = true;

  const style = document.createElement("style");
  style.textContent = FACES.map(
    (f) => `@font-face{font-family:'${f.family}';src:url('${staticFile(f.file)}') format('truetype');` +
           `font-weight:${f.weight};font-style:normal;font-display:block;}`
  ).join("\n");
  document.head.appendChild(style);

  const handle = delayRender("Loading local fonts");
  Promise.all(FACES.map((f) => document.fonts.load(`700 100px '${f.family}'`)))
    .then((results) => {
      // document.fonts.load resolves with the faces it matched. An empty array
      // means the family never registered - fail loudly rather than silently
      // rendering a fallback that looks nothing like the design.
      results.forEach((faces, i) => {
        if (!faces.length) {
          throw new Error(`font not registered: ${FACES[i].family} (${FACES[i].file})`);
        }
      });
      return document.fonts.ready;
    })
    .then(() => continueRender(handle))
    .catch((err) => {
      console.error("[fonts]", err);
      continueRender(handle);
    });
};
