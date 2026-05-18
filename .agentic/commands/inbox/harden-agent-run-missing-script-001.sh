printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'HARDEN AGENT RUN REPORT CREATION WHEN CURRENT SCRIPT IS MISSING\n\n'

TS=$(date +%Y%m%d-%H%M%S)
TMPLOG="/tmp/${TS}_harden-agent-run-missing-script.log"
BRANCH="fix/agent-run-missing-script-report"
OK=1

{
  printf 'HARDEN AGENT RUN REPORT CREATION WHEN CURRENT SCRIPT IS MISSING\n\n'

  printf '### SYNC MAIN ###\n'
  git fetch origin main || OK=0
  git switch main || OK=0
  git pull --ff-only origin main || OK=0
  ./ns artifact-gc --execute || OK=0

  printf '\n### CREATE FEATURE BRANCH ###\n'
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then git branch -D "$BRANCH" || OK=0; fi
  git switch -c "$BRANCH" || OK=0

  printf '\n### WRITE PATCH SCRIPT ###\n'
  mkdir -p tmp
  : > tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'from pathlib import Path' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'p = Path("src/agentic_project_kit/agent_command_runner.py")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 's = p.read_text(encoding="utf-8")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'old = "def script_sha256(path: Path = CURRENT_SCRIPT) -> str:\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n"' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'new = "def script_sha256(path: Path = CURRENT_SCRIPT) -> str:\n    if not path.exists():\n        return \"missing\"\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n"' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'if old not in s:' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' '    raise SystemExit("script_sha256 marker not found")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 's = s.replace(old, new, 1)' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'p.write_text(s, encoding="utf-8")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' '' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 't = Path("tests/test_agent_command_runner.py")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 's = t.read_text(encoding="utf-8")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'if "test_script_sha256_returns_missing_when_current_script_is_gone" not in s:' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' '    s += "\n\ndef test_script_sha256_returns_missing_when_current_script_is_gone(tmp_path):\n    from agentic_project_kit.agent_command_runner import script_sha256\n    missing = tmp_path / \"missing.sh\"\n    assert script_sha256(missing) == \"missing\"\n"' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 't.write_text(s, encoding="utf-8")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' '' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'd = Path("docs/workflow/REPO_COMMAND_RUNNER.md")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 's = d.read_text(encoding="utf-8")' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'if "Missing script report robustness" not in s:' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' '    s = s.rstrip() + "\n\n## Missing script report robustness\n\n`agent-run` report creation must not crash if `.agentic/commands/current.sh` is removed during command execution. In that case the script SHA256 field is recorded as `missing` so the runner can still write durable command-run evidence and return a deterministic outcome.\n"' >> tmp/harden_agent_run_missing_script.py
  printf '%s\n' 'd.write_text(s, encoding="utf-8")' >> tmp/harden_agent_run_missing_script.py

  printf '\n### RUN PATCH SCRIPT ###\n'
  if [ -x .venv/bin/python ]; then .venv/bin/python tmp/harden_agent_run_missing_script.py || OK=0; else PYTHONPATH=src python3 tmp/harden_agent_run_missing_script.py || OK=0; fi
  rm -f tmp/harden_agent_run_missing_script.py

  printf '\n### VERIFY PATCH CONTENT ###\n'
  grep -R "missing\|Missing script report robustness\|test_script_sha256_returns_missing" -n src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py docs/workflow/REPO_COMMAND_RUNNER.md || OK=0

  printf '\n### LOCAL GATES ###\n'
  if [ -x .venv/bin/python ]; then .venv/bin/python -m pytest -q tests/test_agent_command_runner.py tests/test_command_inbox_check.py || OK=0; else PYTHONPATH=src python3 -m pytest -q tests/test_agent_command_runner.py tests/test_command_inbox_check.py || OK=0; fi
  ./ns command-inbox-check || OK=0
  ./ns state-freshness-check || OK=0
  ./ns artifact-gc || OK=0
  ./ns handoff-check || OK=0
  ./ns governance-check || OK=0
  ./ns dev || OK=0

  printf '\n### COMMIT PATCH ###\n'
  git status --short || OK=0
  git add src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py docs/workflow/REPO_COMMAND_RUNNER.md || OK=0
  git commit -m "Harden agent-run missing script report handling" || OK=0

  printf '\n### PUSH AND CREATE PR ###\n'
  git push -u origin "$BRANCH" || OK=0
  gh pr create --title "Harden agent-run missing script report handling" --body "Prevents agent-run report creation from crashing when current.sh is removed during command execution. Records missing script hash deterministically and test-backs the behavior." --base main --head "$BRANCH" || OK=0

  if [ "$OK" -eq 1 ]; then printf '\n### RESULT: PASS ###\n'; else printf '\n### RESULT: FAIL ###\n'; fi
} 2>&1 | tee "$TMPLOG"

printf '\n### FINALIZE TERMINAL LOG ###\n'
FINALIZE_OK=1
./ns terminal-finalize "$TMPLOG" harden-agent-run-missing-script || FINALIZE_OK=0
git add docs/reports/terminal/LATEST_TERMINAL_LOG.txt docs/reports/terminal/*.log || FINALIZE_OK=0
git commit -m "Preserve agent-run missing script hardening log" || FINALIZE_OK=0
git push || FINALIZE_OK=0

printf '\n### FINAL LOCAL STATE ###\n'
git branch --show-current
git status --short

if [ "$OK" -eq 1 ] && [ "$FINALIZE_OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
