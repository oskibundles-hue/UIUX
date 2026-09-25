# HOXrLsVqinY: alternate reconstruction (video not watched)

**How this was built:** YouTube was blocked from this container, so nobody watched the video. The reconstruction uses the video description, the repos and pages it links to, Jack Roberts' other public repos, descriptions of his earlier related videos, Anthropic and Firecrawl docs, and third-party write-ups.
Tags: **[SOURCE: url]** means a page says it. **[INFERRED from chapter title]** means it's reasoned from the chapter list or nearby evidence, not seen in the video. Nothing below quotes the video itself.

---

## 1) Title, creator, length

- **Title:** "Opus 5.5 Just 10X'd Claude Design…". It is also listed as "Claude Design Now Makes Animated Film (INSANE)". [SOURCE: https://chooseto.ai/watch/HOXrLsVqinY]
- **Creator:** Jack Roberts, whose channel is @Itssssss_Jack. His GitHub account is ItsssssJack and his paid community is "AI Automations by Jack" on Skool. [SOURCE: https://chooseto.ai/creator/Itssssss_Jack]
- **Length / date:** 22:20, published 24 Sep 2026. [SOURCE: https://chooseto.ai/watch/HOXrLsVqinY]

## 2) Core thesis (2 sentences)

The video takes Claude Design running on Opus 5.5 through seven levels of motion design, from animated slides up to about 100 branded animations. Each level is grounded in real brand data (logos, colours, fonts) that Firecrawl pulls from a website. [SOURCE: https://chooseto.ai/watch/HOXrLsVqinY] The lasting value is in saving a style once, through his "RISE" prompting system and a "Motion Library" kept in an agentic OS, so that later animations reuse it. That is more useful than prompting from scratch each time. [SOURCE: same description] (His exact wording is not available.)

## 3) Tools, repos, models, services

| Tool | What it does | URL / install | Free vs paid |
|---|---|---|---|
| **Claude Design** | A chat plus canvas for designs, prototypes and animations. It works in any Claude chat, in the Artifacts tab, at claude.ai/design, and in Claude Code through `/design`. `/design-sync` pulls a design system in from code. [SOURCE: https://support.claude.com/en/articles/14604416-get-started-with-claude-design] | claude.ai | Beta on Pro, Max, Team and Enterprise. There is no separate allowance: usage counts against the shared plan limits. [SOURCE: same] |
| Claude Design **export** | Export options: .zip, PDF, PPTX, standalone HTML, Google Slides (only at claude.ai/design), a handoff to Claude Code, and "Send to" Adobe, Canva, HubSpot, **Hyperframes**, Lovable, Miro, Vercel, Wix and others. [SOURCE: https://support.claude.com/en/articles/14604416-get-started-with-claude-design] | Export button, top right | Included |
| Claude Design **animations** | There is an "Animation" template. [SOURCE: https://www.whytryai.com/p/claude-design-animations] Output is code (HTML/CSS/JS) with scene cuts, kinetic type, counters and a per-project tweak panel. You can ask for 16:9, 9:16 or 1:1. **There is no native MP4 button, and no voiceover or music is generated.** [SOURCE: https://maybelabs.ai/blog/claude-motion-graphics, dated 5 Aug 2026] | n/a | Included |
| Claude Design **design systems** | These store colours, type, components and layout, and apply them to every new design. You can create one from chat (brand files, logos, fonts) or with `/design-sync` (React code). They are managed in Settings > Design systems, and each one becomes an artifact that Claude Code can use. [SOURCE: https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design] ⚠ A Firecrawl blog from 1 Sep 2026 said `/design` in Claude Code *couldn't* use design-sync systems and worked around it with a DESIGN.md. Anthropic's help page (updated this week) says it can. Check this yourself. [SOURCE: https://www.firecrawl.dev/blog/claude-code-design-skill] | n/a | Included |
| **Claude Opus 5.5** | Released 22 Sep 2026. It costs $4 in / $20 out per MTok and $0.20 per MTok for cache reads. It runs about 40% cheaper than Opus 5 on typical workloads and produces output more than 30% faster. In a one-prompt game test it scored highest of any model on "graphics and polish". [SOURCE: https://www.anthropic.com/claude-opus-5-5] Early users are making animated shorts from code alone, including one where the music was synthesized in code. [SOURCE: https://newfacedesign.com/blog/claude-opus-5-5-art-animation-from-code] | Model picker | Paid plans / API |
| **Firecrawl** (branding format) | Scrapes a URL and returns a `branding` object with these fields: `colorScheme`, `logo`, `colors` (primary/secondary/accent/background/text/semantic), `fonts`, `typography` (families, sizes, weights, line-heights), `spacing`, `components` (button/input styles), `icons`, `images` (logo, favicon, og), `animations`, `layout`, `personality` (tone, energy, audience). [SOURCE: https://docs.firecrawl.dev/features/scrape] | See the API block below | Free tier is 1,000 credits/month with no card. Hobby is $19/month. A basic scrape costs 1 credit/page. [SOURCE: https://firecrawl.link/jack-roberts, affiliate link from the bit.ly] Keyless requests are allowed but rate-limited. [SOURCE: https://www.firecrawl.dev/blog/claude-code-design-skill] |
| Firecrawl skills / MCP | `npx -y firecrawl-cli@latest init --all --browser` installs the CLI and skills, including `firecrawl-website-design-clone`, which turns branding and a screenshot into a **DESIGN.md**. [SOURCE: https://www.firecrawl.dev/blog/claude-code-design-skill] The MCP URL is `https://mcp.firecrawl.dev/v2/mcp` with a bearer key, or `/v2/mcp-oauth` for browser sign-in. [SOURCE: https://docs.firecrawl.dev/mcp-server] | as shown | Same credits |
| **SlopMonster** (Jack's own repo) | A linter for AI-sounding copy. It scores text out of 5 across five groups: AI vocabulary, AI constructions like "not just X, but Y", em-dash cadence, rule-of-three, and invented proof. It exits non-zero below 5/5, so it can act as a build gate. The loop is: lint → rewrite in three passes → **cleanse with a rival model family** (GPT-5.6 via the `codex` CLI when the draft came from Claude) → re-lint. Hard rule: **never invent proof** (it flags things like "10,000+ happy users"). [SOURCE: https://github.com/ItsssssJack/SlopMonster] | `git clone https://github.com/ItsssssJack/SlopMonster ~/.claude/skills/slopmonster`, then `/slopmonster` or "de-slop this". Scorer: `python3 tools/deslop.py --text "…"` or `deslop.py page.html`. Cleanse: `tools/cleanse.sh draft.md > cleansed.md`. It includes a GitHub Action gate, `.github/workflows/slop.yml`. [SOURCE: same] | Free, MIT. The scorer is stdlib Python only. The cleanse needs `codex` or `claude` CLI, or it prints a prompt to paste. English only. |
| **power-design** (Jack's repo, related) | A Claude skill that turns brand DNA from Firecrawl plus 20 slide rules and 20 web rules into HTML decks or sites. It ships **72+ pre-built `brands/<slug>/brand-style.md` files** and a `_template.md` schema. [SOURCE: https://github.com/ItsssssJack/power-design] | `git clone` into `~/.claude/skills/` | Free |
| **Glaido** | Voice dictation ("the voice layer for every app") for macOS and Windows. [SOURCE: https://get.glaido.com/jack] It's his sponsor/affiliate; he probably dictates prompts with it. [INFERRED] | get.glaido.com | Free-forever tier, $17/month paid [SOURCE: https://get.glaido.com/pricing]. Code WHSAAKXO gives 1 free month [SOURCE: https://chooseto.ai/watch/iyRYc9sVRsw] |
| Savee, Pinterest, Dribbble | Sources of visual references and mood boards used in Level 6. [SOURCE: video description via chooseto.ai] In earlier videos he feeds Savee boards to Claude. [SOURCE: https://chooseto.ai/watch/hNpC5clEbp4] | savee.it etc. | Free to browse [INFERRED] |
| **Free vault** (bit.ly/3RNNDLa) | Resolves to skool.com/ai-automation-vault. It's a free Skool group (38.6k members) and **you need to log in to see the resources**. [SOURCE: https://www.skool.com/ai-automation-vault] | Join (free) | Free, but gated |
| **ALL Systems + Motion Library** (bit.ly/4kol0y5) | Resolves to skool.com/aiautomationsbyjack. The page advertises "FULL Claude Code + Hermes OS", "110+ blueprints", and daily calls. The Motion Library is **not described publicly**. [SOURCE: https://www.skool.com/aiautomationsbyjack/about] | n/a | **Paid, $87/month** |
| HyperFrames (HeyGen, not in the video) | Open-source renderer: HTML + CSS + a paused GSAP timeline in, frame-exact MP4 out. It's an official Claude Design "Send to" target. With the ZIP flow: `npx hyperframes preview`, then `npx hyperframes render -q high -f 30 -o final.mp4`. [SOURCE: https://github.com/heygen-com/hyperframes/blob/main/docs/guides/claude-design-hyperframes.md] | npx | Free/OSS |
| MP4 exporters (third-party) | claude2video.com: paste a share link, get MP4 at 24–60 fps, up to 4K. claude-video-export: CLI plus headless Chromium. [SOURCE: https://claude2video.com/ ; https://github.com/dawoodtrumboo/claude-video-export] | n/a | claude2video is free |
| JackRobertsMotionGraphicSkill (**fan-made, not Jack's**) | Turns a voiceover into a 1080×1920 Remotion reel "in Jack's style": hard cuts plus speed ramps, real logos on white, branding via `fetch_brand.py` with Firecrawl. [SOURCE: https://github.com/datassthou64-source/JackRobertsMotionGraphicSkill] | git clone to `~/.claude/skills/jack-remotion-motion` | Free |

**The exact Firecrawl call** [SOURCE: https://docs.firecrawl.dev/features/scrape]:
```bash
curl -s -X POST "https://api.firecrawl.dev/v2/scrape" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" -H "Content-Type: application/json" \
  -d '{"url":"https://client.com","formats":["branding","screenshot"]}' | jq .data.branding
```
- Python: `Firecrawl(api_key=...).scrape(url=..., formats=['branding'])`.
- Jack's own recipe adds `"rawHtml","links"` so he can grab 5–10 real headlines as voice samples. It also re-colours white-fill SVG logos. [SOURCE: https://github.com/ItsssssJack/power-design/blob/main/lib/extract-brand.md]

## 4) The 7-level workflow, chapter by chapter

Chapter titles and times come from the description [SOURCE: https://chooseto.ai/watch/HOXrLsVqinY]. **Everything below is INFERRED from chapter titles** unless it carries a tag. **No actual prompts from the video are available publicly.**

| Time | Chapter | Likely content |
|---|---|---|
| 0:00 | Claude Design + Opus 5.5 | Opus 5.5 had just launched (22 Sep) and now powers Claude Design. [INFERRED from chapter title + SOURCE: anthropic.com/claude-opus-5-5 for the date] |
| 0:46 | **L1 Animated Slides** | Claude Design animation or deck output: slides with motion. His May 2026 video "Claude Code = $10,000 Beautiful Slides" used Firecrawl brand DNA plus 20 design principles, which is the power-design repo. [SOURCE: https://murmurcast.com/summaries/jack-roberts] |
| 2:28 | Firecrawl: Extract Any Brand Identity | The `branding` scrape above, which returns the real logo, hex colours and fonts. In an earlier video he said Firecrawl "saves you tokens" compared with having Claude browse. [SOURCE: https://chooseto.ai/watch/op0q90XiY8o] |
| 4:04 | **L2 Websites That Come Alive** | Animated hero sections and site graphics built from the extracted brand. [INFERRED from chapter title; the description says "animated website graphics"] |
| 6:16 | **Motion Library & RISE System** | He saves a motion style and reuses it. [SOURCE: description] The method isn't public; the library sits in the paid Skool. |
| 7:30 | Product Demos With Sound | Product demo animations with audio. [SOURCE: description says "product demos"] How the sound is made isn't documented. Claude Design didn't generate audio as of Aug 2026 [SOURCE: maybelabs]. It's probably synthesized in code (Web Audio) by Opus 5.5 or added in an editor. [INFERRED] |
| 8:13 | **L3 Reels, Shorts & Captions** | 9:16 short-form with captions. Claude Design can target 9:16 and often builds a captions toggle into the tweak panel. [SOURCE: https://maybelabs.ai/blog/claude-motion-graphics] |
| 11:10 | **L4 One Animation, Every Size** | Resizing one animation to 16:9, 9:16, 1:1 (and probably 4:5). [INFERRED from chapter title] Caveat: "Retrofitting 9:16 onto a 16:9 layout is a rebuild, not a tweak", so name the ratio in the prompt. [SOURCE: maybelabs] |
| 12:40 | **L5 Animated Logos & Jingles** | Logo reveals with their own jingles. [SOURCE: description] The logo comes from Firecrawl's `branding.logo` / `images.logo` (SVG). [INFERRED] |
| 15:17 | **L6 Turn References Into Motion** | He feeds Savee, Pinterest and Dribbble references into Claude Design to copy a style into motion. [SOURCE: description links] In an earlier video he said "prompting alone fails" and used a free "Design Loop" skill: build a mood board → Claude breaks down the references → codify the result as a reusable skill in a "design OS". [SOURCE: https://chooseto.ai/watch/hNpC5clEbp4] The Design Loop skill link goes to a free Skool post that needs login. [SOURCE: bit.ly/4qXWO9r → skool.com/ai-automation-vault/claude-design-10000-websites-no-ai-slop] |
| 16:55 | SlopMonster: Clean Up AI Copy | He runs the on-screen and marketing copy through SlopMonster (details in section 3). [SOURCE: description + repo] |
| 17:24 | Style Matching: Results & Limitations | He's candid that some examples "still need work". [SOURCE: description: "the examples that still need work"] Which failures he shows is unknown. |
| 19:08 | **L7 Scale To 100 Brands** | About 100 branded animations. [SOURCE: description: "to 100 branded animations"] Most likely method: loop Firecrawl over a list of URLs, save one brand file per brand as power-design does with 72+ brands, then batch-generate. [INFERRED] |
| 21:19 | Save Your Styles In An Agentic OS | Styles and brand kits go into his local "Design OS". An earlier video exported the Claude Design system as a project archive into a local OS with a portfolio view and swappable models. [SOURCE: https://chooseto.ai/watch/iyRYc9sVRsw] |
| 21:53 | Do This Next | Probably a pitch for the Skool community or Motion Library. [INFERRED] |

**The RISE framework.** Jack's version is **not published anywhere public**, whether GitHub, the free Skool pages, summary sites or search. A widely used prompt framework of the same name stands for **Role, Input, Steps, Expectation**. [SOURCE: https://promptfoundry.me/rise-framework/] Whether his RISE uses the same letters is **unverified**. It could be his own acronym. [INFERRED]
Here is RISE adapted for motion. **This is our construct, not his:**
- **R**ole: "Senior motion designer for {brand}."
- **I**nput: brand file (hex, fonts, logo SVG, voice lines), reference frames, script, aspect ratio, duration.
- **S**teps: beats first (hook → problem → product → proof → CTA), then layout, then motion (easing, stagger, transitions), then captions and sound cue.
- **E**xpectation: a single seekable timeline, one accent colour, safe zones, an end card with the CTA, and no invented stats.

**Real prompts available from sources (not from this video):**
- Firecrawl + `/design`: "`/design build a minimal modern site … Use Firecrawl to study this site, get screenshots from it, follow the brand style and use it for the design: <url> … create a design system here in demo-3`" [SOURCE: https://www.firecrawl.dev/blog/claude-code-design-skill]
- B-roll synced to talking head: "Create motion graphics to use over a talking head video. The graphics should follow the transcript pasted below and illustrate the concepts at the matching timestamps… use only minimal text… Aspect ratio: 16:9" [SOURCE: https://www.whytryai.com/p/claude-design-animations]
- To get clarifying questions first: "Before creating the animation, ask me follow-up questions to make sure we're aligned." [SOURCE: same]

## 5) UI and visual output described

- **Outputs named:** animated slides, animated website graphics, product demos with sound, reels/shorts with captions, multi-size variants, B-roll, logo reveals with jingles, and 100 branded animations. [SOURCE: description]
- **Claude Design animation UI:**
  - A canvas next to the chat. The animation is split into named "chapters", with a Comment button and a Reload button. [SOURCE: whytryai]
  - A tweak panel generated for each project, for example an accent swatch, a captions toggle and a CTA text field. [SOURCE: maybelabs]
  - A properties panel and on-canvas drag/resize. [SOURCE: support.claude.com get-started; chooseto.ai/watch/op0q90XiY8o]
  - `/design` in Claude Code produces three parallel versions. [SOURCE: chooseto.ai/watch/op0q90XiY8o]
- **Jack's house style**, from his art-director skill:
  - Dark premium base (#07090f family) with blue→teal→violet accents.
  - Big sans headlines with one italic-serif accent word, and numbers treated as heroes.
  - No em dashes. [SOURCE: https://github.com/ItsssssJack/seven-skills/blob/main/art-director/SKILL.md]
  - Whether the video uses this style is [INFERRED].

## 6) Five most actionable takeaways for NQ OS (focus: FD ad creative)

1. **Brand kit from a URL in one call.**
   - Add `nq-os/brands/<client>/brand.json` (raw Firecrawl `branding` plus a screenshot) and a `brand-style.md` that follows power-design's `_template.md`: colours, type, radius, voice samples, CSS vars, `logo.svg`.
   - Cost is about 1 credit per brand, and the free tier (1,000/month) covers FD, SE and NQ many times over. [SOURCE: Firecrawl docs/pricing; power-design repo]
2. **Register the kit in two places.**
   - (a) As a **Claude Design design system**: in chat, "build a design system from these files", then publish. Every FD animation then inherits it automatically.
   - (b) As a **DESIGN.md in the repo**, so Claude Code and HyperFrames renders read the same tokens. [SOURCE: support.claude.com design-system article; Firecrawl /design blog]
3. **Build our own Motion Library, since his is behind the $87/month paywall.**
   - After each approved ad, save `motion/<style>.md` with the ratio set, duration, beat grammar, easing and stagger values, transition type (for example hard cut plus speed ramp), caption style, end-card rules, sound cue, and one reference MP4.
   - The next brief then says "use motion/<style>.md + brands/fd". This does what "Save your styles in an agentic OS" describes. [INFERRED; the pattern is corroborated by SOURCE: chooseto.ai/watch/hNpC5clEbp4 "codify each result into a reusable skill"]
4. **Concrete FD pipeline**, with sizes handled as separate compositions that share tokens:
   - Step 1: Firecrawl → brand kit (from takeaway 1).
   - Step 2: RISE brief. Beats first, and state the **exact ratio and duration**. Ask for "a single seekable timeline (pure function of time)". [SOURCE: maybelabs]
   - Step 3: Claude Design Animation, with Opus 5.5 selected.
   - Step 4: Export .zip, or "Send to Hyperframes". [SOURCE: support.claude.com]
   - Step 5: Claude Code makes size variants as sibling compositions: 1080×1920 (Reels/Stories), 1080×1350 (feed 4:5), 1080×1080, 1920×1080. Each one gets its layout re-flowed, not scaled.
   - Step 6: `npx hyperframes render -q high -f 30`. [SOURCE: HyperFrames guide] Fallback: claude2video or claude-video-export.
   - Step 7: Add the VO and music bed in an editor, or keep a code-synth sting. Claude Design itself outputs silent video. [SOURCE: maybelabs]
5. **Copy gate before every render.**
   - Run `deslop.py` on all on-screen text and ad copy, and only ship at 5/5.
   - Its "never invent proof" rule lines up with ad-platform claim risk, so use `--allow-proof` only for evidenced client numbers.
   - Wire `slop.yml`, or a pre-render hook, into NQ OS. For Claude-written drafts, cleanse with GPT via `codex`. [SOURCE: SlopMonster repo]
   - For SE or multi-client scale (Level 7), the same pipeline loops over a CSV of URLs. [INFERRED]

**Not verified:** the actual RISE letters; what the Motion Library contains; the prompts shown on screen; how the jingles and demo sound were made; which failures appeared in "Style Matching: Results & Limitations". Checking any of these needs the transcript, or a free Skool login for the Design Loop post.
