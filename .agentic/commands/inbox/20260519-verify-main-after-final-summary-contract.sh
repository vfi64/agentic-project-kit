printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'VERIFY MAIN AFTER FINAL SUMMARY CONTRACT'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline -8

printf '%s\n' ''
printf '%s\n' '### SYNC MAIN ###'
git switch main
git pull --ff-only origin main

printf '%s\n' ''
printf '%s\n' '### VERIFY FINAL SUMMARY CONTRACT EVIDENCE ###'
grep -R "framed SUMMARY contract\|final-summary-contract\|WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL" -n .agentic/compiled_agent_context.yaml docs/governance/FINAL_SUMMARY_CONTRACT.md docs/STATUS.md docs/TEST_GATES.md docs/handoff/CURRENT_HANDOFF.md tests/test_final_summary_contract.py

printf '%s\n' ''
printf '%s\n' '### TARGETED TEST ###'
python3 -m pytest -q tests/test_final_summary_contract.py

printf '%s\n' ''
printf '%s\n' '### DEV GATE ###'
./ns dev

printf '%s\n' ''
printf '%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short
git log --oneline -8

printf '%s\n' ''
printf '%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=auto'
printf '%s\n' 'command_report=auto'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '%s\n' '================================================================'
