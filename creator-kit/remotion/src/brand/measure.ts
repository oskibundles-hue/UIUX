/**
 * Text measurement for brand layouts (canvas measureText, cached). No side effects at import.
 *
 * Deterministic once the brand face is loaded. Components that measure are rendered only
 * after useBrandFonts() reports ready (see BrandMotion), so a fallback width is never
 * measured or cached. Chrome adds CSS letter-spacing after every character, so tracking
 * is counted once per character. Tabular figures are approximated by measuring each digit as "0".
 */
export type TextStyle = { size: number; weight: number; family: string; tracking?: number; tabular?: boolean };

let ctx: CanvasRenderingContext2D | null = null;
const cache = new Map<string, number>();

export const textWidth = (text: string, t: TextStyle): number => {
  const s = t.tabular ? text.replace(/[0-9]/g, "0") : text;
  const key = `${t.weight}|${t.size}|${t.family}|${t.tracking ?? 0}|${s}`;
  const hit = cache.get(key);
  if (hit !== undefined) return hit;
  if (ctx === null) ctx = document.createElement("canvas").getContext("2d");
  let base = s.length * t.size * 0.56;
  if (ctx) {
    ctx.font = `${t.weight} ${t.size}px ${t.family}`;
    base = ctx.measureText(s).width;
  }
  const width = base + [...s].length * (t.tracking ?? 0) * t.size;
  if (ctx) cache.set(key, width);
  return width;
};
