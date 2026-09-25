
# watch: video report

- **Source:** https://www.youtube.com/watch?v=p3_Ql5nq4t4 (URL sent to Google)
- **Engine:** gemini-3-flash-preview (agentic)
- **Gemini tokens:** 106774

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

This report details the strategies and technical configurations for running a team of AI agents as presented by Sharbel.

### 1. Video Identity
*   **Exact Title:** How I run my life with a team of AI agents
*   **Creator/Channel:** Sharbel
*   **Length:** 18:22

### 2. Core Thesis
The video argues that the true "unlock" for AI productivity is not individual bots, but the coordination of specialized agents that talk to each other and hand off work autonomously. By building a team with a clear "orchestrator," specialized "workers," and human-in-the-loop "guardrails," users can automate complex recurring business processes while minimizing costs and risks.

### 3. Tools, Models, and Services
The video features the **Hermes Bot/Agent** platform extensively (00:17).

**Models (05:44):**
*   **GPT-6-astra / GPT-6-astra-900k:** High-tier models.
*   **GPT-5.6-soul / GPT-5.6-sol / GPT-5.6-sol-900k:** Persona-optimized models.
*   **GPT-5.6-terra / GPT-5.6-luna / GPT-5.6-luna-900k:** Various performance tiers.
*   **GPT-5.5:** Shown as a cost-effective option for "grunt work" (12:15).

**Skills (Saved Workflows) (03:31):**
`scriptwriting`, `million-subs-lab`, `hermes-agent`, `notion`, `wiki`, `kanban-agent-workflows`, `creative-web-and-visual-artifacts`, `software-quality-workflows`, `polymarket`, `property-investment-scouting`, `fireflies-meetings`.

**Tools (Live Actions) (03:43):**
`A2A` (Agent-to-Agent protocol), `Browser Automation`, `Clarifying Questions`, `Code Execution`, `Computer Use`, `Cron Jobs`, `File Operations`, `Home Assistant`, `Image Generation`, `Memory`, `Session Search`, `Speech-to-Text`, `Spotify`, `Task Delegation`.

**MCP Servers (The Catalogue) (03:55):**
`Codebase-Memory`, `Airtable`, `Algolia`, `Allrails`, `Amplitude`, `Asana`, `Atlassian`, `Attio`, `Aws-Knowledge`, `Betterstack`, `Buildkite`, `Calendly`, `Canva`.

**Memory Providers (06:30):**
`Honcho`, `Memo`, `Super Memory`, `Built-in only`, `Byteover`, `Hindsight`, `Holographic`, `Openviking`, `Retundo`.

### 4. Workflow and Build Demonstration
*   **02:21 – Step 1: Create the Bot:** Hit "New Bot," assign an icon, Title, and a unique Name for @tagging.
*   **02:51 – Step 2: Write its Soul:** Describe the bot’s job in one sentence. Hermes generates the `SOUL.md` persona file.
*   **03:26 – Step 3: Prune Tools:** Manually toggle off every skill, tool, and MCP server the specific bot doesn't need to save context and money.
*   **05:30 – Step 4: Pick its Brain:** Assign a strong model to the Orchestrator and a cheaper/local model to worker bots.
*   **06:18 – Step 5: Memory and Limits:** Restrict writing to shared memory to only the Orchestrator; set idle timeout to 20-30 minutes for long workflows.
*   **07:17 – Step 6: Set Guardrails:** Enable "Smart Approval" for sensitive actions like spending money or client messaging.
*   **09:16 – Live Team Build (Daily Psych):**
    *   Initiates an Instagram content team with an Orchestrator, Researcher, and Creator.
    *   Orchestrator delegates research to the Researcher bot (13:20).
    *   Creator bot drafts carousel slides based on research (15:36).
    *   Researcher performs a "final quality check" for factual accuracy (16:10).
    *   **16:28 – Post-Action:** Executes the command `@all learn from this round of feedback` to update persistent memory for future tasks.

### 5. Dashboard and UI Layout
*   **Sidebar (00:02):** A dark-themed left panel divided into "Sessions" and "Bots." Bots are organized into "Sections" (folders) like "DAILYPSYCH" (15:06).
*   **Bot Modal (00:51):** Central popup for configuration. Top section features a grid of geometric icons. Bottom section contains tabs: Model, Skills, Tools, MCP, Plugins, and SOUL.md.
*   **Capability Toggles (03:31):** A vertical list of features with blue toggle switches and green/red status indicators ("learned" vs. "not learned").
*   **Chat Interface (13:27):** A clean message thread where bot names are highlighted in purple. Tagging bots (e.g., `@researcher`) triggers a specialized response within the same thread.
*   **Output Viewer (15:36):** A file browser view showing generated assets (e.g., `.png` slides and `.zip` archives) produced by the agent team.

### 6. Takeaways for Marketing/Agency AI OS
1.  **Orchestrator-Worker Split:** Build one high-intelligence "Orchestrator" (using Claude 3.5 Sonnet or Opus) to manage project timelines, and multiple "Workers" (using Haiku) for repetitive tasks like keyword research or caption drafting to optimize cost.
2.  **Hard Gating:** Never allow an agent to "send to client" or "spend budget" without a manual approval gate. Use the "Smart" setting to automate low-risk drafting while blocking high-risk execution.
3.  **Tool Pruning:** Agencies should create minimalist bot profiles for specific tasks (e.g., a "Scraper Bot" only has Browser Automation) to prevent agents from getting "distracted" by irrelevant tools or wasting tokens.
4.  **Cross-Agent Fact-Checking:** Design workflows where a "Researcher" bot's sole job is to audit the factual claims made by a "Copywriter" bot before the draft reaches a human.
5.  **Compounding Memory:** Use the "learn from this" command at the end of every campaign to update the agency's shared brand voice and style guides, ensuring bots get smarter with every client project.
