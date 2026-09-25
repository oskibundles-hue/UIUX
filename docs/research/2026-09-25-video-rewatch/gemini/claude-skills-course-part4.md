
# watch: video report

- **Source:** https://www.youtube.com/watch?v=-DawhgUKiOg (URL sent to Google)
- **Engine:** gemini-3-flash-preview (static clip 1:30:00–2:00:00)
- **Focus range:** 1:30:00 → 2:00:00
- **Gemini tokens:** 167004

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

This report covers the segment of the course detailing the progression from individual automated skills to a fully orchestrated "SEO Department" packaged as a plugin, alongside the creation of a brand voice skill to eliminate "AI slop."

### 1. Frameworks, Rules, Definitions, and Checklists

*   **The Five Gates (90:13):** A checklist for auditing web pages: "Every page has to pass five gates... 1. Can it be found? 2. Is it indexable? 3. Does it have trust signals? 4. Can it be read? 5. Does it convert?"
*   **The Chain Rule (92:13, 107:33):** "If you run the same skills in the same order every time, you have failed. You are then a chain with extra steps, and a chain does not need a manager."
*   **The Manager/Orchestrator Definition (92:48):** "A Manager: You give it a goal in plain language. It works out the route... No-body wrote the sequence... Tells you its plan first... Changes to mind on evidence."
*   **Anti-AI Slop Writing Directive (115:10):** A set of structural rules to make text less "AI-like":
    *   **No Rule of Three:** Avoid the "A, B, and C" pattern.
    *   **No Uniform Sentence Length:** Vary sentence cadence.
    *   **No Parataxis:** Avoid a sequence of short, choppy sentences.
    *   **No Hedging:** "Pick a side. State it plainly."
    *   **No "As [role], ..." Openers:** Avoid typical LLM persona introductions.
*   **The Brand Voice Rule (119:53):** "One rule that outranks everything: Change how it is written. Never change what it says."

### 2. Tools, Connectors, Plugins, and Skills

*   **`search-visibility-audit` (90:08):** Audits a website for search and AI visibility, scoring it out of 10. It has two modes: "Full audit" and "Targeted investigation."
*   **`seo-six-month-strategy` (90:19):** Pulls keyword data and writes a six-month roadmap into Notion.
*   **`seo-blog-writer` (91:42):** Turns transcripts or briefs into publishable SEO-ready blog posts.
*   **`seo-client-report` (92:00):** Pulls GSC and GA4 data to grade performance against the strategic plan.
*   **`seo-department` (105:27):** A Level 5 Orchestrator skill that acts as a "line manager," routing goals to the four specific SEO skills.
*   **`brand-voice` (119:10):** A non-deterministic skill that learns a user's specific writing style through analysis and applies it to drafts.
*   **Connectors (115:16):** Firecrawl (web scraping), DataforSEO (SERP data), Semrush (SEO metrics), Notion (strategy storage), Gmail (outreach), and Google Drive (file management).
*   **SEO Department Plugin (107:11):** A "filing system" package containing the orchestrator, sub-skills, reference files, and required connector definitions.

### 3. Step-by-Step Builds

#### **Building the SEO Orchestrator (92:48 – 105:27)**
1.  **Requirement:** Have individual skills built and "dialed in" (Levels 1-3).
2.  **Prompt (94:23):** "I have 4 skills that make up an SEO department... Build me an orchestrator skill that manages them. It should: Know what each of the five does... Take a goal in plain language... Decide which skills to run and in what order... Tell me its plan before it executes... Report back at the end."
3.  **Result:** Creation of `seo-department`. It generates a plan (e.g., audit first, then strategy) based on real-time data like seasonality (September/December deadlines) (110:11).

#### **Packaging the Skill Plugin (115:15 – 118:02)**
1.  **Requirement:** A set of related skills and their dependencies.
2.  **Prompt (115:57):** "Can we turn my four SEO skills, plus my SEO department skill, into a plugin with all of the skills included, with their reference files, as well as the connectors required to run the SEO department? Call it the SEO department plugin."
3.  **Output:** A structured file set including `plugin.json` (metadata), `.mcp.json` (connectors), and a `SKILL.md` for each component (117:11).

#### **Building the Brand Voice Skill (118:59 – 121:10)**
1.  **Stage 1: Analyse (119:52):** Provide 5-10 samples of human writing. The prompt instructs Claude to extract sentence mechanics, vocabulary, and structure (119:58).
2.  **Stage 2: Build (120:13):** Convert the analysis into a skill that rewrites drafts.
3.  **Stage 3: Refine (120:37):** Bake in the "Anti-AI Slop" rules and a "Banned Words List" (115:45) containing terms like *delve, tapestry, landscape, meticulously,* and *crucial*.

### 4. UI Shown

*   **Skill Proposal Cards (90:08):** Used to update or dismiss proposed changes to skill definitions.
*   **Claude Memory/Context Window (110:56):** Shows Claude reading "SEO loop state files" and "project info" to understand current progress.
*   **Skill Registry (106:45):** A table mapping skills to their functions, required inputs, and outputs.
*   **Plugin Management View (117:33):** Displays the "Overview," "Contents," "Skills," and "Connectors" (Firecrawl, Semrush, etc.) for a package.
*   **Evals Dashboard (121:38):** A multi-agent testing interface showing 6 agents running parallel tests ("Eval with skill" vs "Eval baseline") to quantify the skill's performance.

### 5. Actionable Takeaways for a Marketing Agency

1.  **Don't build everything at once (90:36):** Individual skills must be perfectly "dialed in" before linking them. Building a full suite simultaneously results in a "complete mess."
2.  **Skills as Employees (105:54):** Think of Level 1-4 skills as individual contributors and the Level 5 Orchestrator as the Department Head.
3.  **Use Plugins for Portability (118:23):** Packaging skills as plugins allows an agency to share a standardized "department in a box" with different clients or team members without losing dependencies.
4.  **Implement Automated Evals (121:38):** Use the multi-agent testing feature to compare AI outputs against a human-written baseline. This catches regressions before they reach the client.
5.  **Audit the "AI Telling" (120:37):** Every agency should have a "Banned Words List" and an "Anti-AI Slop" directive baked into their core brand voice skills to ensure content doesn't sound synthesized.
