#!/usr/bin/env python3
"""Paths for the cloud copy of the second brain (recall.py, recall_hook.py).

On the Mac everything lives under ~/.nqos. In this repo it lives next to this file:
    memory/  the notes and their MEMORY.md index
    work/    the hook's prompt log (git-ignored, lost with the container)
Set NQOS_HOME to point the tools at another brain folder (for example ~/.nqos on the Mac).
"""
import os

HOME = os.environ.get("NQOS_HOME") or os.path.dirname(os.path.abspath(__file__))
OS_DIR = HOME
MEM = os.path.join(HOME, "memory")          # memory notes + MEMORY.md + handoff.md
WORK = os.path.join(HOME, "work")           # hook log

for _d in (MEM, WORK):
    os.makedirs(_d, exist_ok=True)
