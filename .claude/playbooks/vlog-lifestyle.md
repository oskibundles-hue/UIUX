# Playbook: lifestyle vlog (the moments that carry a vlog)

How to find, tag and order the moments that make a personal, YouTube-style vlog work, as opposed to a
brand ad cut from the same day. It is general craft, so it fits any workstream: the workstream's own
playbook still decides the brand, colours, logos and where the work lives. Read by `nq-story` when it
picks the hook, the beats and the format, by `nq-label` when it tags a survey, and by `nq-check` before
delivery. (Written on 2026-10-06 from a study of HiddenQuan, Brez Scales and six other car, travel and
lifestyle channels; the evidence and numbers are in the handoff that commissioned it.)

`<repo>` means the main checkout's root: `git rev-parse --show-toplevel`.

## What makes it a vlog, not an ad

An ad sells the car or the company. A vlog sells **the person**, and the viewer stays to find out what
happens to them. Every reference channel follows the same few rules:

- **The host's own voice carries the story.** In the channels studied, captions cover 60–95% of the
  runtime, at about 115–200 words a minute. Silence is short: the longest stretch without talking is
  usually 10–40 s, and it's always a montage or a payoff.
- **The camera is on him a lot.** Selfie-style talk to camera, friends in frame, and reactions set the
  tone. Car and scenery shots are the reward between them, not the main course.
- **One question runs the whole video.** "Will we make it?", "What's the new car?" or "How does the day
  end?" is set up in the first 15 s and answered at the end.
- **It sounds like a day, not a trailer.** Music sits under talk most of the time. It comes up only in the
  montages, and a beat-synced drop is saved for one or two moments.
- **It ends on the person.** A spoken outro ("that was the trip, let me know…"), then a subscribe or next
  video ask. No stacked logo card.

## The moment types (tag these in every survey)

Tag every clip span that holds one of these. One span can carry two tags. A **★** marks a moment strong
enough to be the hook or a chapter's payoff.

| tag | moment | how to spot it in the raw footage | why it carries |
|---|---|---|---|
| `TALK` | personal talk to camera | his face fills the frame, he speaks to the lens; a transcript line with "y'all", "I", "we", feelings, plans | the viewer's relationship with him; the spine of the edit |
| `PLAN` | the setup line | he says what today is ("we're about to…", "the plan is…") | sets the question the video answers; often the first spoken line |
| `REACT` | a reaction | a laugh, a swear, a "yo!", raised voice, a sudden word after silence; loud speech in the audio | proves it is real; the best hook material |
| `FIRST` | a first | first sight of the car, first sit, first start, first time somewhere ("first time…") | a natural mini-payoff; slow down here |
| `ARRIVE` | an arrival or a border | a sign in shot, "we're in…", "we made it", pulling up, doors opening | marks chapters; gives place titles a reason |
| `PEOPLE` | other people | a friend, staff or a stranger in frame or talking with him | warmth and stakes; check releases and mute strangers when needed |
| `FOOD` | a food or rest stop | a drive-thru, a restaurant, a gas station snack, eating on camera | a breather that makes it a lifestyle video; a cheap, likeable beat |
| `SETBACK` | something goes wrong | tired, lost, late, closed, weather, a warning light; low or annoyed voice | the tension a trip needs; never cut it all out |
| `PAYOFF` | the answer | the destination, the reveal, the hand-over, the "we did it" line | the end of the story; the hook often flashes forward to it |
| `DRIVE` | the drive shots | cabin POV, the road ahead, exterior roll-bys, scenery passing; engine sound | the reward between talk; the montage beds |
| `TIME` | the passing of time | dawn, dusk, night, the clock, "it's 2 a.m.", sunrise | gives a long trip its shape; good for chapter stamps |
| `TRANS` | a natural transition | a door closing, a hand over the lens, a whip pan, the car passing the camera | lets the cut jump in time or place without a hard edit |
| `NEVER` | never use | a phone in hand while driving, the speedometer, plates, a stranger's face or voice, music on the stereo | the flags list; the build must stay clear of these |

**How to tag during the survey.** The engine's `index` stage already writes `moments.md` and `flags.json` from
the transcripts and audio. After it runs:

1. Read `moments.md` and the transcript once, top to bottom. Give every span a tag from the table, written as
   `clip:in-out TAG [★] "the line or what's in frame"`, one per line, in a `tags.md` next to `moments.md`.
2. Use the transcript for `TALK`, `PLAN`, `REACT`, `FIRST`, `ARRIVE`, `SETBACK` and `PAYOFF` (his words name
   them). Use the contact sheets for `DRIVE`, `TIME`, `TRANS`, `PEOPLE` and `NEVER`, one sheet per clip, never
   single frames.
3. Copy every `NEVER` span into `flags.json`, so the cut can't land on one.
4. Close with a count per tag and the total minutes of each. That count decides the format (below).

`nq-label` tags. It never decides what gets used. `nq-story` picks from the tags.

## The structure that works

Every reference video opens the same way and has the same middle shape:

1. **Hook, 0–15 s.** One of two openings:
   - **Cold talk:** his first line is the setup, on camera, with energy ("Long story short, we got pulled over
     in…"). HiddenQuan opens this way every time.
   - **Montage then talk:** 15–30 s of the best `DRIVE`/`ARRIVE`/`PAYOFF` shots on music, then his `PLAN` line.
     Brez Scales opens this way.

   Either way, the viewer knows the question before 0:15. A flash-forward to the payoff is the strongest version.
2. **Setup:** the `PLAN`, where he is and who he's with.
3. **Chapters:** one per place or time of day. Each runs talk → drive or montage → a small payoff (`FIRST`,
   `ARRIVE`, `FOOD`), then a `TIME` or `TRANS` into the next. YouTube chapter markers in the description
   follow these.
4. **A low point** (`SETBACK`) about two thirds in: tired, late, lost.
5. **Payoff**, then the spoken outro and the subscribe or next-video ask.

**Pacing.** Talk sections cut on his sentences, with jump cuts that drop the pauses but never a word.
Montages cut on the beat and run 8–30 s. Measured from YouTube storyboards (a rough estimate that
misses the smallest jump cuts), long day-in-the-life videos change picture about 4–7 times a minute,
and short single-story videos (a police stop, "I'm leaving New York") about 10–15. A 15-minute trip
sits between the two: about 6–9 a minute, faster in montages and slower while he talks.

## Graphics for a lifestyle cut

Far less than an ad. Of the channels studied, HiddenQuan shows no added text at all, Brez Scales almost
none (a graded, cinematic look carries it), and Casey Neistat a few typed words used as jokes. Graphics
are seasoning:

- Burned-in captions only on Shorts and vertical cuts. Long-form YouTube relies on the platform's captions,
  with occasional big **word pops** on key lines.
- **Place and time titles** at chapter starts (a city, a state line, a clock), small and quick.
- **A route map** once or twice on a long trip: an animated line from start to the current place. Draw it
  ourselves; never lift one from a reference video.
- Zooms and **speed ramps** on reactions and roll-bys, a shake on a hit, freeze-frame name tags for new people.
- No permanent banner, logo bug or progress rail. One small channel or brand mark at the end at most.

## Voice and sound

- Every sentence ends at least **350 ms** after the last word. Never clip a word, a breath or a laugh tail.
- Voice chain: high-pass, gentle denoise, presence lift, de-ess, compression. The voice sits at least
  **10 dB over the music** at every point he talks.
- Music is a **personal bed**: lo-fi, soft R&B, chill trap or warm synth, at walking tempo under talk. It comes
  up only for montages. One track per chapter, changed at chapter breaks. Only licensed or original tracks,
  and never music picked up from the car stereo or a venue.
- Natural sound is part of the story: the engine on a start, doors, the drive-thru speaker (muted if a
  stranger can be identified), wind.

## Format: long-form first, clips after

When one trip yields **8+ usable minutes**, with **10+ `TALK`/`REACT` moments** and a real `PAYOFF`, cut the
long-form YouTube video first (about 10–20 min). Then cut the vertical 3-minute parts and the Shorts from its
chapters. Each chapter is already a self-contained beat with a hook line, so a part or Short is a re-frame
and a re-time, not a new edit. Below that bar, make 3-minute parts only.

## Before delivery (`nq-check` adds these to `review.md`)

- [ ] The first 15 s state the question or show the payoff, and he is on screen or heard by 0:05.
- [ ] Talk covers at least half the runtime; no silent stretch over 40 s that isn't a montage or payoff.
- [ ] Every sentence has 350 ms clear after its last word; no clipped words at any cut.
- [ ] The voice is 10 dB or more over the music at every spoken word.
- [ ] Every chapter ends on a small payoff and starts with a place or time cue.
- [ ] There is at least one `SETBACK` or honest low moment.
- [ ] The ending is a spoken outro by him plus one clear ask.
- [ ] No `NEVER` span is on screen; plates and speedo blurred; strangers muted.
- [ ] Music is licensed or original, and the source is written in the build README.
- [ ] Only the channel's own brand is used (two brands never share a video).
