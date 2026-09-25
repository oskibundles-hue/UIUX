# Rewatch (alt, reconstructed without video): CLAUDE SKILLS FULL COURSE 2.5 HOURS (Beginner to Expert), by Eliot Prince

**How this was built.** Nobody watched the video, and no transcript was available. The only in-video evidence is the chapter list from the description. Everything else comes from Eliot's other public material and from Anthropic's current docs.
- `[SOURCE: Sx]` means the text was verified at the URL listed as Sx below.
- `[INFERRED from chapter title]` means it is reasoned from the chapter names. It is not confirmed.

**Gated or blocked:**
- The AI Recipe Vault ("Full Guide") was not retrieved. `eliotprince.com/ai-recipe-vault` redirects (301) to `eliot.kit.com/ai-recipe-vault`. That page sits behind a Cloudflare bot challenge, and access requires a free newsletter signup (S4, S6).
- The "skills vault" is inside the paid Half Day Thursdays community (S5).
- The "Six Rules of Skill Development" appear in no public source.

| Key | Source |
|---|---|
| S1 | Video metadata (title/author confirmed): https://noembed.com/embed?url=https://www.youtube.com/watch?v=-DawhgUKiOg |
| S2 | Eliot's LinkedIn post, 17 Aug 2026 (date decoded from the activity ID): https://www.linkedin.com/posts/eliot-prince_i-have-a-google-doc-with-over-137-hand-crafted-activity-7495057425625026560-UXMi |
| S3 | Agents of Change podcast, full transcript, 27 May 2026: https://www.theagentsofchange.com/eliot-prince |
| S4 | https://eliotprince.com/ |
| S5 | https://halfdaythursdays.com/ and checkout https://community.halfdaythursdays.com/checkout/half-day-thursdays |
| S6 | https://eliotprince.com/ai-recipe-vault → https://eliot.kit.com/ai-recipe-vault (captcha). A Wayback snapshot from 2026-09-12 exists but is blocked by egress policy. |
| S7 | https://halfdaythursdays.com/done-by-ai/ (search-result snippet only; the live page now shows community sales copy) |
| S8 | Eliot's standalone video "5 Claude Marketing Skills I Can't Live Without (steal them)": https://www.youtube.com/watch?v=VXEStoKn27Y (existence and author confirmed via noembed) |
| S9 | Claude Code skills docs: https://code.claude.com/docs/en/skills |
| S10 | Skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| S11 | Anthropic, *Complete Guide to Building Skills for Claude*: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf |
| S12 | skill-creator: https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md |
| S13 | https://support.claude.com/en/articles/12599426-how-to-create-a-skill-with-claude-through-conversation |
| S14 | https://academy.claude.com/use-cases/package-your-brand-guidelines-in-a-skill |
| S15 | Record a skill: https://x.com/claudeai/status/2079595988998554047 and https://www.eigent.ai/blog/claude-record-a-skill |
| S16 | Plugins in Claude apps: https://support.claude.com/en/articles/13837440-use-plugins-in-claude, https://claude.com/docs/plugins/create-with-claude, https://claude.com/docs/plugins/share |
| S17 | Claude Code plugins: https://code.claude.com/docs/en/plugins |
| S18 | Subagents: https://code.claude.com/docs/en/sub-agents |
| S19 | Claude Design: https://www.anthropic.com/news/claude-design-anthropic-labs |
| S20 | Anthropic marketing plugin: https://github.com/anthropics/knowledge-work-plugins/tree/main/marketing |
| S21 | SEO connectors (search results, not fetched): https://claude.com/connectors/ahrefs, https://claude.com/connectors/semrush |

---

## 1) Title, creator, length
- **Title and creator:** "CLAUDE SKILLS FULL COURSE 2.5 HOURS (Beginner to Expert)" by Eliot Prince (@princeeliot) [SOURCE: S1].
- **About Eliot:** a UK AI trainer and former senior SEO specialist at an agency. He runs Half Day Thursdays Ltd. His site claims about 43.8k YouTube subscribers and 29.8k newsletter readers [SOURCE: S4, S3].
- **Length:** about 2.5 h. The last chapter starts at 2:18:11 [INFERRED from chapter title].
- **Publish date:** not found. It must be after 21 Jul 2026, because the course covers "Record a Skill" (announced 21 Jul 2026 [SOURCE: S15]) and Claude Design (launched Apr 2026 [SOURCE: S19]) [INFERRED].

## 2) Core thesis
Prompts are only "level 1" of using Claude. The real leverage is turning your expertise (SOPs, checklists, voice rules, templates) into skills, which Eliot describes as "a prompt that's been given a job title" [SOURCE: S2]. You then stack those skills: add connectors, chain skills, add manager and orchestrator skills, and finally package a whole "department" as a shareable plugin [SOURCE: S2 for chaining; the rest INFERRED from chapter titles]. His claim is that expertise matters more with AI, not less: "the best users of AI… are giving it the structures, the templates, the body of information of how they operate" [SOURCE: S3].

## 3) Tools, connectors, plugins and services

| Tool | What it does / role | URL |
|---|---|---|
| Claude app (chat) and Claude desktop | Skills are toggled in Settings > Capabilities > Skills. You can see "Using [skill name]" in Claude's thinking [SOURCE: S13]. The desktop app has Chat, Cowork and Code tabs [SOURCE: S3]. | claude.ai |
| Claude Cowork | Eliot's main surface. It works on local folders and runs scheduled jobs (e.g. every Monday at 9:00), which he calls "the real golden nugget". It uses connectors and drives the browser [SOURCE: S3]. | claude.com/product/cowork |
| skill-creator (Anthropic) | Runs an interview, writes SKILL.md, then runs test cases (`evals/evals.json`) with and without the skill against a baseline. It also has a description optimizer to improve triggering [SOURCE: S12]. claude.ai uses it under the hood when you ask for a skill [SOURCE: S13, S14]. Chapter 0:27:54 "Setting Up the Skill Creator" [INFERRED from chapter title]. | S12 |
| Record a skill | In the Claude desktop app, open the + menu and choose Record a skill. You record your screen and narrate, then Claude proposes a skill for you to review. Saved skills appear in Customize > Skills and run through Claude in Chrome. Available on Pro, Max and Team. The video and audio are not retained; screenshots are kept [SOURCE: S15]. Chapter 0:55:34 [INFERRED from chapter title]. | S15 |
| Connectors (MCP) | Chapter 1:14:00 "Level Three Skills with Connectors" [INFERRED from chapter title]. Ahrefs and Semrush have official Claude connectors [SOURCE: S21]. In May 2026 Eliot said Claude had no direct Google Search Console or GA connector, so he exports the data (e.g. 5,000 rows) or has Cowork drive the tools in the browser [SOURCE: S3]. | S21 |
| Claude in Chrome | Agentic browsing. Cowork used it as a workaround when a scraping API was rate-limited [SOURCE: S3]. | — |
| Google Search Console, GA4, PageSpeed Insights | In Eliot's SEO audit, Cowork drove PageSpeed Insights "without me asking" and pulled GSC data [SOURCE: S3]. The course's SEO skills probably use the same tools [INFERRED]. | — |
| Plugins | A plugin bundles skills, connectors and sub-agents. Hooks and MCP servers are added in Cowork and Claude Code [SOURCE: S16, S17]. Details in section 4.10. | S16, S17 |
| Claude Design (Anthropic Labs) | Builds a design system from your code or design files. Every project then uses your colours, typography and components. Exports to Canva, PDF, PPTX or HTML [SOURCE: S19]. The course compares it with "Brand Print" at 2:17:20 [INFERRED from chapter title]. | S19 |
| Anthropic marketing plugin | Not evidenced in the course; included only as a benchmark. Commands: `/draft-content`, `/campaign-plan`, `/brand-review`, `/competitive-brief`, `/performance-report`, `/seo-audit`, `/email-sequence`. Includes a `brand-voice` skill [SOURCE: S20]. | S20 |
| Kit, Circle | Hosts for the newsletter/vault and the HDT community. HDT costs $150/mo or $1,500/yr and includes the "prompt and skill libraries" [SOURCE: S5, S6]. | S5 |

## 4) The framework, chapter by chapter

**4.1 What a skill is, and its anatomy (0:03:37–0:13:47)**
- Eliot's definition: "A skill is a prompt that's been given a job title. Step-by-step, the voice rules, the checklist, the output template, all packed up so Claude runs it whenever it hears the trigger" [SOURCE: S2]. Elsewhere he calls skills "repeatable processes… custom instructions with supporting files" [SOURCE: S3].
- Official anatomy [SOURCE: S9, S10]:
  - Structure: `SKILL.md` = YAML frontmatter (`name`, `description`) plus a Markdown body. Supporting files (references, scripts, assets) load only when needed ("progressive disclosure").
  - Size: keep SKILL.md under 500 lines.
  - Name and description limits: `name` is at most 64 characters, lowercase and hyphens. `description` is at most 1,024 characters (platform spec). Claude Code truncates `description` + `when_to_use` at 1,536 characters in its skill listing.

**4.2 Triggers and invocation (0:13:47)**
- Eliot triggers skills in plain language, e.g. "search my second brain for gold" or "proposal for the King of England, £7,000 a day". His framing: top operators "don't write prompts, they just say 'go'", or they put the job on a schedule [SOURCE: S2].
- How triggering actually works [SOURCE: S9, S10, S11]:
  - The description is the main trigger. It should say what the skill does and when to use it, written in the third person.
  - In Claude Code a skill runs automatically when its description matches, or directly via `/name`.
  - `disable-model-invocation: true` means only the user can run it. `user-invocable: false` means only Claude can.
  - Anthropic's guide says to test 10–20 trigger queries and aim for about 90% triggering. If a skill fires too often, add negative triggers.

**4.3 Deterministic vs non-deterministic (0:18:09)**
- What Eliot says: likely which steps must be identical every time versus which need judgment [INFERRED from chapter title].
- Anthropic's matching guidance:
  - "Instructions allow interpretation variance. Scripts execute identically every time" [SOURCE: S14].
  - Choose high, medium or low "degrees of freedom" per step: a "narrow bridge with cliffs" needs exact scripts, an "open field" needs only general direction [SOURCE: S10].
- Eliot's own supporting example: his SEO audit uses a checklist spreadsheet, and AI "can follow that step by step better than a human, because a human gets lazy and checks a box that they haven't actually checked" [SOURCE: S3].

**4.4 Levels of skills (0:20:34; "Level Three" at 1:14:00)**
- Sourced ladder: prompts are level 1. Next come skills, then "the level above that is chaining them", and running jobs on a schedule [SOURCE: S2].
- The chapter title fixes one rung: Level 3 = skills with connectors [INFERRED from chapter title].
- Likely full ladder, from the chapter order [INFERRED]:
  - L1: instruction-only skill (Simple SEO Audit, 0:29)
  - L2: skill with your expertise as reference files (0:35 "Building Skills with Expertise"; SEO Reporting, 0:57)
  - L3: skill with connectors and live data (SEO Strategy, 1:17)
  - Then: chains, integrated sets, manager, orchestrator, department, plugin
- Numbering above L3 is not sourced.

**4.5 Building and "locking in" skills (0:27:54–0:57:47)**
- "Building Skills with Expertise": Eliot's stance is that expert judgment is the edge. "I can look at an SEO audit and tell you pretty quickly whether it's a load of rubbish… layer on top… the spreadsheets, the frameworks, my SOPs" [SOURCE: S3].
- "Creating and Locking in Skills" is probably: iterate in chat until the output is right, then freeze it as a skill [INFERRED from chapter title]. Eliot describes the same intern-style loop: "I didn't get it quite right… This is how I want you to do it next time" [SOURCE: S3].
- Anthropic's matching method [SOURCE: S10]:
  - "Claude A / Claude B": do the task once with Claude A, ask it to write the skill, test with a fresh Claude B, then feed observations back to Claude A.
  - Write evals before extensive docs.

**4.6 The Six Rules of Skill Development (1:06:48) — NOT FOUND**
- No public source lists these rules.
- Do not confuse them with Eliot's "six-step AI Handover Method". That is a separate framework about *what* to hand over to AI first (S7), not about how to build skills.
- The next two chapters, "Mastering One Skill at a Time" (1:09:19) and "Technical Tips and Best Practices" (1:12:21), suggest at least one rule: perfect one skill before building the next [INFERRED from chapter title].

**4.7 Chaining, integrated sets, linking (0:22:37; 1:21:36; 1:24:54)**
- Eliot's own example: "My SEO content chain is FIFTEEN custom Claude skills that hand off to each other, audit to draft to publish" [SOURCE: S2].
- The course's integrated set is probably SEO Audit → SEO Reporting → SEO Strategy [INFERRED from chapter sequence].
- How chaining works officially:
  - Skills are composable. For example, a brand-guidelines skill "can work with other skills you've created" [SOURCE: S14].
  - Claude Code expands up to 6 stacked `/skill` invocations [SOURCE: S9].
  - Anthropic's "sequential workflow orchestration" pattern: explicit step order, dependencies between steps, validation at each stage, rollback instructions [SOURCE: S11].

**4.8 Feedback loop (1:27:42)**
- Probably: review the output, then write the corrections back into the skill so it improves each run [INFERRED from chapter title].
- Anthropic's pattern: "Run validator → fix errors → repeat". The validator can be a style-guide checklist instead of a script [SOURCE: S10]. The "iterative refinement" pattern includes knowing when to stop [SOURCE: S11].

**4.9 Skill architecture, manager skills, orchestrator, department (1:29:28–1:40:57)**
- There is no Eliot-specific public text on these chapters.
- Likely model [INFERRED from chapter titles]:
  - Worker skills each do one job.
  - A **manager** skill owns one domain (e.g. SEO): it routes work to its workers and QA-checks their output.
  - An **orchestrator** is the single entry point that sequences the managers.
  - The **department** is the whole set, e.g. "a full department of Claude skills" for SEO.
- Real mechanics for building this in Claude Code [SOURCE: S9, S18]:
  - A skill can invoke other skills through the Skill tool.
  - `context: fork` runs a skill in an isolated subagent. That subagent does not see the conversation history and runs in the background by default.
  - A subagent's `skills:` field preloads the full content of the listed skills.
  - How deep subagents can nest is set by `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`.
  - Gotcha: a skill with `disable-model-invocation: true` cannot be invoked by Claude or preloaded. Worker skills that a manager must call have to stay model-invocable.

**4.10 Plugins: structure, first plugin, sharing (1:40:57–1:48:57)**
- What the course does: probably packages the SEO department as its first plugin and shares it [INFERRED from chapter title].
- How plugins actually work [SOURCE: S16, S17]:
  - **Contents:** a plugin bundles skills, connectors and sub-agents. Hooks and MCP servers run in Cowork and Claude Code.
  - **Folder structure (Claude Code):** manifest at `.claude-plugin/plugin.json`, plus `skills/`, agents, hooks and MCP folders. Plugin skills are namespaced `/plugin-name:skill-name`.
  - **Create in the apps:** Customize > Plugins > Add > Create with Claude produces a `.plugin` file.
  - **Share:**
    - with specific people (Team/Enterprise plans); recipients get view-only use and receive your updates automatically
    - publish to your organization's library, optionally with review
    - send the `.plugin` file or a zip, which others add via Upload plugin
    - use a Git marketplace
  - Connector sign-ins are not shared; each person connects their own accounts.

**4.11 Voice skill and Brand Voice Profile (1:48:57; the 1:51:35 chapter runs about 18 min, the longest in the course) — the best-sourced part**
- Eliot's method [SOURCE: S3]:
  1. Collect evidence: blog posts, LinkedIn posts, transcripts ("great for capturing a natural tone of voice"), and professionally written website copy ("absolute gold"). Label each file with where it came from.
  2. Ask Claude to analyse the material and return "a one pager of how you write and what you do and don't do". Claude found "dry, British wit humor and cynicism" in his writing without being told.
  3. Refine with explicit do/don't rules, e.g. British spelling.
  4. Keep tone variants per channel: email is more relaxed than website copy, which differs from LinkedIn. YouTube has its own dialled-in profile.
- Anthropic's benchmark is the `brand-voice` skill plus `/brand-review` in its marketing plugin [SOURCE: S20].

**4.12 Brand Print, Brand Audit, and Claude Design vs Brand Print (2:09:42–2:18:11)**
- Eliot's visual-brand skill [SOURCE: S3]:
  - Give Claude your logos, fonts, colours and "the brand instructions… from their designer", then "Create a Claude skill that when I ask it to apply my company branding, it applies it to whatever I want".
  - Examples: an invoice straight from an email, branded PDF LinkedIn carousels.
  - His proposal skill "turns a call into a branded PDF in two minutes" [SOURCE: S2].
- "Brand Print" is very likely this skill [INFERRED from chapter title].
- "Brand Audit" probably checks existing assets against the voice and visual profile [INFERRED].
- On the comparison: Claude Design builds an in-product design system for canvas work [SOURCE: S19]. A Brand Print skill is portable to any chat or Cowork output [INFERRED].
- Anthropic tip: put exact brand values in a script so they are applied deterministically [SOURCE: S14].

**4.13 Bonus: 5 marketing skills (2:18:11)**
- Names only: Director of Psychology, Trend Jacking, Clipper Army, Lead Magnet Creation, Email Sequences [chapter title].
- These are probably reused from Eliot's standalone video "5 Claude Marketing Skills I Can't Live Without" [SOURCE: S8 that the video exists; the link to this course is INFERRED].
- Likely functions [INFERRED from names]:
  - Director of Psychology: reviews copy for persuasion and buyer psychology.
  - Trend Jacking: finds trending topics and angles them to the brand. Eliot described a scheduled Cowork job that pulls trending topics and cross-references them with his notes [SOURCE: S3].
  - Clipper Army: turns long video or transcripts into many short clips and posts.
  - Lead Magnet Creation.
  - Email Sequences.

## 5) UI shown
No source describes the video's screens. These UI surfaces exist and match the chapters, but whether each appears on screen is [INFERRED]:
- The Claude desktop app with Chat/Cowork/Code tabs, and the Cowork toggle at the top middle with a folder picker [SOURCE: S3].
- Settings > Capabilities > Skills toggles, and "Using [skill]" shown in thinking [SOURCE: S13].
- + menu > Record a skill [SOURCE: S15].
- Customize > Plugins > Add > Create with Claude / Upload plugin, and the "…" > Share dialog [SOURCE: S16].
- The Claude Design canvas [SOURCE: S19].
- The HDT site shows Eliot building "an SEO content dashboard" live [SOURCE: S5].

## 6) Five most actionable takeaways for NQ OS
These are all INFERRED applications of the sourced mechanics above.
1. **Split out voice and brand as shared reference skills, one per workstream.**
   - Create `nq-voice`, `fd-voice` and `se-voice`, plus a `brand-print` per brand.
   - Build each voice profile with Eliot's evidence method: transcripts and site copy, labelled sources, a do/don't list, and per-channel tone.
   - Make them `user-invocable: false` background skills, and put hex codes and fonts in a script.
   - Remove the embedded style rules from `/ad-copy` and `/campaign-brief` so they defer to these skills.
   - Add a brand-review pass as the feedback-loop step.
2. **Rebuild `/site-audit` as a levelled SEO chain.**
   - L1: a deterministic checklist script.
   - L2: your SOP as a reference file.
   - L3: connectors. Use Ahrefs or Semrush; for GSC, use a CSV export or the browser, since there is no first-party GSC connector per S3/S21.
   - Each skill writes a named output file that the next one reads, so `/site-audit` → `/perf-report` → a new `/seo-strategy` hand off cleanly.
3. **Add a manager skill per workstream and one orchestrator.**
   - Example: `/fd` routes `/campaign-brief` → `/ad-copy` → brand review → `/perf-report`.
   - Grow `/morning-brief` into the orchestrator that dispatches across NQ, FD and SE.
   - Run heavy workers (`/deep-research`, `/site-audit`) with `context: fork`.
   - Managers can be manual-only. Workers must stay model-invocable, or the managers can't call them.
4. **Lock in one skill at a time, using a learnings loop.**
   - Each run appends corrections to that skill's `learnings.md`.
   - Periodically fold them into SKILL.md through skill-creator's with-skill vs baseline evals and its description optimizer.
   - Start with `/ad-copy`, since it runs most often for FD.
5. **Build the five bonus skills for FD, then ship FD as a plugin.**
   - Priority: Email Sequences and Lead Magnet first (closest to revenue).
   - Trend Jacking as a weekly scheduled job.
   - Director of Psychology as a reviewer layered onto `/ad-copy`.
   - Clipper Army fits SE (production) better than FD.
   - Package the FD department as a plugin (`.claude-plugin/plugin.json`, or Customize > Plugins) to share with the client or collaborators. Each person connects their own connector accounts.

**To close the gaps (the six rules, exact level definitions, the manager/orchestrator prompts):** the free Recipe Vault is the source. Getting it needs a newsletter signup, which is the user's decision. Nothing was signed up for.
