printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'HARDEN COMMAND INBOX LIFECYCLE CLEANUP AFTER COMPLETED RUNS\n\n'

OK=1

printf '### SYNC MAIN ###\n'
git fetch origin main || OK=0
git switch main || OK=0
git pull --ff-only origin main || OK=0

printf '\n### DIAGNOSE CURRENT INBOX STATE ###\n'
find .agentic/commands/inbox -maxdepth 1 -type f -print | sort || true

printf '\n### VERIFY COMPLETED RUNS CONSUME THEIR INBOX PAIRS ###\n'
if [ -f docs/reports/command_runs/smoke-agent-run-missing-script-001.md ]; then printf 'completed_smoke_report=present\n'; else OK=0; fi
if find .agentic/commands/inbox -maxdepth 1 -type f -name 'smoke-agent-run-missing-script-001.*' | grep .; then printf 'FAIL_STALE_COMPLETED_SMOKE_PAIR\n'; OK=0; else printf 'PASS_NO_STALE_COMPLETED_SMOKE_PAIR\n'; fi

printf '\n### REQUIRED GATES ###\n'
./ns command-inbox-check || OK=0
./ns state-freshness-check || OK=0
./ns artifact-gc || true
./ns handoff-check || OK=0
./ns governance-check || OK=0

printf '\n### CLASSIFICATION ###\n'
printf 'next_patch_needed=make_completed_inbox_pair_absence_machine_checked\n'
printf 'reason=completed commands should not remain pending on main and cause FAIL_AMBIGUOUS_COMMANDS\n'
printf 'suggested_gate=command-inbox-check should reject pending files whose command_id already appears in executed.jsonl or docs/reports/command_runs\n'

if [ "$OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
