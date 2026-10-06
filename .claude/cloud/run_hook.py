#!/usr/bin/env python3
"""Run one NQ OS hook from the user-level install, unless the session's own project already runs it.

Called from ~/.claude/settings.json (written by install.py): python3 run_hook.py .claude/hooks/cost_guard.py

When a session opens inside the uiux repo, the repo's .claude/settings.json runs the same hooks. Running both
would make the regret gate ask twice and the cost guard count every call twice, so if the project folder
carries this hook and its own settings file, exit 0 and let the project's copy run. Otherwise run the
installed copy with the same stdin and arguments.
"""
import os
import sys

rel = sys.argv[1]
project = os.environ.get("CLAUDE_PROJECT_DIR", "")
if project and os.path.isfile(os.path.join(project, rel)) \
        and os.path.isfile(os.path.join(project, ".claude", "settings.json")):
    sys.exit(0)
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.execv(sys.executable, [sys.executable, os.path.join(root, rel)] + sys.argv[2:])
