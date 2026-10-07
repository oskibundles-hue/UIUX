# Handoff: One-way ticket Part 2 v2 (in progress, 2026-10-07)

Goal: Part 2 v2 (in-car stereo bed + NO MUSIC fallback, food break + talk-to-camera, strip scrubber only,
end card "RENTERS 25+ · AGES 21–24 WITH UNDERAGE FEE" with no "$", voice fix A/B passing), ~2:45, delivered
to Video Drop, lead session session_013JoCuN8AVJiDRcQU8W2e21 messaged.

State:
- Part 1 v2 code ported into part2/ (commit 258d4ed). bed.segs empty; STRIP timings still v1 (`_todo`).
- Clips 0103–0123 ingested in the build container's day dir (/tmp/claude-0/p2day: tr/, kf/, day.md, moments.md);
  a fresh container has to re-ingest (vlog.py links/ingest, Dropbox download links).
- Song spans: ../in_car_tracks.json (Part 2 rows 0103–0122).
- Candidate moments (sheet qa/candidates.jpg, awaiting nq-check hands/phone call):
  food 0105 10.6–13.8, 0107 14.6–19.0 (phone?), 0112 39.0–43.0;
  talk 0116 142.6–159.4 (top pick), 0121 28.7–32.6 → exhaust, 0106 283.2–291, 0118 49.9–53.6.

Next: nq-check verdict on candidates → pick → nq-build recut (make_edl, bed.segs + subs, STRIP retime,
clockAs, captions) → nq-check sheets → render → nq-check / nq-facts / nq-second → Video Drop → lead message.
