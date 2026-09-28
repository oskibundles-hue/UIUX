[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 00:00–04:36)
- **Focus range:** 00:00 → 04:36
- **Gemini tokens:** 26285

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Certainly! Here are the timestamps, the layout of the daily brief, the apps connected, and the on-screen setup steps as shown and discussed in the video.

---

### **1. What the Daily Brief Looks Like**
- **00:07 / 01:23** – The video shows the daily briefing interface with the following sections and components:
  - A greeting banner ("Good morning, Simon.") along with key metrics and counts (e.g., 5 TO ACT ON, 3 MEETINGS, 19 TEAM ITEMS, 8 ISSUES).
  - **"Needs attention today"**: A curated list of urgent items requiring action, such as payment requests, follow-ups, and app setup roadblocks (00:08).
  - **"Today's schedule"**: A timeline of the day's events pulled from Google Calendar, showing appointments, lunch breaks, and busy blocks (00:10 / 01:26).
  - **"Your action items"**: Pending tasks grouped by priority from a Notion shared dashboard (00:10 / 01:29).
  - **"Relevant in Slack"**: Important messages and thread highlights from team communications (00:11 / 01:31).
  - **"Issues to raise"**: A list of reported blockers and topics to discuss (00:12 / 01:33).
  - **"The Team"**: Updates on open items and progress across team members (00:12 / 01:37).
  - **"Overdue backlog"** and **"Personal / finance" / "System" updates** (00:13 / 01:40).

---

### **2. Apps Connected & How**
- **03:13** – The speaker navigates to the **Customize** > **Connectors** tab within the Claude desktop interface.
- **03:16–03:32** – The video displays the list of top available connectors. The speaker specifies connecting:
  - **Google Drive** (for searching, reading, and uploading files)
  - **Google Calendar** (for managing schedule and coordinating meetings)
  - **Notion** (for accessing workspace pages, tasks, and databases)
  - **Microsoft 365** (mentioned as an alternative option for Microsoft users)
  - **Custom Connectors / MCP Apps** (such as an Agentic Business Guide MCP)
- **03:52–04:03** – Under individual connector settings (e.g., Notion), the speaker demonstrates configuring **tool permissions** for read-only and interactive tools (setting specific actions to *Always allow*, *Needs approval*, or *Never*).
- **04:19–04:26** – The speaker confirms the essential connected apps for the Personal Assistant: **Google Calendar, Notion, Slack, and local folders in Claude**.

---

### **3. On-Screen Setup Steps & Text**

#### **Chapter: Overview (00:16)**
- **00:16** – On-screen text chapter title: `#01 OVERVIEW: THE DAILY BRIEF WE'RE BUILDING` (Subtitle: *Build a Daily Briefing PA in Claude*).

#### **Chapter: Install Claude & Pick Your Folder (01:53)**
- **01:44** – On-screen text: `#02 INSTALL CLAUDE & PICK YOUR FOLDER`.
- **01:47** – The speaker demonstrates opening the Claude desktop app and selecting a folder.
- **01:53** – On-screen text note: *"Cowork is the system that runs on your computer..."*
- **02:00** – The video shows local folder structure in Finder / Dropbox (containing subfolders like `ABOUT ME`, `KNOWLEDGE`, `RESOURCES`, `WORK AREAS`, `Claude-outputs`).
- **02:11** – The speaker right-clicks a folder in macOS Finder and selects **"Make available offline"** to sync files locally and on the web.
- **02:38** – The speaker shows the project/folder dropdown in Claude to select the working directory (`CoWork`).

#### **Chapter: Connect Your Apps (03:20)**
- **03:11** – On-screen text chapter title: `#03 CONNECT YOUR APPS (CONNECTORS)`.
- **03:14** – The speaker clicks **Customize** and then the **Connectors** tab.
- **03:52** – The video shows detailed toggle switches under *Tool permissions* for interactive and read-only tools, categorized by *Always allow* and *Custom* approval levels.
[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 04:36–08:09)
- **Focus range:** 04:36 → 08:09
- **Gemini tokens:** 19895

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here are the Notion database fields/columns and briefing design details shown and discussed in the video, with timestamps:

- **Notion Task Database Columns (seen at 06:16):**
  - Task name/description (seen at 06:16)
  - Person (assigned user, e.g., Simon, Jakub Skupień) (seen at 06:16)
  - Priority (e.g., High, Medium) (seen at 06:16)
  - Status (e.g., "Not started", "In progress") (seen at 06:16)
  - Deadline (seen at 06:16)

- **Briefing Design Structure / Elements (seen at 05:25, 05:50):**
  - **What's in the morning briefing?** (sections include: Daily overview, Calendar & meetings, Email / transcript triage, Tasks & deadlines, News & industry topics, Weather & commute, Yesterday's design, Suggested focus for today, Open questions for list) (seen at 05:25)
  - **Where do you read it?** (options: Phone-first, Desktop-first, Both equally) (seen at 05:25)
  - **How long should reading it take?** (options: 30 seconds, 2-3 minutes, 10 minutes, deep) (seen at 05:25)
  - **Information density:** (options: Very sparse, Balanced, Dense) (seen at 05:25)
  - Visual elements shown in the wireframe template include date header ("Wednesday, 17 Sep"), section headings, body copy style ("terse, one clause per line"), color swatch palette, and modular content blocks (seen at 05:50).
[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 08:09–12:40)
- **Focus range:** 08:09 → 12:40
- **Gemini tokens:** 25058

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here is a transcription of the on-screen text, matching the instructions from the video:

- **08:18** "I would like to create a scheduled task that is a personal assistant that runs a daily briefing on my current circumstance. We're going to do this only inside my Demo PA folder."
- **08:41** "Create two things:
1. A first draft of a scheduled task which asks you, on a Monday morning at 8 am., to deliver a briefing of the day and the week. Every other working day, it delivers a daily brief. It should deliver it as an HTML report using the above design system.
2. The report should be delivered both in the chat of the scheduled task, but also as an artefact in a briefs folder inside the demo PA.
3. Create a memory file and project file for how the demo PA should work that exists in that folder, so that you have a clear set of instructions on how to operate."
- **09:23** "Want my personal assistant to be able to brief me on:
- the work I have coming up for the day
- my clear, important priorities
- what's happening for my schedule
It will need to read my Gmail, my Google Calendar, and a specific Notion task database that it will read from to inform its decisions.
Please draft the scheduled task and set up the folder."
[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 12:40–17:07)
- **Focus range:** 12:40 → 17:07
- **Gemini tokens:** 25223

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here are the on-screen PA instruction texts shown in the video, with timestamps:

* **13:58** `You are "Simon's" personal assistant, running his scheduled morning briefing at 06:00 (London). Read and follow the runbook at CLAUDE.md in the connected "Demo PA" folder exactly, top to bottom, before doing anything else. It tells you how to operate in full.`
* **13:59** `CONTEXT (best effort): Simon's Co-work folder lives in Dropbox at /Users/simon/Library/CloudStorage/Dropbox/CloudStorage/Co-Work/. Read if over the remote devices bridge if his desktop app is connected. If NOT connected, read the SAME FILES through the local access files from the prompt as covering either route first. READ CLAUDE.md and 'ABOUT-ME' at that root, and the last 7 DAYS of `WORK-AREAS/ADMIN-PA/captain's-log` if ABOUT-ME at that root, and the last 7 DAYS of WORK-AREAS/ADMIN-PA/captain's-log`
* **14:44** `CONTEXT (best effort): Simon's Co-work folder lives in Dropbox at /Users/simon/Library/CloudStorage/Dropbox/CloudStorage/Co-Work/. Read if over the remote devices bridge if his desktop app is connected. If NOT connected, read the SAME FILES through the local access files from the prompt as covering either route first. READ CLAUDE.md and 'ABOUT-ME' at that root, and the last 7 DAYS of WORK-AREAS/ADMIN-PA/captain's-log`
* **14:46** `GATHER: 1. Today's Google Calendar events (times > 06:00). 2. Team action items – Notion "Task List" (` Outstanding " view https://app.notion.com/...); and Gmail (the "Simon's inbox" label plus main-inbox `0000000bc571...` Status: Not Done, ordered by Priority (High > Medium > Low). 20%, Schedule, Tasks (3 groups, ready for Claude AI to approve, with the VA, Simon's own), Waiting on, and on Mondays the Week ahead. 3. Simon's overdue backlog from his main personal Notion Tasks database (`BC Tasks Database` collection:00940003bc...): Status: Not Done/Does with a Deadline on or before today, ordered by Priority. Remove Person ID to names: flag anyone unresponsive or badly backed up.`
* **14:51** `RENDER a single self-contained branded HTML page, (Better Creating design pack: BC Orange #FF5D26 used spangly, Funnel sans, warm brown/beige neutrals, crisp Swiss/Apple design - Helvetica, orange reserved for hard blockers only). Blocks: Top line, The 20% Schedule, Tasks (3 groups, ready for Claude AI to approve, with the VA, Simon's own), Waiting on, and on Mondays the Week ahead.`
* **14:52** `DELIVER has ways EVERY RUN (1) ALWAYS send the finished briefing as an .html file via Sendwfile.file as it sends in this standard and is readable on ANY device – including on mobile straight from the push notifications; and (2) if the desktop is connected, ALSO update the precached Claude's artifical daily briefing' - daily-briefing/ as place on device. If the folder is reachable, also save a dated copy to the briefing-delivery project outputs. Do NOT push to Brief Buddy – retreat! Finish with a one line chat summary of the single most important thing for Simon today.`
[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 17:07–21:21)
- **Focus range:** 17:07 → 21:21
- **Gemini tokens:** 24262

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here is the requested information based on the video:

### Chapters & Timestamps
* **17:07** – Setting up and refining scheduled tasks
* **20:31** – Top tip on delivery: ASD-STE100

---

### Scheduled Task Details (Seen & Heard)
* **Frequency (Seen at 17:08 & 17:10):** Weekdays at 08:00.
* **Prompt Instructions (Seen at 17:08 & 17:10):**
  > Read Simon’s morning briefing (Demo PA persistent assistant).
  > 
  > Read and follow the outlook at CLAUDE.md in the connected “Demo PA” folder exactly, top to bottom, before doing any tasks. It tells you how to operate in full.
  > 
  > **STEPS:**
  > 1. Read the three ABOUT-ME identity files, .system/Project.md, and .system/Memory.md.
  > 2. Find today's date in Europe/London, it’s Monday; produce the weekly + daily brief.
  > 3. Gather (READ-ONLY) today's Google Calendar (“Simon's Inbox / Brown Weekly Schedule”), the Notion Task Operations Database (Demo), and Gmail (re: “Simon’s Inbox” label plus main inbox unread +prior / >trips, via #sport).
  > 4. Build one self-contained HTML brief / iframe, structured per templates/html.tmpl (Apple Swiss design template). Paste it as a system prompt or at the top of a chat, then give it your text.
  > 
  > 💡 Demo PA /Users/username/cloud/cloudrive/...

---

### ASD-STE100 Details (Heard & Seen)
* **What he says about ASD-STE100 (20:11–20:25):** 
  He explains that ASD-STE100 stands for *Simplified Technical English*. He says it is a system designed to make AI "speak to you in a far more focused and clear way." 
* **Prompt text shown on screen for ASD-STE100 (Seen at 20:11 & 20:20):**
  > You are a Simplified Technical English (ASD-STE100) issue. REWRITE. Read the text I give you to follow the STE rules below. Do not add common technical meaning.
  > 
  > **VOCABULARY**
  > - Use the simplest common word for each idea. Give each word one meaning only.
  > - Do not use a word more as part of speech (e.g. do not use "oil" as both a noun and a verb).
  > - Choose one technical name for each thing and one technical verb for each already named.
  > - Use them every time. Never use a synonym for something you have already named.
  > - No jargon, no idioms, no slang, no figures of speech.
  > 
  > **SENTENCES**
  > - Instructions (procedures): maximum 20 words per sentence.
  > - Descriptions: maximum 25 words per sentence.
  > - Write one instruction per sentence. For two actions, write two sentences.
  > - Use the command (imperative) form for instructions: "Remove the bolt."
  > - Use the active voice. Do not use the passive, past, future. Do not use perfect tenses.
  > - Keep articles (a, an, the) and other small words that make the meaning clear.
  > 
  > **STRUCTURE**
  > - Write procedures as a numbered vertical list. One step per number.
  > - Paragraphs: maximum 6 sentences per paragraph.
  > - Put the instruction first, then the condition or reason.
  > - Use a vertical list when there is more than one condition or item.
  > 
  > **WARNINGS AND CAUTIONS**
  > - Start a warning or caution with a clear or direct command. State the condition after it.
  > - Put the warning before the step it applies to.
  > 
  > **OUTPUT**
  > - Return the rewritten text.
  > - Then, under a heading “Check These Words”, list any words you used that you think might be unapproved based on the STE approved dictionary, so a human can verify.
  > - If it is on the STE approved dictionary, do not flag.
  > - If you cannot be confident all words are fine, write “None flagged”.
[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 21:21–26:18)
- **Focus range:** 21:21 → 26:18
- **Gemini tokens:** 28015

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here is what the finished daily brief looks like when it is delivered, along with what happens in the demo:

### The Finished Daily Brief (23:35)
* **Header & Overview:** The brief is titled with the current date (e.g., “Friday, 18 Sep 2026” at 23:35) and notes that today is a delivery day with an important task to finalise contracts before 17:45. It includes stat counters for “Ready for review” (1), “P1 task” (1), and “Needs review” (3) (23:36).
* **The 20% — Focus Today (23:40):** 
  1. *Send the finalised contracts to the team* — Hard deadline today at 17:45, noting a clash with the plan-next-week block.
  2. *Film Module 3 for the Accelerator cohort* — 60 minutes.
  3. *Sign off Claude’s Community Digest* — 15 minutes.
* **Schedule (23:46):** A full hourly timeline for the day starting with “El Studio Day”, “Weekly call — Simon x Lisa”, gaps, filming, time blocks for video uploads/av/calls, a clash warning at 17:00, and a 20-minute daily reset at 18:00.
* **Tasks & Deadlines (23:49):** Categorised by “Your tasks” (2 open), “Your VA's tasks” (3 allocator tasks), and “Automated — ready for Simon PA” (various automated checks and digests).
* **Email Waiting on You (23:53):** A read-only section showing important emails needing attention from a glance inbox, Lisa Says (new invoice), and GoCardless (Direct Debit set up).

---

### What Happens in the Demo

* **21:21 – 21:31:** The speaker opens the “Captain’s Log” folder to read the first entry so the system understands how to work with him.
* **21:32 – 22:02:** The speaker reviews the Notion-generated “Task Executor – Demo PA” task, verifies the rules (only updating tasks assigned to “Claude [AI]” with status “To Do [AI]”), and clicks **Schedule** (22:01).
* **22:02 – 22:11:** The system reorders tasks, updates email sections, shifts tone, and establishes an approval loop.
* **22:12 – 22:27:** The speaker checks the scheduled tasks list and confirms the “Daily Briefing – Demo PA” is set up to run without requiring a local computer folder.
* **22:28 – 22:43:** The speaker manually tests the scheduled task by clicking **Run now** (22:35), generating a manual execution item under history (23:39) and working through Dropbox integration.
* **22:44 – 23:17:** The speaker demonstrates how this links into a broader “Agentic Business OS” team system in Notion, featuring dashboards for meetings, issues, and actions.
* **23:25 – 23:56:** The speaker reveals the final generated brief output, reviewing the delivery day summary, schedule, tasks, and email digests.
* **23:57 – 24:37:** Using WhisperFlow for dictation (23:58), the speaker dictates a new note (e.g., about calling the accountant), shares it, and watches the system automatically update both the Notion task list and the Captain's Log file.
* **24:38 – 25:42:** The speaker enables the Task Executor to run automatically, demonstrating how it queries Notion, detects queued tasks (such as drafting the weekly community digest), executes the work, moves items to “Needs Review”, and logs execution notes.
[watch] asking gemini-flash-lite-latest…

# watch: video report

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk (URL sent to Google)
- **Engine:** gemini-flash-lite-latest (static clip 26:18–27:09)
- **Focus range:** 26:18 → 27:09
- **Gemini tokens:** 5091

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here are the details from the specified chapter of the video (26:18 to the end):

* **26:25** — **What is the context map?** Visually shown on-screen in Notion, the context map is titled "Agentic Context Map & Write Rules" under "Agentic Context Map." It serves as a master directory or guide for where information belongs across the workspace (e.g., BusinessOS databases). It contains sections such as:
  * **Work & time** (mapping tasks and projects to their respective databases and routes).
  * **Clients & delivery** (mapping client relationships and delivery records).
  * **Direction & measurement** (mapping KPIs, meeting notes, issues, and decisions).
  * **Content & channels** (mapping long-form content and newsletters/marketing).
  * **Knowledge & documentation** (mapping internal knowledge and business operating procedures).

* **26:45** — **How it is used:** The speaker explains that you build this context map so that an AI agent can read it, understand where to put specific types of content or updates (whether in Claude or Notion), and follow proper routing rules.

* **27:01** — **How the video ends:** The speaker returns to full-screen view (26:51), talks briefly about how quickly the setup took (around an hour while filming), and then transitions to show a screen recording of "Scheduled tasks" in Task Executor (27:02–27:08) while concluding the video overview.
