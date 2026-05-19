#!/bin/sh
status=PASS
terminal_log=docs/reports/terminal/20260519-verify-main-after-pr445.log

printf '%s\n' '' '' ''
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '' '' ''
printf '%s\n' 'VERIFY MAIN AFTER PR 445 COMPILED AGENT CONTEXT YAML'
printf '%s\n' ''

cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit || status=FAIL

printf '%s\n' '### PRECHECK ###'
git branch --show-current || status=FAIL
git status --short || status=FAIL
git log --oneline -8 || status=FAIL

printf '%s\n' ''
printf '%s\n' '### SYNC MAIN ###'
if git switch main; then
  printf '%s\n' 'switch main PASS'
else
  printf '%s\n' 'switch main FAIL'
  status=FAIL
fi
if git pull --ff-only origin main; then
  printf '%s\n' 'pull main PASS'
else
  printf '%s\n' 'pull main FAIL'
  status=FAIL
fi

printf '%s\n' ''
printf '%s\n' '### VERIFY PR 445 MERGE IN HISTORY ###'
if git log --oneline -12 | grep 'Add compiled agent context YAML (#445)'; then
  printf '%s\n' 'pr445 history PASS'
else
  printf '%s\n' 'pr445 history FAIL'
  status=FAIL
fi

printf '%s\n' ''
printf '%s\n' '### VERIFY COMPILED CONTEXT FILES ###'
if test -f .agentic/compiled_agent_context.yaml && test -f docs/governance/COMPILED_AGENT_CONTEXT.md && test -f tests/test_compiled_agent_context.py; then
  printf '%s\n' 'compiled context files PASS'
else
  printf '%s\n' 'compiled context files FAIL'
  status=FAIL
fi

printf '%s\n' ''
printf '%s\n' '### TARGETED PYTEST ###'
if ./.venv/bin/python -m pytest tests/test_compiled_agent_context.py -q; then
  printf '%s\n' 'targeted pytest PASS'
else
  printf '%s\n' 'targeted pytest FAIL'
  status=FAIL
fi

printf '%s\n' ''
printf '%s\n' '### PATCH PREFLIGHT ###'
if ./ns patch-preflight; then
  printf '%s\n' 'patch-preflight PASS'
else
  printf '%s\n' 'patch-preflight FAIL'
  status=FAIL
fi

printf '%s\n' ''
printf '%s\n' '### DEV GATE ###'
if ./ns dev; then
  printf '%s\n' 'dev PASS'
else
  printf '%s\n' 'dev FAIL'
  status=FAIL
fi

printf '%s\n' ''
printf '%s\n' '### FINAL STATE ###'
git branch --show-current || status=FAIL
git status --short || status=FAIL
git log --oneline -8 || status=FAIL

if test "$status" = PASS; then
  printf '%s\n' '================================================================'
  printf '%s\n' 'SUMMARY'
  printf '%s\n' 'WORK RESULT: PASS'
  printf '%s\n' 'EVIDENCE RESULT: PASS'
  printf '%s\n' 'OVERALL RESULT: PASS'
  printf '%s\n' 'REMOTE_EVIDENCE: PASS'
  printf '%s\n' "terminal_log=$terminal_log"
  printf '%s\n' 'command_report=docs/reports/command_runs/20260519-verify-main-after-pr445.md'
  printf '%s\n' 'NEXT_CHAT_REPLY: p'
  printf '%s\n' '### RESULT: PASS ###'
  printf '%s\n' '================================================================'
else
  printf '%s\n' '================================================================'
  printf '%s\n' 'SUMMARY'
  printf '%s\n' 'WORK RESULT: FAIL'
  printf '%s\n' 'EVIDENCE RESULT: CHAT_ONLY'
  printf '%s\n' 'OVERALL RESULT: FAIL'
  printf '%s\n' 'REMOTE_EVIDENCE: FAIL'
  printf '%s\n' "terminal_log=$terminal_log"
  printf '%s\n' 'command_report=NONE'
  printf '%s\n' 'NEXT_CHAT_REPLY: paste-output'
  printf '%s\n' '### RESULT: FAIL ###'
  printf '%s\n' '================================================================'
fi

test "$status" = PASS
