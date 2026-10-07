# Handoff: "One-way ticket" v2 of both episodes (Omarie's notes, 6 Oct 2026)

Omarie watched Part 1 and Part 2 on 6 Oct: "you did real well, the content is postable for Supercar Experience". These are his notes for a v2 of **both** episodes. Part 1 v1.1 (`HANDOFF-part1-v1.1.md`) is folded into this job, so read it too: Part 1 v2 carries the voice fixes A and B.

**Style is unchanged** (rally v2 + HUDs, dark glass, SE orange #FF4F16, MCLAREN 600LT). Don't ask about it again.

## His notes, and what each one means

1. **Music.** "replace the filler music, id like to hear some music that im jamming too in the car, and some driving with the exhaust sound as well".
   - Drop the rally library track in both episodes.
   - The music bed becomes his own in-car audio (the stereo he's playing in the cabin clips), plus stretches where the exhaust carries it, with the voice ducking it as now.
   - Find the in-car music spans and the best exhaust spans from the transcripts and audio, and from the survey: `engine/` index, flags, loudness.
   - **His click (6 Oct): "Use it, flag the tracks".** List every track the build can identify (title and artist where possible, with timecodes) for him to check before posting. Also export a **voice + exhaust only, no music** version of each episode as a fallback, because commercial tracks can get a business-page post muted.
2. **Part 1, CH 01 title.** WHEELS UP "doesn't make sense". **His click: the CH 01 card reads ONE-WAY TICKET.** CH 02 THE PICKUP and CH 03 HIT THE ROAD stay.
3. **Part 2, missing moments.** "i got no clips of me taking a break eating, or just some 1 on 1 time with you guys". Add:
   - the food break, which is In-N-Out at 19:53, clips 0105–0108;
   - one or more talk-to-camera moments where he speaks to the viewers.
   Find them in `/tmp`-surveyed transcripts, or re-survey 0103–0123 with the engine; the Part 2 survey container may be gone. Hands, phone, speedo and two-model caption rules still apply. This also brings Part 2 back toward the 2:45 aim (it's 2:25 now).
4. **The sidebar, both episodes.** "i dont like the sidebar on both episodes i thought we went over that and took it out and made a new progress bar".
   - On 5 Oct he replaced the side rail with the clock-scrubber progress bar in the dark-glass strip (`../hud-layouts/README.md`: A2 `"rail": false`, PRG `underline`, then the One-strip `drive_strip.js` with the progress scrubber built in).
   - The vlogs still carry the rally v2 side rail or chapter sidebar (`v2kit`). Remove it from both episodes and use the strip's progress scrubber as the one progress element, all the way through the episode, not only on HUD shots.
   - Confirm which element he means on one contact sheet before changing it. If it's ambiguous, the lead asks him with a still.
5. **Voice fixes in Part 1** (from `HANDOFF-part1-v1.1.md`):
   - fix A, the tails (gap of 350 ms or more, check fails under 300 ms);
   - fix B, the voice chain.
   Part 2 already has both.

## How to run it

- **Chain:** nq-build, then nq-check, then nq-facts and nq-second (independently, because chapter text and captions change), then the lead delivers.
- **Delivery:** Video Drop (https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP, version 13, no parts on the page now). Use new cards with a SHA-256 test. Read the page once, with `path: "index.html"`.
- **File names:**
  - `2026-09-26 One-way ticket Part 1 v2 - SE LOCKED-ON vlog - 1080x1920.mp4`
  - `... Part 2 v2 ...`
  - and their `- NO MUSIC` fallbacks.
- **Dropbox:** v1 of each is in `/Supercar Experience/05 Vlogs/2026-09-26 One-way ticket Part 1/` and `.../Part 2/`. Ask before archiving v1.
- **Token cost rules** (`CLAUDE.md`) apply. Lessons from Part 2:
  - nq-check looks at contact sheets of every driving and replacement shot **before** the full render (both Part 2 fix rounds were picture problems);
  - one hand on the wheel while he talks is fine;
  - save Dropbox link answers from the transcript instead of retyping them;
  - pin `av` to 15.x.

## After this: the YouTube-length vlog

Omarie: "after we're done with our research for both youtubers i sent lets make a youtube length vlog like we said we were gonna do". That's the lifestyle version in `HANDOFF-lifestyle.md`. It starts after this v2 is delivered and the research on both YouTubers is done. It's not part of this job.
