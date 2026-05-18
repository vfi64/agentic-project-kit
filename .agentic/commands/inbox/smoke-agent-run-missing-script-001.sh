printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'SMOKE TEST AGENT RUN WHEN CURRENT SCRIPT IS REMOVED DURING EXECUTION\n\n'

OK=1

printf '### START STATE ###\n'
git branch --show-current || OK=0
git status --short || true
git log --oneline -6 || true

printf '\n### REMOVE CURRENT SCRIPT FILES DURING COMMAND EXECUTION ###\n'
rm -f .agentic/commands/current.sh .agentic/commands/current.yaml || OK=0
printf 'removed_current_files=yes\n'

printf '\n### REQUIRED READONLY GATES AFTER REMOVAL ###\n'
./ns state-freshness-check || OK=0
./ns artifact-gc || true
./ns governance-check || OK=0

printf '\n### EXPECTED OUTCOME ###\n'
printf 'agent_run_should_not_crash_after_current_script_removed=yes\n'
printf 'script_sha256_should_be_missing_in_command_report=yes\n'

if [ "$OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
