
# watch: video report

- **Source:** https://www.youtube.com/watch?v=-DawhgUKiOg (URL sent to Google)
- **Engine:** gemini-3-flash-preview (static clip 1:00:00–1:30:00)
- **Focus range:** 1:00:00 → 1:30:00
- **Gemini tokens:** 166759

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

This segment of Eliot Prince’s course focuses on "Level 3" skills: using the **Recorder** feature to capture workflows, integrating **Connectors** (APIs), and **Chaining** multiple skills together into a production line.

### 1. Frameworks, Rules, and Checklists

**Six Rules for Building (06:51)**
1.  **One skill, one job (07:15):** "The most common structural mistake is the skill that does four things adequately. Split the job and compose focused skills instead."
2.  **Keep the main file tight (08:28):** "Under about 500 lines. Everything long goes into reference files that get loaded only when needed."
3.  **Write code for the mechanical bits (09:20):** Use scripts (e.g., Python) for arithmetic, file conversion, or bulk renaming rather than asking the LLM to do it directly. "One correct answer and no judgement? That is a script, not an instruction."
4.  **Build from work you have done well (10:21):** "Proof-based creation. Do the job, get it right, then capture it."
5.  **Show it three to five examples of good (11:21):** Provide actual pairs of "flat versions" and "versions you would ship."
6.  **Stop them fighting each other (11:33):** Ensure descriptions and trigger words don't overlap, which causes the wrong skill to fire.

**The Test That Tells the Truth (11:46)**
*   Run the same brief twice: once with the skill and once without. "If the skill does not clearly win, it is decoration."

**Three That Cost an Afternoon (11:51)**
*   **1024 characters:** The hard limit for a skill description.
*   **One reserved word:** You cannot use the word "Claude" in a skill name.
*   **A colon or a quote:** Using these inside the description can break the file.

### 2. Tools, Connectors, and Skills

*   **Claude in Chrome (01:51, 02:04):** An agentic web browser extension that allows Claude to navigate the web, summarize pages, and automate clicks.
*   **Recorder Skill (00:00, 06:11):** A feature in Claude Co-work that captures screen actions (clicks, typing) and audio commentary to generate a skill.
*   **Google Search Console (GSC) & Google Analytics (GA4) (01:00):** Sources for SEO data used in the demo.
*   **Apify (13:36, 14:19):** A connector used to scrape web data.
*   **Semrush (14:47):** An SEO connector for keyword and competitor analysis.
*   **DataForSEO (13:39):** A connector for quantitative SEO data.
*   **Firecrawl (13:39):** A connector used to read competitor pages.
*   **Notion (13:35):** Used as a push destination for finished work.

### 3. Step-by-Step Builds

**Build 1: SEO Client Report (Recorder Feature)**
*   **Workflow (00:00–01:53):** Eliot starts the recorder, opens Google Docs to type a report template, then moves to Gmail to draft a client email.
*   **Processing (01:54):** Claude processes 199 steps, including every click and keystroke.
*   **Skill Proposal (02:30):** Claude proposes `/seo-client-report`.
    *   *SKILL.md content visible:* "Run Eliot's monthly client SEO report; pull GSC + GA4 data year-over-year, write the good/bad/insight/opportunity report doc, and draft the client email."
*   **Execution (04:17):** Eliot runs the skill on `courchevel.vip`.
*   **Automation (04:29):** The UI glows orange as **Claude in Chrome** automates date range selections in Google Search Console without user input.

**Build 2: Six-Month SEO Strategy (Prompt-Based)**
*   **Prompt (15:13):** Eliot pastes a lengthy prompt: "You are Aleyda Solis, International SEO consultant... known for turning audits into sequenced, prioritized roadmaps... objective: build me a six-month SEO strategy..."
*   **Creation (16:33):** Claude generates the skill and several reference files: `SKILL.md`, `scoring-and-forecast.md`, `tool-routing.md`, `notion-build.md`, and `forecast.py`.
*   **Error Handling (18:35):** The build fails due to the 1024-character description limit. Eliot fixes this by pasting the error back to Claude to truncate the description.

**Build 3: Chaining Skills (Level 4)**
*   **Logic (19:35):** Eliot chains `/search-visibility-audit` to `/seo-six-month-strategy`.
*   **Trigger Options (20:39):** Claude asks how to trigger the next step:
    1.  **Offer, then wait:** Audit ends with a handoff block and asks the user to run the strategy (Recommended).
    2.  **Auto-chain always:** Immediately invokes the next skill.
    3.  **Only on explicit request:** Audit writes the file but says nothing.

### 4. UI Descriptions

*   **Claude Co-work Interface (00:46):** Central "How can I help you today?" box with "Chat" and "Co-work" tabs. Sidebar shows pinned, active, and scheduled tasks.
*   **Recorder Overlay (00:00):** A "Capturing" pill at the bottom of the screen showing "steps" and "Discard/Done" buttons.
*   **Claude in Chrome Indicator (04:29):** The browser tab and active window glow with an **orange border** and show an orange cursor when the agent is controlling the screen.
*   **File Browser (16:45):** A split-screen view in Claude showing generated Markdown and Python files on the left and the rendered output/chat on the right.

### 5. Actionable Takeaways for Agencies

*   **Clicks are the Process (06:09):** If a job is hard to describe in text, use the recorder. It treats browser navigation as a repeatable script.
*   **The Handoff Format (21:18):** When chaining skills, use an "explicit handoff block." This ensures the data from an audit is formatted correctly to serve as the "intake" for a strategy or reporting skill.
*   **Build a Database of Record (20:12):** Store outputs in Notion or a dedicated Claude Project folder. Chained skills need historical context (e.g., a reporting skill needs to see the original strategy to grade performance).
*   **Shift to Mechanical Bits (09:20):** For agency scaling, move math and data formatting into `.py` or `.js` reference files. This saves tokens and increases reliability over standard prompting.
