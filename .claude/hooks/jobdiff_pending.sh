#!/bin/sh
# PostToolUse on every tool: show a pending job-diff note (job_diff_hook.py) on the lead's next call.
# A background nq-check's FAIL leaves the note in work/jobdiff-pending/; this checks that folder in the shell and
# starts Python only when it holds a note, so an ordinary tool call costs about 4 ms instead of 30 (2026-10-27).
# Agent and Task calls go to job_diff_hook.py's own entry; --pending-only keeps the two from both showing a note.
here=$(dirname "$0")
dir="${NQOS_WORK:-$here/../brain/work}/jobdiff-pending"
[ -n "$(ls -A "$dir" 2>/dev/null)" ] || exit 0
exec python3 "$here/job_diff_hook.py" --pending-only
