# Artifacts review — 2026-10-06 (read-only; nothing changed)

Scheduled routine, no one live. Per your instruction ("do not post, send, or change
anything without my approval") I read only. Nothing was published, moved, retired or
pushed. The one write I made is this session's own Working-now card on the control room
(`work/s_01PfuZbz…`), which is your standing rule for any job past a couple of minutes.

This file is a draft on disk only (not committed, not pushed). The container is
ephemeral — say the word and I commit it to `claude/eloquent-ptolemy-p44a4v`.

---

## 1. The brief, as I read it

1. **Organize the artifacts page chronologically** — critical changes, information, rules
   and finished videos pulled together from the artifact gallery.
2. **Find duplicates, outdated content, items no longer in use.**
3. **Archive, never delete.** Superseded items move to a labelled Archive section stating
   what replaced them and when. Links stay live, files stay put, rows are never removed.
   No page is ever retired whole — it gets a "reference / superseded" banner. Only
   exception: a genuinely dead pointer, which gets repointed or annotated.
4. **Any large sweep is proposed first, with a reason per item, and waits for your yes.**
5. **Update the approved-work memory** from every session, so the things that work and
   their style are remembered.
6. **Answer the open questions, and recommend what to do.**

Already decided (not re-asked): archive over delete; links stay live; no page retired
whole; banner instead of removal; approval before any sweep; results shown in chat.

---

## 2. Three things blocked part of the job

| Blocker | Effect |
|---|---|
| **Source list in your prompt is an unfilled placeholder** — "[ADD: Dropbox folders? Drive? Gmail? — name them or say 'artifacts only']" | I ran it as **artifacts only**. Dropbox, Drive and Gmail connectors are live in this session, so say the word and I sweep them too. (Indeed and Lovable failed to connect — unrelated to this job.) |
| **No past session transcripts in a cloud container.** `/root/.claude/projects/` holds this session only; a cloud container clones the repo fresh. | "Thoroughly go through every session" cannot be done from a cloud routine. I reconstructed the approved-work history from the control room's own archive (82 settled items), HOUSE-STYLE.md, and the git log instead — see §6. |
| **The second brain is not attached.** `recall.py` → "No second-brain notes found… attach `oskibundles-hue/nq-agent-channel`." | Every fact below is traced to the control room page, HOUSE-STYLE.md, this repo or the gallery — not to your notes. Attach that repo to scheduled sessions and the next run is much sharper. |

---

## 3. The gallery, chronologically (newest first)

47 pages: 46 yours, 1 shared with you. Dates are **last updated**, which is what the
gallery exposes — not created. Status column: **LIVE** = current, keep; **REF** =
superseded, keep with a banner; **ARCH?** = proposed for the Archive section;
**WAIT** = waiting on your decision; **DEAD** = pointer to something gone.

Confidence is marked: ✔ verified this run from page content or the control room's own
record; ○ read from the title and date only (I did not open it, to keep this run cheap).

### 6 Oct
| Page | Status | Note |
|---|---|---|
| control-room (NQ OS) | LIVE ✔ | The hub: 4.2 MB, 78 files, 30 sections, already has `#archive` "Past approved work" (82 items, newest first) and a Styles tab. Also where the artifacts index belongs — see §7. |
| NQ Jarvis V2 | LIVE ✔ | Brain note in the page: runs the real claude.ai Jarvis since 2026-09-25; "never republish an old copy". |
| Video Drop | LIVE ✔ | The one delivery page for videos, per CLAUDE.md. Never make a second. |
| Layout Library | REF ✔ (ask) | The control room says "merged into this tab on 5 Oct (46 rows); open it for the HUD clips". But it was updated **6 Oct**, after the merge — so it may still be live. Question 4. |
| Style Library Preview | ○ | Same-day sibling of the Styles tab merge. Unverified — I did not open it. |
| NQ OS Token Ledger | ○ LIVE | Cost work shipped 5–6 Oct (token meter, cost guard, 300k compact). Likely current. |

### 5 Oct
| Page | Status | Note |
|---|---|---|
| Race Weekend Storyboard | LIVE ○ | `race-weekend` is an approved layout (HOUSE-STYLE, 3 Oct). Pinned. |
| Wayline HUD | ○ | Unverified. |
| NQ OS Layout Options | ARCH? ○ | Decision page; the layout shipped. |
| NQ OS Creations | WAIT ✔ | Its own banner: "For your approval. Nothing is built." 10 built creations + 8 ideas needing your yes. Do **not** archive — it is waiting on you. |

### 4 Oct
| Page | Status | Note |
|---|---|---|
| Formula Dynamics Job Board | LIVE ○ | Pinned; the Render cache-header row (4 Oct) in the control room is about this. |
| Motion Capabilities | REF ✔ | Control room: "merged into this tab on 5 Oct (41 rows); open it for the short clips". |
| Yahoo Cleanup Pass 2 | ARCH? ○ | Task page, pass 2 — the newer of the pair. Job appears finished (134 of 187 unsubscribes done). |
| Content Surveyor | ○ | The control room has a `#surveyor` section; this page may be its mockup ancestor. Unverified. |

### 3 Oct
| Page | Status | Note |
|---|---|---|
| Scroll Hero Variations | ARCH? ○ | Exploration set. |
| GT3 RS Scroll Hero | ARCH? ○ | Exploration set. |
| NQ OS Glass Preview | ARCH? ✔ | The glass command bar shipped into the control room on 2026-10-03 (its CSS carries the dated comment and a rollback backup). The preview's decision is spent. |
| Yahoo Inbox Cleanup | ARCH? ✔ | Superseded by **Yahoo Cleanup Pass 2** (4 Oct). |

### 1–2 Oct
| Page | Status | Note |
|---|---|---|
| Chase AI Skill Audit | LIVE ✔ | Cited as the source of the Higgsfield prompt-craft creation (30 Sep). Pinned, still referenced. |
| Plugin Cleanup | ARCH? ✔ | A round-2 checklist page; the control room still carries one open row ("switch off Cowork Plugin Management"). Archive only once that row is ticked. |
| September 2026 Progress Report | LIVE ○ | A period report — by nature historical, keep as a dated record, not an archive candidate. |
| NQ OS vs Hermes Layouts | REF ✔ | Round-two verdict; five items explicitly deferred ("leave as backlog"). Reference, not active. |

### 29–30 Sep
| Page | Status | Note |
|---|---|---|
| Locked-On Standard | LIVE ✔ | **The standard for every job**, every workstream (CLAUDE.md, HOUSE-STYLE, both agent briefs). Never archive. |
| Black Hex Garage, Hermes Agent Assessment, Rally Ad Mockups, Car Trace Six Ways, Agent Video Research, Download Everything, FD Reel Clock, FD Master Record | mixed ○ | Car Trace is a **live kit move** (vlog kit C4, in the Styles tab) — its "Six Ways" chooser page is the spent decision, not the move. Download Everything looks like a finished one-off. The rest unverified. |
| Mac Takeover Guide (28 Sep) | ARCH? ○ | A how-to for a setup that has since happened. |
| Claude Showreel 2026 (26 Sep) | ○ | Unverified. |
| Options Traders Academy Ad (27 Sep) | LIVE ○ | Side project, not NQ/FD/SE (control room: filed under `Dropbox/Side Projects/`). Keep separate from the NQ chronology. |
| Dropbox Finder (27 Sep) | LIVE ✔ | Feeds the approved.json list the daily librarian rebuilds. Pinned, active. |

### 10–14 Sep
| Page | Status | Note |
|---|---|---|
| FD Overlays, SE Overlays, Brake Poster Pick, Sep 10 Story Cut, SE Deliverables, Ad Ratios Filing Sheet, Behind The Build, The Branded Cut, FD Ad Room, Osmo to Reel | mixed ○ | Ad Ratios is still a **live filing convention** (`Portfolio/06 Send to Boss/07 Ad Ratios/…` paths are in current state). FD Overlays is pinned. The rest are September delivery pages — historical by nature. |
| **Fast Cut** (10 Sep) | ARCH? ✔ (conflict) | You retired it: *"i dont need fastcuts anymore thats a old model and or aventador clips"*. **But CLAUDE.md still lists Fast Cut as an approved Anti Stock format.** Question 3 before anything moves. |
| OTA 7-Day Launch (shared with you) | LIVE ○ | Someone else's page; not yours to archive. |

---

## 4. Duplicates, outdated, no longer in use

1. **Yahoo Inbox Cleanup → Yahoo Cleanup Pass 2.** Same job, two pages, one day apart. ✔
2. **Layout Library + Motion Capabilities → the control room's Styles tab** (merged 5 Oct,
   46 + 41 rows). The control room already calls them "Older reference pages" — the
   banner just isn't on the pages themselves. ✔
3. **The NQ OS look-and-feel exploration set** — NQ OS vs Hermes Layouts (2 Oct), Glass
   Preview (3 Oct), Scroll Hero Variations (3 Oct), GT3 RS Scroll Hero (3 Oct), Layout
   Options (5 Oct). Five pages, one question each, all decided; the glass bar is verifiably
   shipped. They are records of decisions, not live tools.
4. **Four dead pointers in the control room's own memory** (§5). ✔
5. **Fast Cut** — retired by you, still named as approved in CLAUDE.md. A live
   contradiction, not just a stale page. ✔
6. **No duplicate of the control room, Locked-On Standard, Video Drop or NQ Jarvis V2** —
   the four load-bearing pages are each singular, which is the thing that matters most. ✔

---

## 5. Dead pointers (the one deletion exception) — propose annotate, not remove

Four artifact links inside the control room's memory notes return
"artifact not found — it may have been deleted". I checked each one:

| Linked as | ID | Verdict |
|---|---|---|
| Jarvis command view, mockup A "Chase look" | `8i5m5hV1ZgkyUUhAB2esVJ` | gone ✔ |
| Jarvis command view, mockup B "Locked-On fonts" | `5fAYpqTwmL8YERSw3LH22b` | gone ✔ |
| Jarvis command view, mockup C **(the one you chose)** | `2yTgReHkaShCd4B6NeDsRR` | gone ✔ |
| V.A.U.L.T. dashboard layout mockups (you leaned to B, "Wordmark monochrome") | `NqAaGwQFKCiLVHe7UqDxGr` | gone ✔ |

Proposed annotation (your approval needed — it edits the control room's note text):

> Mockup pages A/B/C were deleted after the build. The shipped version is the control
> room's own Command view (`#hud`, command view v2, 2026-09-30, mockup C as approved:
> sparse, no boxes, 4–6 skills) with rollback `Agentic OS/template.html.bak_2026-09-30_cmdview`.
> V.A.U.L.T. mockups likewise: the chosen look is B "Wordmark monochrome"; no page survives.

That keeps the decision and the reason even though the pictures are gone. Nothing deleted.

---

## 6. Approved-work memory — what exists, and what is missing

Three stores hold "what works and its style". They do not agree.

| Store | Covers | State |
|---|---|---|
| Control room `#archive` "Past approved work" | 82 settled items, newest first, with date + where it lives | **Current** — rows through 6 Oct ✔ |
| Control room Styles tab (Looks / Layouts / Moves / Story shapes / Sound / Grades / Proven mixes) | Approved looks and the mixes that worked (Locked-On Vlog 29 Sep, Kinetic set 21 Sep…) | **Current** ✔ |
| `HOUSE-STYLE.md` feedback log | The ads/vlog standard and every reaction you've given | **Stale and hidden** ✔ |

HOUSE-STYLE.md problems, all verified:
- **Last feedback row is 2026-10-03.** Nothing from 4, 5 or 6 Oct, although the control
  room records approvals on each of those days.
- **It is SE-only.** Zero mentions of Formula Dynamics; one of Anti Stock. FD has its own
  approved rules (music-only on real-footage commercials) recorded nowhere in it.
- **It lives only on branch `claude/supercar-rental-ad-graphics-o64vo3`**, so a session on
  any other branch cannot read the thing CLAUDE.md tells it to read.
- **Nothing about page/UI style**, although the iPhone index layout is a standing rule.

Rows I propose adding (drafted from the control room's own record; each needs your yes):

| Date | Thing | What you said / what was settled |
|---|---|---|
| 2026-09-28 | iPhone index layout for any index, directory or deliverables page | "save this apple layout it looks so nice" / "i love it" — Apple system font, iOS colours, tab bar, one search. `design-systems/iphone-index/`, run `qa.js` before publishing |
| 2026-09-29 | FD real-footage commercials (MC20 "How PPF goes on", GT3 RS "In the bay") | "i think we should take the animation sounds out but the videos look great lets add some music instead" — **music only** on real-footage FD commercials; AI-generated clips keep their generated audio and are labelled AI |
| 2026-10-03 | Control-room glass command bar + live usage meter | "fix the command center text box hud it gets in the way" and "add a live usage meter glass ui onto the dash" — frosted pill resting slim, opens on use, never closes while working; rollback backups kept |
| 2026-10-05 | FD SF90 full detail ad (28 s, detailing layout) | "go". Music: donovano type beat from his Downloads |
| 2026-10-05 | ECU tuning service ad (AI, story-driven) | Approved with one change: rev shot instead of the flames card |
| 2026-10-05 | F1 race-weekend Night v5 (RENT) recipe | Approved; the two hook placements outside the 4:5 band (+12 px, +43 px) approved as named exceptions — every new layout stays strict |
| 2026-10-06 | Plan-card stop limit | You said "build #1": `--cap "250k tokens / 45 min"` + `cap-check --step` at each build step |

---

## 7. Where the artifacts page should live (recommendation)

There is **no artifacts index page today** — I checked all 47 titles against the control
room and only 7 artifacts are linked from it at all. So "the artifacts page" is a page
that does not exist yet, or it means the control room itself.

Recommendation: **one Artifacts block inside the control room**, not a new page. It
already has the Archive section, the "Older reference pages" pattern, and your eyes are
already on it. A second index page is the duplicate problem this job is meant to fix.

Per your standing rule, an index/directory page gets the **iPhone index layout** first
(`design-systems/iphone-index/`, `qa.js` before publishing) — but the rule also says ask
which style first, so that is Question 1.

---

## 8. Archive proposal — nothing moves until you say yes

Item 5 of your prompt: a sweep is proposed with a reason per item and waits. Here it is.
Every row keeps its link live, keeps its files, keeps its row. Nothing is deleted.

| # | Item | Reason | Replaced by, when |
|---|---|---|---|
| A1 | Yahoo Inbox Cleanup | Same job, earlier pass | Yahoo Cleanup Pass 2, 2026-10-04 |
| A2 | Layout Library | Merged into the Styles tab (46 rows) — **hold if you're still editing it (updated 6 Oct)** | Control room Styles tab, 2026-10-05 |
| A3 | Motion Capabilities | Merged into the Styles tab (41 rows) | Control room Styles tab, 2026-10-05 |
| A4 | NQ OS Glass Preview | Decision shipped into the page | Control-room glass command bar, 2026-10-03 |
| A5 | NQ OS vs Hermes Layouts | Round-two verdict; 5 items deferred as backlog by you | Control room; backlog, 2026-09-21 |
| A6 | NQ OS Layout Options | Decision page, layout chosen and shipped | Control room, 2026-10-05 |
| A7 | Scroll Hero Variations | Exploration set, choice made | GT3 RS Scroll Hero → shipped hero, 2026-10-03 |
| A8 | Mac Takeover Guide | A how-to for a setup since completed | — (done, 2026-09-28) |
| A9 | Download Everything | One-off task page, task finished | — (done, 2026-09-29) |
| A10 | Fast Cut | You retired fast cuts — **blocked on Question 3** | — |
| A11 | Plugin Cleanup | Checklist page — **hold**, one row still open in the control room | — |
| A12 | 4 dead mockup links | Pages deleted; annotate in place (§5) | Shipped Command view / NQ Jarvis V2 |

**Not proposed for archive, deliberately:** control room, Locked-On Standard, Video Drop,
NQ Jarvis V2, Dropbox Finder, FD Job Board, Race Weekend Storyboard, Chase AI Skill
Audit, Ad Ratios Filing Sheet, FD Overlays, NQ OS Creations (waiting on you), September
Progress Report (a dated record), Options Traders Academy Ad (side project), OTA 7-Day
Launch (not yours). Nine of the ARCH? rows above I judged from title and date only (○ in
§3); A2–A5 and A1 I verified. If you want certainty on the ○ ones before they move, I
open each page first — about 10 reads.

---

## 9. Questions you didn't get to

1. **Which page is "the artifacts page"?** → Recommend: a new Artifacts block on the
   control room (§7). And which style — iPhone index (my pick, your standing rule for
   index pages), or Locked-On?
2. **Sources**: artifacts only (what I did), or also Dropbox folders / Drive / Gmail?
   → Recommend artifacts + the Dropbox finished-video list, skip Gmail and Drive.
3. **Fast Cut**: retired everywhere, or only the SE/Aventador MR1–MR8 files? CLAUDE.md
   still names it an approved Anti Stock format. → Recommend: keep the *format* approved
   for Anti Stock, archive the September deliverable page. Your call.
4. **Layout Library** was updated today, after being merged. Still live, or safe to banner?
5. **HOUSE-STYLE.md on the default branch?** → Recommend yes: CLAUDE.md tells every
   session to read it, and today only one branch has it.
6. **One source of truth for approved work?** → Recommend: control room Styles +
   Past approved work is the index; HOUSE-STYLE stays the ads/vlog detail, and gets FD
   and Anti Stock sections.

## 10. What I'd do, in order

1. Answer Q1–Q2 (one click). Everything else follows from those.
2. Annotate the 4 dead pointers (§5) — smallest change, biggest honesty gain.
3. Add the 7 HOUSE-STYLE rows (§6) and move that file to the default branch.
4. Build the Artifacts block on the control room: chronological, with an Archive section,
   and the A-list above moved into it with reasons.
5. Attach `nq-agent-channel` to scheduled sessions, so routines can read your notes.
6. Stop expecting any cloud routine to read past sessions — it starts with none. Keep the
   weekly correction audit / post_mortem on the Mac, where the transcripts live.

**Status: the artifacts page is NOT yet clean or organized — because organizing it means
changing it, and you said not to without approval.** Everything is proposed, nothing done.
