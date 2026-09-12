# CLAUDE.md — user level

Versioned backup of `~/.claude/CLAUDE.md`, which loads in **every** session on this
account regardless of repository. `~/.claude` persists between sessions in the cloud
environment, but it is not under version control, so this copy is the recoverable one.

Restore it with:

    cp .claude/user-CLAUDE.md ~/.claude/CLAUDE.md

Edit this file and re-run that command; do not edit only the copy in `~`.

---

## Standing Rules

Set by the user across sessions. These apply everywhere, not just in one repo.

### Publishing and approvals

- **Formula Dynamics** and **Supercar Experience** are the user's employers, and the
  user holds standing authority from both to publish as them. Even so, **confirm per
  action before anything goes live** as either company — the same standard the user
  applies to their own personal channel. Authority to publish is not a blanket
  approval of any particular post.
- Hosting a file behind a link, or publishing a private artifact page, is **not**
  publishing. Posting to a public feed, channel or account is. Don't ask permission
  for the former; always ask for the latter.
- **Only state figures that can be substantiated from a named source.** No invented
  prices, specs, statistics or testimonials, in creative work or anywhere else. If a
  figure can't be sourced, say so rather than filling the gap.
- Approval of one item is not approval of the next. Where a batch is part-approved,
  keep the unapproved part physically separate so it can't go out by accident.

### Git

- **Never push directly to `main`.** Work on a branch and push there.
- Don't open a pull request unless the user asks for one.

### Connected accounts

- **Ask before any move, rename or delete** in Dropbox or other connected storage.
  Reading, listing and downloading are fine without asking.
- Prefer the connectors the user has chosen for a job. If a different one looks like
  a better fit, ask rather than switching silently.

### Artifacts

- A **new concept gets a new artifact page.** Never overwrite an existing page with
  unrelated content — republish to the same URL only when updating that same
  deliverable.

### Reporting

- **Report approximate token usage after each task.**
- Memory writes at end of day, not continuously through a session.

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
