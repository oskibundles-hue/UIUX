import React, { useMemo } from "react";
import type { MotionProps } from "../../Motion";
import { SE } from "../tokens";
import { SeBirthday, SeBirthdayScrim, birthdayEnd } from "./SeBirthday";
import { SeCallout, type SeCalloutSpec } from "./SeCallout";
import { SeCaptions, captionPages } from "./SeCaptions";
import { SeChapterBar } from "./SeChapterBar";
import { SeCta } from "./SeCta";
import { SeEndCard } from "./SeEndCard";
import { SeStamp, SeTransition } from "./SeExtras";
import { SeFollow } from "./SeFollow";
import { SeLowerThird, lowerThirdBottom, type SeLowerThirdSpec } from "./SeLowerThird";
import { SeTitle, SeTitleScrim, type SeTitleSpec } from "./SeTitle";
import { SeStage, seCopy, useClock } from "./kit";

/** MotionProps as the se-booking pack reads them (element extras from ../types). */
export type SeMotionProps = Omit<MotionProps, "callouts" | "lowerThird" | "lowerThirds" | "title"> & {
  title?: SeTitleSpec;
  callouts?: SeCalloutSpec[];
  lowerThird?: SeLowerThirdSpec;
  lowerThirds?: SeLowerThirdSpec[];
};

/**
 * Supercar Experience "Booking-first Luxury" (brand: "se-booking").
 *
 * Layers, bottom to top: title scrim > transition > chapter bar > corner bug (from BrandMotion) > title >
 * captions > callouts > lower thirds > CTA > follow > stamps > end card.
 * The transition passes under the chapter bar and the bug, so the brand chrome never dims.
 * Windows: captions after title.until and before outro.at, yielding to CTAs; chapter bar from
 * title.until, gone from outro.at; lower thirds step above captions when they overlap.
 * Ignored in this pack: keyWord, emphasis, outro.cta, outro.endCardSrc.
 */
export const SeMotion: React.FC<{ p: SeMotionProps; bug: React.ReactNode }> = ({ p, bug }) => {
  const { duration } = useClock();
  const copy = useMemo(() => seCopy(p.brandCopy), [p.brandCopy]);
  const after = p.title?.until ?? 0;
  const outroAt = p.outro?.at ?? null;
  const breaks = useMemo(() => (p.cuts ?? []).map((c) => c.at), [p.cuts]);
  const pages = useMemo(() => captionPages(p.words ?? [], breaks, after), [p.words, breaks, after]);
  const ctas = p.ctas ?? [];
  const yields = ctas.map((c) => [c.at - 0.25, c.at + c.hold + 0.45] as [number, number]);
  const lts = [...(p.lowerThird ? [p.lowerThird] : []), ...(p.lowerThirds ?? [])];
  const chapters = p.chapters ?? [];
  const chapterAfter = p.birthday ? Math.max(after, birthdayEnd(p.birthday)) : after;   // birthday opener: the chapter bar waits for it
  return (
    <>
      <SeStage>
        {p.title ? <SeTitleScrim t={p.title} /> : null}
        {p.birthday ? <SeBirthdayScrim b={p.birthday} /> : null}
        {p.wipes && chapters.length > 1 ? <SeTransition ats={chapters.slice(1).map((c) => c.at)} /> : null}
        {chapters.length ? <SeChapterBar chapters={chapters} after={chapterAfter} endAt={outroAt ?? duration} hideAt={outroAt} show={p.chapterShow ?? SE.timing.chapterShow} /> : null}
      </SeStage>
      {bug}
      <SeStage>
        {p.title ? <SeTitle t={p.title} /> : null}
        {p.birthday ? <SeBirthday b={p.birthday} /> : null}
        <SeCaptions pages={pages} until={outroAt ?? Infinity} yields={yields} />
        {(p.callouts ?? []).map((c, i) => <SeCallout key={i} c={c} />)}
        {lts.map((l, i) => <SeLowerThird key={i} l={l} bottom={lowerThirdBottom(l, pages)} copy={copy} />)}
        {ctas.map((c, i) => <SeCta key={i} c={c} copy={copy} />)}
        {(p.follows ?? []).map((f, i) => <SeFollow key={i} f={f} />)}
        {(p.stamps ?? []).map((st, i) => <SeStamp key={i} st={st} />)}
        {p.outro ? <SeEndCard at={p.outro.at} copy={copy} /> : null}
      </SeStage>
    </>
  );
};
