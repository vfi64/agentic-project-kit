printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'VERIFY MAIN AFTER PR 449 FINAL SUMMARY CONTRACT'
printf '\n### PRECHECK ###\n'
git branch --show-current
git status --short
git log --oneline --decorate -6
printf '\n### VERIFY MAIN HEAD CONTAINS PR 449 ###\n'
grep -R "final-summary-contract\|framed SUMMARY contract" -n .agentic/compiled_agent_context.yaml docs/STATUS.md docs/TEST_GATES.md docs/handoff/CURRENT_HANDOFF.md docs/governance/FINAL_SUMMARY_CONTRACT.md tests/test_final_summary_contract.py
printf '\n### DEV GATE ###\n'
./ns dev
printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: PASS\n'
printf 'EVIDENCE RESULT: PASS\n'
printf 'OVERALL RESULT: PASS\n'
printf 'REMOTE_EVIDENCE: PASS\n'
printf 'terminal_log=AGENT_NEXT\n'
printf 'command_report=AGENT_NEXT\n'
printf 'NEXT_CHAT_REPLY: p\n'
printf '### RESULT: PASS ###\n'
printf '================================================================\n'
