printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'VERIFY AGENT-NEXT P/F FOOTER CONTRACT ON MAIN\n\n'

OK=1

printf '### START STATE ###\n'
git branch --show-current || OK=0
git status --short || true
git log --oneline -8 || true

printf '\n### SYNC MAIN ###\n'
git fetch origin main || OK=0
git switch main || OK=0
git pull --ff-only origin main || OK=0

printf '\n### VERIFY FOOTER CONTRACT FILE CONTENT ###\n'
grep -R "NEXT CHAT REPLY: PASS -> p\|NEXT CHAT REPLY: FAIL -> f\|NEXT CHAT REPLY: HARD-FAIL -> paste output\|print_agent_next_footer(\"PASS\", \"p\")" -n src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py docs/workflow/REPO_COMMAND_RUNNER.md || OK=0

printf '\n### TARGETED TESTS ###\n'
if [ -x .venv/bin/python ]; then
  .venv/bin/python -m pytest -q tests/test_agent_command_runner.py tests/test_command_inbox_check.py || OK=0
else
  PYTHONPATH=src python3 -m pytest -q tests/test_agent_command_runner.py tests/test_command_inbox_check.py || OK=0
fi

printf '\n### REQUIRED GATES ###\n'
./ns command-inbox-check || OK=0
./ns terminal-remote-preflight || OK=0
./ns state-freshness-check || OK=0
./ns artifact-gc || OK=0
./ns handoff-check || OK=0
./ns governance-check || OK=0
./ns dev || OK=0

printf '\n### FINAL STATE ###\n'
git branch --show-current
git status --short
git log --oneline -8

if [ "$OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
