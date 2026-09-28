# watch: video report — every attempt failed

- **Source:** https://www.youtube.com/watch?v=dCZK-VssIWw
- **Video:** "The LATEST Hermes Agent Update is INSANE!" — Teku AI
- **Engine:** gemini (all four models in the fallback order failed)

## Attempts, in order

1. `gemini-3-flash-preview` — one attempt timed out in-flight at 200s (agentic video processing appears to need longer than that for some requests); the retried attempt returned HTTP 503 "service": high demand.
2. `gemini-3.6-flash` — HTTP 503 "service": high demand.
3. `gemini-flash-lite-latest` — HTTP 503 "service": high demand. (repeated on 1 further retry)
4. `gemini-3.7-flash` — HTTP 503 "service": high demand.

## Outcome

No answer text was ever returned for this video. This video was never tried against the three models after their daily quota ran out on videos 1–3, so it wasn't hit with a 429 quota error — only 503 "high demand" on every model tried.

Metadata: YouTube's oEmbed returned "Unauthorized" for this video, as flagged in the task brief. Title and channel are taken from the task brief itself, not verified independently in this session: "The LATEST Hermes Agent Update is INSANE!", Teku AI.
