# watch — source and local rules

- **Upstream:** https://github.com/bradautomates/claude-video, `skills/watch/` (Bradley Bonanno, MIT — see `LICENSE`)
- **Pinned at:** `03ceb42` (release 0.3.2), copied 2026-09-25.

## What works from these cloud containers (tested 2026-09-25)

YouTube blocks this container's IP for everything that touches the video itself: yt-dlp, captions,
transcripts, Invidious/Piped mirrors, a headless browser. **Use the Gemini engine** — the URL goes to
Google, which watches it.

    WATCH_GEMINI_MODEL=gemini-3-flash-preview \
      python3 .claude/skills/watch/scripts/watch.py "<youtube url>" --engine gemini \
      --question "<what to look for>" [--start MM:SS --end MM:SS]

**Key:** `GEMINI_API_KEY` in the environment, or `~/.config/watch/.env` (mode 600). Never in this repo —
it is public. The container is wiped between sessions, so the durable place is the environment's secrets
setting in Claude Code on the web.

**Free tier limits:** about 5 requests a minute and 20 a day **per model**. Model order that worked:
`gemini-3-flash-preview` → `gemini-3.6-flash` → `gemini-flash-lite-latest` → `gemini-3.7-flash`.
`gemini-flash-latest` resolves to `gemini-3.8-flash` and shares its daily 20.

| error | meaning | do |
|---|---|---|
| 503 | model overloaded | wait 20–45 s, try the next model |
| 429 "per day" | that model's daily quota is gone | drop it until 07:00 UTC |
| 429 "per minute" | too fast | one request at a time |
| 400 on a long video | too long for one request | split into 30-minute `--start/--end` pieces |

**Check the metadata.** Gemini gets titles, creators and lengths wrong — it named the wrong title and
creator on two of four videos on 2026-09-25, and summarised only the first 16 minutes of a 37-minute one.
Confirm with YouTube's oEmbed (works from here) and compare against the chapter list:

    curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<id>&format=json"

**When Gemini is down or out of quota,** Jina's reader can still load the watch page from its own servers.
Ask for raw HTML and read the description, chapter list and links out of `attributedDescription`:

    curl -s -H "X-Return-Format: html" "https://r.jina.ai/https://www.youtube.com/watch?v=<id>"

Then follow the creator's own companion page, repo or docs (also via `r.jina.ai/<url>`). That route
recovered most of three videos on 2026-09-25; the video content itself it cannot give you.
