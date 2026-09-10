# Paste this into the Graphify-Labs/graphify session

A verified one-hunk fix for graphify's Python import extractor, ready to turn
into a PR against Graphify-Labs/graphify (base branch `v8`).

## The bug

In `graphify/extract.py`, `_import_python`, the absolute from-import branch uses
the bare module name as the edge target id. That id matches a file node only when
the basename is unique across the scan. A repo with a live module plus a vendored
copy of the same name leaves the target matching nothing, so the edge dangles, is
pruned, and a real dependency disappears from the graph.

The symbol-level pass in `extractors/resolution.py` does not cover it either: it
resolves imported functions and classes, so `from m import CONST` leaves no trace
while `from m import func` in the same file resolves normally.

Real case: `build_ad.py` line 41 does `from layouts import LAYOUTS` after
`sys.path.insert(0, dirname(__file__))`. That module controls the visual layout of
every rendered ad, and the graph showed it with zero incoming edges.

## The fix

In the `else:` branch that currently reads `tgt_nid = _make_id(raw)`, probe the
importing file's own directory first. That is exactly how the import resolves at
runtime for a script that puts its own directory on `sys.path`. Setting
`target_path` lets the existing `target_file` stamp canonicalize the id.

```python
sibling = Path(str_path).parent / (raw.replace(".", "/") + ".py")
try:
    sibling_exists = (
        sibling.is_file()
        and sibling.resolve() != Path(str_path).resolve()
    )
except OSError:
    sibling_exists = False
if sibling_exists:
    target_path = sibling
    tgt_nid = _make_id(str(target_path))
else:
    tgt_nid = _make_id(raw)
```

The self-resolution guard is load-bearing. Without it `tests/test_import_self_loops.py`
fails: a module named `contracting.py` doing `from contracting import constants`
imports the external package of that name, not itself, and would gain a fabricated
self-loop. Their suite caught exactly that on the first attempt.

## The test

Append to `tests/test_python_import_resolution.py`, reusing that file's existing
`_write` / `_node_id` / `_has_edge` helpers. Create `live/layouts.py`,
`vendor/layouts.py` (the duplicate basename is what makes the bare id ambiguous),
and `live/build.py` with `sys.path.insert` then `from layouts import LAYOUTS`.
Extract all three. Assert an `imports_from` edge from `build.py` to
`live/layouts.py`, and assert no such edge to `vendor/layouts.py`.

## Verification already done — redo it, do not trust it

- The new test fails on unpatched code and passes with the fix.
- Full suite is identical before and after: 5359 passed, 16 failed, 95 skipped.
  Those 16 are pre-existing and unrelated, so baseline first and compare.
- On a real 261-file repo: 3307 edges before, 3319 after, and the missing
  `build_ad` to `layouts` edge appears at the correct line 41.

## PR

Suggested title:

    fix(python): resolve absolute sibling imports to the importing file's directory

Write the body from what you verify yourself. Do not repeat numbers you have not
reproduced. Worth saying plainly that this changes only absolute from-imports that
resolve to an existing sibling file, and everything else keeps the old bare-name
behaviour.

The PR would be opened under oskibundles-hue's account, so confirm before opening.

The ready-made patch, if it is easier than re-applying by hand, is in the UIUX repo
at `tooling/graphify/graphify-sibling-import.patch` on branch
`claude/skills-download-ai3m6a`. Apply with `git am`.
