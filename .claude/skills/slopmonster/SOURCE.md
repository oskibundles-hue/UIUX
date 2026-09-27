# SlopMonster — source and local rules

- **Upstream:** https://github.com/ItsssssJack/SlopMonster (Jack Roberts, MIT — see `LICENSE`)
- **Pinned at:** `f261dbf`, copied 2026-09-25. `docs/img/` left out (README images only).
- **Found via:** Jack Roberts, "Opus 5.5 Just 10X'd Claude Design…" (youtube.com/watch?v=HOXrLsVqinY), chapter 16:55.

## How it is used here

The scorer is the part we use. It is stdlib Python and needs nothing installed:

    python3 .claude/skills/slopmonster/tools/deslop.py --text "the copy"
    python3 .claude/skills/slopmonster/tools/deslop.py page.html

It scores out of 5 and exits non-zero below 5/5. Ship at 5/5.

**Scope — this is the rule that matters:**

- Run it on copy Claude wrote: hooks, titles, post captions, ad headlines, CTAs, lower-third text,
  README text in delivery zips.
- **Never run it on Omarie's own words.** Captions in the Anti Stock pipeline are his transcribed
  speech, and his voice is the product. A "cleaner" caption is a wrong caption.
- Its "invented proof" check is the same rule as ours: only state figures that can be substantiated
  from a named source. Use `--allow-proof` only when every figure in the text has a source you can name.

The rival-model cleanse (`tools/cleanse.sh`) needs the `codex` CLI, which this environment does not
have. Rewrite by hand from the scorer's findings instead.
