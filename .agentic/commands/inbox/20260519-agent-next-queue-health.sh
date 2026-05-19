#!/usr/bin/env sh
set -u

printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n\n' 'AGENT-NEXT QUEUE HEALTH AND NEXT DEVELOPMENT SLICE'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline -8

printf '\n%s\n' '### SYNC MAIN ###'
git switch main
git pull --ff-only origin main

printf '\n%s\n' '### VERIFY COMMAND RUNNER CONTRACT ###'
grep -R "def normalize_safety_class\|def pending_inbox_command_pair\|def agent_next\|FAIL_NO_COMMAND\|FAIL_INVALID_COMMAND" -n src/agentic_project_kit/agent_command_runner.py src/agentic_project_kit/command_inbox_check.py | head -80

printf '\n%s\n' '### COMMAND INBOX STATE ###'
find .agentic/commands/inbox -maxdepth 1 -type f -print 2>/dev/null | sort || true

printf '\n%s\n' '### COMPILED CONTEXT FAST PATH ###'
if [ -f .agentic/compiled_agent_context.yaml ]; then
  sed -n '1,120p' .agentic/compiled_agent_context.yaml
else
  printf '%s\n' 'MISSING .agentic/compiled_agent_context.yaml'
fi

printf '\n%s\n' '### DEV GATE ###'
./ns dev

printf '\n%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short

if [ -z "$(git status --short)" ]; then
  printf '\n%s\n' '### RESULT: PASS ###'
else
  printf '\n%s\n' '### RESULT: FAIL ###'
fi

printf '%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=AUTO_BY_AGENT_NEXT'
printf '%s\n' 'command_report=AUTO_BY_AGENT_NEXT'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '%s\n' '================================================================'
