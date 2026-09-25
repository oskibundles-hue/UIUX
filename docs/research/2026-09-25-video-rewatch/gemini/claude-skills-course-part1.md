
# watch: video report

- **Source:** https://www.youtube.com/watch?v=-DawhgUKiOg (URL sent to Google)
- **Engine:** gemini-3.6-flash (static clip 00:00–30:00)
- **Focus range:** 00:00 → 30:00
- **Gemini tokens:** 169330

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here is a comprehensive, structured report of the provided video segment from Eliot Prince’s **Claude Skills Full Course**.

---

### 1. Frameworks, Rules, Definitions & Checklists Taught

#### **Definitions**
* **Claude Skill** (03:38): *"A set of instructions Claude keeps, to run on command."* Conceptually, it is an automated, self-executing Standard Operating Procedure (SOP) or checklist stored inside a folder.
* **Deterministic Skill** (18:20): A skill where *"you already know the shape of the answer before you build the skill."* Output follows a set template (e.g., invoices, structured audits, monthly reports).
  * **Rule**: Deterministic skills **fail loudly** (04:11, 19:04)—missing columns or numbers are obvious immediately.
* **Non-Deterministic Skill** (19:32): A skill where *"you know the quality you want, not the shape."* Relies on judgment, tone, or thinking frameworks (e.g., brand voice, second opinion, strategic advice).
  * **Rule**: Non-deterministic skills **fail quietly** (20:09)—outputs may look plausible but subtly drift from your standard or voice without raising an error.

---

#### **Frameworks & Models**

##### **1. Anatomy of a Skill (Folder Structure)** (06:08)
A skill is structured as a folder containing up to four components:
1. **The Description / Trigger** (`06:23`): A short summary at the top of the folder. It is the **only part Claude reads** when deciding whether to invoke the skill automatically.
2. **`SKILL.md` (The Decisions)** (`06:23`, `11:08`): The main instruction set. Controls how the job gets done, execution sequence, standards, output formatting, and prohibitions.
   * **Rule**: Keep `SKILL.md` tight and under ~500 lines (`10:31`).
3. **Reference Files (The Detail)** (`06:23`, `11:35`): Secondary files stored inside a `/references/` subfolder (e.g., style guides, checklists, schemas, long examples). They are **fetched dynamically** only when the workflow calls for them.
4. **Scripts (Optional / Mechanical Steps)** (`06:23`, `10:54`): Executable code (e.g., Python scripts) for exact calculations, formatting, or mechanical tasks. Faster, cheaper, and immune to prompt drift.

##### **2. The Five Levels of Skills** (21:07)
* **Level 1 — Run**: Triggered directly; requires no additional human input (`21:19`).
* **Level 2 — Ask**: Requires user input/context (e.g., pasting a transcript or answering questions) before completing the task (`21:37`).
* **Level 3 — Connect**: Reaches outside the chat interface to pull data from or push data to external tools via connectors/APIs (`22:21`).
* **Level 4 — Chain**: Multiple skills handing off output sequentially to one another in a predetermined pipeline (`23:51`).
* **Level 5 — Team / Orchestrator**: A manager skill sits on top, receives high-level natural language goals, and dynamically decides which sub-skills to invoke and in what order (`25:01`).

##### **3. Level Evaluation Principles** (25:45)
* **Rule**: *"Levels are not a score."* A Level 1 skill executed daily provides more real-world value than an over-engineered Level 5 system (`25:52`).
* **Rule**: Build to solve business pain, not to prove complexity (`26:27`).

---

#### **Checklists & Writing Rules**

##### **Rules for Skill Descriptions / Triggers** (12:20, 13:35)
1. **Use natural phrasing**: Write trigger words using the exact natural language you type during daily work (`13:36`).
2. **Include failed phrasings**: Add alternative phrases that previously failed to trigger the skill (`13:46`).
3. **Define negative scope**: Explicitly state what the skill is *not* for to prevent accidental firing (`13:51`).

##### **The 5-Gate SEO Audit Framework** (shown at 29:22)
1. **Gate 1 — Can it be found?**: Indexability, canonicals, sitemaps, internal link depth.
2. **Gate 2 — Can it be understood?**: Topic clarity, headings ($H1, H2$), search intent match.
3. **Gate 3 — Can it be trusted?**: E-E-A-T, named authors, contact details, original evidence.
4. **Gate 4 — Can it be cited?**: AI searchability, liftable quote passages, structured data.
5. **Gate 5 — Does it convert?**: Clear call-to-action (CTA), next steps, no dead ends.

---

### 2. Tools, Connectors, Plugins & Skills Named or Shown

| Tool / Skill / Plugin Name | Type | Function / Purpose |
| :--- | :--- | :--- |
| **Claude (Anthropic)** | AI Platform | Primary environment for running and executing skills (`01:00`). |
| **`skill-creator`** | Built-in Anthropic Skill | Anthropic’s native skill builder used to generate, evaluate, and structure new skills (`16:30`, `27:28`). |
| **`seo-audit`** | Custom Skill (Level 1) | Takes a website URL and produces a 5-gate scored SEO audit (`02:38`, `29:05`). |
| **`seo-blog-writer`** | Custom Skill (Level 2) | Converts YouTube transcripts/notes into structured SEO blog posts matching brand voice (`02:38`, `06:48`). |
| **`seo-reporting`** | Custom Skill (Level 3) | Connects to Google Search Console to pull performance metrics and generate reports (`02:38`). |
| **`seo-strategy`** | Custom Skill (Level 3) | Pulls keyword data and writes strategic plans directly into Notion (`02:38`). |
| **`voice`** | Custom Skill (Level 2) | Rewrites text drafts to match a specific personal or brand tone of voice (`02:38`, `05:22`). |
| **`seo-orchestrator`** | Custom Skill (Level 5) | Manager skill that directs the SEO team skills based on high-level goals (`02:38`, `25:07`). |
| **`Whisper Flow`** | Mac Dictation App | Voice-to-text dictation software used by the presenter to input prompts (`15:00`, `28:34`). |
| **Notion / AI Recipe Vault**| External Resource | Repository containing course guides, templates, and copy-paste skill prompts (`03:19`, `29:20`). |

---

### 3. Step-by-Step Builds Demonstrated & On-Screen Prompts

#### **Build Demonstration 1: Executing an Existing Skill (`seo-blog-writer`)** (`14:50`–`16:24`)
1. **Trigger**: User inputs text in chat: *"Hey, I want to turn this YouTube video transcript into an SEO blog post. Here's the transcript. Let's get to work."*
2. **Pasted Content**: Raw video transcript pasted into chat (`15:26`).
3. **Execution Chain**:
   * Reads trigger phrase $\rightarrow$ Invokes `seo-blog-writer` skill (`15:43`).
   * Loads `references/article-template.md` (`15:50`).
   * Loads `references/seo-checklist.md` (`15:52`).
   * Fetches Voice DNA file (`15:55`).
   * Begins drafting structured title, slug, meta description, and outline (`16:24`).

---

#### **Build Demonstration 2: Creating a Level 1 Skill (`seo-audit`) using `skill-creator`** (`27:10`–`29:59`)

##### **Step-by-Step Process**:
1. Navigate to **Customize** $\rightarrow$ **Skills** (`27:11`).
2. Verify `skill-creator` by Anthropic is toggled **ON** (`27:32`).
3. Open a new chat and invoke the builder by typing `/skill-creator` (`28:25`).
4. Enter instructions to `skill-creator`:
   > *"I'm going to give you a prompt for an SEO audit skill. I want you to take this prompt and wrap it in a Claude skill so that I can fire it and invoke it at any time."* (`29:04`)
5. Paste the complete prompt text into the chat (`29:33`).

---

##### **On-Screen Prompt Content (`seo-audit` Prompt)** (`29:21`–`29:59`):

```markdown
ROLE
You audit websites for search visibility — both traditional search and AI search. 
You are calm, specific and hard to impress. You would rather ship a short report 
that is true than a long one that is padded.

INPUT
A URL. That is the only thing you require.

If the user also gives you business context, target customers, priority pages or named competitors, 
use all of it. If they give you nothing but a URL, proceed anyway and note in the output 
what extra context would have sharpened the audit. NEVER stop and ask before starting. 
This skill runs on a URL alone.

WHAT TO LOOK AT
Do not audit one page in isolation. Fetch and read, at minimum:
- the URL given
- the homepage, if different
- whatever the main navigation points at
- two or three of the deepest content pages you can reach
- robots.txt and the sitemap, if they resolve

FIVE GATES
Gate 1 — CAN IT BE FOUND? (Indexability, directives, canonicals)
Gate 2 — CAN IT BE UNDERSTOOD? (Headings, structure, intent)
Gate 3 — CAN IT BE TRUSTED? (Authors, contact info, evidence)
Gate 4 — CAN IT BE CITED? (AI Searchability, quote passages, schemas)
Gate 5 — DOES IT CONVERT? (CTAs, user journey, next steps)

SCORING
Score each gate out of 10 with one sentence of reasoning, giving an overall score out of 50.
```

---

### 4. User Interface (UI) Walkthrough

* **Customize Panel** (`06:33`): Located on the left navigation sidebar. Contains four sub-tabs:
  * **Skills**: Shows installed and custom skills.
  * **Connectors**: For external API integration.
  * **Plugins**: For packaged extension bundles.
  * **Discover / Yours**: Marketplaces for pre-built or personal skills.
* **Skill Detail View** (`06:51`, `17:12`):
  * **Overview Tab**: Displays the skill name, author, updated date, and description (triggers).
  * **Contents Tab**: File tree showing `SKILL.md`, `/references/`, and `/scripts/`.
  * **Actions Bar**: Top-right controls:
    * **Toggle Switch**: Turn skill On/Off (`17:23`).
    * **Download Icon**: Export skill folder as a `.zip` or `.skill` file (`17:34`).
    * **Edit Icon**: Edit text inside files directly in the browser (`17:40`).
    * **Three-Dots Menu**: Options to *Try in chat*, *Replace*, or *Delete* (`17:46`).
* **Slash Command Menu** (`14:13`): Typing `/` in the main chat prompt bar opens an auto-complete dropdown menu listing all enabled skills.

---

### 5. Actionable Takeaways for Marketing & Agency Teams

1. **Standardize Workflows as Skills**: Convert standard internal agency SOPs (e.g., client onboarding audits, ad copy generation, reporting) into `.skill` folders so every team member gets identical outputs without prompt variation (`03:48`, `04:12`).
2. **Decouple Instructions from Reference Data**: Keep your main `SKILL.md` file lean by offloading long brand voice guidelines, design systems, and client examples into a `/references/` subfolder. This reduces token consumption and improves output quality (`11:35`).
3. **Prevent False Triggers Across Clients**: If managing multiple client accounts or brands, explicitly state brand-specific trigger phrases in the skill description to avoid firing the wrong brand voice or template (`13:08`).
4. **Automate Deterministic Tasks First**: Focus initial skill-building on high-frequency, deterministic tasks (e.g., technical SEO audits, invoice generation, structured client reports) where errors are obvious and time savings are immediate (`19:15`, `26:39`).
5. **Leverage `skill-creator` for Rapid Build**: Do not write skill Markdown structures by hand. Feed existing text prompts or SOPs into the native `/skill-creator` skill to automatically format them into compliant Claude skill packages (`27:28`, `28:10`).
