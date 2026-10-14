# Lead playbook (read on demand)

Detail the lead session needs only at certain moments. It was moved out of the root `CLAUDE.md` on
2026-10-06 so every call doesn't pay for it; `CLAUDE.md` keeps the short rule and a pointer here.

## Delivering finished videos: Video Drop steps

Omarie, 2026-09-28: "keep that as a rule for the future for when we come into this problem and keep it all in that
artifact." Finished videos go into his Dropbox (the notes' `deliver-to-dropbox` has the folders and naming). The
Dropbox connector can't upload a video, and chat attachments stop at 30 MiB. So when a session can't put the file
in Dropbox itself, deliver it through the **Video Drop** page: https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP

- Each video is a card. Omarie taps **Save video**; the page rejoins the parts and opens his phone's share sheet,
  and he picks **Dropbox** and the folder named on the card.
- Use this one page for every delivery. Never make a second one.
- The steps are in the notes:
  1. Split the master into 19 MiB parts.
  2. Upload them as the page's assets in one call.
  3. Add a card and republish. Read the page once first, with `path: "index.html"`, never a plain read
     plus a path read: each returns the whole page (in Part 2 the double read pushed the lead past 300k for
     9 calls).
  4. Test that the rejoined file's SHA-256 matches the master: check that the local parts `cat` to the master's
     hash, then go down the card's parts in order and match each one's SHA-256 against the one `list` with
     `scope: "assets"` prints for its asset id, so a part out of place on the card is caught (one or two calls
     for all the parts). Omarie, 7 Oct: Part 2 v2 checked 26 parts this way, where reading each back with its
     own `path` would have taken 26 calls; a multi-`paths` read of asset ids failed in Part 2.
  5. Once he has saved it, get the Dropbox copy (`download_link`, then `curl`; on the Mac it is already in the
     Dropbox folder) and confirm it against the master. If the file isn't in the card's folder, search Dropbox
     for its filename: the showreel trial landed in the Dropbox root. Ask him before moving it. The copy won't
     have the master's size or its whole-file SHA-256: claude.ai's save path adds a C2PA box right after `ftyp`
     (a top-level MP4 `uuid` box, type `d8fec3d6-1b0e-483c-9297-5828877ec481`), and because the box sits before
     `mdat`, every `stco`/`co64` chunk offset goes up by the box's size. Nothing else changes. Expect the
     master's size plus the box, and don't fail a file on a `shasum -a 256` mismatch alone. Either of these
     checks the whole file end to end:
     - (a) The streams match: `ffmpeg -v error -i FILE -map 0 -c copy -f streamhash -hash sha256 -` prints the
       same per-stream hashes for the master and the Dropbox copy, and the same command ending `-f framemd5 -`
       prints the same packet list.
     - (b) The file matches with the box out: `python3 .claude/brain/c2pa_strip_check.py MASTER DROPBOX_COPY`
       leaves the box out, moves the chunk offsets back and prints PASS when the SHA-256 is then exactly the
       master's. MASTER is the master file, or its SHA-256 when the master isn't on this machine. A copy with
       no box passes only when it is the master byte for byte. It writes nothing.

     Seen 12 Oct on four FD Opus clips and the Showreel 2026 sound trial: each landed 5,893 bytes over its
     master, the size of the box, so the old exact-size check failed every time.
- The box is Content Credentials, signed "Anthropic Claude Content Signing" with claim generator "Anthropic
  Claude.ai" and the action `com.anthropic.claude.provided`. Instagram reads C2PA and may add its own "AI info"
  tag to a post. Whether a post gets labelled is Omarie's call.
- The page holds 1 GiB. Clear older cards only once they're confirmed in Dropbox, and ask him first.

## Adding the post to the Posts Library (at every hand-over)

Omarie, 2026-10-13: "i cant keep track of all this through dropbox and dropbox aint gonna keep my captions." The
**NQ Posts Library**, https://claude.ai/artifact/Y3shBejn5Lat1TZY7hVWYk, keeps each post's video, final caption and
stills together, with a tab per brand and a status he can trust: Built, Checked, In Dropbox, Posted. Video Drop is
still the one delivery page; the library is where a post lives afterwards. Use this one page. Never make a second.

Right after the Video Drop card step, add the post, with nothing typed twice:

1. `python3 .claude/brain/posts_library.py add VIDEO --brand fd|se|as --id <post-id> --title "..." --work <your
   scratchpad>`, plus the caption file and who approved it, the Dropbox path and the Video Drop card id. It cuts
   the poster, a small preview and three frames, splits the master and prints the upload call. Add `--still FILE`
   for each cover or AI still, and `--ai` when every shot is generated.
2. Make the upload call it printed (one call for up to 25 files). When the master is already on Video Drop, pass
   `--no-parts` and copy those parts across on the server instead of uploading them again.
3. `python3 .claude/brain/posts_library.py record <post-id> name=<asset id>... --work <same folder>` writes the
   record and prints the database call. Make it. The post appears on the page at once; the page itself is not
   edited or republished.
4. Open the page and check the post plays, its caption copies and Save offers the full file.

- The caption is the approved one, read from its file byte for byte. With no approved caption, leave it out: the
  page then shows the hook and "caption not on record". Never write one to fill the gap.
- The caption file holds the caption and nothing else. A hand-over note with a heading, a "Post with" line or a
  code fence is refused; save the caption lines to their own file first.
- Once the Dropbox copy is confirmed (Video Drop step 5), run `posts_library.py dropbox <post-id>` and make the
  call it prints, so In Dropbox is true on the page. For any other change to a post already on the page, use
  `record ... --update`: a plain `record` replaces the whole record and would clear his Posted tick.
- One brand per post. A newer cut replaces an older one with `posts_library.py supersede <old-id> "<why>"`; the
  old one stays on the page, greyed, with saving off.
- **Posted is his tick.** He taps Posted on the page once it's up on Instagram. To see what's posted, run
  `posts_library.py read` and make the call it prints: `steps.posted` and `posted_at` on each post. Don't set
  them for him.
- Post records live in the page's database, never in this repo or the page's source.

## The Working-now card: step detail

Omarie, 2026-09-30: "I want my NQ OS system to show me when it's actively working on something." The
control room (https://claude.ai/artifact/JdMaXgCuUu7XHQ3yRhEYFy) opens with a **Working now** block. It
reads the page's `work` collection, one document per session, so he can see from his phone what every
session is on, with a link to it. A card with no update for 20 minutes shows as quiet and drops out
after a day, so a card you stop updating goes stale in the open rather than looking current.

The lead keeps the card; agents never write it. On any job past a couple of minutes:

1. **Start:** `python3 .claude/brain/live_card.py start "<job>" "<first step>" --role <id>` prints the payload
   (url, collection `work`, this session's doc id, data). Pass it to `ArtifactData` as a `set`; a new
   card needs no `if_version`. `live_card.py roles` lists the ids; it lights that role on the Agents page map.
2. **Each new step, and at least every 15 minutes while working:** `... step "<what you're on now>"`
   (add `--pct N` when there's a real percentage), then `ArtifactData` `update` with `if_version` set
   to the version the last write returned.
3. **End:** `... done "<what shipped>"`, or `blocked` / `waiting` with what's needed from him. Never
   stop with a card still on `working`. `done` also logs the job's cost line (see the token cost rules).

One small tool call per step and no model call, so it costs almost nothing. The Mac runs the same rule
(its handoff is in Dropbox `NQ Studio/06 Creator Kit/Agentic OS/`).

## The NQ OS team: background and enforcement detail

Omarie, 2026-09-30: "I want my nq os team to be the main team that also runs with my second brain." The
agents in `.claude/agents/` are the NQ OS agentmesh classes, the same team his Mac runs. Each job goes
to a class, and the class decides the model and effort. On 2026-09-30 he had the cloud cells tuned for
speed ("assign each of my agents a sonnet to opus model ... for max efficiency"): Sonnet runs the lanes
that follow a plan, Opus keeps the judgment calls. The head-to-head bench the same day moved build to
Opus (only Opus caught a real defect in its own spec) and fix to Sonnet (same answer, twice as fast);
see `.claude/agentmesh/bench-2026-09-30.md`. The policy and the reasons are in
`.claude/agentmesh/MESH.md` (cloud v1.3); the Mac's `~/.nqos/os/agentmesh/` is still on v1.2.

**Brief with the class, the playbook and the style.** The workstream knowledge (branches, worktrees,
pipelines, brand rules) is in `.claude/playbooks/`: `formula-dynamics.md`, `supercar-experience.md`,
`anti-stock.md`, `research.md`, `sound-layer.md` for recorded sound effects on any video (added with the
workstream's playbook), and `review.md` for the checks. Name the one that applies, so the same
`nq-build` builds any workstream's piece. Builders work in worktrees of their workstream's branch,
because this default branch doesn't carry `creator-kit/`, `formula-dynamics/` or `supercar-experience/`.

**The facts panel.** Either `nq-facts` or `nq-second` can block, and only both together clear. Don't
pass one voter's verdict to the other, because a vote that saw the other's answer isn't independent.
Run `nq-story` first only when the creative direction isn't settled.

**Claude Code enforces the chain** (Omarie, 2026-09-28). `.claude/settings.json` sets
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to 1: one subagent runs at a time,
and subagents can't start their own. Claude 5 models delegate more readily, and every agent costs a full conversation's
worth of tokens. A second spawn while one is running comes back as `Concurrent subagent limit reached`: wait for the
first to finish. Sessions with ultracode on are never refused.

## The regret-list gate: full list

Omarie, 2026-09-27. `.claude/hooks/regret_gate.py` runs before every Bash and connector call (wired in
`.claude/settings.json`). It **asks** before any paid Higgsfield call (quote the cost first), anything
that publishes or changes a live account, Dropbox moves or deletes, Windsor.ai write actions,
memory-store writes, force pushes, `git reset --hard`, `git clean -f`, and recursive deletes (`rm -r`,
`find -delete`) outside `/tmp`. It **refuses** any push to `main`, `master` or this repo's default branch
`claude/new-session-mucc2q`, because those only change through a PR. That covers a bare `git push` from
one of them, `git -C`, and commands wrapped in `sudo`, `env` or `bash -c`. Its GitHub connector rules are
on too: it refuses file writes to those branches and asks before merging a PR. An "ask" waits for
Omarie's click, so an unattended routine that hits one stops there until he answers. Test it with
`python3 .claude/hooks/test_regret_gate.py`.

## Prompting Claude 5 models (sourced, not Omarie's own rule)

From research, 2026-09-28 — Ben AI, "Anthropic Just Revealed 7 New Rules for Prompting Claude 5
Models" (full notes on the `claude/deep-research-report-5oh5nm-gemini-notes` branch, under
`research/agent-videos-2026-09-28/gemini-notes.md`, video 1). Applies to how the lead briefs
the NQ OS agents and how any agent prompts a Claude 5 model directly. This is adopted guidance,
not a standing instruction from Omarie — update or drop it if it doesn't hold up.

1. **Give the whole job, not steps.** State the task, guardrails and exit criteria up front rather
   than spelling out step 1/2/3 for anything past a trivial task.
2. **Say why, not just what.** A brief that names who the output is for and why it matters gets
   better judgment calls on the details it doesn't spell out.
3. **Define what done looks like.** State the exit criteria and output shape explicitly — Claude 5
   models tend to over-run rather than under-run without one.
4. **Reasons beat hard rules.** "Never do X" lands worse than "do Y, because Z." Prefer the second
   form when writing standing rules, including in `CLAUDE.md`.
5. **Don't ask it to double-check itself.** Skip "verify your work," "think step by step," or a
   built-in review pass — Claude 5 models already self-correct on their own. Ask a human or
   `nq-check` for a second look instead, not the same agent again.
6. **Fix tone once, not every time.** If an agent's output keeps needing the same tone or
   format correction, put it in that agent's `.md` file once instead of repeating it in every brief.

Left out: the source's "Interview Me" skill (Anthropic uses one internally to ask clarifying
questions before a big task) — worth building only if we make a matching step for large briefs.
