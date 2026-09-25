
# watch: video report

- **Source:** https://www.youtube.com/watch?v=HOXrLsVqinY (URL sent to Google)
- **Engine:** gemini-3.6-flash (agentic)
- **Gemini tokens:** 75630

## Answer (from Gemini)

_These are Gemini's observations of the video, not frames you viewed yourself. Relay them as such; rerun with `--engine local` to inspect frames directly._

Here is the report based on the provided video:

---

### 1) Basic Video Information
* **Exact Title:** Claude Design Genius *(shown on title card at 00:05)*
* **Creator / Channel:** Jack Roberts *(Channel: Jack Roberts)*
* **Video Length:** 22:19 (1,339 seconds)

---

### 2) Core Thesis
Anthropic’s Claude Opus 5.5 and Claude Code enable programmatic, code-drawn motion graphics, interactive web assets, and dynamic marketing visuals directly in HTML/Canvas/CSS at a fraction of the cost and render time of traditional animation tools or AI video generators. By coupling Claude Code with scraping pipelines like Firecrawl and a centralized Agentic OS dashboard, agency owners and creators can systematically automate client branding and multi-platform content production at scale.

---

### 3) Tools, Repositories, Models, MCP Servers, Plugins, Skills, & Services Mentioned or Shown

* **Claude Opus 5.5 / Claude Code / Opus 5** *(Model / AI Agent)*
  * *Function:* Code-based reasoning and programmatic generation of 60fps canvas animations, HTML/JS graphics, logo stings, and visual assets (00:01, 00:26, 04:00, 06:50).
* **Fable 5.1** *(Motion Graphics Tool / Benchmark)*
  * *Function:* Used as a benchmark for comparison (Opus 5.5 is cited as 40% cheaper and 30% faster than Fable 5.1) (00:30).
* **Firecrawl** *(Web Scraper / API / MCP Server)*
  * *Function:* Web scraper and API that extracts brand identity, hex colors, typography, layout specs, and SVGs from any URL to feed into Claude prompts (02:30, 03:01, 03:45, 10:53, 19:20).
  * *Visible URL:* `firecrawl.dev` / `firecrawl.dev/dashboard/19324bc4...`
  * *MCP Server Endpoint Visible:* `https://mcp.firecrawl.dev/group-vauth` (03:01).
  * *Commands Visible on Screen (03:01):*
    * `npx -y firecrawl-cli login`
    * `npx -y firecrawl-cli search "launch darkly"`
    * `firecrawl-mcp`
  * *Supported Coding Agents/Integrations Shown:* Claude Code, Codex, Cursor, Opencode, OpenClaw, Hermes (03:01).
* **Glaido** *(Speech-to-Text / Dictation App)*
  * *Function:* Dictation software used by the creator to speak prompts into code editors (02:50, 03:35, 05:00).
  * *Visible URL:* `glaido.com`
* **ChatGPT / OpenAI** *(AI Model / Interface)*
  * *Function:* Named as alternative LLM interface for executing Firecrawl-enriched prompts (03:57, 06:46, 09:12, 13:38).
* **Agentic OS** *(Local Operating System / Web Dashboard)*
  * *Function:* Custom local control dashboard built by Jack Roberts to manage Claude Code workflows, select motion styles, run auto-enhancements, and trigger multi-platform production (06:17, 12:00, 18:20, 21:50).
  * *Visible URL:* `http://127.0.0.1:4100/motion`
* **Codex** *(AI Coding Agent)*
  * *Function:* Code execution agent integrated into Agentic OS and Firecrawl dropdowns (03:01, 06:50).
* **Cursor** *(AI Code Editor)*
  * *Function:* AI code editor listed under Firecrawl coding integrations (03:01).
* **Opencode & OpenClaw** *(AI Coding Agents)*
  * *Function:* Listed under Firecrawl CLI integration options (03:01).
* **Hermes / Hermes Agent** *(AI Agent Framework)*
  * *Function:* Listed under Firecrawl integrations (03:01) and named as an Agentic OS agent connection (21:30).
* **Grok / Grokbot** *(AI Agent)*
  * *Function:* Mentioned as a connected agent in the OS framework (21:30).
* **Notion** *(Workspace / Document Management)*
  * *Function:* Hosts the creator’s RISE framework documentation and course prompt templates (01:40, 05:32, 14:05).
  * *Visible URL:* `app.notion.so`
* **SlopMonster** *(GitHub Repository / Quality Control Tool)*
  * *Function:* GitHub repository built by Jack Roberts that combines AI slop detection rules (rule of three, cadence, buzzwords) to clean generated marketing text and copy (17:01).
  * *Visible URL:* `github.com/Jack-Roberts/SlopMonster`
* **Savee** *(Design Inspiration Platform)*
  * *Function:* Platform for curating graphic design, motion, and visual style references to pass into Claude Opus 5.5 (15:40, 16:00).
  * *Visible URL:* `savee.ai` / `savee.ai/graphics`
* **Higgsfield** *(AI Video / Image Generator)*
  * *Function:* Mentioned as an image/video generator alternative for film burn or vintage filters (17:50).
* **Pinterest** *(Design Inspiration Service)*
  * *Function:* Mentioned verbally as an alternative visual source (16:05).
* **Blur Tato** *(Social Carousel App)*
  * *Function:* Named at 12:05 for publishing visual carousels across social channels.
* **Social Platforms Mentioned/Shown:** Instagram (`instagram.com/jackroberts_`), TikTok, YouTube Shorts, X (Twitter) (08:42, 12:10).

---

### 4) Step-by-Step Demonstrated Workflow & Progression

#### **Intro & Benchmark (00:00 – 02:00)**
* Introduces Claude Opus 5.5 benchmarks (40% cheaper, 30% faster than Fable 5.1).
* Introduces the **RISE** prompt methodology (**R**eferences, **I**dea, **S**tyle, **E**xamine).

#### **Level 1: Animated Slides (00:40 – 02:20)**
* **Step 1:** Prompt Claude Opus 5.5 with a slide concept and desired loop duration (5–20 seconds).
* **Step 2:** Include the RISE framework prompt to enforce code-drawn constraints.
* **Step 3:** Claude generates code rendered directly in HTML/Canvas, displaying an animated slide deck inside a simulated PowerPoint window loop in one shot (02:05).

#### **Level 2: A Website That Comes Alive / Firecrawl Scrape & Interactive Hero/Footer (02:20 – 08:05)**
* **Step 1:** Navigate to the Firecrawl dashboard (`firecrawl.dev/dashboard`) (03:01).
* **Step 2:** Paste the target brand URL (e.g., `glaido.com`) into the "Scrape" tab and set output format to `Branding` (03:22).
* **Step 3:** Firecrawl extracts the primary/accent hex colors, typography, button shapes, and audience description (03:45).
* **Step 4:** Pass the Firecrawl API key or extracted JSON/Markdown branding data to Claude Code alongside a hero/footer animation idea (04:35).
* **Step 5:** Claude outputs code for interactive web elements: a hero section where spoken words transform into flying birds (05:00) and an interactive canvas footer with dynamic particle text/logos (05:40, 07:35).

#### **Level 3: Reels with Custom Graphics & Premium Captions (08:10 – 11:05)**
* **Step 1:** Import talking-head video footage into the pipeline.
* **Step 2:** Prompt Claude to slice video frames and generate custom top-screen animated overlays (e.g., split Claude vs ChatGPT graphics) timed to spoken audio (09:15).
* **Step 3:** Apply styled captions (Editorial, Boxed, or Premium) synchronized three words per caption (09:55).

#### **Level 4: One B-Roll Clip, Every Size (Aspect Ratio Adaptation) (11:05 – 12:40)**
* **Step 1:** Render a single code-driven animation loop (e.g., hot air balloon rising above a coffee cup with text) (11:25).
* **Step 2:** Instruct Claude Code to re-frame the CSS/Canvas layout for vertical 9:16 (Shorts/Reels), 16:9 (Widescreen), and 1:1 (Square) aspect ratios without breaking visual composition (11:50).

#### **Level 5: Any Logo Animated, with its own Jingle (12:40 – 15:15)**
* **Step 1:** Extract target brand logos (Nike, Duolingo, Spotify, Notion) using Firecrawl (13:35).
* **Step 2:** Prompt Claude in Notion / Claude Code to build a 3-second animated swoosh or bouncing loop along with code-generated audio jingles (14:05).
* **Step 3:** Render custom animated brand stings (14:15 – 14:40).

#### **Level 6: Style Reference & Slop Monster Filtering (15:15 – 19:10)**
* **Step 1:** Find high-end graphic design references on `savee.ai/graphics` (16:10).
* **Step 2:** Pass the reference image URL to Claude Opus 5.5 to replicate layout, typography, and motion style (16:40).
* **Step 3:** Pass all generated marketing copy through the `SlopMonster` GitHub repository rules to eliminate generic AI writing patterns and exaggerated sales tropes (17:01).

#### **Level 7: Scaling to 100 Websites / "100 Films Out" (19:10 – 22:19)**
* **Step 1:** Feed a batch list of 100 SaaS/brand URLs into Firecrawl (19:20).
* **Step 2:** Pipeline the scraped branding specs into Agentic OS and Claude Code.
* **Step 3:** Programmatically render a 100-tile animated logo grid, where each card automatically executes brand-specific particle explosions and color transitions (20:10).

---

### 5) Visual Layouts & UI Descriptions

#### **A. Custom Showcase Web Deck (`http://localhost:4110`)** *(00:00–02:20, 04:05–05:00, 08:10–08:35, 11:10–11:55, 12:40–13:35, 16:30–17:00, 19:10–20:05)*
* **Theme & Palette:** Ultra-dark background (`#0D0D0D`) featuring gold/copper metallic glowing edges, textured torn-paper corner accents in beige, and off-white/serif headers.
* **Header Bar:** Displays current port/address `localhost:4110` with browser tabs across top.
* **Level Section Cards:** Pink filled circle icons containing level numbers (e.g., `01`, `02`), uppercase section labels (`LEVEL 1 • PRESENTATIONS`), serif headlines ("Animated slides"), and a prompt breakdown drawer.
* **Interactive Preview Window:** Dark embedded viewport with playback control bar (`0:00 / 0:10`) showing live Canvas animations, simulated PowerPoint windows, or video reels.
* **Tab Navigation inside Card:** Pill buttons for `The story`, `The idea`, `Prompt`, `Demo`, `Result`, `Brand pulled with Firecrawl`.

#### **B. Notion Workspace ("Motion, drawn in code - The RISE method")** *(01:40–01:58, 05:30–05:35)*
* **Theme & Palette:** Clean light mode layout with standard Notion typography.
* **Header Graphic:** Wide banner image with Earth and cosmic imagery. Title: "Motion, drawn in code - The RISE method", subtitle "Free guide • The RISE method • by Jack Roberts".
* **Components:** Numbered instructional blocks ("01 / Write a RISE prompt"), acronym graphic for R-I-S-E, callout boxes, and formatted code blocks.

#### **C. Firecrawl Dashboard (`firecrawl.dev/dashboard`)** *(03:01–03:34, 03:45–03:58, 10:50–10:58)*
* **Theme & Palette:** Bright white content area paired with a dark slate-gray left sidebar and orange logo highlights.
* **Left Sidebar:** Displays navigation items: `Overview`, `Integrations`, `API Keys`, `Extract`, `Search the web`, `Scrape a single web...`, `Crawl a website`, `Map a website`, `Usage`, `Settings`. Bottom left shows credit meter ("5,000 credits left").
* **Main Panel:**
  * **Integrations tab (03:01):** Lists "Coding agents" (Claude Code, Codex, Cursor, Opencode, OpenClaw, Hermes) with "Install" buttons and an MCP server box (`https://mcp.firecrawl.dev/group-vauth`).
  * **Scrape tab (03:15):** Contains input field (`glaido.com`), action selector (`Search`, `Scrape`, `Map`, `Crawl`), format selector (`Branding`, `Markdown`, `JSON`), and a red "Start scraping" CTA.
  * **Branding Result View (03:45):** Grid displaying extracted brand details: Logo previews, hex color blocks (`Primary #111111`, `Accent #8DDB00`, `Background #FFFFFF`), font name (`Space Grotesk`), and tone profile summary.

#### **D. Agentic OS Local Dashboard (`http://127.0.0.1:4100/motion`)** *(06:17–07:10, 12:00–12:18, 18:20–18:28, 21:50–22:00)*
* **Theme & Palette:** Dark theme UI (`#080808`) with glowing cyan-purple headline text ("Unlimited motion styles") and subtle glassmorphic container cards.
* **Left Sidebar:** Dark vertical bar with icons for `Dashboard`, `Design`, `Chat`, `Calendar`, `Memory`, `Settings`, `Motion Library`.
* **Prompt Controller Bar:** Central input text field ("Describe the idea. Drop in a logo, an image, a video or a link..."), horizontal slider (`10s`–`30s`), "Auto-enhance" toggle switch, target application dropdown (`Claude`, `Claude Code`, `Codex`, `ChatGPT`), and a black "Write prompt" button.
* **Gallery & Style Grid:** Tabs for `Styles (109)`, `Made in this video (17)`, `Inspiration (12)`. Displays style thumbnails (Screenprint Flowers, Cyanotype Botanicals, Pencil Hatch, Ballpoint Doodle, Oil Impasto).

#### **E. Proven AI Systems Course Portal** *(07:10–07:18)*
* **Theme & Palette:** Dark green and black layout. Top banner features Jack Roberts headshot next to text "PROVEN AI SYSTEMS".
* **Navigation Header:** Bright green pill tabs (`Foundation`, `Power Features`, `Memory Agent`, `Apps`, `Build Anything`, `Completeness`).
* **Content Grid:** Module cards (`01 Foundation + Setup`, `06 Apps`, `07 Build Anything`) with lesson checklists and status tags.

#### **F. SlopMonster GitHub Repository (`github.com/Jack-Roberts/SlopMonster`)** *(17:01–17:18)*
* **Theme & Palette:** Standard GitHub white light mode UI.
* **Layout:** Top bar showing `Jack-Roberts / SlopMonster` repository header. File directory containing `prompts`, `references`, `rules`, `LICENSE`, `README.md`.
* **README View:** Graphic banners and formatted text detailing anti-slop rules (Rule 3: "Punctuation cadence", Rule 4: "Rule-of-three rhythm").

#### **G. 100 Brand Motion Grid UI** *(20:10–21:00)*
* **Layout:** Full-screen 10x10 grid matrix containing 100 rounded rectangular dark tiles for top tech companies (OpenAI, Anthropic, Cursor, Stripe, Revolut, Wise, Monzo, Convex, Vercel, Supabase, Linear, etc.).
* **Visual Animation:** Cards periodically trigger color particle bursts and animated fluid gradient rings matching each brand's exact hex identity.

---

### 6) 5 Actionable Takeaways for Building an Agency AI OS on Claude Code

1. **Standardize Creative Prompts Using the RISE Framework (01:30–01:55):**
   * Structure all programmatic design prompts in Claude Code into four explicit blocks: **References** (scraped URLs/brand JSON), **Idea** (the narrative motion loop), **Style** (typography, exact hex swatches, textures), and **Examine** (quality checking render frames at 0%, 25%, 50%, 75%, and 100%). This eliminates prompt trial-and-error and guarantees single-shot HTML/Canvas output.

2. **Automate Client Brand Onboarding via Firecrawl Scraping Pipelines (02:30–03:55):**
   * Connect Firecrawl via CLI or MCP server into Claude Code. Before generating marketing creative or decks for a client, run a Firecrawl scrape targeting the `Branding` output format. This automatically feeds Claude exact brand hex codes, typography rules, logo SVGs, and brand voice profiles, lowering token spend by up to 80%.

3. **Replace Static & AI-Video B-Roll with Code-Drawn Canvas Animations (00:40, 11:10, 12:40):**
   * Transition agency B-roll, social reels, logo stings, and deck slides to code-native HTML5 Canvas/CSS animations. Code-drawn graphics render in crisp 60fps, are 40% cheaper and 30% faster on Claude Opus 5.5 than specialized video tools, and can be resized across 9:16, 16:9, and 1:1 aspect ratios without quality loss.

4. **Integrate an Anti-AI Slop Audit into Content Pipelines (17:00–17:20):**
   * Run all marketing copy, slide text, and social script output through a dedicated quality-control repository/prompt set (such as `SlopMonster`). Automatically strip away obvious AI markers—such as repetitive rule-of-three phrasing, unnatural punctuation cadences, generic fonts, and exaggerated sales claims—before client delivery.

5. **Consolidate Agency Assets into a Local Centralized Agentic OS Dashboard (06:17–07:05, 21:20–21:50):**
   * Build or host a local web dashboard (`Agentic OS`) linked to Claude Code, Codex, and Firecrawl. Save reusable style libraries (100+ motion templates, carousel presets, caption styles) and client brand specs in one dashboard. This allows agency team members to input a simple prompt or client URL and trigger multi-channel creative generation across web, video, and social channels simultaneously.
