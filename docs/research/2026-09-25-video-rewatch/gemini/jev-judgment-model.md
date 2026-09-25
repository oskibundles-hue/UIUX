
# watch: video report

- **Source:** https://www.youtube.com/watch?v=D-Z5HnLW_ho (URL sent to Google)
- **Engine:** gemini-3-flash-preview (agentic)
- **Gemini tokens:** 208694

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

This report details the video analysis of "The Missing Piece for Claude Code (and how to build with it)," focusing on the integration of Jev (TypeSafe AI) with Anthropic’s Claude Code.

### 1. Metadata
*   **Exact Title:** The Missing Piece for Claude Code (and how to build with it)
*   **Creator/Channel:** Simon MacDonald
*   **Length:** 15:58

### 2. Core Thesis
Jev is a specialized "System One" judgment model designed to perform fast, cheap, and deterministic classifications that complement the "System Two" reasoning capabilities of frontier models like Claude. By acting as a probabilistic "plumbing" layer, Jev allows developers to handle bulk data categorization and routing at scale while LLMs focus on high-level drafting and conversational reasoning.

### 3. Tools, Repos, and Services Named
*   **Claude Code:** Terminal-based AI coding agent used to orchestrate the build.
*   **Jev (by TypeSafe AI):** A "judgment model" designed for high-speed, parallel processing of discrete questions ([typesafe.ai](https://typesafe.ai)).
*   **TypeSafe Agent Skill:** A plugin/skill for Claude Code. 
    *   *Commands:* `claude plugin marketplace add typesafe-ai/skills`, `claude plugin install typesafe-ai/skills` (10:39).
*   **Claude 3.5 Sonnet:** Referred to as the primary "reasoning" model for drafting replies and planning logic.
*   **OpenRouter:** A unified API service used to access Jev and other models (11:45).
*   **Jev Lab:** A repository of "recipes" for common Jev use cases like support triage or lead scoring (11:45).
*   **MCP (Model Context Protocol):** Mentioned as a method to connect Jev directly to local resources like email inboxes (12:45).
*   **Python:** The language used to write the triage execution script (`questions.py`).

### 4. Step-by-Step Workflow/Build Demonstration
1.  **Skill Installation (10:29):** The user installs the `typesafe-ai/skills` plugin from the Claude Code marketplace to give Claude context on how Jev operates.
2.  **Environment Setup (11:12):** A TypeSafe API key is generated from the dashboard and saved in a `.env` file as `TYPESAFE_API_KEY`.
3.  **Triage Initialization (12:45):** A comprehensive prompt is issued to Claude Code, instructing it to triage 50 support emails from a local `emails.csv` file using the TypeSafe skill.
4.  **Logic Planning (13:52):** Claude reads the skill and generates a Python file (`questions.py`) that defines three key sections: the **State** (data schema), **Questions** (the specific judgments Jev must make), and **Routing** (IF/THEN logic based on Jev’s confidence scores).
5.  **Parallel Execution (14:58):** The script executes, sending the 50 emails to Jev. Jev processes multiple questions (Anger, Severity, Category, Refund request) for every email simultaneously in parallel.
6.  **Report Generation (15:26):** The script processes Jev’s scores through the routing logic and outputs a Markdown file (`triage.md`) prioritizing "angriest" customers first and routing others to engineering or automated drafting piles.

### 5. UI and Dashboard Visual Layouts
*   **Browser Use Demo (00:09):** A split screen. Left side shows a live browser navigating Google Flights. Right side features a dark-themed terminal overlay called "Jev Ultrafast" displaying a decision trace and a 7.1-second timer.
*   **Lost Customer Heatmap (00:17):** A grid of small rectangular video session thumbnails. A sidebar displays a list of session events (e.g., "Rage Click", "Dead Click") with pink and white status indicators.
*   **Model Comparison Table (03:39):** A stark white interface comparing "Frontier LLM" and "System One (Jev-1.1)". Features green and red highlights for performance metrics (Speed: 3-329s vs. 70ms-500ms; Cost: $0.20-$10 vs. $0.042 per M tokens).
*   **Judgment Result Components (06:32 - 10:05):** Dark background grid panels illustrating judgment types:
    *   **NOUL:** A single pink horizontal progress bar representing the probability of a "Yes" answer (0.0 to 1.0).
    *   **CHOICE:** Multiple pink bars of varying lengths representing the probability distribution across defined categories (e.g., Billing 85%, Technical 10%).
    *   **SCORE:** A continuous horizontal axis with markers for "Calm", "Annoyed", and "Furious", with a pink vertical line indicating the result (e.g., 2.4/3.0).
*   **Triage Report UI (15:26):** A terminal-based Markdown table with columns for `Pri` (Priority), `ID`, `Subject`, `Anger`, `Sev` (Severity), and `Why`. High-priority items are at the top, and the "Why" column explains the Jev judgment (e.g., "asking for money back (0.99)").

### 6. 5 Actionable Takeaways for Marketing/Agency AI OS
1.  **Optimize the Triage Layer:** Do not use Claude Sonnet to classify every incoming lead. Use Jev as a high-speed "gatekeeper" to categorize inquiries (e.g., "New Business," "Support," "Spam") before committing expensive reasoning tokens to a reply (15:55).
2.  **Implement Automated Quality Checks:** Add a "second pass" verification step. After Claude drafts a marketing proposal, have Jev check it against a specific rubric (e.g., "Does this include the client’s brand name?" "Is the tone professional?") to ensure accuracy without full re-generation costs (12:48).
3.  **Scale Lead Scoring:** Use the `SCORE` judgment type to rank leads from 1-10 based on "fit" for your agency. By defining criteria like "budget mentioned" or "high-urgency keywords," you can sort thousands of leads in seconds for a few cents (14:02).
4.  **Deterministic Routing:** Build "Agentic" workflows where Jev handles the branching logic. If Jev identifies a "Legal/GDPR" category with >90% confidence, the code automatically routes the ticket to a human partner, skipping the LLM entirely (08:26).
5.  **Parallelize Decision-Making:** Instead of asking an LLM three sequential questions about a client request, pack all three into one Jev request. You only pay to "read" the input text once, and Jev evaluates all dimensions in parallel, significantly reducing agent latency (14:40).
