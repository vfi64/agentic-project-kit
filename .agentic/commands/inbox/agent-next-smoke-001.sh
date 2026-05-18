#!/usr/bin/env sh
set -eu

printf "### AGENT-NEXT SMOKE TEST ###\n"

printf "\n### BRANCH ###\n"
git branch --show-current

printf "\n### VERIFY AGENT-NEXT COMMANDS ###\n"
./ns cockpit-readiness | sed -n "1,260p"

printf "\n### LOCAL GATE ###\n"
./ns dev

printf "\n### RECORD CONSUMED INBOX COMMAND ###\n"
git add -u .agentic/commands/inbox
if git diff --cached --quiet; then
  printf "No inbox deletion to commit.\n"
else
  git commit -m "Consume agent-next smoke command"
fi

printf "\n### RESULT: PASS ###\n"
