import React from "react";
import { interpolate } from "remotion";
import { textWidth } from "../measure";
import { C, L, T, clampX, easeIn, fitTracking, font, panel, ramp, ts, useClock } from "./kit";

export type SeChapter = { at: number; label: string };

const CH = L.chapter;
const IDX = ts(T.chapter, 700, 0.04, true);
const OF = ts(T.chapter, 500, 0.04, true);
const NAME = ts(T.chapter, 600, 0.2);

/**
 * Chapter bar (restyled ChapterBar): glass rail top left, "03 / 07" (orange index, white 56% total),
 * the chapter name in caps, and one segment per chapter sized by its length: done white 92%,
 * pending white 22%, the current one fills orange with progress. The last chapter runs to `endAt`.
 *
 * Shown from `after` (title.until, or 0) and hidden over the 8 frames before `hideAt` (outro.at),
 * like the corner bug. `show` "always" (se-booking default) or N seconds from each chapter change.
 */
export const SeChapterBar: React.FC<{ chapters: SeChapter[]; after: number; endAt: number; hideAt: number | null; show: "always" | number }> = ({ chapters, after, endAt, hideAt, show }) => {
  const { frame, fps, s } = useClock();
  const hideF = hideAt == null ? null : Math.round(hideAt * fps);
  if (hideF !== null && frame >= hideF) return null;
  const ch = [...chapters].sort((a, b) => a.at - b.at);
  let vis = 0;
  if (show === "always") vis = ramp(s, after, after + 10 / fps);
  else {
    for (const c of ch) {
      const a = Math.max(c.at, after), b = a + Math.max(show, 0.6);
      vis = Math.max(vis, Math.min(ramp(s, a, a + 8 / fps), 1 - ramp(s, b - 8 / fps, b, easeIn)));
    }
  }
  const out = hideF === null ? 1 : interpolate(frame, [hideF - 8, hideF], [1, 0], clampX);
  const opacity = vis * out;
  if (opacity <= 0) return null;

  let cur = 0;
  ch.forEach((c, i) => { if (s >= c.at) cur = i; });
  const lens = ch.map((c, i) => Math.max(0.5, (i + 1 < ch.length ? ch[i + 1].at : endAt) - c.at));
  const prog = Math.min(1, Math.max(0, (s - ch[cur].at) / lens[cur]));
  const idx = String(cur + 1).padStart(2, "0");
  const of = ` / ${String(ch.length).padStart(2, "0")}`;
  const name = ch[cur].label.toUpperCase();
  const room = CH.width - 2 * CH.padX - textWidth(idx, IDX) - textWidth(of, OF) - CH.itemGap;
  const nameSt = fitTracking(name, NAME, room, 0.1);
  const chF = Math.round(ch[cur].at * fps);
  const swap = cur === 0 || chF <= Math.round(after * fps) ? 1 : ramp(frame, chF, chF + 8);

  return (
    <div style={{ position: "absolute", left: CH.left, top: CH.top, width: CH.width, height: CH.height, boxSizing: "border-box", padding: `0 ${CH.padX}px`,
                  display: "flex", flexDirection: "column", justifyContent: "center", gap: CH.rowGap, ...panel(false, 28), opacity }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: CH.itemGap, whiteSpace: "nowrap", lineHeight: 1 }}>
        <span style={{ ...font(IDX), color: C.accent }}>{idx}<span style={{ ...font(OF), color: C.ink56 }}>{of}</span></span>
        <span style={{ ...font(nameSt), color: C.ink, display: "inline-block", opacity: swap, transform: `translateY(${(1 - swap) * 14}px)` }}>{name}</span>
      </div>
      <div style={{ display: "flex", gap: CH.segGap, height: CH.segHeight }}>
        {lens.map((len, i) => (
          <div key={i} style={{ flexGrow: len, flexBasis: 0, minWidth: 0, height: CH.segHeight, borderRadius: CH.segHeight / 2, position: "relative", overflow: "hidden",
                                background: i < cur ? "rgba(255,255,255,.92)" : "rgba(255,255,255,.22)" }}>
            {i === cur ? <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${prog * 100}%`, background: C.accent, borderRadius: CH.segHeight / 2 }} /> : null}
          </div>
        ))}
      </div>
    </div>
  );
};
