# One-way ticket: handoff for the full long-form cut, then the verticals and Shorts

Written 2026-10-08 by the session that built the opening. Branch `claude/one-way-ticket-youtube`.
Lead session: session_013JoCuN8AVJiDRcQU8W2e21 (send_message it at final delivery with card ids, bytes and SHA-256).

## Brief (Omarie's words where possible)
Style: **Lifestyle** (proposed). Personal channel @nq.young, 16:9. Personal brand only: no SE logo, HUD, strip,
end card, SE orange or gold, and no SE print on signs (blur it). The SE hoodie/jacket print is NOT blurred from Ch3 on (Omarie, 2026-10-09: "the jacket dont need blur"; Ch1, Ch2 and Ch4 keep their blur, his call). Never mix brands.

The 12 points Omarie approved (2026-10-07):
1. Hook "Running on empty", ~15 s, no text, straight into the 4:30 a.m. Uber line.
2. About 16 min.
3. About 70% talk.
4. 6-9 picture changes a minute; faster in hook and montages, 10-20 s holds on talk.
5. 2-3 word pops for the whole video. Place titles only once nq-facts and nq-second clear them.
6. One warm grade (`test-ch3/look.json`, locked).
7. One music track per chapter, up only in montages. No music on the first-sight moment. Swap to Epidemic Sound before upload.
8. The 1:29 a.m. setback stays at about 62% through.
9. Route map drawn twice, once it has a source.
10. Chapter markers plus the SE thank-you in the description.
11. The spoken outro ends the video, no card.
12. No burned-in captions on the long-form; upload a caption file from words both ASR models agree on.
    Burned-in captions on the verticals and Shorts only.

## Done so far
- **Opening: B2 v2.2 is Omarie's pick** (2026-10-08). `opening-test/` has the EDL (`edl_B2.json`), mix, render,
  `look_v2.json`, `subject_lift.py` and README (v2.2 section has the shot list). It passed nq-check three times.
  It is hook (0121 152 + 0121 199.6 desert road cutaways, 0075 56.45 + 69.32), a 30.4 s story montage
  (0091, 0093, 0102, 0105, 0107 pic/0106 audio, 0111, 0112, 0114 x2, 0115, 0118 x2, 0122), then CH1 at 0075 82.04
  with a 1.54 s J-cut. The CH1 face lift stops at source 83.0, then a natural silhouette.
- **Chapter 3 (Seattle noon) test** is approved: `test-ch3/`.
- `PLAN.md` has every chapter's spans and the facts list.

## Next job: the full cut
1. Build chapters 1-8 from `PLAN.md` behind the B2 opening, to the 12 points above. Reuse test-ch3's grade, mix and
   blur code and the opening-test render (blur `from` key, subject lift). Engine: `../../engine/vlog.py`
   (plan -> Dropbox `download_link` -> fetch, `VLOG_MEZZ_LONG=3840`).
2. Blur list already known: every cluster/TFT only while the car is moving (Omarie, 2026-10-09: "speedometer only when car
   is driving"; parked, it stays), the hoodie print NOT (see above),
   every plate, the "$6.99" billboard in 0122, the SE sign and phone number in the 0123 outro. 0116 and 0117 have
   a phone in hand in every frame: cutaway or audio only.
3. Chain: nq-build -> nq-check -> nq-facts -> nq-second. Facts to clear: Pahranagat and "Club 93", camera-clock time
   zone, the route-map source, any on-screen place or time. Spoken figures (830 miles, 18 hours, 186 miles,
   9 h 27 m, "15 and a half") stay spoken only.
4. Deliver the 4K master and the NOMUSIC master through Video Drop (https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP,
   never a second page; read it once with `path: "index.html"`), folder
   `NQ Studio/04 Exports/2026-09-26 One-way ticket YouTube`, v1/v2 names kept side by side. Then send_message the lead.
5. Open a draft PR for this branch and subscribe to it.

## After that: verticals and Shorts (9:16, burned-in captions from words both ASR models agree on)
Shorts candidates: the first sight and sound (0090), "No cell service…" (0117), "We're in Oregon!" (0100),
the 1:29 a.m. setback (0114/0115), and the B2 montage recut to 9:16.

## Survey data the next session needs
The survey data (word transcripts `tr/`, `flags.json`, `moments.*`, `day.md`, `clips.*`, `speakers.json`, `shz.py`)
is in the private repo `oskibundles-hue/nq-agent-channel`, branch `data/one-way-ticket-survey`, folder
`handoff/2026-09-26-one-way-ticket/` (Omarie, 2026-10-08). Attach that repo and copy the folder to
`/home/user/day-owt/`. `tags.md` here holds the survey tags.

## Lessons for the next session (token rules)
- Give builders a lean brief and a turn budget that fits; the montage builder hit 100 turns once and grew to
  ~224k context. Split big builds per chapter, each a fresh agent from a short summary.
- Write Dropbox links straight to `links/N.json`; don't read them back into the lead.
- Disk: about 2.5 GB was free at the end here. A 4K full cut needs a fresh container.
