# Handoff: "One-way ticket" Part 2, and the token-cost test (6 Oct 2026)

From the lead session that built Part 1 (session 367d87e8, `claude.ai/code/session_013JoCuN8AVJiDRcQU8W2e21`).

## The job

Build **Part 2** of the SE vlog "One-way ticket": the night drive (Sep 26, 19:23) to the arrival at Supercar Experience
Las Vegas (Sep 27, 09:10). Part 1 was delivered on 6 Oct through the Video Drop page, and both facts voters cleared it.

- **Style: already chosen. Don't ask again.** Omarie, 6 Oct: rally v2 + HUDs (the Sep 15 rally v2 build with the
  dark-glass STRIP), in SE orange #FF4F16 ("keep the orange"). The car reads **MCLAREN 600LT** ("its a mclaren 600 lt").
- **Length:** at least 2:00, which is his hard floor. Aim for about 2:45–3:00, like Part 1.
- **Beats:** the draft is in `README.md` here ("Part 2", hook on the 06:26 sunrise) and `mockup/storyboard-part2.jpg`.
  Improve it from what the transcripts hold; his own talk carries the story.
- **Template:** copy `part1/` to `part2/`. It carries everything five fix rounds taught:
  - orange accents;
  - the STRIP with `hide_g`;
  - the `speedo` blur list;
  - `forbidden` spans;
  - mutes in `lib/mix.py`;
  - DELIVERY encoded at 11.1M.

  Read `part1/README.md` first.
- **Footage:** clips 0103–0123 in Dropbox (`NQ Studio/raw footage/2026-09-26/` and `2026-09-27/`). The table is in
  `README.md` here. Part 1's survey lived in a container that is gone, so survey only these 21 clips with the engine
  (`../engine/README.md`: `links --clips`, `ingest`, `index`, then `plan` and `fetch` for the cut).
- **Delivery:** the one Video Drop page, https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP. Add a card on top, as for
  Part 1. Folder: `Supercar Experience / 05 Vlogs / 2026-09-26 One-way ticket Part 2`.

## What blocked Part 1, so Part 2 gets it right first time

Each of these cost a fix round and a re-render of 30–45 minutes:

1. **Captions:** a word from one ASR pass ("our") was wrong. Take caption words that two models agree on, and check
   brand lines by ear.
2. **HUD figures:** SIDE G came from an uncalibrated axis, so it was cut. Only show figures with a named source. Clocks
   = file-name start + in-point.
3. **Hands and phones:** check every driving shot frame by frame, the hook included. Hands off the wheel, or a phone or
   camera in hand while moving or stopped in traffic, means a cutaway, and the audio runs on. Part 1 used 0095 road
   cutaways.
4. **Slam clocks:** a slam clock follows the picture under it, not the dialog.
5. **Repeats:** never reuse a source span in two shots. Fetch fresh footage instead.
6. **Nat beds:** mute third-party speech in them.
7. **DELIVERY:** must come out under 11.5 Mb/s; check it with ffprobe.
8. **Speedometer:** blurred on every cabin shot. No speed words anywhere.

## The cost test (Omarie, 6 Oct)

His words: "use the new skills and updates we've implemented on token cost and usage on the next video to compare and
see if it really works." Run Part 2 under the token cost rules in `CLAUDE.md`:
- hand off after each job;
- auto-compact at 300k;
- change effort, not the model;
- fresh agents from a summary;
- frames only in `nq-check`/`nq-label` contact sheets;
- no wait loops (use `run_in_background`, a PID or a marker, with a hard timeout);
- logs through `tail`/`grep`;
- lean agents;
- the live card with its cost line.

**Part 1 baseline** (`python3 .claude/brain/cost_meter.py` on session 367d87e8, at delivery):

| measure | Part 1 |
|---|---|
| cost (API-equivalent) | $177.53 |
| calls | 1,314 (lead 728) |
| agents | 9 |
| lead cost | $128.77 (73%) |
| lead context median / max | 403k / 775k |
| lead calls above 300k | 488 |
| compactions | 3 |
| cost share | cache write 48%, cache read 43%, output 9% |
| biggest agent | the build agent, $29.46, max 485k |
| fix rounds / facts re-votes | 5 / 2 |
| finished video | 3:00 |

Part 1's session also did work Part 2 won't repeat:
- finding the next vlog;
- both storyboards;
- a 49-clip survey (Part 2 surveys 21);
- an options discussion on the cost system.

So compare the measures the rules target, not only the total:
- lead median and max context;
- lead calls above 300k;
- the cache-write share;
- cost per finished minute;
- fix rounds.

**At the end:**
1. Run `live_card.py done --job "SE vlog One-way ticket Part 2" --note "<what went wrong>"`.
2. Run `cost_meter.py`.
3. Give Omarie a side-by-side table, Part 1 against Part 2, with a plain verdict on which rules worked and which didn't.
4. Proposed rule changes go to him as a click before anything changes.
