#!/usr/bin/env python3
"""Paths for the cloud copy of the second brain (recall.py, recall_hook.py).

The notes are private, so they live in the private repo oskibundles-hue/nq-agent-channel, folder
brain/ (memory/*.md plus the memory/MEMORY.md index). A cloud session sees them when that repo is
attached; it is cloned next to this one (/home/user/nq-agent-channel). Lookup order:
    1. NQOS_HOME, if set (for example ~/.nqos on the Mac)
    2. nq-agent-channel/brain next to this repo, then in the home folder
    3. this folder (no notes: recall.py says the private repo isn't attached)
The hook's prompt log goes in work/ next to this file (git-ignored, lost with the container), so the
private repo's checkout stays clean.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
_CANDIDATES = [
    os.path.join(os.path.dirname(_REPO_ROOT), "nq-agent-channel", "brain"),
    os.path.expanduser("~/nq-agent-channel/brain"),
    "/home/user/nq-agent-channel/brain",
]


def _find_home():
    if os.environ.get("NQOS_HOME"):
        return os.path.expanduser(os.environ["NQOS_HOME"])
    for c in _CANDIDATES:
        if os.path.isfile(os.path.join(c, "memory", "MEMORY.md")):
            return c
    return HERE


HOME = _find_home()
OS_DIR = HERE
MEM = os.path.join(HOME, "memory")          # memory notes + MEMORY.md + handoff.md
WORK = os.environ.get("NQOS_WORK") or os.path.join(HERE, "work")   # hook log
HAVE_NOTES = os.path.isfile(os.path.join(MEM, "MEMORY.md"))
NO_NOTES = ("No second-brain notes found. They live in the private repo oskibundles-hue/nq-agent-channel "
            "(folder brain/): attach that repo to this session, or set NQOS_HOME to a brain folder.")

os.makedirs(WORK, exist_ok=True)
