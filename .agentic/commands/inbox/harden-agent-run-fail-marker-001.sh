printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'HARDEN AGENT RUN FAIL MARKER DETECTION\n\n'

OK=1

printf '### SYNC MAIN ###\n'
git fetch origin main || OK=0
git switch main || OK=0
git pull --ff-only origin main || OK=0

printf '\n### CURRENT GAP ###\n'
printf 'The previous verification log showed an inner FAIL marker followed by EXIT 0 and PASS_EXECUTED.\n'
printf 'This command preserves that gap as the next repo-backed work item; implementation should patch agent_command_runner to treat the last RESULT FAIL marker as FAIL_COMMAND.\n'

printf '\n### EVIDENCE POINTERS ###\n'
cat docs/reports/command_runs/verify-agent-next-footer-pf-001.md || OK=0
printf '\n'
cat docs/reports/terminal/20260518-222953_verify-agent-next-footer-pf-001.log | grep -n 'RESULT: FAIL\|EXIT: 0\|PASS_EXECUTED\|NEXT CHAT REPLY' || OK=0

printf '\n### READONLY GATES ###\n'
./ns command-inbox-check || OK=0
./ns state-freshness-check || OK=0
./ns artifact-gc || true
./ns handoff-check || OK=0
./ns governance-check || OK=0

printf '\n### CLASSIFICATION ###\n'
printf 'next_patch=agent_run_fail_marker_detection\n'
printf 'expected_contract=inner_RESULT_FAIL_dominates_EXIT_0\n'

if [ "$OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
