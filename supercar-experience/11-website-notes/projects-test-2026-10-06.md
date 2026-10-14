# Projects test, 2026-10-06 (answered 6 Oct 2026, about 10:40 PM PDT)

Written by the thread session that drafted `posts/which-rental-length-fits-a-vegas-trip/` on branch
`claude/se-post-rental-length`. Short, factual answers to the 8 questions.

## 1. Instruction files and text at the start

- **CLAUDE.md:** one file, `/home/claude/UIUX/CLAUDE.md`, loaded from the checkout the session started on (the
  default branch, `claude/new-session-mucc2q`). The `claude/se-website-render` branch has a different CLAUDE.md;
  that one was not loaded. There was no `~/.claude/CLAUDE.md` and no `.claude/CLAUDE.md`.
- **Project instructions:** yes, the "SE website" project instructions (branch rules, public repo, site rules,
  self-check, reporting).
- **Project memory:** yes, a team MEMORY.md (`team/silo/MEMORY.md`). First line: `# SE website project`.

## 2. Skills I could see

session-start-hook, ckm:banner-design, ckm:brand, ckm:design, ckm:design-system, ckm:slides, slopmonster,
ckm:ui-styling, ui-ux-pro-max, watch, the render:* set (check-render-status, deploy-to-render,
render-background-workers, render-blueprints, render-cli, render-cron-jobs, render-debug, render-deploy,
render-disks, render-docker, render-domains, render-env-vars, render-keyvalue, render-mcp,
render-migrate-from-heroku, render-monitor, render-networking, render-postgres, render-private-services,
render-scaling, render-static-sites, render-web-services, render-workflows),
cowork-plugin-management:cowork-plugin-customizer, cowork-plugin-management:create-cowork-plugin, dataviz,
artifact-design, artifact-diagramming, artifact-capabilities, update-config, keybindings-help, code-review,
simplify, fewer-permission-prompts, loop, claude-api, workflow-authoring, run, plugin-authoring, init,
security-review, and the anthropic-skills:* set (algorithmic-art, brand-guidelines, built-in-browser,
canvas-design, chrome-browser, computer-use, deep-research, doc-coauthoring, docs, docx, google-workspace,
import-memory, internal-comms, learn, mcp-builder, morning, pdf, pptx, skill-creator, slack-gif-creator,
task-observer, theme-factory, web-artifacts-builder, xlsx).

## 3. Connectors and MCP tools I could see

- Connected: github, Gmail, Dropbox (connected a few seconds after start), Claude_Docs, Figma
  (generate_image only), Higgsfield, TubeAlfred, vidIQ, Vertiso_Memory (approve_constraint only),
  claude-code-remote, hearthbot (the project's reply/status tools).
- Failed: the Render plugin's MCP server (`plugin:render:render`), "Proxy refused to open a tunnel: 403 Forbidden".
- None of these were used for the post. GitHub was reached through git only.

## 4. Did the repository's hooks run?

No. The session's own log (`/tmp/claude-code.log`) shows one UserPromptSubmit hook, the environment's
`~/.claude/user-prompt-submit-reply-reminder.py`, and no line naming `regret_gate.py`, `recall_hook.py`,
`prompt_brief.py`, `cost_guard.py` or `session_refresh.py` (0 matches for `regret_gate`). No recall note
was added to the prompt, and no PreToolUse hook ran on any Bash command. The project's
`.claude/settings.json` lists those hooks, but they weren't loaded in this session.

## 5. Network from the sandbox

- `curl https://supercarexp.vip/`: no HTTP status (000). The proxy refused the tunnel: "CONNECT tunnel failed,
  response 403". `https://www.supercarexp.vip/cars` gave the same.
- `curl https://github.com/`: HTTP 400. `git fetch` from GitHub worked.

## 6. How long the clone took

3.8 seconds (3,838 ms), from the environment manager's log. It was a fast resume: it reused an existing clone
from a previous session (repository 163 MB) rather than cloning fresh.

## 7. What I couldn't do

- Reach supercarexp.vip, so no rate, 3-hour rate or miles figure was re-checked against the live listings today.
- Find any source for miles included per rental length. It's a marked open question in the draft.
- Find 3-hour rates in `cars[]` (it has day and 5-hour only). The draft uses the 3-hour rates for 5 cars already
  in the repo (the live renting post, read from supercarexp.vip on 6 Oct, and the 750S ad config, read on 27
  Sept), marked as an open question to confirm. Every other car's 3-hour rate is unknown.
- Find what "full day" means (24 hours or set times) or whether short rentals have set start times. Marked as an
  open question.
- Use the Render MCP server (failed to connect). It wasn't needed.

## 8. How I checked the page

- Served `supercar-experience/11-website/` with `python3 -m http.server` and loaded
  `/posts/which-rental-length-fits-a-vegas-trip/` in headless Chromium (Playwright) at 375 px and 1280 px wide.
- Both widths: page width equals viewport width (375/375, 1280/1280), so no sideways scroll; 0 console errors;
  0 failed or 4xx/5xx requests; the page has no images. 3 of 3 internal links return 200 (`/`, `/#watch`,
  `#s1`). The robots tag reads `noindex`, and the Article data parses. The "Hide review marks" switch hides the
  open-question boxes.
- Checked it isn't linked: no page or `sitemap.xml` mentions `which-rental-length`.
- Not checked: the external links (supercarexp.vip/cars is unreachable from here; the `sms:` link needs a phone),
  a real phone or Safari, and a visual review of the screenshots by a person.
