# Artifacts page — one decision, nine reports deep

**Page:** Download Everything — https://claude.ai/artifact/QzgoR9wsQGonTidm9vX6m2
**Run:** scheduled sweep, 24 Oct 2026. Read-only.
**Nothing was posted, sent, published or changed.** The page is exactly as it was.

---

## Read this part only

The sweep you scheduled has produced the same review nine times. **Eight of them are
open draft pull requests right now**, going back to 5 Oct, and not one has been
applied — each ends by waiting for a yes that has not come. This is the ninth.

| Report | PR | State |
|---|---|---|
| 5 Oct review | [#31](https://github.com/oskibundles-hue/UIUX/pull/31) | open draft, unapplied |
| 6 Oct — inventory, archive proposals, memory gaps | [#38](https://github.com/oskibundles-hue/UIUX/pull/38) | open draft, unapplied |
| 9 Oct review | [#50](https://github.com/oskibundles-hue/UIUX/pull/50) | open draft, unapplied |
| 10 Oct review | [#52](https://github.com/oskibundles-hue/UIUX/pull/52) | open draft, unapplied |
| 12 Oct sweep | [#58](https://github.com/oskibundles-hue/UIUX/pull/58) | open draft, unapplied |
| 13 Oct sweep (itself a consolidation of **six** earlier reports) | [#68](https://github.com/oskibundles-hue/UIUX/pull/68) | open draft, unapplied |
| 14 Oct review | [#71](https://github.com/oskibundles-hue/UIUX/pull/71) | open draft, unapplied |
| **22 Oct review — the standing proposal, still accurate** | [#74](https://github.com/oskibundles-hue/UIUX/pull/74) | open draft, unapplied |
| 24 Oct (this one) | this PR | asks for the yes |

Writing a tenth would be the wrong thing to do, so this one does not re-review the
page. It asks for the decision and then recommends the routine be changed.

I re-ran the whole audit from scratch today and independently reproduced the 22 Oct
findings: **22 missing rows, 5 pages carrying more than one row, 15 rows to archive,
1 dead pointer.** That report is correct and complete. This file does not restate it.

**So there is nothing left to review. There is one decision:**

> **Apply the 22 Oct proposal to the page?** It adds the missing day groups, adds one
> labelled Archive section (rows stay in the chronology too), re-points the one dead
> link, and re-stamps the counts. Nothing is deleted, no page retired, no link broken.

Reply **"apply it"** and it goes up in one edit. Reply with changes and I'll amend first.
The two questions that need you regardless are at the bottom.

**And then change the routine**, because a read-only sweep that cannot apply its own
findings will keep producing these. Three options, my pick first:

1. **Let the sweep apply the mechanical half itself** — add missing rows, re-stamp dates
   and counts, annotate dead pointers — and keep asking before anything is archived,
   re-pointed or re-statused. Those additions are reversible, and the page's own history
   blocks already record who added what and when. This is what I'd do.
2. **Keep it read-only but make it update one page instead of opening a PR** — the sweep
   rewrites a single standing "artifacts page: what needs your yes" page each run, so
   there is one thing to read rather than a growing pile.
3. **Turn the schedule off** and run the sweep when you ask for it.

Either way, PRs #31 through #74 should be closed once this decision lands — their
findings are either folded in here or superseded by it. I have not closed them.

---

## What changed in the two days since the 22 Oct report

1. **The page has not been touched.** Its dated spine still ends **Tue 13 Oct** — now
   **11 days** stale, where the 22 Oct report said nine.
2. **Approved work kept accumulating somewhere else.** The control room's "Past approved
   work" archive read **337 items** on 22 Oct; today it reads **347**. Ten more
   approvals in two days, none of them recorded on the artifacts page or in the
   house-style log.
3. **One new stale row.** **Dropbox Finder** (`PhiU7AGWbxCrB59C8EcHin`) was updated
   **23 Oct** but its row is filed under **Sep 27** and still reads Current. That makes
   the "row older than the page it points at" list **11 rows**, not 10.
4. **No new artifacts** were published on 23–24 Oct, so the missing-row count is
   unchanged at 22 (plus Download Everything's own hrefless self-row).

Nothing in the 22 Oct proposal is invalidated by any of this. It only got more overdue.

---

## Your item 8, and why it is the one thing I would not postpone

You asked to go through every session and record approved work and the style of it, so
there is memory of what works. **That memory exists in three places and all three have
stopped at different dates:**

| Record | Holds | Last entry | Behind |
|---|---|---|---|
| Control room "Past approved work" | 347 approvals | 24 Oct (live) | current |
| Artifacts page → Rules tab | 66 standing rules | **7 Oct** | 17 days |
| `HOUSE-STYLE.md` feedback log (SE branch) | your words per approval, the reason a settled look is never re-litigated | **3 Oct** | **three weeks** |

The feedback log is the one that matters most and has decayed worst. It is the file that
stops a future session re-asking a question you already answered — and it has no record
of anything approved in the last three weeks. The approvals are not lost (the control
room has them), but they are logged as *events*, not as *"this look is approved, in these
words, for this kind of job"*, which is what a builder reads before it starts.

**What I cannot do, plainly:** I have no tool that enumerates your past chat sessions. I
can read the artifact gallery, this repo and its branches, and the pages themselves — and
I did. "Every session" can only be reconstructed from what those leave behind. If the
second brain were attached (`oskibundles-hue/nq-agent-channel`, folder `brain/`) that
would close most of the gap; `recall.py` returns no notes in this session, so nothing here
was checked against your notes.

**Recommendation:** let me bring the feedback log and the Rules tab up to 24 Oct from the
control room's 347-item archive and the dated rules already in `CLAUDE.md` (the post
mockup, 10 Oct; the studio carousel, 13 Oct; the Video Drop auto-save; "do it for him
unless only he can", 20 Oct). That is a repo edit plus one page edit, and it waits on your
word like everything else.

---

## The two questions that block work regardless of the decision above

1. **Scope — still a blank in the prompt.** The source list in the scheduled task reads
   *"the artifact gallery, [ADD: Dropbox folders? Drive? Gmail? — name them or say
   artifacts only]"*. It has never been filled in, so four runs have now read **the
   gallery only**. Say **"artifacts only"** and the scope stops being a question. I'd add
   Dropbox: it holds the finished videos, 26 file rows have no Dropbox copy, and the
   K1–K6 kits are still only chat attachments, which is not storage.

2. **The 17 edit styles.** On **NQ Edit Styles** — the page other sessions read before
   they edit — 17 styles carry your own words of approval (*"this is great approve it"*,
   *"all 3 are approved ads and styles continue"*, *"yes to the 14"*) but now read
   **"Not now"**, and 34 read Approved with no words of yours recorded. The buttons are
   toggles, so a fast pass down the list would produce exactly this. It matters now
   because the Two-a-Day trial run is built on *"one video for each of the 66 edit styles
   you approved"* — and that 66 includes the 34 unquoted ones and excludes the 17 quoted
   ones. **Everything the reel builder makes next rests on this.** I will not write to
   that database without your word.

The remaining open questions — the Formula Dynamics poster route (those posters all print
the parts-store domain on service ads), the SE accent colour, the top keep-out, the vlog
standard, the Posting Calendar pick — are unchanged and listed in full in §7 of the 22 Oct
report.

---

## Item 7: is the page clean and organized?

**No, and I did not make it so, because that needs your yes.** The chronology ends 13 Oct,
the counts still read "73 pages" against 94 in the gallery, and the Archive section does
not exist yet. That is one edit, already written and waiting.
