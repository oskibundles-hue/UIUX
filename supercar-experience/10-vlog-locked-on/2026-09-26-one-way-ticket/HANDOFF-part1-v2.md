# One-way ticket Part 1 v2: handoff (7 Oct 2026)

**Delivered** to Video Drop on 7 Oct, as two new cards, each checked by SHA-256 part by part:

| File | Bytes | SHA-256 |
|---|---|---|
| `2026-09-26 One-way ticket Part 1 v2 - SE LOCKED-ON vlog - 1080x1920.mp4` | 251,976,333 | `8b43ef98…e08a` |
| `… - NO MUSIC.mp4` | 251,941,774 | `1041728a…eedd` |

Specs: 2:58.3, −14.1 LUFS, −1.9 dBTP, 11.05 Mb/s.

**Rebuild:** run these from `part1/`:

```
python3 tools/make_edl.py && python3 tools/make_captions.py
python3 build.py --stage shots,track,join,prep,audio,gates
python3 build.py --stage front,compose,qa
python3 tools/tail_check.py
python3 tools/clock_check.py
python3 tools/track_list.py
```

**Changes from v1** are in `part1/README.md`. Omarie cut the engine line and the "one more hour" line on 7 Oct.

**Open items:**
- Circle K window prices show in the background at about 2:51 (advisory only).
- The brain note on the end card still says $299, and Omarie needs to OK the update.
- v1 is still in Dropbox. Archive it only after Omarie says yes.
- The caption at 0:47.5 runs +230 ms late. It was checked by hand.
- Part 2 v2 is being built in its own session (see `HANDOFF-part2-v2.md`).
