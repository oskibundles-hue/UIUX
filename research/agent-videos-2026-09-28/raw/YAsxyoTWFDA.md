[watch] asking gemini-3-flash-preview…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=YAsxyoTWFDA (URL sent to Google)
- **Engine:** gemini-3-flash-preview (agentic)
- **Gemini tokens:** 126953

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

This video is **22:31** in length.

### **Full Tier List of Claude Code Features**
The creator builds this tier list throughout the video, ranking features from F to SSS (Vibes) based on their utility and cost-effectiveness.

*   **S-Tier**
    *   **Plans / Plan Mode** (06:52): "If you hit shift and tab on Claude Code, Claude goes into plan mode." Used for "BIG TASKS" (07:23).
    *   **Verification** (08:38): "I'm giving this feature like an S tier and if anything a double S or even a triple S."
    *   **Subagents** (20:25): Ranked S-Tier for users on high-tier plans or with "unlimited tokens."
    *   **/loop** (17:59, 19:06): "S tier for real this time."
*   **A-Tier**
    *   **Skills** (05:07): "But if you're smart with it, easy S tier."
    *   **CLAUDE.md file** (04:13): Upgraded from B to A-Tier after "months of dealing with the sloppy code" (04:15).
    *   **MCPs (Model Context Protocol)** (10:01): "Actually, I'm lying. A tier."
    *   **Subagents** (20:24): Standard ranking for users on the $20/month plan due to token costs.
    *   **Worktrees** (20:32): "A tier."
    *   **Pre-installed Skills** (05:33): Such as `/code-review` and `/security-review`.
    *   **/teleport and /remote control** (11:54): "I'll give it an A tier" if you "touch grass a lot."
*   **B-Tier**
    *   **/voice** (10:52): "B tier."
    *   **/context** (13:48): "I'll give this command a B tier. I think it's pretty important to use."
    *   **/goal** (19:22): Ranked B-Tier for lower plans, A-Tier for higher plans (19:28).
*   **C-Tier**
    *   **/btw** (11:10): "C tier. Probably won't use this much, but it's nice to have."
    *   **Shell Mode / ! prefix** (12:01): "Also a C tier."
    *   **/compact** (15:03): Ranked C-Tier when used automatically, B-Tier if you use it manually (15:07).
*   **D-Tier**
    *   **/init** (04:10): "In it still stays the same. I think it's pretty mid."
    *   **/teleport and /remote control** (11:58): Ranked D-Tier if you "just don't use it."
*   **F-Tier**
    *   **/radio** (12:20): "F tier for productivity but triple S tier for vibes" (12:22).

---

### **Token and Context Management Tips**
The creator emphasizes that Claude tracks usage by tokens, not prompts (12:54).

*   **Context Limits** (13:23): On-screen text: "Sonnet 4.5, have a 200k-token context window." "claude-mythos-5 have a 1M-token context window." "Claude Code defaults to a 1-million-token context window for users on Max, Team, and Enterprise plans" (13:27).
*   **The "Dumb Zone"** (13:38): Performance dips once above **100k or 200k tokens**. "That's when the performance starts to dip a bit and those usage limits get cooked" (13:41).
*   **Task Cost** (14:15): A medium or big task uses a minimum of **50k tokens**.
*   **Heavy Usage** (14:18): Using a skill or MCP can easily push a single response above **100k tokens**.
*   **New Sessions** (14:04): "Number #1: for every new task start a new session." This prevents the model from getting "dementia" due to high context.
*   **Specific Prompts** (14:44): Be "STUPIDLY SPECIFIC" (14:46) to prevent Claude from reading unnecessary files and wasting tokens.

---

### **Specific Tool Usage**
*   **skills.sh** (05:58): Described as the "go-to place for finding and installing skills."
*   **Ponytail, rtk, and Caveman** (15:32): These are community-built "High-performance CLI proxy[s] that cut[s] up to 90% of the bash output your agent reads" (15:33).
    *   **On-screen text**: "Ponytail... -54% less code (up to 94%) -- -20% cheaper -- -27% faster -- 100% safe" (15:33).
    *   **On-screen text**: "Caveman: Cut 65% of your AI costs" (15:35).

---

### **Views on Claude Code Alternatives**
The creator notes that this video is "not sponsored" (01:52) and discusses alternatives:

*   **Codex** (21:11): "I personally love it. I think that's the one I've been using the most. Their usage limits are actually generous" (21:12).
*   **OpenCode** (21:21): "Essentially the open source version of Claude Code... if you want to use any model, I do recommend you check it out" (21:25).
*   **Pi** (21:28): "Basically like a minimalist setup... if you're the type of person that wants to create their own workflow from scratch, this is the tool for you" (21:34).
*   **Cursor** (21:36): "What I like to use if I need to use an IDE... this one also lets you pick any type of model" (21:41).
*   **T3 Code** (21:54): "The UI of T3 Code way more... if you have multiple subscriptions... then maybe you should check out T3 Code since you can basically use all your subscriptions in just one application" (22:11). On-screen text: "The open-source control plane for coding agents" (21:58).

---

### **Testing and Verification Advice**
The creator stresses that Claude "can't know if it's correct" without verification (08:55).

*   **Test-Driven Development** (09:09): "Tell Claude to write the tests first and then implement so you don't cheat and write sloppy toppy code."
*   **The Trap** (09:12): Do not tell it to implement and *then* test. "It's just going to write tests that pass its own code... that's cheating" (09:16).
*   **Selective Testing** (09:20): "Make sure you don't test every single line, just test the most important things."
*   **Type Checks** (09:31): "Tell Claude run type checks... before considering the task done" (09:35).
*   **UI/Frontend** (09:40): Use "screenshot testing" and "browser testing" because Claude is "literally blind" to what it makes (09:44).
