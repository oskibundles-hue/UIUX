# Handoff: "One-way ticket", the YouTube lifestyle version (6 Oct 2026)

From the research lead session (`claude.ai/code/session_01EwQdh3ZM2widrCFF4QtLKD`). It's research and
decisions only; no video was made. **Start the build only once Part 2 has been delivered** (`HANDOFF-part2.md`,
session `session_016zw3JbE8jhHMYYnssAMeTj`). Don't touch `part1/` or `part2/`.

## What Omarie asked (6 Oct)

Part 1 is good, but it "feels like a Supercar Experience ad", which is fine for the business page. He also wants
something "more vlog-like, lifestyle … more YouTube-like", with music that isn't the rally track ("make it more
personable"). He asked to decide long-form vs 3-minute parts before anything is built, and to learn how to spot
the critical components of a vlog.

## His picks (clicks, 6 Oct; all four were the recommended option)

| Question | Pick |
|---|---|
| Channel / brand | **His personal YouTube (@nq.young).** His own look, no SE logos, HUD or end card. SE gets a spoken thank-you and a link in the description. Two brands never share a video, so this is not an SE piece. Look up his personal-channel palette and type with `recall.py` ("personal vlog palette"); never copy SE orange or gold. |
| Format | **Long-form first:** one YouTube video of the whole trip (aim 12–16 min, 16:9), then the 3-minute vertical parts and Shorts cut from its chapters. |
| Style | **Lifestyle (new, proposed):** spec below. It's his first build in this style, so show him a test chapter before the full render. |
| Music | **Epidemic Sound.** He signs up and whitelists his channel. The build doesn't start the music pass until he confirms the account; until then it uses a temp bed or the NO MUSIC mix. Record every track's ID in the README. |

## The playbook

`.claude/playbooks/vlog-lifestyle.md` (uiux PR #36, into the default branch) holds:
- the moment tags (`TALK PLAN REACT FIRST ARRIVE PEOPLE FOOD SETBACK PAYOFF DRIVE TIME TRANS NEVER`);
- how to tag a survey;
- the structure, the pacing numbers, the sound rules and the pre-delivery checklist.

Brief `nq-story`, `nq-label` and `nq-check` with it.

## What the references do (evidence for the picks)

Fourteen videos were measured: talk share from YouTube captions, picture changes from storyboard frames (video downloads are blocked
from the cloud), and the look from contact sheets read by a label agent.

| Channel | Long-form | Talk share | Picture changes/min | Hook | Graphics | End |
|---|---|---|---|---|---|---|
| HiddenQuan (5 videos incl. "unemployed with supercars", 40:03, 160k views) | 8–40 min, mostly 18–40 | 59–70% | 4–13 (short single-story ones are fastest) | Cold talk to camera from frame 0 | None at all | Just stops on a talking shot |
| Brez Scales (4 videos, 23–28 min, 0.5–1.2M views) | 23–28 min | 72–80% | 5–6 | 15–30 s music montage, then his setup line | Almost none; a graded cinematic teal-and-orange look carries it | Spoken subscribe and next-video ask |
| Casey Neistat, Mat Armstrong, SoulDrives, Mr JWW, Yiannimize | 10–56 min | 94–95% where measured | 6–15 | Talk or montage | Sparse typed text, a diagram, a black credit card | Spoken outro |

- **Shorts:** Quan posts none. Brez's Shorts (18k–717k views) are clips from podcasts and streams, not from his vlogs. So
  Shorts work best as one strong moment, not a recap.
- **Road trips as long-form:** Mat Armstrong's 2,053-mile trip, 56 min, has 8.6M views. Gears and Gasoline's Florida to
  Alaska ep 1, 35 min, has 4.6M. SoulDrives' Dolomites trip, 24 min, has 2.0M.

## The footage (survey run 6 Oct)

- **Survey:** all 49 clips (0075–0123) were streamed through the engine. There are **112.9 min of raw footage** across the 46
  clips whose length was read before streaming finished (the other 3 were surveyed, but their lengths weren't added up).
- **Survey output:** in this session's container, at `/tmp/claude-0/day-owt` (lost when the container ends). Transcription
  and `index` finished with exit 0, but **their results weren't read back here** (the lead's read of the output was
  blocked). The build session re-runs `links`/`ingest`/`index` on the 49 clips. It takes about 8 minutes to stream, using
  `../engine/README.md` and the clip list in `README.md` here. Then it reads `moments.md` and tags it with the playbook.
- **PyAV:** install `av<15`, which is a prebuilt wheel. With av 19, faster-whisper fails on every clip (`metadata_errors`).
- **What tells long-form vs parts** (the playbook's bar): 8+ usable minutes, 10+ `TALK`/`REACT` moments and a real
  `PAYOFF`. Part 1 alone used 27 dialog pieces from 0075–0102, and the arrival at SE Las Vegas is the payoff, so the trip
  clears it easily. Confirm the counts from the new index before cutting.

## The Lifestyle style spec

- **Frame:** 16:9, 3840x2160, cut from the 3840x3840 open-gate source (crop per shot), 29.97 fps.
- **Structure (about 14 min):**
  - **Hook 0–15 s:** a flash-forward to the arrival line or the best `REACT`, then his 4:37 a.m. setup line.
  - **Chapters:** the airport run → the flight → the pickup and first sit (`FIRST`) → the drive into Oregon (`ARRIVE`) →
    the night and In-N-Out (`FOOD`) → still driving at 01:29 (`SETBACK`: tired) → sunrise (`TIME`) → the freeway into
    Las Vegas → the arrival (`PAYOFF`) → a spoken outro.
  - **Pacing:** 6–9 picture changes a minute overall. Jump cuts in talk drop pauses, never words. Montages of 8–30 s
    only between chapters.
- **Graphics (seasoning, not an ad):**
  - Small place and time titles at chapter starts.
  - One route map drawn by us, twice: Seattle → Oregon, then → Las Vegas.
  - Word pops on two or three key lines, speed ramps on reactions and roll-bys, and a freeze-frame name tag for new people.
  - No permanent banner, HUD, progress rail or logo card. YouTube's own captions on long-form; burned-in captions only
    on the vertical parts and Shorts.
- **Grade:** warm and natural, with skin first. Night shots keep their colour, with no crushed blacks.
- **Voice (same rules as Part 2):**
  - Every sentence ends at least 350 ms after the last word, never clipped.
  - Chain: high-pass, gentle denoise, presence lift, de-ess, compression.
  - The voice sits at least 10 dB over the music at every spoken word.
- **Music:**
  - One Epidemic Sound track per chapter, in the lo-fi, soft R&B, chill trap or warm synth family.
  - Walking tempo under talk; it comes up only in montages and the arrival.
  - Never stereo or venue music from the footage: 0092 has a song on the car stereo, and 0094–0099's own audio may too.
- **Ending:** his spoken outro, then a subscribe or next-video ask. A YouTube end screen (video plus subscribe) over the
  last 20 s.
- **Carry over from Part 1/2:**
  - blurred plates and speedometer, no speed words;
  - no hands-off-wheel or phone-in-hand driving shots;
  - captions taken from words two ASR models agree on;
  - figures only with a named source;
  - strangers muted.

## The work and cost, long-form first vs parts

| | Long-form first | More 3-min parts |
|---|---|---|
| New edit | One 14 min story cut (the bulk of the work), reusing Part 1/2's caption fixes, blur lists and forbidden spans | A new cut per part, each with its own hook, setup and end |
| Derivatives | 3-min verticals and Shorts are re-frames and re-times of finished chapters (cheap) | n/a |
| Render | About 4–5x a 3-min render for the master | 1x per part |
| Token cost (Part 1 baseline $177.53 for 3:00) | The rules target cost per finished minute: one long cut spreads the setup over 14 min | Pays the setup cost on every part |

## Before the build starts

1. **Run it in a session that opens inside the `uiux` repo, on the current default branch.** This research session
   opened one folder up and on a stale checkout, so the cost guard, the 300k auto-compact, the note-lookup hook, the
   regret gate and the NQ agents never loaded. It hit 324k context, and two banned `pgrep -f` waits ran. Making the
   system load in every session needs an installer that writes the user-level Claude settings. This session was
   **blocked from building it** (a self-modification guard); it waits on Omarie's OK.
2. Ask Omarie whether Epidemic Sound is set up. Ask for the style only if he changes his mind (it's picked above).
3. Re-run the survey, tag it with the playbook (`nq-label`), and have `nq-story` pick the hook and chapter beats
   (2 or 3 options). Then he picks.
4. Build a test chapter first, the pickup and the first drive, then the full cut, `nq-check`, and the facts panel for
   any on-screen place or figure.
5. **Delivery:** the Video Drop page, card folder `NQ Studio/04 Exports/2026-09-26 One-way ticket YouTube` (check the
   notes' `omarie-dropbox-layout` for the personal-channel folder first).
