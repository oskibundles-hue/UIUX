# The footage index

`INDEX.csv` plus one contact sheet per clip in `sheets/`. Committed so every
session has it without touching Dropbox — that is the whole point.

## Ask it things

    python3 ../fd_index.py search . --colour pink red --all --min 5
    python3 ../fd_index.py search . --colour teal --min 5
    python3 ../fd_index.py search . --sharp --vertical --no-people
    python3 ../fd_index.py search . --clip "aston" --sharp

`--colour` takes several hues. By default it sums them (any of these); `--all`
requires every one. The difference matters more than it sounds:

| query | what comes back |
|---|---|
| `--colour pink` | nothing at the old default of 8 — the car scores 8.9 |
| `--colour pink red` | red floor mats and tail lights at 40%+, car buried |
| `--colour pink red --all` | **two frames, both the red 911 oil change** |

A car sitting on a hue boundary splits across two buckets. The red 911 is
`pink:8.9 red:8.4` — honestly both colours, and neither half clears a sensible
single-hue threshold on its own.

## What is in it

894 rows over 29 clips: the 2026-09-03/04 shop night, three clips from 09-09,
the shop tour, and the phone days 09-17 and 09-21.

## Two caveats on this first build

**It was backfilled from frames already extracted during the 22 Sept session,
not from the clips themselves.** The clips were deleted after use — they are
164 GB and the container is ephemeral. So:

- `t` is the frame's index times two seconds. Close to true but not read from
  the container timestamps.
- `w` and `h` are the *extracted* frame size (1080x1920 or 1920x1080), not the
  source clip's. `orient` is still correct; the red 911's true 720x1280 is
  recorded in `14-stills/photos-footage/00-SOURCE.md` instead.

Re-running `fd_index.py index` over the real files would fix both. It is not
worth 164 GB of downloads to do it.

**Two clips could not be traced to a filename.** `BRAKES` and `WHEELSOFF` were
pulled in a session before this one and their rows say so rather than guessing.

## Adding to it

    python3 ../fd_index.py index <folder> -o .

Already-indexed clips are skipped, so it is safe to re-run. Commit the CSV and
the new sheets afterwards or the next session starts blind.

The `objects` column is empty on purpose. Filling it needs CLIP on a machine
that persists; this container has no torch, cv2 or transformers and anything
installed dies with the session.
