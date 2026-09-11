# CLAUDE.md — user level

Versioned backup of `~/.claude/CLAUDE.md`, which loads in **every** session on this
account regardless of repository. `~/.claude` persists between sessions in the cloud
environment, but it is not under version control, so this copy is the recoverable one.

Restore it with:

    cp .claude/user-CLAUDE.md ~/.claude/CLAUDE.md

Edit this file and re-run that command; do not edit only the copy in `~`.

---

## Delivering Video Sets

Whenever handing over **more than one video**, package them as a zip and give a
download link. Never send a stream of individual file cards, and never hand over
raw per-file hosted URLs — those save under their storage UUIDs, so the user ends
up with a folder of unrecognisable filenames. The user works from an iOS phone, so
a link beats a large chat attachment.

1. **Rename for a human, not for the pipeline.**
   `SCE_Ferrari-F8-Tributo_3-Occasion_15s-9x16.mp4` — brand, subject, variant, then
   specs. Identity first, so the name survives truncation in a phone's Files app.
   Variants get plain-English names and a number, not pipeline letter codes.
2. **A numbered folder per subject**, most important first, so the order holds on
   any device.
3. **A `README.txt` inside** saying what each variant leads with, plus the key
   figures.
4. **`zip -0`** — store, don't deflate. Video is already compressed, so compression
   only costs time.
5. **Host it**: Higgsfield `media_upload` (zip is a whitelisted general-file
   extension) → PUT the bytes → `media_confirm(type="file")` → permanent URL.
6. **Verify before claiming delivery**: compare the remote content-length against
   the local file.
7. **Where approval status differs, ship two zips** — a client copy carrying only
   approved material, and our copy adding anything held, inside a folder whose name
   says it is not approved. This keeps unapproved cuts from being forwarded by
   accident.

Build the trees with hardlinks rather than copies; renders are large and the zip
reads the content either way.

Working reference implementation:
`oskibundles-hue/UIUX` → `supercar-experience/09-campaign-ads/build_deliverables.py`
