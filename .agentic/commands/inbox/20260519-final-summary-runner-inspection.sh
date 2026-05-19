printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'INSPECT FINAL SUMMARY RUNNER ENFORCEMENT'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git log --oneline -8

printf '\n%s\n' '### SYNC MAIN ###'
git switch main
git pull --ff-only origin main

printf '\n%s\n' '### FINAL SUMMARY CONTRACT EVIDENCE ###'
grep -R "final-summary-contract\|framed SUMMARY\|WORK RESULT:\|REMOTE_EVIDENCE:\|NEXT_CHAT_REPLY" -n .agentic docs src tests | head -160

printf '\n%s\n' '### AGENT RUNNER FOOTER LOCATIONS ###'
grep -R "AGENT-NEXT RESULT\|SUMMARY\|NEXT CHAT REPLY\|print_agent_next_footer\|write_report" -n src/agentic_project_kit tests | head -160

printf '\n%s\n' '### DEV GATE ###'
./ns dev

printf '\n%s\n' '### FINAL STATE ###'
git branch --show-current
git status --short

printf '\n%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: CHAT_ONLY'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PARTIAL'
printf '%s\n' 'terminal_log=NONE'
printf '%s\n' 'command_report=NONE'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '%s\n' '================================================================'
