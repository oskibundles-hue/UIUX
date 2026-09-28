# watch: video report — every attempt failed

- **Source:** https://www.youtube.com/watch?v=3ZT0upsICHk
- **Video:** "I Made Claude My Personal Assistant (Full Build)" — Systems Made Better
- **Engine:** gemini (all four models in the fallback order failed)

## Attempts, in order

1. `gemini-3-flash-preview` — HTTP 503 "service": high demand.
2. `gemini-3.6-flash` — HTTP 503 "service": high demand. (repeated on 1 further retry)
3. `gemini-flash-lite-latest` — HTTP 503 "service": high demand. (repeated on 1 further retry)
4. `gemini-3.7-flash` — HTTP 503 "service": high demand.
5. `gemini-3-flash-preview` (retry) — HTTP 429 "quota": "Rate limit exceeded for model gemini-3-flash (limit: 20 requests per day on Free Tier)" — this model's daily cap had already been spent on video 1's attempts in this same session.

## Outcome

No answer text was ever returned for this video. Same picture as video 1: three of the four models are now over their per-model 20-requests-per-day Free Tier cap for this key (spent across all four videos in this session, not just this one), and `gemini-flash-lite-latest` returned HTTP 503 "high demand" on every attempt.

Metadata (confirmed via oEmbed, not by Gemini): title "I Made Claude My Personal Assistant (Full Build)", channel "Systems Made Better".
