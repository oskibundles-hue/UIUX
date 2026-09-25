# Video re-watch, 2026-09-25

Four videos first looked at on 25 Sept could not be watched: YouTube returned a bot check to this
container, so any conclusions were guesses. They were re-done two ways:

- **`gemini/`** — Google's Gemini watched each video (the 2.5-hour course in five 30-minute pieces).
  These are Gemini's observations, not frames anyone here checked. Gemini got the title and creator
  wrong on the Hermes and Jev videos and covered only about the first 16 minutes of the Jev video;
  the metadata below comes from YouTube's oEmbed instead.
- **`sourced/`** — research agents rebuilt each video from the creator's own companion pages, repos and
  official docs, tagging every claim `[SOURCE]` or `[INFERRED]`.

| video | creator | best source | what we took |
|---|---|---|---|
| Hermes Bot Mode Is A Cheat Code (p3_Ql5nq4t4) | Sharbel A. | `sourced/` — his article follows the video chapter by chapter | lead agent + specialists, pruned tools, model tiers, the regret list with hard gates, a verification hop, "save what you learned" |
| CLAUDE SKILLS FULL COURSE (-DawhgUKiOg) | Eliot Prince | `gemini/` — his rules are behind a newsletter signup | five skill levels, six build rules, description rules, the chain-vs-manager test, with/without-skill evals, brand voice rules |
| Opus 5.5 Just 10X'd Claude Design (HOXrLsVqinY) | Jack Roberts | both | SlopMonster (installed), RISE = References · Idea · Style · Examine, the frame check at 0/25/50/75/100% |
| Every Jev Concept Explained for Claude Users (D-Z5HnLW_ho) | Simon Scrapes | `sourced/` — TypeSafe's docs | nothing yet — see below |

## Not adopted, and why

- **Jev (TypeSafe).** New signups paused since 22 Sept; at these volumes it saves under $1 a month;
  single-question accuracy trailed Claude Haiku in independent tests. Revisit if inbox or lead volume grows.
- **Claude Design → HyperFrames motion pipeline.** Formula Dynamics' pipeline is Pillow + ffmpeg by
  standing rule, and the Anti Stock format question (Observation 1) is still open. Not a decision to take
  without Omarie.
- **Firecrawl brand kits.** Formula Dynamics and Supercar Experience already have measured brand kits on
  their branches (`fd_brand.py`, `brand-tokens.json`). A second copy would drift. Useful for a new client.
- **Hermes Agent itself.** Its patterns map onto Claude Code subagents, hooks and permissions, which is
  what was built.
- **Gated material.** Jack's RISE guide and Motion Library (Skool, $87/month for the library) and Eliot's
  AI Recipe Vault (free newsletter signup). Nothing was joined.
