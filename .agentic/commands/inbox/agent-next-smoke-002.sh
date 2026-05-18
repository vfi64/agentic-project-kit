#!/usr/bin/env sh
set -eu

printf "### AGENT-NEXT CONSUMPTION SMOKE TEST ###\n"
printf "\n### VERIFY INBOX PAIR WAS CONSUMED BEFORE SCRIPT RUN ###\n"
test ! -e .agentic/commands/inbox/agent-next-smoke-002.yaml
test ! -e .agentic/commands/inbox/agent-next-smoke-002.sh
printf "Inbox pair consumed.\n"
printf "\n### LOCAL GATE ###\n"
./ns dev
printf "\n### RESULT: PASS ###\n"
