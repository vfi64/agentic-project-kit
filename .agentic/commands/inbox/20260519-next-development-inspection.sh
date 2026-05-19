#!/usr/bin/env sh

printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n\n' 'INSPECT NEXT DEVELOPMENT SLICE AFTER FLOW REPAIR'

cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline -8

printf '\n%s\n' '### SYNC MAIN ###'
git switch main
git pull --ff-only origin main

printf '\n%s\n' '### FLOW-REPAIR BASELINE EVIDENCE ###'
git log --oneline -12
grep -R "no remote command deadlock\|remote-first no-guess\|compiled_agent_context\|local-verification\|No complete pending command pair" -n .agentic docs src tests 2>/dev/null | head -120

printf '\n%s\n' '### AGENT COMMAND QUEUE STATE ###'
find .agentic/commands -maxdepth 3 -type f -print 2>/dev/null | sort

printf '\n%s\n' '### AVAILABLE NS / ACTION ENTRYPOINTS ###'
./ns actions 2>/dev/null || true

printf '\n%s\n' '### DEV GATE ###'
./ns dev
DEV_STATUS=$?

printf '\n%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short

if [ "$DEV_STATUS" -eq 0 ] && [ -z "$(git status --short)" ]; then
  printf '\n%s\n' '### RESULT: PASS ###'
  printf '%s\n' 'NEXT: choose the next small feature slice from the inspected evidence; prefer one queued command pair, not manual long terminal blocks.'
else
  printf '\n%s\n' '### RESULT: FAIL ###'
fi

printf '%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
if [ "$DEV_STATUS" -eq 0 ] && [ -z "$(git status --short)" ]; then
  printf '%s\n' 'WORK RESULT: PASS'
  printf '%s\n' 'EVIDENCE RESULT: PASS'
  printf '%s\n' 'OVERALL RESULT: PASS'
  printf '%s\n' 'REMOTE_EVIDENCE: PASS'
  printf '%s\n' 'NEXT_CHAT_REPLY: p'
  printf '%s\n' '### RESULT: PASS ###'
else
  printf '%s\n' 'WORK RESULT: FAIL'
  printf '%s\n' 'EVIDENCE RESULT: CHAT_ONLY'
  printf '%s\n' 'OVERALL RESULT: FAIL'
  printf '%s\n' 'REMOTE_EVIDENCE: FAIL'
  printf '%s\n' 'NEXT_CHAT_REPLY: paste-output'
  printf '%s\n' '### RESULT: FAIL ###'
fi
printf '%s\n' '================================================================'
