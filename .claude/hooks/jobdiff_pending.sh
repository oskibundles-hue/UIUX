#!/bin/sh
# PostToolUse on every tool: show a pending job-diff note (job_diff_hook.py) on the lead's next call.
# A background nq-check's FAIL leaves the note in work/jobdiff-pending/<session>.txt; this checks for this session's
# note in the shell and starts Python only when there is one, so an ordinary tool call costs a few ms instead of 30
# (2026-10-27). Another session's leftover note doesn't count, or every call would start Python.
# Agent and Task calls go to job_diff_hook.py's own entry; --pending-only keeps the two from both showing a note.
here=$(dirname "$0")
dir="${NQOS_WORK:-$here/../brain/work}/jobdiff-pending"
[ -n "$(ls -A "$dir" 2>/dev/null)" ] || exit 0
input=$(cat)
for f in "$dir"/*.txt; do
  id=$(basename "$f" .txt)
  case "$input" in *"\"$id\""*) printf '%s' "$input" | exec python3 "$here/job_diff_hook.py" --pending-only ;; esac
done
exit 0
