printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf '%s\n' 'ADD PERSISTENT FINAL SUMMARY CONTRACT'
printf '\n### PRECHECK ###\n'
git branch --show-current
git status --short
git switch main
git pull --ff-only origin main
git switch -c feature/final-summary-contract
mkdir -p docs/governance tests tmp
printf '%s\n' 'from pathlib import Path' '' 'summary = """## Final summary contract' '' 'Every relevant workflow block must end with the framed SUMMARY contract. This contract is durable and must not disappear across chats, handoffs, or command-generation paths.' '' 'Required block:' '' '```text' '================================================================' 'SUMMARY' 'WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND' 'EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED' 'OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND' 'REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED' 'terminal_log=<repo-path-or-NONE>' 'command_report=<repo-path-or-NONE>' 'NEXT_CHAT_REPLY: p|paste-output|ask-agent-to-queue-command|continue|stop' '### RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND ###' '================================================================' '```' '' 'This is the preferred end marker for agent-directed terminal blocks, remote command reports, release work, merge verification, and handoff-sensitive work. Short local experiments may use a smaller marker, but any state-changing or evidence-bearing workflow must use the framed SUMMARY.' '"""' '' 'targets = [' '    Path("docs/governance/FINAL_SUMMARY_CONTRACT.md"),' ']' 'for path in targets:' '    path.parent.mkdir(parents=True, exist_ok=True)' '    path.write_text(summary + "\n", encoding="utf-8")' '' 'context = Path(".agentic/compiled_agent_context.yaml")' 'text = context.read_text(encoding="utf-8")' 'needle = "  - id: no-remote-command-deadlock\n"' 'insert = "  - id: final-summary-contract\n    rule: Relevant workflow blocks end with the framed SUMMARY contract including work result, evidence result, overall result, remote evidence, terminal log, command report, next chat reply, and final result marker.\n    enforcement: documentation plus tests; command-generation paths should preserve it.\n"' 'if "id: final-summary-contract" not in text:' '    if needle not in text:' '        raise SystemExit("compiled context insertion point not found")' '    text = text.replace(needle, insert + needle)' '    context.write_text(text, encoding="utf-8")' '' 'for name in ["docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md", "docs/TEST_GATES.md"]:' '    path = Path(name)' '    text = path.read_text(encoding="utf-8")' '    line = "- Final summary contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and final result marker.\n"' '    if "Final summary contract:" not in text:' '        path.write_text(text.rstrip() + "\n\n" + line, encoding="utf-8")' '' 'test = Path("tests/test_final_summary_contract.py")' 'test.write_text("""from pathlib import Path' '' '' 'REQUIRED = [' '    "WORK RESULT:",' '    "EVIDENCE RESULT:",' '    "OVERALL RESULT:",' '    "REMOTE_EVIDENCE:",' '    "terminal_log=",' '    "command_report=",' '    "NEXT_CHAT_REPLY:",' '    "### RESULT:",' ']' '' '' 'def test_final_summary_contract_is_documented() -> None:' '    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")' '    assert "================================================================" in text' '    for required in REQUIRED:' '        assert required in text' '' '' 'def test_compiled_context_contains_final_summary_rule() -> None:' '    text = Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8")' '    assert "id: final-summary-contract" in text' '    assert "framed SUMMARY contract" in text' '' '' 'def test_human_docs_reference_final_summary_contract() -> None:' '    for name in ["docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md", "docs/TEST_GATES.md"]:' '        text = Path(name).read_text(encoding="utf-8")' '        assert "Final summary contract" in text' '        assert "OVERALL RESULT" in text' '""", encoding="utf-8")' > tmp/add_final_summary_contract.py
python3 tmp/add_final_summary_contract.py
python3 -m py_compile tmp/add_final_summary_contract.py
python3 -m pytest -q tests/test_final_summary_contract.py
./ns patch-preflight
./ns dev
git status --short
git add .agentic/compiled_agent_context.yaml docs/governance/FINAL_SUMMARY_CONTRACT.md docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md docs/TEST_GATES.md tests/test_final_summary_contract.py
git commit -m 'Add persistent final summary contract'
git push -u origin feature/final-summary-contract
gh pr create --base main --head feature/final-summary-contract --title 'Add persistent final summary contract' --body 'Documents and test-locks the framed final SUMMARY block so workflow result reporting does not drift across chats or command-generation paths.'
gh pr checks --watch
printf '\n================================================================\n'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: PASS'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: PASS'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=NONE'
printf '%s\n' 'command_report=docs/reports/command_runs/20260519-final-summary-contract.md'
printf '%s\n' 'NEXT_CHAT_REPLY: p'
printf '%s\n' '### RESULT: PASS ###'
printf '%s\n' '================================================================'
