printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'PATCH AGENT RUN FAIL MARKER DETECTION\n\n'

TS=$(date +%Y%m%d-%H%M%S)
TMPLOG="/tmp/${TS}_patch-agent-run-fail-marker.log"
BRANCH="fix/agent-run-fail-marker-detection"
OK=1

{
  printf 'PATCH AGENT RUN FAIL MARKER DETECTION\n\n'

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
  : > tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'from pathlib import Path' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'p = Path("src/agentic_project_kit/agent_command_runner.py")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 's = p.read_text(encoding="utf-8")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'helper = """def logged_script_has_fail_result_marker(log_path: Path | None) -> bool:\n    if log_path is None or not log_path.exists():\n        return False\n    text = log_path.read_text(encoding=\"utf-8\", errors=\"replace\")\n    fail_pos = text.rfind(\"### RESULT: FAIL ###\")\n    pass_pos = text.rfind(\"### RESULT: PASS ###\")\n    return fail_pos != -1 and fail_pos > pass_pos\n\n\n"""' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'anchor = "def agent_run(extra_upload_paths: list[Path] | None = None) -> int:\n"' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'if "def logged_script_has_fail_result_marker" not in s:' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '    s = s.replace(anchor, helper + anchor, 1)' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'old = "    outcome = OUTCOME_PASS_EXECUTED if exit_code == 0 else OUTCOME_FAIL_COMMAND\n"' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'new = "    fail_marker = logged_script_has_fail_result_marker(log_path)\n    outcome = OUTCOME_PASS_EXECUTED if exit_code == 0 and not fail_marker else OUTCOME_FAIL_COMMAND\n    if fail_marker and exit_code == 0:\n        exit_code = 1\n"' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'if "fail_marker = logged_script_has_fail_result_marker(log_path)" not in s:' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '    if old not in s: raise SystemExit("outcome marker not found")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '    s = s.replace(old, new, 1)' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'p.write_text(s, encoding="utf-8")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 't = Path("tests/test_agent_command_runner.py")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 's = t.read_text(encoding="utf-8")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'if "test_logged_script_has_fail_result_marker" not in s:' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '    s += "\n\ndef test_logged_script_has_fail_result_marker(tmp_path):\n    from agentic_project_kit.agent_command_runner import logged_script_has_fail_result_marker\n    log = tmp_path / \"run.log\"\n    log.write_text(\"### RESULT: FAIL ###\\n### EXIT: 0\\n\", encoding=\"utf-8\")\n    assert logged_script_has_fail_result_marker(log)\n    log.write_text(\"### RESULT: FAIL ###\\n### RESULT: PASS ###\\n\", encoding=\"utf-8\")\n    assert not logged_script_has_fail_result_marker(log)\n"' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 't.write_text(s, encoding="utf-8")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'd = Path("docs/workflow/REPO_COMMAND_RUNNER.md")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 's = d.read_text(encoding="utf-8")' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'if "Inner fail marker detection" not in s:' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' '    s = s.rstrip() + "\n\n## Inner fail marker detection\n\n`agent-run` treats a terminal log whose last result marker is `### RESULT: FAIL ###` as `FAIL_COMMAND`, even if the shell process exits with code 0. This prevents evidence finalization or wrapper layers from masking failed command scripts as `PASS_EXECUTED`.\n"' >> tmp/patch_agent_run_fail_marker.py
  printf '%s\n' 'd.write_text(s, encoding="utf-8")' >> tmp/patch_agent_run_fail_marker.py

  printf '\n### RUN PATCH SCRIPT ###\n'
  if [ -x .venv/bin/python ]; then .venv/bin/python tmp/patch_agent_run_fail_marker.py || OK=0; else PYTHONPATH=src python3 tmp/patch_agent_run_fail_marker.py || OK=0; fi
  rm -f tmp/patch_agent_run_fail_marker.py

  printf '\n### VERIFY PATCH CONTENT ###\n'
  grep -R "logged_script_has_fail_result_marker\|Inner fail marker detection" -n src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py docs/workflow/REPO_COMMAND_RUNNER.md || OK=0

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
  git commit -m "Harden agent-run fail marker detection" || OK=0

  printf '\n### PUSH AND CREATE PR ###\n'
  git push -u origin "$BRANCH" || OK=0
  gh pr create --title "Harden agent-run fail marker detection" --body "Treats a logged inner RESULT FAIL marker as FAIL_COMMAND even when the shell exits 0." --base main --head "$BRANCH" || OK=0

  if [ "$OK" -eq 1 ]; then printf '\n### RESULT: PASS ###\n'; else printf '\n### RESULT: FAIL ###\n'; fi
} 2>&1 | tee "$TMPLOG"

printf '\n### FINALIZE TERMINAL LOG ###\n'
FINALIZE_OK=1
./ns terminal-finalize "$TMPLOG" patch-agent-run-fail-marker || FINALIZE_OK=0
git add docs/reports/terminal/LATEST_TERMINAL_LOG.txt docs/reports/terminal/*.log || FINALIZE_OK=0
git commit -m "Preserve agent-run fail marker patch log" || FINALIZE_OK=0
git push || FINALIZE_OK=0

printf '\n### FINAL LOCAL STATE ###\n'
git branch --show-current
git status --short

if [ "$OK" -eq 1 ] && [ "$FINALIZE_OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
