import React, { useMemo } from "react";
import type { MotionProps } from "../../Motion";
import { FD } from "../tokens";
import { FdCallout, type FdCalloutSpec } from "./FdCallout";
import { FdCaptions, captionPhrases } from "./FdCaptions";
import { FdChapterBar } from "./FdChapterBar";
import { FdCta } from "./FdCta";
import { FdEndCard } from "./FdEndCard";
import { FdFollow, FdScanline, FdStamp } from "./FdExtras";
import { FdJobSheet, type FdTitleSpec } from "./FdJobSheet";
import { FdLowerThird, deferPastTitle, fdLowerThirdBottom, type FdLowerThirdSpec } from "./FdLowerThird";
import { FdStage, fdCopy, useClock } from "./kit";

/** MotionProps as the fd-telemetry pack reads them (element extras from ../types). */
export type FdMotionProps = Omit<MotionProps, "callouts" | "lowerThird" | "lowerThirds" | "title"> & {
  title?: FdTitleSpec;
  callouts?: FdCalloutSpec[];
  lowerThird?: FdLowerThirdSpec;
  lowerThirds?: FdLowerThirdSpec[];
};

/**
 * Formula Dynamics "Telemetry" (brand: "fd-telemetry").
 *
 * Layers, bottom to top: chapter bar > corner bug (from BrandMotion) > title (job sheet) > captions > callouts >
 * lower thirds > CTA > follow > stamps > transition (scan line) > end card.
 * Windows: chapter bar for chapterShow (3.5 s) from each chapter change, the first once the title clears, gone from outro.at;
 * captions after title.until and before outro.at; captions and chapter bar yield to CTAs; lower thirds wait for the title
 * to clear and step above captions when they overlap.
 * Ignored in this pack: keyWord, emphasis, outro.cta, outro.endCardSrc.
 */
export const FdMotion: React.FC<{ p: FdMotionProps; bug: React.ReactNode }> = ({ p, bug }) => {
  const { duration, fps } = useClock();
  const copy = useMemo(() => fdCopy(p.brandCopy), [p.brandCopy]);
  const after = p.title?.until ?? 0;
  const outroAt = p.outro?.at ?? null;
  const breaks = useMemo(() => (p.cuts ?? []).map((c) => c.at), [p.cuts]);
  const phrases = useMemo(() => captionPhrases(p.words ?? [], breaks, after, fps), [p.words, breaks, after, fps]);
  const ctas = p.ctas ?? [];
  const yields = ctas.map((c) => [c.at - 8 / fps, c.at + c.hold + 0.4] as [number, number]);
  const titleUntil = p.title ? p.title.until : null;
  const lts = useMemo(
    () => [...(p.lowerThird ? [p.lowerThird] : []), ...(p.lowerThirds ?? [])].map((l) => deferPastTitle(l, titleUntil)),
    [p.lowerThird, p.lowerThirds, titleUntil],
  );
  const chapters = p.chapters ?? [];
  return (
    <>
      <FdStage>
        {chapters.length ? <FdChapterBar chapters={chapters} after={after} total={duration} hideAt={outroAt} show={p.chapterShow ?? FD.timing.chapterShow} yields={yields} /> : null}
      </FdStage>
      {bug}
      <FdStage>
        {p.title ? <FdJobSheet t={p.title} /> : null}
        <FdCaptions phrases={phrases} until={outroAt ?? Infinity} yields={yields} haze={p.captionHaze} />
        {(p.callouts ?? []).map((c, i) => <FdCallout key={i} c={c} />)}
        {lts.map((l, i) => <FdLowerThird key={i} l={l} bottom={fdLowerThirdBottom(l, phrases)} />)}
        {ctas.map((c, i) => <FdCta key={i} c={c} copy={copy} />)}
        {(p.follows ?? []).map((f, i) => <FdFollow key={i} f={f} />)}
        {(p.stamps ?? []).map((st, i) => <FdStamp key={i} st={st} />)}
        {p.wipes && chapters.length > 1 ? <FdScanline ats={chapters.slice(1).map((c) => c.at)} /> : null}
        {p.outro ? <FdEndCard at={p.outro.at} copy={copy} /> : null}
      </FdStage>
    </>
  );
};
