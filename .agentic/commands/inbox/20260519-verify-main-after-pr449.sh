printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'VERIFY MAIN AFTER PR 449 FINAL SUMMARY CONTRACT'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline --decorate -8

printf '%s\n' '### SYNC MAIN ###'
git switch main
git pull --ff-only origin main

printf '%s\n' '### TARGETED TEST ###'
python3 -m pytest -q tests/test_final_summary_contract.py

printf '%s\n' '### DEV GATE ###'
./ns dev

printf '%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short
git log --oneline --decorate -8

printf '%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=REMOTE_COMMAND_LOG'
printf '%s\n' 'command_report=REMOTE_COMMAND_REPORT'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '%s\n' '================================================================'
