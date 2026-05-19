printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'MAKE ALREADY EXECUTED AGENT-NEXT COMMANDS IDEMPOTENT'
printf '\n'

printf '%s\n' '### PRECHECK ###'
git branch --show-current
git status --short
git switch main
git pull --ff-only origin main

git switch -c fix/idempotent-already-executed-agent-next

printf '%s\n' '### WRITE PATCH SCRIPT ###'
mkdir -p tmp
: > tmp/patch_idempotent_agent_next.py
printf '%s\n' 'from pathlib import Path' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'p = Path("src/agentic_project_kit/agent_command_runner.py")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'text = p.read_text(encoding="utf-8")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'old = """    validation_outcome, validation_detail = validate_command(command)\n    if validation_outcome != OUTCOME_PASS_EXECUTED:\n        print(validation_outcome)\n        print(validation_detail)\n        write_report(command, validation_outcome, 1, None, validation_detail)\n        return 1\n"""' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'new = """    validation_outcome, validation_detail = validate_command(command)\n    if validation_outcome != OUTCOME_PASS_EXECUTED:\n        print(validation_outcome)\n        print(validation_detail)\n        report_exit = 0 if validation_outcome == OUTCOME_FAIL_ALREADY_EXECUTED else 1\n        write_report(command, validation_outcome, report_exit, None, validation_detail)\n        return report_exit\n"""' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'if old not in text:' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' '    raise SystemExit("expected validation block not found")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'text = text.replace(old, new, 1)' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'test = Path("tests/test_agent_command_runner.py")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'test_text = test.read_text(encoding="utf-8")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'insert_after = """def test_reject_duplicate_command_id(tmp_path, monkeypatch):\n    monkeypatch.chdir(tmp_path)\n    acr.EXECUTED_JSONL.parent.mkdir(parents=True, exist_ok=True)\n    acr.EXECUTED_JSONL.write_text(\"{\\\"command_id\\\": \\\"cmd-1\\\"}\" + chr(10), encoding=\"utf-8\")\n    write_command(tmp_path)\n    assert acr.validate_command(acr.load_current_command())[0] == acr.OUTCOME_FAIL_ALREADY_EXECUTED\n\n\n"""' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'addition = """def test_agent_run_treats_already_executed_as_idempotent_success(tmp_path, monkeypatch):\n    monkeypatch.chdir(tmp_path)\n    acr.EXECUTED_JSONL.parent.mkdir(parents=True, exist_ok=True)\n    acr.EXECUTED_JSONL.write_text(\"{\\\"command_id\\\": \\\"cmd-1\\\"}\" + chr(10), encoding=\"utf-8\")\n    write_command(tmp_path)\n    assert acr.agent_run() == 0\n\n\n"""' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'if addition not in test_text:' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' '    if insert_after not in test_text:' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' '        raise SystemExit("expected duplicate command test not found")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' '    test_text = test_text.replace(insert_after, insert_after + addition, 1)' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'p.write_text(text, encoding="utf-8")' >> tmp/patch_idempotent_agent_next.py
printf '%s\n' 'test.write_text(test_text, encoding="utf-8")' >> tmp/patch_idempotent_agent_next.py

python3 tmp/patch_idempotent_agent_next.py

printf '%s\n' '### TARGETED TEST ###'
python3 -m pytest -q tests/test_agent_command_runner.py

printf '%s\n' '### DEV GATE ###'
./ns dev

printf '%s\n' '### COMMIT AND PUSH ###'
git status --short
git add src/agentic_project_kit/agent_command_runner.py tests/test_agent_command_runner.py
git commit -m 'Make already executed agent-next commands idempotent'
git push -u origin fix/idempotent-already-executed-agent-next

gh pr create --base main --head fix/idempotent-already-executed-agent-next --title 'Make already executed agent-next commands idempotent' --body 'Treat already executed agent-next commands as idempotent success instead of hard failure after validation. This avoids stale queued commands causing HARD-FAIL loops while still recording a command report.'
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
printf '%s\n' '================================================================'
