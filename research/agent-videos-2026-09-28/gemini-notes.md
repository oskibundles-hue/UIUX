# Gemini watch notes — 2026-09-28 agent-videos batch

Four videos, watched with the `watch` skill's Gemini engine (agentic video processing — Google
watches the video directly; this container's IP is blocked from touching YouTube itself, so this
was the only route). Free-tier limits (~5 req/min, 20 req/day per model) and 503 "high demand"
errors blocked a first pass on 3 of the 4 videos. A follow-up pass got **all four** videos
answered: `gemini-flash-lite-latest` came back online, and for the two longest/most-overloaded
videos, splitting the ask into short 4–5 minute clips (`--start`/`--end`, aligned to the video's
own chapters) got through where one big agentic request kept 503'ing. Raw Gemini output for each
video is saved under `raw/<video-id>.md`.

---

## 1. Ben AI — "Anthropic Just Revealed 7 New Rules for Prompting Claude 5 Models"

- **URL:** https://www.youtube.com/watch?v=HDmBwU5uvEE
- **Channel (confirmed via oEmbed):** Ben AI
- **Length:** 13:15 (per Gemini)
- **Model that answered:** `gemini-flash-lite-latest` (agentic, one pass, 7,294 tokens)

### The 7 rules

1. **Give Claude 5 models the entire job instead of prompting it step-by-step** [SEEN @0:34–0:37] —
   modern models do best given the complete task spec upfront and left to run; describe the task,
   guardrails and exit criteria at a high level rather than "do 1, then 2, then 3." No before/after
   example shown for this one. Cited: Anthropic prompting guides for Opus 5 / Haiku 5
   [SEEN @0:39–0:50]; Boris Cherny's Y Combinator talk [SEEN @1:02–1:11]; a free resource link in
   the description [SEEN @2:40].
2. **Use an "Interview Me" skill before sending the model off end-to-end** [SEEN @3:02–3:10] —
   Anthropic internally uses a skill that asks clarifying questions up front to surface unknowns
   and build a complete brief. He shows the resulting brief for a personal analytics dashboard
   [SEEN @3:55–4:22] rather than a before/after pair. Cited: an Anthropic article on how the team
   uses Claude 5 [SEEN @3:20–3:30]; Andrej Karpathy and voice transcription via Whisperflow or
   Claude's built-in voice tool [SEEN @4:55–5:10]; his own "Prompt Master skill" [SEEN @5:20–5:30];
   his AI Accelerator / AI Operator program and free resources [SEEN @5:32–6:05].
3. **Prompt why it needs to do the job, not just what** [SEEN @6:05–6:21] — models make better
   micro-decisions on under-specified tasks when they understand the bigger picture. Template shown
   [SEEN @6:50–7:05]: *"I'm working on [larger task] for [specific person/audience]. They need
   [what the output enables], and with that in mind, [request]."* His own example [SEEN @7:15–7:30]:
   *"I'm working on a video for my YouTube channel on how to prompt Claude models and how it's
   changed. The video is for non-technical professionals and business owners that are using Claude
   to automate their work. They need practical tips, examples and frameworks on how to improve
   their prompting, not just theory."*
4. **Define what done looks like** [SEEN @7:57–8:03] — Claude 5 models tend to over-run rather than
   under-run, so exit criteria and output style keep them from burning extra tokens. His example
   criteria [SEEN @8:33–8:45]: *"a pre-outline for this video, that means 8 to 15 practical tips on
   how to prompt cloud models together with a specific example for each and the source you found
   this tip for, again the source you found for this tip should be backed up by [Anthropic]."*
   Cited: a Boris (Cherny) talk at Y Combinator [SEEN @8:15–8:21].
5. **Swap hard rules for reasons** [SEEN @9:17–9:22] — models respond better to an instruction plus
   its reason than to a "never do X" constraint. Before [SEEN @9:55–10:04]: *"Never give a point
   that is not backed up by Anthropic."* After: *"Make sure that the points that are mentioned are
   backed up by Anthropic's own team so we actually have proof for the claims we're making and the
   reason behind it."* Cited: Anthropic's context-engineering research/article and a keynote on
   prompting [SEEN @9:25–9:35]; Anthropic's "Rule Rewriter skill" for updating `CLAUDE.md`/skill
   files [SEEN @10:10–10:27].
6. **Avoid telling it to double-check itself** [SEEN @10:27–10:40] — explicit verification asks,
   sub-agent double-checks, or all-caps emphasis add cost without improving results, since Claude 5
   models already self-correct; also avoid "think step by step" / "explain your reasoning." No
   before/after example shown for this one.
7. **Fix Claude's voice once** [SEEN @11:38–11:46] — to stop Opus 5 from being jargon-heavy or
   verbose, set one global instruction (in `CLAUDE.md`, Claude Desktop instructions, or project
   settings). Example shown [SEEN @12:15–12:22]: *"keep responses focused, brief and concise, avoid
   jargon and being overly verbose."* Cited/quoted [SEEN @12:45–13:00]: an Anthropic article's line
   — *"think of Claude as a brilliant but new employee who lacks context on your norms and
   workflows"* — and the "golden rule": show your prompt to a colleague with minimal context and
   see if they'd be confused; Claude will be too.

**Gaps:** speech-to-text in the transcript is imperfect — "Fable 5" appears to be Gemini
mis-hearing "Claude 5" / "Opus 5" in a couple of spots, and "entropic" in rule 4's quote is almost
certainly "Anthropic" mis-transcribed. Take those two words as probable ASR errors, not intentional
phrasing by the creator.

---

## 2. The Coding Sloth — "I Have Spent 1000+ Hours With Claude Code. This Is What I Learned"

- **URL:** https://www.youtube.com/watch?v=YAsxyoTWFDA
- **Channel (confirmed via oEmbed):** The Coding Sloth
- **Length:** 22:31 (per Gemini; this video has no chapters, so not independently cross-checked)
- **Model that answered:** `gemini-3-flash-preview` (agentic; 126,953 tokens)

### Full tier list of Claude Code features

- **S-Tier**
  - Plans / Plan Mode [SEEN @06:52] — "If you hit shift and tab on Claude Code, Claude goes into
    plan mode." Used for "BIG TASKS" [SEEN @07:23].
  - Verification [SEEN @08:38] — "I'm giving this feature like an S tier and if anything a double
    S or even a triple S."
  - Subagents [SEEN @20:25] — S-Tier specifically for users on high-tier plans or with "unlimited
    tokens."
  - `/loop` [SEEN @17:59, @19:06] — "S tier for real this time."
- **A-Tier**
  - Skills [SEEN @05:07] — "But if you're smart with it, easy S tier" (his words go higher than
    the tier label he gives it).
  - `CLAUDE.md` file [SEEN @04:13] — upgraded from B to A-Tier "after months of dealing with the
    sloppy code" [SEEN @04:15].
  - MCPs [SEEN @10:01] — "Actually, I'm lying. A tier."
  - Subagents [SEEN @20:24] — standard ranking for users on the $20/month plan, due to token
    costs.
  - Worktrees [SEEN @20:32] — "A tier."
  - Pre-installed skills [SEEN @05:33] — e.g. `/code-review`, `/security-review`.
  - `/teleport` and `/remote control` [SEEN @11:54] — "I'll give it an A tier" if "you touch grass
    a lot."
- **B-Tier**
  - `/voice` [SEEN @10:52] — "B tier."
  - `/context` [SEEN @13:48] — "I'll give this command a B tier. I think it's pretty important to
    use."
  - `/goal` [SEEN @19:22] — B-Tier on lower plans, A-Tier on higher plans [SEEN @19:28].
- **C-Tier**
  - `/btw` [SEEN @11:10] — "C tier. Probably won't use this much, but it's nice to have."
  - Shell mode / `!` prefix [SEEN @12:01] — "Also a C tier."
  - `/compact` [SEEN @15:03] — C-Tier when it runs automatically, B-Tier if used manually
    [SEEN @15:07].
- **D-Tier**
  - `/init` [SEEN @04:10] — "In it still stays the same. I think it's pretty mid."
  - `/teleport` and `/remote control` [SEEN @11:58] — D-Tier "if you just don't use it."
- **F-Tier**
  - `/radio` [SEEN @12:20] — "F tier for productivity but triple S tier for vibes" [SEEN @12:22].

### Token / context tips (with numbers)

- Claude tracks usage by tokens, not prompts [SEEN @12:54].
- On-screen text he quotes [SEEN @13:23]: "Sonnet 4.5, have a 200k-token context window." /
  "claude-mythos-5 have a 1M-token context window." / "Claude Code defaults to a 1-million-token
  context window for users on Max, Team, and Enterprise plans" [SEEN @13:27].
- The "dumb zone": performance dips once above **100k–200k tokens** — "that's when the performance
  starts to dip a bit and those usage limits get cooked" [SEEN @13:38–13:41].
- A medium or big task uses a minimum of **50k tokens** [SEEN @14:15].
- A skill or MCP call can easily push a single response above **100k tokens** [SEEN @14:18].
- Rule #1: start a new session for every new task, to avoid the model getting "dementia" from high
  context [SEEN @14:04].
- Be "STUPIDLY SPECIFIC" in prompts so Claude doesn't read unnecessary files and waste tokens
  [SEEN @14:44–14:46].

### ponytail, rtk, caveman, skills.sh

- **skills.sh** [SEEN @05:58] — "go-to place for finding and installing skills."
- **Ponytail, rtk, Caveman** [SEEN @15:32] — community-built "high-performance CLI proxy[s] that
  cut[s] up to 90% of the bash output your agent reads" [SEEN @15:33]. On-screen text he quotes:
  "Ponytail... -54% less code (up to 94%) -- -20% cheaper -- -27% faster -- 100% safe"
  [SEEN @15:33]; "Caveman: Cut 65% of your AI costs" [SEEN @15:35].

### Views on alternatives

- **Codex** [SEEN @21:11] — "I personally love it. I think that's the one I've been using the
  most. Their usage limits are actually generous" [SEEN @21:12].
- **OpenCode** [SEEN @21:21] — "Essentially the open source version of Claude Code... if you want
  to use any model, I do recommend you check it out" [SEEN @21:25].
- **Pi** [SEEN @21:28] — "Basically like a minimalist setup... if you're the type of person that
  wants to create their own workflow from scratch, this is the tool for you" [SEEN @21:34].
- **Cursor** [SEEN @21:36] — "What I like to use if I need to use an IDE... this one also lets you
  pick any type of model" [SEEN @21:41].
- **T3 Code** [SEEN @21:54] — "The UI of T3 Code way more... if you have multiple subscriptions...
  then maybe you should check out T3 Code since you can basically use all your subscriptions in
  just one application" [SEEN @22:11]. On-screen text: "The open-source control plane for coding
  agents" [SEEN @21:58].

### Testing and verification advice

- Claude "can't know if it's correct" without verification [SEEN @08:55].
- Tell Claude to write tests first, then implement — "so you don't cheat and write sloppy toppy
  code" [SEEN @09:09].
- Don't implement then test after — "it's just going to write tests that pass its own code... that's
  cheating" [SEEN @09:12–09:16].
- Don't test every line — "just test the most important things" [SEEN @09:20].
- Run type checks before considering a task done [SEEN @09:31–09:35].
- For UI/frontend, use screenshot testing and browser testing, because Claude is "literally blind"
  to what it makes [SEEN @09:40–09:44].

**Gaps:** the video has no chapter list to check the timestamps against, so these mm:ss marks are
Gemini's own placement and weren't cross-checked against a second source. Nothing flagged as
unseen/unheard by Gemini for this video.

---

## 3. Systems Made Better — "I Made Claude My Personal Assistant (Full Build)"

- **URL:** https://www.youtube.com/watch?v=3ZT0upsICHk
- **Channel (confirmed via oEmbed):** Systems Made Better (channel handle @BetterCreating, creator
  goes by "Simon" — confirmed via the video's own YouTube description, fetched with Jina's reader
  as a metadata cross-check per SOURCE.md's fallback route)
- **Length:** 27:09 (confirmed via chapter-list source and consistent with the last clip's range)
- **Model that answered:** `gemini-flash-lite-latest`, in **7 short clips** aligned to the video's
  own chapters (one full-video agentic attempt kept 503'ing; splitting into ~4–5 minute
  `--start`/`--end` clips got through every time). Total ~154,000 tokens across all 7 clips.

### What the daily brief looks like (built up across the video)

- Early mockup version [SEEN @0:07–0:13, @1:23–1:40]: greeting banner ("Good morning, Simon."),
  stat counts (5 TO ACT ON, 3 MEETINGS, 19 TEAM ITEMS, 8 ISSUES), sections "Needs attention today,"
  "Today's schedule," "Your action items," "Relevant in Slack," "Issues to raise," "The Team,"
  "Overdue backlog," and "Personal/finance / System updates."
- Design brainstorm on-screen questions [SEEN @5:25]: "What's in the morning briefing?" (daily
  overview, calendar & meetings, email/transcript triage, tasks & deadlines, news & industry
  topics, weather & commute, yesterday's design, suggested focus for today, open questions);
  "Where do you read it?" (phone-first / desktop-first / both); "How long should reading it take?"
  (30 seconds / 2–3 min / 10 min / deep); "Information density" (very sparse / balanced / dense).
  Wireframe template shown [SEEN @5:50] with a date header ("Wednesday, 17 Sep"), section headings,
  terse one-clause-per-line body copy, a colour swatch palette, and modular blocks.
- Finished brief actually delivered [SEEN @23:35–23:56]: header "Friday, 18 Sep 2026," notes it's a
  delivery day with a hard deadline at 17:45; stat counters "Ready for review" (1), "P1 task" (1),
  "Needs review" (3); **"The 20% — Focus Today"** with 3 items (send finalised contracts by 17:45,
  film Module 3 for the Accelerator cohort — 60 min, sign off Claude's Community Digest — 15 min);
  an hourly **Schedule** with named blocks and a clash warning at 17:00 plus a 20-minute daily reset
  at 18:00; **Tasks & Deadlines** split into "Your tasks" (2 open), "Your VA's tasks" (3), and
  "Automated — ready for Simon [to approve]"; **Email waiting on you** (a glance inbox, an invoice
  from "Lisa," a GoCardless Direct Debit notice).

### Apps connected, and how

- Navigates Claude Desktop's **Customize → Connectors** tab [SEEN @3:13–3:32] and connects
  **Google Drive**, **Google Calendar**, **Notion**, mentions **Microsoft 365** as an alternative,
  and a custom MCP ("Agentic Business Guide MCP").
- Configures per-connector tool permissions (Always allow / Needs approval / Never) [SEEN
  @3:52–4:03].
- Confirms the essential set for the PA: **Google Calendar, Notion, Slack, and local folders in
  Claude** [SEEN @4:19–4:26].

### Install & folder setup

- Chapter title on screen: `#02 INSTALL CLAUDE & PICK YOUR FOLDER` [SEEN @1:44].
- On-screen note: *"Cowork is the system that runs on your computer..."* [SEEN @1:53].
- Local folder structure shown in Finder/Dropbox: `ABOUT ME`, `KNOWLEDGE`, `RESOURCES`,
  `WORK AREAS`, `Claude-outputs` [SEEN @2:00].
- Right-clicks a folder in Finder → "Make available offline" to sync it [SEEN @2:11]; picks the
  working directory (`CoWork`) from Claude's project dropdown [SEEN @2:38].

### Notion database fields

- Task database columns [SEEN @6:16]: task name/description, Person (e.g. Simon, Jakub Skupień),
  Priority (High/Medium), Status (Not started / In progress), Deadline.

### The PA instructions (quoted as shown on screen)

First draft brief [SEEN @8:18–9:23]:
> "I would like to create a scheduled task that is a personal assistant that runs a daily briefing
> on my current circumstance. We're going to do this only inside my Demo PA folder."
>
> "Create two things: 1. A first draft of a scheduled task which asks you, on a Monday morning at
> 8 am., to deliver a briefing of the day and the week. Every other working day, it delivers a
> daily brief. It should deliver it as an HTML report using the above design system. 2. The report
> should be delivered both in the chat of the scheduled task, but also as an artefact in a briefs
> folder inside the demo PA. 3. Create a memory file and project file for how the demo PA should
> work that exists in that folder, so that you have a clear set of instructions on how to operate."
>
> "Want my personal assistant to be able to brief me on: the work I have coming up for the day, my
> clear, important priorities, what's happening for my schedule. It will need to read my Gmail, my
> Google Calendar, and a specific Notion task database that it will read from to inform its
> decisions. Please draft the scheduled task and set up the folder."

Refined system prompt [SEEN @13:58–14:52] — **note:** Gemini's own OCR/transcription of this
on-screen block has visible garbling (repeated fragments, a broken sentence around "20%, Schedule,
Tasks... Status: Not Done/Does with a Deadline"), so read the specifics as best-effort, not a
guaranteed exact transcript:
> "You are 'Simon's' personal assistant, running his scheduled morning briefing at 06:00 (London).
> Read and follow the runbook at CLAUDE.md in the connected 'Demo PA' folder exactly, top to
> bottom, before doing anything else. It tells you how to operate in full."
>
> "CONTEXT (best effort): Simon's Co-work folder lives in Dropbox at
> /Users/simon/Library/CloudStorage/Dropbox/CloudStorage/Co-Work/. Read [it] over the remote
> devices bridge if his desktop app is connected. If NOT connected, read the SAME FILES through the
> local access files... READ CLAUDE.md and 'ABOUT-ME' at that root, and the last 7 DAYS of
> WORK-AREAS/ADMIN-PA/captain's-log."
>
> "GATHER: 1. Today's Google Calendar events (times > 06:00). 2. Team action items – Notion 'Task
> List' ('Outstanding' view) and Gmail ('Simon's inbox' label plus main inbox), Status: Not Done,
> ordered by Priority (High > Medium > Low). 3. Simon's overdue backlog from his main personal
> Notion Tasks database ('BC Tasks Database'): Status: Not Done, with a Deadline on or before
> today, ordered by Priority. Remove Person ID to names: flag anyone unresponsive or badly backed
> up."
>
> "RENDER a single self-contained branded HTML page (Better Creating design pack: BC Orange
> #FF5D26 used sparingly, Funnel sans, warm brown/beige neutrals, crisp Swiss/Apple design —
> Helvetica, orange reserved for hard blockers only). Blocks: Top line, The 20% Schedule, Tasks (3
> groups: ready for Claude AI to approve, with the VA, Simon's own), Waiting on, and on Mondays the
> Week ahead."
>
> "DELIVER two ways EVERY RUN: (1) ALWAYS send the finished briefing as an .html file... readable
> on ANY device — including on mobile straight from push notifications; and (2) if the desktop is
> connected, ALSO update the cached daily briefing on device. If the folder is reachable, also save
> a dated copy to the briefing-delivery project outputs. Finish with a one line chat summary of the
> single most important thing for Simon today."

### Scheduled task — cadence and prompt

- **Cadence** [SEEN @17:08–17:10]: weekdays at 08:00.
- **Prompt** [SEEN @17:08–17:10]:
  > "Read Simon's morning briefing (Demo PA persistent assistant). Read and follow the outlook at
  > CLAUDE.md in the connected 'Demo PA' folder exactly, top to bottom, before doing any tasks. It
  > tells you how to operate in full.
  >
  > STEPS: 1. Read the three ABOUT-ME identity files, .system/Project.md, and .system/Memory.md.
  > 2. Find today's date in Europe/London; [e.g.] it's Monday — produce the weekly + daily brief.
  > 3. Gather (READ-ONLY) today's Google Calendar, the Notion Task Operations Database (Demo), and
  > Gmail. 4. Build one self-contained HTML brief structured per templates/html.tmpl (Apple Swiss
  > design template)."

### ASD-STE100 — exactly what he says and shows

- He explains ASD-STE100 stands for **Simplified Technical English** — a system meant to make the
  AI "speak to you in a far more focused and clear way" [SEEN @20:11–20:25].
- The on-screen rewrite-prompt he uses [SEEN @20:11–20:20]:
  > "You are a Simplified Technical English (ASD-STE100) [rewriter]. REWRITE. Read the text I give
  > you [and] follow the STE rules below. Do not add [new] technical meaning.
  >
  > VOCABULARY — Use the simplest common word for each idea. Give each word one meaning only. Do
  > not use a word as more than one part of speech. Choose one technical name for each thing and
  > one technical verb for each action; use them every time — never a synonym for something already
  > named. No jargon, no idioms, no slang, no figures of speech.
  >
  > SENTENCES — Instructions (procedures): maximum 20 words per sentence. Descriptions: maximum 25
  > words per sentence. One instruction per sentence — two actions get two sentences. Use the
  > imperative for instructions ('Remove the bolt.'). Use active voice; no passive, no future, no
  > perfect tenses. Keep small words (a, an, the) that make meaning clear.
  >
  > STRUCTURE — Write procedures as a numbered vertical list, one step per number. Max 6 sentences
  > per paragraph. Put the instruction first, then the condition or reason. Use a vertical list for
  > more than one condition or item.
  >
  > WARNINGS AND CAUTIONS — Start with a clear direct command; state the condition after. Put the
  > warning before the step it applies to.
  >
  > OUTPUT — Return the rewritten text. Then, under a heading 'Check These Words,' list any words
  > you used that might be unapproved per the STE dictionary, so a human can verify. If confident
  > all words are fine, write 'None flagged.'"

### The context map

- On-screen title [SEEN @26:25]: "Agentic Context Map & Write Rules." It's a Notion page acting as
  a master directory for where information belongs across the workspace's databases, with sections
  for Work & time, Clients & delivery, Direction & measurement, Content & channels, and Knowledge &
  documentation.
- Purpose [SEEN @26:45]: built so an AI agent can read it and know where to put or find specific
  content across Claude/Notion, following consistent routing rules.

### How the demo runs, and how the video ends

- Opens the "Captain's Log" folder so the system understands how to work with him [SEEN
  @21:21–21:31]; reviews the Notion "Task Executor – Demo PA" task and its rule (only touch tasks
  assigned to "Claude [AI]" with status "To Do [AI]") [SEEN @21:32–22:02]; clicks **Run now** to
  manually trigger the scheduled task [SEEN @22:28–22:43]; ties it into a broader "Agentic Business
  OS" Notion system [SEEN @22:44–23:17]; dictates a new note with WhisperFlow and watches it flow
  into both the Notion task list and the Captain's Log file [SEEN @23:57–24:37]; lets the Task
  Executor run automatically, moving completed items to "Needs Review" [SEEN @24:38–25:42].
- The video ends [SEEN @26:51–27:08]: he returns to full screen, remarks that the whole setup took
  about an hour while filming, then shows a closing screen recording of the scheduled-tasks list.

**Gaps:** the "refined system prompt" block (13:58–14:52) has visible OCR noise in Gemini's
transcription — a few fragments repeat or don't parse cleanly (IDs like "0000000bc571" and
"collection:00940003bc" look like blurred/illegible on-screen text rather than real values). Treat
that quote as the best available reading, not a guaranteed verbatim transcript. Everything else in
this section came through clean across all 7 clips.

---

## 4. Teku AI — "The LATEST Hermes Agent Update is INSANE!"

- **URL:** https://www.youtube.com/watch?v=dCZK-VssIWw
- **Channel:** Teku AI (YouTube's oEmbed returned "Unauthorized" for this video, as expected per
  the task brief; confirmed instead via the video's own description, fetched with Jina's reader)
- **Length:** ~7:30 (the video actually ends around 7:27 with the outro — noticeably shorter than
  the chapter list's final marker of 7:28 would suggest; see Gaps)
- **Model that answered:** `gemini-flash-lite-latest`, in **3 short clips** (0:00–4:00, 4:00–8:30,
  7:00–13:07) — the full-video agentic attempt 503'd repeatedly; clips got through immediately.

### Bot Screen [SEEN @0:20]

- Test: worked well once he copied the pull request link and gave it to Hermes, which then built a
  skill specific to the bot screen; some initial confusion before that.
- Hardware/plan: not shown or said.
- Disappointment: initial hiccups (resolved).
- Prices: none mentioned.
- Verdict: found it "very useful and cool for watching agents work live."

### Simple layout mode [SEEN @2:54]

- Test: showed switching between advanced mode and the new simple mode in the desktop app's layout
  editor.
- Hardware/plan: not shown or said.
- Disappointment: none mentioned.
- Prices: none mentioned.
- Verdict: liked the cleaner interface "without developer instrumentation."

### Connectors menu [SEEN @4:00]

- His own words [SEEN @4:06]: "this is more like a change that I notice while, you know,
  navigating and using the desktop app." [SEEN @4:42]: "I knew the MCP menu was here, but I quite
  don't remember all of these options."
- Test/hardware/model/disappointment/prices: not shown or said beyond the above.

### One-click local models [SEEN @4:54]

- Test: tried the one-click local model setup.
- Disappointment [SEEN @5:36]: "None of them is suitable for my machine, in your case this could be
  different."
- Verdict [SEEN @4:57]: "If you run local models, you're gonna like this one. I don't, at least not
  for now."
- Which model the setup picked: not established in this segment; prices not mentioned.

### "Hey Hermes" wake word [chapter marker @7:28; actual demo content ~6:23–6:53]

- Test: asked it "Can you please search the release date of the new Avengers movie Avengers:
  Doomsday?" [SEEN @6:23]; got back "Avengers: Doomsday in theaters December 18, 2026, US wide
  release in 4000+ theaters" [SEEN @6:36].
- Model picked: **Hermes-3-Llama-3.1-8B** [SEEN @6:43].
- Disappointment [SEEN @6:53]: "currently we don't have a mobile app for Hermes because this kind
  of feature is much more often used on the phone than on the computer, at least in my case,
  right?"
- Verdict [SEEN @6:46]: "you can pretty much use Hermes as you would with Siri, except that Hermes
  can do a lot more than Siri can."
- Prices: none mentioned for this feature specifically (a Hermes Plus discount link appears in the
  video's description, not shown as an on-screen price in the video itself).

### Overall verdict and ending

- At [SEEN @7:00] he sums up his experience with the update as disappointing overall ("at least in
  my case, right?"), while inviting viewers to share their own results in the comments.
- Outro [SEEN @7:08–7:27]: asks for likes/subscribes/comments with suggestions for future videos,
  says goodbye, then a "TEKU AI" logo/website outro screen plays to the end.

**Gaps:** the chapter list places "Hey Hermes" at 7:28, but Gemini's own timestamps put that demo
content around 6:23–6:53 and have the video's outro finishing by 7:27 — i.e., the video appears to
be about a minute shorter than the declared chapter marker implies, or the marker itself is
slightly off. No hardware, plan, or price was shown or said for the Bot Screen, Connectors menu, or
wake-word test beyond what's quoted above.

---

## Session-level notes for the lead

- **All 4 videos are now fully answered.** The retry pass succeeded where the first pass didn't
  because (a) `gemini-flash-lite-latest`'s overload cleared, and (b) splitting the two
  longest/most-congested videos (video 3 at 27 minutes, video 4 which kept 503'ing even as a single
  short clip) into 4–5 minute clips aligned to their own chapters got requests through reliably,
  even while a single full-video agentic request to the same model kept failing with 503.
- **If this pattern shows up again:** don't burn a model's daily quota retrying a full-video
  agentic request into a wall of 503s — switch to `--start`/`--end` clips on the same model first;
  it worked far more often here than waiting and retrying the whole video.
- Video 2 (The Coding Sloth) still stands as answered by `gemini-3-flash-preview` in one agentic
  pass from the first session; that model's daily quota was fully spent on repeat attempts against
  video 1 in the first pass and had not recovered by the time of this retry.
- Two OCR/transcription caveats worth flagging to whoever drafts the report: video 1's rule 4 quote
  contains the word "entropic," almost certainly a mis-hearing of "Anthropic"; video 3's refined
  system-prompt quote (13:58–14:52) has some garbled fragments from on-screen OCR — treat both as
  best-effort, not verbatim.
