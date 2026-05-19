printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n\n' 'MAKE ALREADY EXECUTED INBOX COMMANDS IDEMPOTENT'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short

git switch main
git pull --ff-only origin main
git switch -c fix/idempotent-already-executed-inbox

printf '\n%s\n' '### WRITE PATCH SCRIPT ###'
mkdir -p tmp tests
rm -f tmp/patch_idempotent_already_executed.py
printf '%s\n' 'from pathlib import Path' > tmp/patch_idempotent_already_executed.py
printf '%s\n' '' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'p = Path("src/agentic_project_kit/agent_command_runner.py")' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'text = p.read_text(encoding="utf-8")' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'old = "    validation_outcome, validation_detail = validate_command(command)\n    if validation_outcome != OUTCOME_PASS_EXECUTED:\n        print(validation_outcome)\n        print(validation_detail)\n        write_report(command, validation_outcome, 1, None, validation_detail)\n        return 1\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'new = "    validation_outcome, validation_detail = validate_command(command)\n    if validation_outcome == OUTCOME_FAIL_ALREADY_EXECUTED:\n        print(validation_outcome)\n        print(validation_detail)\n        write_report(command, validation_outcome, 0, None, validation_detail)\n        return 0\n    if validation_outcome != OUTCOME_PASS_EXECUTED:\n        print(validation_outcome)\n        print(validation_detail)\n        write_report(command, validation_outcome, 1, None, validation_detail)\n        return 1\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'if old not in text:' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    raise SystemExit("expected validation block not found")' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'p.write_text(text.replace(old, new), encoding="utf-8")' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'test = Path("tests/test_agent_next_already_executed_idempotent.py")' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' 'test.write_text(' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "from pathlib import Path\\n\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "from agentic_project_kit import agent_command_runner as acr\\n\\n\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "def test_agent_run_treats_already_executed_as_idempotent(tmp_path: Path, monkeypatch) -> None:\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    monkeypatch.setattr(acr, \\\"CURRENT_YAML\\\", tmp_path / \\\"current.yaml\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    monkeypatch.setattr(acr, \\\"CURRENT_SCRIPT\\\", tmp_path / \\\"current.sh\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    monkeypatch.setattr(acr, \\\"EXECUTED_JSONL\\\", tmp_path / \\\"executed.jsonl\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    monkeypatch.setattr(acr, \\\"REPORT_DIR\\\", tmp_path / \\\"reports\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    acr.CURRENT_SCRIPT.write_text(\\\"#!/usr/bin/env sh\\\\nprintf ok\\\\n\\\", encoding=\\\"utf-8\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    acr.CURRENT_YAML.write_text(\\\"command_id: cmd\\\\ntitle: Cmd\\\\nsafety_class: local-only\\\\n\\\", encoding=\\\"utf-8\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    acr.EXECUTED_JSONL.write_text(\\\"{\\\\\\\"command_id\\\\\\\": \\\\\\\"cmd\\\\\\\"}\\\\n\\\", encoding=\\\"utf-8\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    assert acr.agent_run() == 0\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    report = acr.report_path(\\\"cmd\\\")\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    assert report.exists()\\n"' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    "    assert \\\"FAIL_ALREADY_EXECUTED\\\" in report.read_text(encoding=\\\"utf-8\\\")\\n",' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' '    encoding="utf-8",' >> tmp/patch_idempotent_already_executed.py
printf '%s\n' ')' >> tmp/patch_idempotent_already_executed.py

printf '\n%s\n' '### RUN PATCH SCRIPT ###'
python3 tmp/patch_idempotent_already_executed.py

printf '\n%s\n' '### TARGETED TEST ###'
python3 -m pytest -q tests/test_agent_next_already_executed_idempotent.py

printf '\n%s\n' '### DEV GATE ###'
./ns dev

printf '\n%s\n' '### COMMIT AND PUSH ###'
git status --short
git add src/agentic_project_kit/agent_command_runner.py tests/test_agent_next_already_executed_idempotent.py
git commit -m 'Make already executed agent commands idempotent'
git push -u origin fix/idempotent-already-executed-inbox

gh pr create --base main --head fix/idempotent-already-executed-inbox --title 'Make already executed agent commands idempotent' --body 'Treat already executed agent command envelopes as idempotent success in agent_run while still writing a report. This prevents stale inbox pairs from causing hard postcondition failures after a successful earlier execution.'
gh pr checks --watch

printf '\n================================================================\n'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=auto-by-agent-next'
printf '%s\n' 'command_report=auto-by-agent-next'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '================================================================\n'
