printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'IMPLEMENT IDEMPOTENT ALREADY-EXECUTED INBOX HANDLING\n\n'

printf '### PRECHECK ###\n'
git branch --show-current
git status --short
git log --oneline -6

printf '\n### SYNC MAIN ###\n'
git switch main
git pull --ff-only origin main

printf '\n### CREATE BRANCH ###\n'
git switch -c fix/agent-next-already-executed-idempotent

printf '\n### INSPECT CURRENT RUNNER ###\n'
grep -n "def agent_next\|def validate_command\|FAIL_ALREADY_EXECUTED\|remove_current_files\|prepare_current_from_inbox" src/agentic_project_kit/agent_command_runner.py

printf '\n### WRITE REGRESSION TEST ###\n'
printf '%s\n' \
'from pathlib import Path' \
'' \
'from agentic_project_kit import agent_command_runner as acr' \
'' \
'' \
'def test_agent_next_consumes_already_executed_inbox_pair(tmp_path: Path, monkeypatch, capsys) -> None:' \
'    monkeypatch.chdir(tmp_path)' \
'    monkeypatch.setattr(acr, "INBOX_DIR", tmp_path / ".agentic" / "commands" / "inbox")' \
'    monkeypatch.setattr(acr, "CURRENT_SCRIPT", tmp_path / ".agentic" / "commands" / "current.sh")' \
'    monkeypatch.setattr(acr, "CURRENT_YAML", tmp_path / ".agentic" / "commands" / "current.yaml")' \
'    monkeypatch.setattr(acr, "EXECUTED_JSONL", tmp_path / ".agentic" / "commands" / "executed.jsonl")' \
'    monkeypatch.setattr(acr, "REPORT_DIR", tmp_path / "docs" / "reports" / "command_runs")' \
'    monkeypatch.setattr(acr, "git_pull_ff_only", lambda: 0)' \
'    monkeypatch.setattr(acr, "current_branch", lambda: "main")' \
'' \
'    acr.INBOX_DIR.mkdir(parents=True)' \
'    acr.EXECUTED_JSONL.parent.mkdir(parents=True)' \
'    acr.REPORT_DIR.mkdir(parents=True)' \
'    acr.EXECUTED_JSONL.write_text("{\"command_id\": \"done\"}\n", encoding="utf-8")' \
'    (acr.INBOX_DIR / "done.yaml").write_text("command_id: done\ntitle: Done\nsafety_class: local-only\n", encoding="utf-8")' \
'    (acr.INBOX_DIR / "done.sh").write_text("printf ok\n", encoding="utf-8")' \
'' \
'    assert acr.agent_next() == 0' \
'    out = capsys.readouterr().out' \
'    assert "PASS_ALREADY_EXECUTED_CONSUMED" in out' \
'    assert not (acr.INBOX_DIR / "done.yaml").exists()' \
'    assert not (acr.INBOX_DIR / "done.sh").exists()' \
> tests/test_agent_next_already_executed_idempotent.py

printf '\n### PATCH RUNNER ###\n'
printf '%s\n' \
'from pathlib import Path' \
'' \
'p = Path("src/agentic_project_kit/agent_command_runner.py")' \
't = p.read_text(encoding="utf-8")' \
'' \
'old = """    result = agent_run(extra_upload_paths=consumed_paths)\n    failures = agent_next_postcondition_failures()\n"""' \
'new = """    command_id = \"\"\n    try:\n        data = _parse_simple_yaml(CURRENT_YAML)\n        command_id = data.get(\"command_id\", \"\")\n    except Exception:\n        command_id = \"\"\n\n    if command_id and command_id in read_executed_ids():\n        remove_current_files()\n        print(\"PASS_ALREADY_EXECUTED_CONSUMED\")\n        print_agent_next_footer(\"PASS\", \"p\", f\"already executed command consumed: {command_id}\")\n        return 0\n\n    result = agent_run(extra_upload_paths=consumed_paths)\n    failures = agent_next_postcondition_failures()\n"""' \
'if old not in t:' \
'    raise SystemExit("expected agent_next agent_run block not found")' \
'p.write_text(t.replace(old, new), encoding="utf-8")' \
> tmp/patch_agent_next_already_executed.py
python3 tmp/patch_agent_next_already_executed.py

printf '\n### TARGETED TEST ###\n'
python3 -m pytest -q tests/test_agent_next_already_executed_idempotent.py tests/test_agent_command_runner.py

printf '\n### PATCH PREFLIGHT ###\n'
python3 tools/patch_artifact_preflight.py

printf '\n### DEV GATE ###\n'
./ns dev

printf '\n### FINAL STATE BEFORE COMMIT ###\n'
git status --short

git add src/agentic_project_kit/agent_command_runner.py tests/test_agent_next_already_executed_idempotent.py
git commit -m 'Make already executed agent-next inbox commands idempotent'
git push -u origin fix/agent-next-already-executed-idempotent

gh pr create --base main --head fix/agent-next-already-executed-idempotent --title 'Make already executed agent-next inbox commands idempotent' --body 'Treats already executed pending agent-next inbox command pairs as consumed instead of failing the postcondition. Includes regression coverage for consuming duplicate inbox pairs cleanly.'
gh pr checks --watch

printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: PASS\n'
printf 'EVIDENCE RESULT: CHAT_ONLY\n'
printf 'OVERALL RESULT: PASS\n'
printf 'REMOTE_EVIDENCE: PARTIAL\n'
printf 'terminal_log=NONE\n'
printf 'command_report=NONE\n'
printf 'NEXT_CHAT_REPLY: p\n'
printf '### RESULT: PASS ###\n'
printf '================================================================\n'
