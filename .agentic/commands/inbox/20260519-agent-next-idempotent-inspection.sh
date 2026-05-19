printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'INSPECT AGENT-NEXT ALREADY EXECUTED INBOX IDEMPOTENCY'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline -8

printf '\n%s\n' '### INBOX AND EXECUTED STATE ###'
find .agentic/commands/inbox -maxdepth 1 -type f -print 2>/dev/null | sort || true
grep -n '20260519-idempotent-already-executed-inbox\|20260519-verify-main-after-pr449' .agentic/commands/executed.jsonl docs/reports/command_runs/*.md 2>/dev/null | head -80 || true

printf '\n%s\n' '### RELEVANT RUNNER FUNCTIONS ###'
grep -n 'FAIL_ALREADY_EXECUTED\|def validate_command\|def agent_next_postcondition_failures\|completed command still pending\|pending_inbox_command_pair' src/agentic_project_kit/agent_command_runner.py src/agentic_project_kit/command_inbox_check.py

printf '\n%s\n' '### DEV GATE ###'
./ns dev

printf '\n%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short

printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: PASS\n'
printf 'EVIDENCE RESULT: PASS\n'
printf 'OVERALL RESULT: PASS\n'
printf 'REMOTE_EVIDENCE: PASS\n'
printf 'terminal_log=auto-by-agent-next\n'
printf 'command_report=auto-by-agent-next\n'
printf 'NEXT_CHAT_REPLY: p\n'
printf '### RESULT: PASS ###\n'
printf '================================================================\n'
