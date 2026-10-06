# Handoff: "One-way ticket" Part 1 v1.1 (clearer voice), sound only

Omarie, 6 Oct, after watching Part 1: "can we work on the clarification of my voice?" and "in some parts ... my voice gets cut off at the end of the sentence ... too early." His clicks: Part 1 gets a sound-only update with the same two fixes as Part 2. Same picture, same edit. Run it in a fresh, small session (token cost rules in `CLAUDE.md`).

- **Fixes:** port them from `part2/`, where fix A is `tools/tail_check.py` and the tail rule in the edl build, and fix B is the voice chain and ducking in `lib/mix.py`.
  - **A, tails:** the out-point is at least 350 ms after the last word ends, or at the end of the sentence. Never cut mid-word. Fade over 100 ms. When the picture cuts first, use an L-cut. Fail any gap under 300 ms. First list where v1 cut early: run the check on `part1/data/edl.json`.
  - **B, voice chain:** high-pass at 90 Hz, gentle noise reduction, −2 dB at 250–350 Hz, +2–3 dB at 3–4 kHz, a de-esser, 3:1 compression. Voice at least 10 dB over music and nat.
- **Footage:** re-fetch Part 1's mezzanines with the engine (`plan`/`fetch` from `part1/data/edl.json`). The lead calls Dropbox `download_link`; the Part 1 container is gone.
- **Delivery spec:** −14 LUFS / −1.5 dBTP, under 11.5 Mb/s. File: `2026-09-26 One-way ticket Part 1 v1.1 (clearer voice) - SE LOCKED-ON vlog - 1080x1920.mp4`.
- **Checks:** nq-check on the audio, by the numbers (voice-to-music level before and after, and the tail-gap list). The facts panel only runs if any on-screen text changes.
- **Delivery:** a new card on top of Video Drop (https://claude.ai/artifact/5pW7z8z8fqRa35vMjNUYYP, read it first; it was at version 11 after Part 2). Test the SHA-256.
  - v1 is in Dropbox at `/Supercar Experience/05 Vlogs/2026-09-26 One-way ticket Part 1/` (256,870,221 bytes).
  - Ask Omarie before archiving v1.
  - If the saved file lands in the Dropbox root, find it by name and move it after his click.
- **Lessons from Part 2:**
  - Read a page's file with `path: "index.html"` only. A plain read and a path read each return the whole page.
  - Save Dropbox link answers from the transcript (`.jsonl`) instead of retyping URLs.
  - Pin `av` to 15.x for faster-whisper.
