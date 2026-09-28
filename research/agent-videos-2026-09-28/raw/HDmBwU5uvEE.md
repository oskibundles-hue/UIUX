# watch: video report — every attempt failed

- **Source:** https://www.youtube.com/watch?v=HDmBwU5uvEE
- **Video:** "Anthropic Just Revealed 7 New Rules for Prompting Claude 5 Models" — Ben AI
- **Engine:** gemini (all four models in the fallback order failed)

## Attempts, in order

1. `gemini-3-flash-preview` — HTTP 400 "rejected": "Agentic video processing is not enabled for this model."
2. `gemini-3.6-flash` — HTTP 503 "service": high demand. (repeated on 3 further retries)
3. `gemini-flash-lite-latest` — HTTP 503 "service": high demand. (repeated on 3 further retries)
4. `gemini-3.7-flash` — HTTP 503 "service": high demand. (repeated on 2 further retries)
5. `gemini-3-flash-preview` (retry) — HTTP 429 "quota": "Rate limit exceeded for model gemini-3-flash (limit: 20 requests per day on Free Tier)."
6. `gemini-3.6-flash` (retry) — HTTP 429 "quota": "Rate limit exceeded for model gemini-3.6-flash (limit: 20 requests per day on Free Tier)."
7. `gemini-3.7-flash` (retry) — HTTP 429 "quota": "Rate limit exceeded for model gemini-3.7-flash (limit: 20 requests per day on Free Tier)."
8. `gemini-flash-lite-latest` (3 further retries, waits of 30–45s between each) — HTTP 503 "service": high demand every time.

## Outcome

No answer text was ever returned for this video. By the end of the session, `gemini-3-flash-preview`, `gemini-3.6-flash`, and `gemini-3.7-flash` had all hit their per-model 20-requests-per-day Free Tier cap (shared across every video asked of them in this session, not just this one). `gemini-flash-lite-latest` never hit a quota error but returned HTTP 503 "high demand" on every single attempt across the whole session (also true for videos 3 and 4) — Google's backend was overloaded for that model this whole run.

Metadata (confirmed via oEmbed, not by Gemini): title "Anthropic Just Revealed 7 New Rules for Prompting Claude 5 Models", channel "Ben AI".
