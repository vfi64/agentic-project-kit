#!/usr/bin/env sh
set -eu

printf "### FINALIZE AFTER REPO COMMAND RUNNER MVP ###\n"

status_note='- Completed: PR #334 added repo command runner MVP and ./ns agent-run as the intended no-copy local agent handoff path.'
handoff_note='- Completed: PR #334 merged repo command runner MVP. Routine local instructions should move toward committed agent command files and ./ns agent-run; manual terminal copy-and-paste is recovery-only.'

grep -F "$status_note" docs/STATUS.md >/dev/null || printf "%s\n" "$status_note" >> docs/STATUS.md
grep -F "$handoff_note" docs/handoff/CURRENT_HANDOFF.md >/dev/null || printf "%s\n" "$handoff_note" >> docs/handoff/CURRENT_HANDOFF.md

printf "\n### VERIFY NOTES ###\n"
grep -n "PR #334" docs/STATUS.md
grep -n "PR #334" docs/handoff/CURRENT_HANDOFF.md

printf "\n### LOCAL GATE ###\n"
./ns dev

printf "\n### RESULT: PASS ###\n"
