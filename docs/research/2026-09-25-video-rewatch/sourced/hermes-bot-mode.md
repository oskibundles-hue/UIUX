# Hermes Bot Mode Is A Cheat Code. Here's How I Use It (reconstruction without watching)

**How to read the tags.** `[SOURCE: Sx]` means the claim comes from a page in the key below. `[SOURCE: S1-img]` means it was read from a screenshot or graphic in S1. Those images are stills and graphics from the video: the article's structured data lists the video as its `VideoObject` and uses the video thumbnail as its image. `[INFERRED …]` means the claim is my reconstruction. `[REC]` marks my own recommendation for NQ OS.

| Key | URL | What it is |
|---|---|---|
| S1 | https://sharbel.com/s/hykjy → https://sharbel.com/articles/build-ai-agent-team | The creator's companion article for this video, published 2026-09-22, the same day as the video. Its sections follow the video's chapters one to one. **This is the primary source.** |
| S2 | https://hermes-agent.nousresearch.com/docs/user-guide/bot-mode | Official Bot Mode docs |
| S3 | https://github.com/NousResearch/Hermes-Bot-Mode | Original plugin README (now archived) |
| S4 | https://hermes-agent.nousresearch.com/docs/user-guide/security | Approvals and security docs |
| S5 | https://hermes-agent.nousresearch.com/docs/user-guide/profiles | Profiles docs (SOUL.md, cloning) |
| S6 | https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers | Memory providers docs |
| S7 | https://hermes-agent.nousresearch.com/docs/user-guide/features/tools | Tools and toolsets docs |
| S8 | https://hermes-agent.nousresearch.com/docs/user-guide/features/skills | Skills docs (progressive disclosure) |
| S9 | https://hermes-agent.nousresearch.com/docs/getting-started/installation | Install docs |
| S10 | https://aitoolsreview.co.uk/insights/hermes-agent-bot-mode-release | Release history |
| C1 | https://code.claude.com/docs/en/sub-agents | Claude Code subagents |
| C2 | https://code.claude.com/docs/en/agent-teams | Claude Code agent teams |

---

## 1) Title, creator, length, and what Hermes is

- **Title:** "Hermes Bot Mode Is A Cheat Code. Here's How I Use It". **Creator:** Sharbel Ayyoub (@sharbelxyz on YouTube, @sharbel on X). **Length:** about 17 minutes, published 2026-09-22. [SOURCE: S1]
- **Hermes** is **Hermes Agent** by Nous Research. It is free, open source (MIT) and self-hosted. It runs from a CLI, a desktop app and messaging gateways (Telegram, Slack, and others). It has persistent memory, skills, cron, subagents and MCP. [SOURCE: S1, https://hermes-agent.nousresearch.com/]
- **Bot Mode** is part of the Hermes **Desktop app**. It turns Hermes *profiles* into a roster of named Bots, each with its own role, model, memory, skills and avatar. Bots run routines, share group chats and message each other. It is built in and on by default, and appears as a **Bots** tab next to Sessions. [SOURCE: S2]
- **A Bot is a profile.** Each profile lives under `~/.hermes/profiles/<name>/` with its own `config.yaml`, `.env`, `SOUL.md`, memories, skills, cron jobs and `state.db`. The CLI equivalent is `hermes -p <bot> chat`. [SOURCE: S2, S5]
- **Timeline.** Bot Mode started as Teknium's one-day beta plugin. It was bundled and turned on by default in Hermes Agent **v0.20.3 (2026-08-16)** via PR #87886, and group-chat fixes followed in v0.20.4. [SOURCE: S3, S10]

## 2) Core thesis

Bot Mode does not give you smarter agents. It lets agents coordinate, so you stop being the person who carries work between five chats. You give one orchestrator a job, and it hands pieces to specialist bots in a shared room. [SOURCE: S1]

What makes the team cheap and safe is discipline applied to each bot. Give each bot one job and only the tools that job needs. Put a strong model on the orchestrator and cheap models on the workers. Put hard approval gates on the few actions you would regret. [SOURCE: S1]

## 3) Tools, repos, models, MCPs and services

| Item | What it does | URL / install |
|---|---|---|
| Hermes Agent | Agent runtime, CLI and gateway | `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash`, then `hermes desktop` [SOURCE: S9] |
| Hermes Desktop + Bot Mode | Bots roster, Routines pane, group rooms, `message_agent` | Built in. Toggle it at Capabilities → Plugins → Bots [SOURCE: S2]. The old plugin repo is S3 (archived) |
| Model Context Protocol (MCP) | Connects a bot to external systems such as Gmail, Notion and GitHub | https://modelcontextprotocol.io/ and https://github.com/modelcontextprotocol [SOURCE: S1] |
| Sales CRM MCP | Gives his "Sales Agent" search and sort over leads. The vendor is not named | [SOURCE: S1] |
| Instagram access | Given to the content creator bot only. The mechanism (MCP or tool) is not named | [SOURCE: S1] |
| Honcho / mem0 / Supermemory | External shared-memory providers. Only one can be active per profile, and built-in `MEMORY.md`/`USER.md` memory stays on alongside it | https://honcho.dev, https://mem0.ai, https://supermemory.ai. Set it with `hermes memory setup` or `memory.provider:` in `config.yaml` [SOURCE: S1, S6] |
| Models | The orchestrator gets "your strongest model". Workers get a cheaper model or a free local model. **No specific model names appear in any source I found.** | [SOURCE: S1] |
| Image generation | The creator bot produced carousel PNGs (`carousel/slide-01.png` to `slide-07.png`) and a `contact-sheet.jpg` | [SOURCE: S1-img] |

## 4) Step-by-step build, by chapter

Chapter timestamps come from the YouTube description. Matching each timestamp to an article section is **[INFERRED from chapter title]**. The content under each chapter is **[SOURCE]**-tagged.

### 0:00 My AI Agents Run the Business
- He used to run one agent. He now runs a team that handles his inbox, clients and content. "The thing that changed was not the agents. It was the coordination." [SOURCE: S1]
- His roster also includes Sales Agent, Youtube (a bot called "Nova"), Engineer and Admin. [SOURCE: S1-img]

### 0:40 What Hermes Bot Mode Actually Is
- "A bot is a profile." It has its own persona, model, tools, access and memory. What is new is that bots talk to each other. You give one bot a job, it splits the work and passes pieces on, and the bots sort it out in one shared room. [SOURCE: S1]
- Graphic: "FIVE SEPARATE CHATS versus ONE SHARED ROOM" and "the number of times you got pulled in". The point is that you stop being the router. [SOURCE: S1-img alt text]

### 1:35 Three Ways Hermes Bots Communicate
1. **One on one.** A permanent chat with a single bot. In the docs this is the canonical, forever "Bot Chat". [SOURCE: S1, S2]
2. **Direct.** One bot messages another. Under the hood this is `message_agent(target="researcher", message="…")`, which is fire-and-forget, auto-attributed as `Message from 🤖 <name> (@<handle>): …`, and delivered into the target's Bot Chat. [SOURCE: S1, S2]
3. **Group room.** Two to six bots in one thread with a turn cap. He says the cap is what stops two agents looping "until your tokens are gone". The docs specify **up to 3 serial rounds and 10 messages per send**. A bot can pass or stay silent, and the room settles when a whole round is silent. [SOURCE: S1, S2]

### 2:09 Build Your First Bot Team
- "Build one bot. Understand what each setting does to it. Then add the second." If you don't understand the individual bot, you can't tell whether a bad result came from the model, the tools or the soul. [SOURCE: S1]

### 2:21 Create the Bot
- Click **New bot**. The dialog has **Create on** (which machine), **Title**, **Description**, an **Advanced** disclosure, and a **Create Bot** button. His example title is "Sales Agent". [SOURCE: S1-img]
- The **title** is what shows in the sidebar, and the **name** is the `@` tag. A one- or two-sentence description is enough, because "Hermes writes the bot's whole personality for you". You can clone from your default profile so the bot inherits your setup, and you can pick a model. [SOURCE: S1]
- The Advanced section offers: clone from an existing profile or start fresh; **Create empty** (skips bundled skills); a model and provider pin; a custom SOUL.md; per-skill, per-toolset and per-MCP enablement; and "copy API keys from main profile" (on by default). [SOURCE: S2]

### 2:52 Write Its Soul
- The description becomes the bot's **soul** (`SOUL.md`), which holds its personality and rules. You can open it and tighten it whenever you like. [SOURCE: S1, S5]
- Lines he added to his sales agent's soul, verbatim: [SOURCE: S1]
  ```
  Never discuss prices unless I approve them first.
  Always hand the result back to my main Hermes instance, never straight to me.
  ```
- "A vague soul file produces a bot that improvises, and improvisation is what you are trying to remove." [SOURCE: S1]
- Per the docs, SOUL.md changes apply cleanly on a *new* session, and SOUL.md guides behaviour but does not enforce boundaries. [SOURCE: S5]

### 3:26 Prune Its Tools and MCPs (the longest segment, about 2 minutes)
- He splits capabilities into three kinds. **Skills** are saved workflows that load only when needed, so they cost almost nothing to leave on. The docs call this progressive disclosure, with about 3k tokens for the skills index. **Tools** are live actions that load into every message. **MCPs** are external connections. [SOURCE: S1, S8]
- "Every new bot starts with every tool and MCP its parent had switched on." [SOURCE: S1]
- "Some tools carry upwards of 50,000 tokens that load into every message." This is the creator's figure; the docs don't confirm it. [SOURCE: S1]
- Graphic: "EVERY TOOL LOADS, EVERY MESSAGE" compares 20 tools enabled with 3 tools enabled and the context each spends per message. [SOURCE: S1-img]
- The tools pane he showed is sorted by "Most used", with a toggle per toolset:

  | Toolset | Tools | State |
  |---|---|---|
  | cua-driver desktop control | 1 | off |
  | Cron Jobs | 1 | on |
  | File Operations | 4 | on |
  | Home Assistant | 4 | off |
  | Image Generation | 1 | off |
  | Memory | 1 | on |
  | Session Search | 1 | on |
  | Skills | 3 | on |
  | Speech-to-Text | 0 | on |

  [SOURCE: S1-img]
- The rule: give each bot only what its one job needs, because "a bot choosing between three tools makes better choices than one choosing between twenty." [SOURCE: S1]
- The reverse also holds: MCPs are what make a bot a specialist. His Sales Agent alone gets the sales CRM MCP. "One bot, one upgrade, and the whole team's output improves." [SOURCE: S1]
- CLI equivalents: `hermes tools`, `hermes chat --toolsets "web,terminal"`, and dynamic MCP toolsets named `mcp-<server>`. [SOURCE: S7]

### 5:30 Pick the Right Model
- The **orchestrator** gets the strongest model, because it decides, delegates and reasons. The **workers** get a cheaper model, or a local one "for free". Same result on simple work at a fraction of the cost. [SOURCE: S1]
- To set it, use the model pin in Advanced or Edit Profile. Different bots can run different providers side by side. [SOURCE: S2]

### 6:18 Memory, Warm Bots, and Timeouts
- **Memory.** Only the orchestrator writes to a shared provider (Honcho, mem0 or Supermemory). Every other bot uses built-in memory only, which avoids storing the same fact twice and wasting context. [SOURCE: S1]
  ```
  Orchestrator  ->  shared memory provider (Honcho / mem0 / Supermemory)
  Every other bot  ->  built-in memory only
  ```
  The docs back this up: `memory.provider` sits in each profile's `config.yaml`, and Honcho creates one AI peer per profile in a shared workspace. [SOURCE: S6]
- **Warm bots.** Raise the number kept warm from **3 to 5** so switching bots is instant. The setting is Settings → Advanced → Warm Bot Backends, default 3, about 60 MB each. If every slot is busy, a newly opened bot waits 30 seconds and then fails. [SOURCE: S1, S2]
- **Idle timeout.** The default is **10 minutes**. Raise it to **20–30 minutes** depending on your longest job, so long jobs don't die halfway. [SOURCE: S1, S2]

### 7:17 Set Guardrails That Actually Work
- Write a **regret list**. His has three items: `1. Spending money  2. Sending something to a client  3. Deleting things`. Everything else runs without asking him. [SOURCE: S1] The graphic reads "THE RULE I NEVER SKIP: ONE GATE, THREE THINGS". [SOURCE: S1-img]
- He sets gates in three layers, strongest first: [SOURCE: S1]
  1. **Don't give the bot the tool.** "Never handing a bot the keys is the only gate that cannot be argued with."
  2. **Set the approval setting to Smart.** It auto-runs safe actions, blocks dangerous ones and asks about the rest. The prompt offers **Allow once / Allow for the session / Always allow / Deny**. In config this is `approvals: mode: smart` (options: smart, manual, off). An auxiliary LLM judges risk. "Always" writes to `command_allowlist`. The timeout defaults to 300 seconds and fails closed. Related keys are `cron_mode: deny`, `single_query_mode: deny` and `approvals.deny` glob rules, which even YOLO mode can't override. [SOURCE: S4] In group rooms, approvals are answered inline and light a "needs you" badge. [SOURCE: S2]
  3. **Add a soul rule:** `Never send anything to a client without my explicit approval.` It is "not a hard wall … use the soul to reinforce a gate, never as the only lock." [SOURCE: S1]

### 9:16 Build a Real Content Team (about 7 minutes, the demo)
- **Team:** an orchestrator plus a researcher plus a content creator, to run an Instagram page. [SOURCE: S1]
- He didn't build the bots by hand. He asked his main Hermes instance, "Hermy", to build the team with this prompt (verbatim): [SOURCE: S1]
  ```
  Hey Hermes, I'd like for you to help me build a team that will post and
  manage content creation on an Instagram page for me. You can ask me as many
  questions as you would like until you reach clarity.

  Ultimately, I'm thinking we could have two Hermes Bot employees. The first
  one, a researcher that monitors what is working in that specific niche. And
  the second one, a content creator that will take that information and create
  content, posts and graphics in the approved styles that we end up choosing
  and the direction we end up going for.

  Ultimately, I want you to be the one relaying the information back to me. I
  don't want to be speaking to the other bots. I want you to be my main point
  of contact. Can you help me out with that?
  ```
- Hermy asked clarifying questions, then created both profiles, wrote their soul files and created the group chat itself. The souls it wrote each had "a mission, a reporting line, responsibilities". [SOURCE: S1] The full text of those souls is **not published** in any source.
- The one manual step: he opened each bot and pruned its tools. The creator gets Instagram; the researcher gets only what research needs. [SOURCE: S1]
- **Tagging:** `@researcher`, `@creator`, `@all`, or the orchestrator by name. [SOURCE: S1] The composer placeholder reads "(@name to direct, @everyone for all)". [SOURCE: S1-img]
- **The job:** find content angles to revive "Daily Psych", a psychology page he used to run. He tagged the orchestrator and left it alone. [SOURCE: S1]
- **Kickoff message from Hermy:** "I'll coordinate and quality-check the final package. @researcher, surface today's strongest evidence-backed psychology angles; @creator, turn the best one into a sharp, practical conc[ept]…" [SOURCE: S1-img]
- **The flow:**
  1. The researcher returns angles.
  2. The creator turns the best one into a concept and hands back to the orchestrator.
  3. The orchestrator **tags the researcher again to fact-check the copy**.
  4. The researcher replies "@hermes no res[ervations]… claim streng[th]…".
  5. Only then does the result reach him.

  "Nothing reached me until it had been through another agent." [SOURCE: S1, S1-img]
- Hermy's "Final quality c[heck]" list includes (truncated in the screenshot): "Behavioral…", "No promise…", "Uses Resea[rch]…", "Slide 1 work[s]…", "Clear CTA", "Faceless br[and]…", "Evidence-b[ased]…". [SOURCE: S1-img]
- **Output:** a "MIND + BODY" carousel about sleep and mood. Slide 1: "Before you blame your personality, check your sleep." The article says six slides. The screenshot shows slides numbered /07 and files `slide-01.png` to `slide-07.png`, so there is a minor inconsistency. [SOURCE: S1, S1-img]

### 16:21 Make the Team Improve Itself
- After each job, send this prompt (verbatim): [SOURCE: S1]
  ```
  Save what you learned from this round: my format, my style, the sources I
  trust, and anything I corrected. Use it as the default next time.
  ```
- "You are not running a team, you are training one." [SOURCE: S1]

### 16:51 When Bot Teams Are Worth It
- Don't build a team for one-off jobs: "Do not build a company to answer one email." Build teams for **weekly recurring** work such as content, business processes and routine workflows. [SOURCE: S1]
- His closing checklist: [SOURCE: S1]
  1. One bot with a name, a title and a one-sentence job.
  2. Turn off unneeded tools.
  3. Use a cheap model for grunt work.
  4. Write the regret list and set the gates.
  5. Only then add bot #2.
- His FAQ recommends that three bots (orchestrator, researcher, maker) are enough for most workflows. [SOURCE: S1]

## 5) UI and dashboard shown

All from video stills in S1. [SOURCE: S1-img]

- **Hermes Desktop left sidebar:** tabs **SESSIONS | BOTS**, a mute bell and **+**, and a search box "Search bots and group chats…".
  - **DAILYPSYCH** section (3): the room "Daily Psych Content Team" (preview "@hermes: @user this room…"), Creator and Researcher.
  - **UNASSIGNED** (5): Hermy (pinned), Sales Agent, Youtube ("Nova here…"), Engineer and Admin.
  - A pixel pet sits bottom-left. The docs confirm pets (the petdex gallery) and sections. [SOURCE: S2]
- **Top tab strip:** "HERMY" and "DAILY PSYCH CONTENT TEAM". The room header has **Back** and a collapsed **Activity** line reading "turn settled". Messages are threaded with **Reply in thread** links, and a "Researcher is thinking…" indicator appears while a member works.
- **In-chat file preview:** `contact-sheet.jpg` with an "Open with Preview" button, which suggests macOS.
- **New Bot dialog** and **toolset toggle list:** described in section 4 above.

## 6) Five most actionable takeaways for NQ OS, mapped to Claude Code

The mapping assumes NQ OS stays on Claude Code and doesn't adopt Hermes. Claude Code facts are tagged C1/C2; the recommendations themselves are `[REC]`.

1. **One orchestrator you talk to; specialists report to it, never to you.** This is from his soul line and his team-building prompt. [SOURCE: S1] [REC]
   - Make the main session the NQ chief of staff.
   - Define one subagent per workstream or function in `.claude/agents/`: `fd-ads.md`, `se-production.md`, `nq-content-researcher.md`, `nq-content-creator.md`, `reviewer.md`. Each is YAML frontmatter plus a body; the body is the "soul". [SOURCE: C1]
   - Content pipelines are sequential, so plain subagents fit better than agent teams. Claude Code's docs say agent teams "use significantly more tokens" and suit parallel work. Teams are behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. [SOURCE: C2]
   - Copy his demo pattern: ask the main session to *interview you and then write* the agent files. [SOURCE: S1] [REC]

2. **Prune tools and MCPs per agent; this is the main cost lever.** [SOURCE: S1] [REC]
   - Give each agent a `tools:` allowlist and `disallowedTools:`.
   - Define heavy MCPs **inline in that agent's `mcpServers:`** rather than in `.mcp.json`. The docs say an inline server "keep[s] [it] out of the main conversation entirely"; it connects when the subagent starts and disconnects when it finishes. [SOURCE: C1]
   - Examples: Windsor.ai goes only on `fd-ads`, Dropbox only on `se-production`, Higgsfield/Adobe only on `nq-content-creator`. [REC]
   - Keep skills broadly available, since they load lazily in both Hermes and Claude Code. [SOURCE: S8] [REC]

3. **Tier models by role.** Use `model: opus` for the orchestrator and reviewer, and `model: sonnet` or `haiku` for researchers and formatters. Set it in each agent's frontmatter, or with `CLAUDE_CODE_SUBAGENT_MODEL`. [SOURCE: C1] [REC]

4. **Turn the regret list into hard gates, in his three layers.** For NQ OS the regret list is ad spend, anything sent to a client, and deletes. [SOURCE: S1] [REC]
   - **(a) Don't grant the tool.** The client-facing agent doesn't hold Gmail-send or Windsor `execute_action`. [REC]
   - **(b) Use `permissions.deny`/`ask` rules plus PreToolUse hooks in `settings.json`.** Target Windsor.ai `execute_action` (budget and bid changes), Dropbox `delete`, email send and `rm`. This matters because **a subagent's `permissionMode` is ignored when the main session is in auto, acceptEdits or bypass**, so hard gates can't rely on mode. [SOURCE: C1] Claude Code's auto mode is the closest analogue of Hermes "Smart" (classifier-judged). [INFERRED]
   - **(c) Repeat the rule in the agent prompt and CLAUDE.md**, as reinforcement only. [SOURCE: S1] [REC]

5. **Build in a verification hop and compounding memory.** [SOURCE: S1] [REC]
   - **Verification:** route the creator's output back to a researcher or reviewer subagent for fact-checking before it reaches you. In agent teams, a `TaskCompleted` hook that exits with code 2 can enforce this. [SOURCE: C2]
   - **Learnings:** end each recurring job with his "save what you learned" prompt, written to `memory: project` (`.claude/agent-memory/<agent>/MEMORY.md`). [SOURCE: C1]
   - **Single writer:** only the orchestrator writes to a shared store, such as Vertiso Memory `remember`, mirroring his rule that only the orchestrator uses Honcho/mem0. [SOURCE: S1] [REC]
   - Build this only for **weekly** workflows (FD reporting, SE production cadence, NQ content), not one-offs. [SOURCE: S1]

### Gaps: not recoverable without the video
- Exact spoken wording and any asides.
- Which models he actually picked.
- The full auto-generated soul files.
- Which Instagram and CRM connectors he used.
- The clarifying questions Hermy asked.
- Any on-screen numbers beyond those quoted above.
