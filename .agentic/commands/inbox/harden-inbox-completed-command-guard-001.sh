printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'REJECT COMPLETED COMMAND IDS IN COMMAND INBOX CHECK\n\n'

TS=$(date +%Y%m%d-%H%M%S)
TMPLOG="/tmp/${TS}_harden-inbox-completed-command-guard.log"
BRANCH="fix/command-inbox-completed-command-guard"
OK=1

{
  printf 'REJECT COMPLETED COMMAND IDS IN COMMAND INBOX CHECK\n\n'

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
  : > tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'from pathlib import Path' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'p = Path("src/agentic_project_kit/command_inbox_check.py")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 's = p.read_text(encoding="utf-8")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'if "EXECUTED_JSONL" not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    s = s.replace("from agentic_project_kit.agent_command_runner import ALLOWED_SAFETY_CLASSES, INBOX_DIR, _parse_simple_yaml", "from agentic_project_kit.agent_command_runner import ALLOWED_SAFETY_CLASSES, EXECUTED_JSONL, INBOX_DIR, REPORT_DIR, _parse_simple_yaml")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'insert_after = "def _pending_files(inbox_dir: Path) -> tuple[list[Path], list[Path]]:\n    if not inbox_dir.exists():\n        return [], []\n    return sorted(inbox_dir.glob(\"*.yaml\")), sorted(inbox_dir.glob(\"*.sh\"))\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'helper = "\ndef completed_command_ids(report_dir: Path = REPORT_DIR, executed_jsonl: Path = EXECUTED_JSONL) -> set[str]:\n    ids: set[str] = set()\n    if report_dir.exists():\n        for path in report_dir.glob(\"*.md\"):\n            if path.name != \"LATEST_COMMAND_RUN.txt\":\n                ids.add(path.stem)\n    if executed_jsonl.exists():\n        for line in executed_jsonl.read_text(encoding=\"utf-8\").splitlines():\n            if \"\\\"command_id\\\"\" not in line:\n                continue\n            before, _, after = line.partition(\"\\\"command_id\\\"\")\n            _, _, tail = after.partition(\":\")\n            value = tail.strip().lstrip(\"\\\"\").split(\"\\\"\", 1)[0]\n            if value:\n                ids.add(value)\n    return ids\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'if "def completed_command_ids" not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    if insert_after not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '        raise SystemExit("pending files helper marker not found")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    s = s.replace(insert_after, insert_after + helper, 1)' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'old = "    complete = sorted(yaml_stems & script_stems)\n    if len(complete) > 1:\n        findings.append(\"multiple complete pending commands: \" + \", \".join(complete))\n    seen_ids: set[str] = set()\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'new = "    complete = sorted(yaml_stems & script_stems)\n    if len(complete) > 1:\n        findings.append(\"multiple complete pending commands: \" + \", \".join(complete))\n    completed_ids = completed_command_ids()\n    seen_ids: set[str] = set()\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'if old not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    raise SystemExit("complete block marker not found")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 's = s.replace(old, new, 1)' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'old = "        if not command_id:\n            findings.append(f\"{yaml_path.as_posix()}: missing command_id\")\n        elif command_id in seen_ids:\n            findings.append(f\"duplicate command_id: {command_id}\")\n        else:\n            seen_ids.add(command_id)\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'new = "        if not command_id:\n            findings.append(f\"{yaml_path.as_posix()}: missing command_id\")\n        elif command_id in seen_ids:\n            findings.append(f\"duplicate command_id: {command_id}\")\n        else:\n            seen_ids.add(command_id)\n        if command_id in completed_ids:\n            findings.append(f\"completed command still pending: {command_id}\")\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'if old not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    raise SystemExit("command id block marker not found")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 's = s.replace(old, new, 1)' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'p.write_text(s, encoding="utf-8")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 't = Path("tests/test_command_inbox_check.py")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 's = t.read_text(encoding="utf-8")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'if "test_command_inbox_check_rejects_completed_pending_command" not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    s += "\n\ndef test_command_inbox_check_rejects_completed_pending_command(tmp_path, monkeypatch):\n    import agentic_project_kit.command_inbox_check as cic\n    inbox = tmp_path / \".agentic/commands/inbox\"\n    write_pair(inbox, \"done\")\n    reports = tmp_path / \"docs/reports/command_runs\"\n    reports.mkdir(parents=True)\n    (reports / \"done.md\").write_text(\"# done\\n\", encoding=\"utf-8\")\n    monkeypatch.setattr(cic, \"REPORT_DIR\", reports)\n    monkeypatch.setattr(cic, \"EXECUTED_JSONL\", tmp_path / \"executed.jsonl\")\n    result = cic.check_command_inbox(inbox)\n    assert not result.ok\n    assert any(\"completed command still pending: done\" in item for item in result.findings)\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 't.write_text(s, encoding="utf-8")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'd = Path("docs/workflow/REPO_COMMAND_RUNNER.md")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 's = d.read_text(encoding="utf-8")' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'if "Completed command inbox guard" not in s:' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' '    s = s.rstrip() + "\n\n## Completed command inbox guard\n\n`./ns command-inbox-check` rejects a pending inbox pair if its `command_id` already has durable command-run evidence. This prevents completed remote commands from remaining on `main` as stale queue artifacts and causing later `FAIL_AMBIGUOUS_COMMANDS` runs.\n"' >> tmp/harden_inbox_completed_guard.py
  printf '%s\n' 'd.write_text(s, encoding="utf-8")' >> tmp/harden_inbox_completed_guard.py

  printf '\n### RUN PATCH SCRIPT ###\n'
  if [ -x .venv/bin/python ]; then .venv/bin/python tmp/harden_inbox_completed_guard.py || OK=0; else PYTHONPATH=src python3 tmp/harden_inbox_completed_guard.py || OK=0; fi
  rm -f tmp/harden_inbox_completed_guard.py

  printf '\n### VERIFY PATCH CONTENT ###\n'
  grep -R "completed command still pending\|Completed command inbox guard\|completed_command_ids" -n src/agentic_project_kit/command_inbox_check.py tests/test_command_inbox_check.py docs/workflow/REPO_COMMAND_RUNNER.md || OK=0

  printf '\n### LOCAL GATES ###\n'
  if [ -x .venv/bin/python ]; then .venv/bin/python -m pytest -q tests/test_command_inbox_check.py tests/test_agent_command_runner.py || OK=0; else PYTHONPATH=src python3 -m pytest -q tests/test_command_inbox_check.py tests/test_agent_command_runner.py || OK=0; fi
  ./ns command-inbox-check || OK=0
  ./ns state-freshness-check || OK=0
  ./ns artifact-gc || OK=0
  ./ns handoff-check || OK=0
  ./ns governance-check || OK=0
  ./ns dev || OK=0

  printf '\n### COMMIT PATCH ###\n'
  git status --short || OK=0
  git add src/agentic_project_kit/command_inbox_check.py tests/test_command_inbox_check.py docs/workflow/REPO_COMMAND_RUNNER.md || OK=0
  git commit -m "Reject completed commands in inbox check" || OK=0

  printf '\n### PUSH AND CREATE PR ###\n'
  git push -u origin "$BRANCH" || OK=0
  gh pr create --title "Reject completed commands in inbox check" --body "Hardens command-inbox-check so pending command pairs whose command_id already has durable command-run evidence are rejected before agent-next can hit ambiguous stale queue state." --base main --head "$BRANCH" || OK=0

  if [ "$OK" -eq 1 ]; then printf '\n### RESULT: PASS ###\n'; else printf '\n### RESULT: FAIL ###\n'; fi
} 2>&1 | tee "$TMPLOG"

printf '\n### FINALIZE TERMINAL LOG ###\n'
FINALIZE_OK=1
./ns terminal-finalize "$TMPLOG" harden-inbox-completed-command-guard || FINALIZE_OK=0
git add docs/reports/terminal/LATEST_TERMINAL_LOG.txt docs/reports/terminal/*.log || FINALIZE_OK=0
git commit -m "Preserve completed inbox guard terminal log" || FINALIZE_OK=0
git push || FINALIZE_OK=0

printf '\n### FINAL LOCAL STATE ###\n'
git branch --show-current
git status --short

if [ "$OK" -eq 1 ] && [ "$FINALIZE_OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
fi
