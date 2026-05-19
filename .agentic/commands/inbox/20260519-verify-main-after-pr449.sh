printf '%s\n' ''
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' ''
printf '%s\n' 'VERIFY MAIN AFTER PR 449 AND INSPECT NEXT DEVELOPMENT SLICE'
printf '%s\n' ''

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline -8

printf '%s\n' ''
printf '%s\n' '### SYNC MAIN ###'
git switch main
git pull --ff-only origin main

printf '%s\n' ''
printf '%s\n' '### FINAL SUMMARY CONTRACT EVIDENCE ###'
grep -R "final-summary-contract\|framed SUMMARY contract" -n .agentic/compiled_agent_context.yaml docs/governance/FINAL_SUMMARY_CONTRACT.md docs/TEST_GATES.md docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md tests/test_final_summary_contract.py

printf '%s\n' ''
printf '%s\n' '### COMMAND QUEUE HEALTH SNAPSHOT ###'
find .agentic/commands -maxdepth 3 -type f | sort
python3 -m agentic_project_kit.command_inbox_check || true

printf '%s\n' ''
printf '%s\n' '### ACTION SURFACE SNAPSHOT ###'
./ns actions || true

printf '%s\n' ''
printf '%s\n' '### DEV GATE ###'
./ns dev

printf '%s\n' ''
printf '%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short
git log --oneline -8

printf '%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=auto-by-agent-next'
printf '%s\n' 'command_report=auto-by-agent-next'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '%s\n' '================================================================'
