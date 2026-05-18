#!/usr/bin/env sh
set -eu

printf "### FINALIZE AFTER AGENT-NEXT INBOX RUNNER ###\n"

status_note="- Completed: PR #336 added inbox-based ./ns agent-next so routine local handoff can pull and execute exactly one pending repo-backed command pair."
handoff_note="- Completed: PR #336 merged agent-next inbox mode. Preferred routine workflow is now: commit one command pair under .agentic/commands/inbox/, run ./ns agent-next locally, and use committed command-run/terminal artifacts instead of pasted terminal output."

grep -F -- "$status_note" docs/STATUS.md >/dev/null || printf "%s\n" "$status_note" >> docs/STATUS.md
grep -F -- "$handoff_note" docs/handoff/CURRENT_HANDOFF.md >/dev/null || printf "%s\n" "$handoff_note" >> docs/handoff/CURRENT_HANDOFF.md

rm -f .agentic/commands/inbox/finalize-after-agent-next-001.yaml .agentic/commands/inbox/finalize-after-agent-next-001.sh

printf "\n### VERIFY NOTES ###\n"
grep -n "PR #336" docs/STATUS.md
grep -n "PR #336" docs/handoff/CURRENT_HANDOFF.md

printf "\n### LOCAL GATE ###\n"
./ns dev

git add docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md .agentic/commands/inbox/finalize-after-agent-next-001.yaml .agentic/commands/inbox/finalize-after-agent-next-001.sh
git commit -m "Finalize state after agent-next inbox runner" || true

printf "\n### RESULT: PASS ###\n"
