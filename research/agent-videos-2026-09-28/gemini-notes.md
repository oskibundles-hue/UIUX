# Gemini watch notes — 2026-09-28 agent-videos batch

Four videos, watched with the `watch` skill's Gemini engine (agentic video processing — Google
watches the video directly; this container's IP is blocked from touching YouTube itself, so this
was the only route). Free-tier limits (~5 req/min, 20 req/day per model) and 503 "high demand"
errors meant only one of the four videos got a full answer this session; the other three are
documented as failures below rather than guessed at. Raw Gemini output (or raw failure log) for
each video is saved under `raw/<video-id>.md`.

---

## 1. Ben AI — "Anthropic Just Revealed 7 New Rules for Prompting Claude 5 Models"

- **URL:** https://www.youtube.com/watch?v=HDmBwU5uvEE
- **Channel (confirmed via oEmbed):** Ben AI
- **Length:** not obtained
- **Model that answered:** none — every model in the fallback order failed

**Gaps:** Gemini never watched this video. `gemini-3-flash-preview` first refused with "Agentic
video processing is not enabled for this model" (HTTP 400), then on retry hit its 20/day quota
(HTTP 429). `gemini-3.6-flash` and `gemini-3.7-flash` also hit their 20/day quota after repeated
503 retries. `gemini-flash-lite-latest` returned HTTP 503 "high demand" on every single attempt
(6+ tries across this session) and never once succeeded. None of the 7 rules, their explanations,
before/after prompt examples, cited Anthropic pages, or shown tools/links could be captured. Full
attempt log in `raw/HDmBwU5uvEE.md`.

---

## 2. The Coding Sloth — "I Have Spent 1000+ Hours With Claude Code. This Is What I Learned"

- **URL:** https://www.youtube.com/watch?v=YAsxyoTWFDA
- **Channel (confirmed via oEmbed):** The Coding Sloth
- **Length:** 22:31 (per Gemini; not independently re-verified against a chapter list — this
  video has none)
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

**Gaps:** the video has no chapter list to check the timestamps against (per the task brief), so
these mm:ss marks are Gemini's own placement and weren't cross-checked against a second source.
Nothing in the answer flagged as unseen/unheard — Gemini didn't note any gaps of its own for this
video.

---

## 3. Systems Made Better — "I Made Claude My Personal Assistant (Full Build)"

- **URL:** https://www.youtube.com/watch?v=3ZT0upsICHk
- **Channel (confirmed via oEmbed):** Systems Made Better
- **Length:** not obtained
- **Model that answered:** none — every model in the fallback order failed

**Gaps:** Gemini never watched this video. All four models returned HTTP 503 "high demand" on
their first attempts; by the time a retry reached `gemini-3-flash-preview`, that model had already
spent its 20/day quota on video 1's attempts (HTTP 429). None of the assistant's on-screen
instruction text, the Notion database fields, the scheduled task's cadence/prompt, the ASD-STE100
discussion, the context map, or the finished daily brief could be captured. Full attempt log in
`raw/3ZT0upsICHk.md`.

---

## 4. Teku AI — "The LATEST Hermes Agent Update is INSANE!"

- **URL:** https://www.youtube.com/watch?v=dCZK-VssIWw
- **Channel:** Teku AI (per the task brief — YouTube's oEmbed returned "Unauthorized" for this
  video, as expected)
- **Length:** not obtained
- **Model that answered:** none — every model in the fallback order failed

**Gaps:** Gemini never watched this video. One `gemini-3-flash-preview` attempt timed out in-flight
after 200s without an error (possibly still processing when the client gave up); its retry and
every attempt on the other three models returned HTTP 503 "high demand." This video was not tried
against a fifth round, so no 429 quota errors were seen for it specifically — the models were
simply unavailable at every attempt. None of the four features (Bot Screen, Simple layout mode,
Connectors menu, One-click local models, "Hey Hermes" wake word) could be assessed — no test
results, hardware/plan, picked model, breakage, prices, or verdict. Full attempt log in
`raw/dCZK-VssIWw.md`.

---

## Session-level notes for the lead

- Only **1 of 4** videos got a real answer: video 2 (The Coding Sloth), on `gemini-3-flash-preview`.
- By the end of this session, `gemini-3-flash-preview`, `gemini-3.6-flash`, and `gemini-3.7-flash`
  had all hit their 20-requests-per-day Free Tier cap (per SOURCE.md, that resets ~07:00 UTC).
  `gemini-flash-lite-latest` never hit a quota wall but returned HTTP 503 "high demand" on every
  single attempt all session — Google's backend for that model was persistently overloaded during
  this run, independent of quota.
- Retrying videos 1, 3, and 4 after 07:00 UTC (when the daily caps reset) is the most likely way to
  get them answered — start with `gemini-flash-lite-latest` or `gemini-3-flash-preview` first,
  since those showed the least resistance in this session (`gemini-3-flash-preview` was the one
  that actually worked).
