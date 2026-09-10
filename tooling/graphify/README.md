# graphify: sibling-import fix

A patch against [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify),
written 2026-09-10 against v0.9.57. Not yet upstream.

## What it fixes

`build_ad.py` line 41 does:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layouts import LAYOUTS
```

graphify recorded no edge for that import, so its graph showed `layouts.py`
with zero incoming edges: nothing appeared to use the module that decides how
every ad looks.

Cause: for an absolute from-import the extractor used the bare module name as
the edge target. That only matches a file node when the basename is unique in
the scan. This repo has three `layouts.py` (the live one plus two copies under
`_fd-reference/`), so the target matched nothing and the edge was pruned. The
symbol-level pass did not cover it either, because it resolves imported
functions and classes and `LAYOUTS` is a dict.

The fix probes the importing file's own directory first, which is how the
import actually resolves at runtime. It is existence-gated and guarded against
a file binding to itself.

Effect here: 3,307 edges before, 3,319 after.

## Applying it

```bash
git clone https://github.com/Graphify-Labs/graphify && cd graphify
git am < ../tooling/graphify/graphify-sibling-import.patch
uv tool install --force --editable .
```

Drop this folder once the change is upstream.

## Known limit that this does NOT fix

An AST parser cannot see a dependency that only exists at runtime. `make_cues.py`
writes a `layoutStyle` key into a JSON cue file and `build_ad.py` reads it back,
and no amount of parsing will connect those two. Read the graph as a map of
imports and calls, not of how the pipeline behaves.
