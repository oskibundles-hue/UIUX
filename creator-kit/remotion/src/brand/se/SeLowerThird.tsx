import React from "react";
import type { LowerThirdSpec } from "../../Motion";
import type { BrandLowerThirdFields } from "../types";
import { textWidth } from "../measure";
import { captionTop, type CapPage } from "./SeCaptions";
import { ArrowUpRight, C, H4, L, LABEL, LINING, SAFE, T, bracket, easeIn, fitSize, font, panel, ramp, rich, ts, useClock, type SeCopy } from "./kit";

export type SeLowerThirdSpec = LowerThirdSpec & BrandLowerThirdFields;

const LT = L.lowerThird;
const KICK = ts(T.lowerThirdKicker, 600, 0.26);
const TITLE = ts(T.lowerThirdTitle, 700, -0.022);
const META = ts(T.lowerThirdMeta, 500);
const META_B = ts(T.lowerThirdMeta, 700);
const BOOK_K = ts(T.lowerThirdBookK, 800, 0.22);
const BOOK_V = ts(T.lowerThirdBookV, 600);

/**
 * Collision rule: the design puts the lower third in the caption band (bottom 2892). When any
 * caption page overlaps the lower third's window, the whole lower third sits above the tallest
 * such caption panel (40 px gap) for its entire hold, so speech stays captioned and nothing jumps.
 */
export const lowerThirdBottom = (l: { at: number; hold: number }, pages: CapPage[]): number => {
  const t0 = l.at, t1 = l.at + l.hold + 0.5;
  const lines = pages.reduce((m, p) => (p.start < t1 && p.tailEnd > t0 ? Math.max(m, p.lines.length) : m), 0);
  return lines ? Math.min(LT.bottom, captionTop(lines) - LT.aboveCaptions) : LT.bottom;
};

/**
 * Lower third (restyled): solid panel; eyebrow row (orange bracket label + caps kicker white 72%),
 * 132 px title, meta row 54 px with orange dots between items; light #EEEEEF book block on the
 * right ("Reserve"/"Book" + orange up-right arrow, site below). Fleet and city variants differ only
 * in their defaults. Legacy-shaped props (title + sub) render as title + one meta line.
 */
export const SeLowerThird: React.FC<{ l: SeLowerThirdSpec; bottom: number; copy: SeCopy }> = ({ l, bottom, copy }) => {
  const { frame, fps, s } = useClock();
  if (s < l.at || s > l.at + l.hold + 0.5) return null;
  const f0 = frame - Math.round(l.at * fps);
  const inK = ramp(f0, 0, 16);
  const bookK = ramp(f0, 6, 20);
  const out = ramp(s, l.at + l.hold, l.at + l.hold + 0.4, easeIn);

  const variantLabel = l.variant === "fleet" ? "In the fleet" : l.variant === "city" ? "Pick-up" : undefined;
  const labelRaw = l.label ?? variantLabel;
  const labelText = labelRaw ? bracket(labelRaw) : "";
  const kicker = (l.kicker ?? "").toUpperCase();
  const meta = (l.meta ?? (l.sub ? [l.sub] : [])).filter(Boolean);
  const metaParts = meta.map(rich);
  const book = l.book === false ? null : { k: (l.book?.k ?? (l.variant === "fleet" ? "Reserve" : "Book")).toUpperCase(), v: l.book?.v ?? copy.site };
  const bookW = book ? Math.max(LT.bookWidth, Math.ceil(Math.max(textWidth(book.k, BOOK_K) + 16 + LT.icon, textWidth(book.v, BOOK_V)) + 2 * LT.bookPadX)) : 0;
  const maxMain = SAFE.right - SAFE.left - bookW - 2 * LT.padX;
  const titleSt = fitSize([l.title], TITLE, maxMain, 96);
  const hasEyebrow = !!(labelText || kicker);

  return (
    <div style={{ position: "absolute", left: LT.left, bottom: H4 - bottom, display: "flex", alignItems: "stretch", overflow: "hidden", ...panel(true, LT.radius),
                  opacity: (1 - out) * Math.min(1, inK * 1.4), transform: `translateX(${(1 - inK) * -48 - out * 36}px)`,
                  clipPath: `inset(0 ${(1 - inK) * 100}% 0 0 round ${LT.radius}px)` }}>
      <div style={{ padding: `${LT.padT}px ${LT.padX}px ${LT.padB}px`, whiteSpace: "nowrap", maxWidth: maxMain + 2 * LT.padX, boxSizing: "border-box", overflow: "hidden" }}>
        {hasEyebrow ? (
          <div style={{ display: "flex", alignItems: "center", gap: LT.eyebrowGap, lineHeight: 1 }}>
            {labelText ? <span style={{ ...font(LABEL), color: C.accent }}>{labelText}</span> : null}
            {kicker ? <span style={{ ...font(KICK), color: C.ink72 }}>{kicker}</span> : null}
          </div>
        ) : null}
        <div style={{ ...font(titleSt), lineHeight: 1, marginTop: hasEyebrow ? LT.titleGap : 0 }}>{l.title}</div>
        {meta.length ? (
          <div style={{ display: "flex", alignItems: "center", gap: LT.metaItemGap, marginTop: LT.metaGap, ...font(META), lineHeight: 1.2, color: C.ink84, ...LINING }}>
            {metaParts.map((parts, i) => (
              <React.Fragment key={i}>
                {i ? <i style={{ display: "block", width: LT.dot, height: LT.dot, borderRadius: LT.dot / 2, background: C.accent, flex: "none" }} /> : null}
                <span>{parts.map((p, k) => (p.bold ? <b key={k} style={{ fontWeight: META_B.weight, color: C.ink }}>{p.text}</b> : <React.Fragment key={k}>{p.text}</React.Fragment>))}</span>
              </React.Fragment>
            ))}
          </div>
        ) : null}
      </div>
      {book ? (
        <div style={{ width: bookW, flex: "none", boxSizing: "border-box", background: C.light, color: C.ground, padding: `0 ${LT.bookPadX}px`,
                      display: "flex", flexDirection: "column", justifyContent: "center", gap: LT.bookGap }}>
          <div style={{ ...font(BOOK_K), lineHeight: 1, display: "flex", alignItems: "center", justifyContent: "space-between", opacity: bookK }}>
            <span>{book.k}</span>
            <span style={{ transform: `translate(${(1 - bookK) * -10}px, ${(1 - bookK) * 10}px)` }}><ArrowUpRight size={LT.icon} color={C.accent} /></span>
          </div>
          <div style={{ ...font(BOOK_V), lineHeight: 1.1, color: "rgba(15,16,20,.68)", whiteSpace: "nowrap", opacity: bookK }}>{book.v}</div>
        </div>
      ) : null}
    </div>
  );
};
