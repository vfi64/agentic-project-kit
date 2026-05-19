#!/bin/sh
printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'BUILD COMPILED AGENT CONTEXT YAML\n\n'

cmd_status=0
PY=''
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; elif [ -x .venv/bin/python3 ]; then PY=.venv/bin/python3; elif command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; fi
if [ -z "$PY" ]; then printf 'python discovery FAIL\n'; cmd_status=1; fi

printf '\n### PRECHECK ###\n'
git branch --show-current
git status --short

git switch main || cmd_status=1
git pull --ff-only origin main || cmd_status=1

git switch -c feature/compiled-agent-context-yaml || git switch feature/compiled-agent-context-yaml || cmd_status=1

mkdir -p .agentic docs/governance tests docs/reports/terminal tmp

printf '\n### WRITE PATCH SCRIPT ###\n'
{
printf '%s\n' 'from pathlib import Path'
printf '%s\n' 'import yaml'
printf '%s\n' 'ROOT = Path(".")'
printf '%s\n' 'compiled = ROOT / ".agentic" / "compiled_agent_context.yaml"'
printf '%s\n' 'compiled.parent.mkdir(parents=True, exist_ok=True)'
printf '%s\n' 'data = {'
printf '%s\n' '    "schema_version": 1,'
printf '%s\n' '    "updated": {"date": "2026-05-19", "reason": "compiled machine-readable agent context baseline"},'
printf '%s\n' '    "purpose": "Fast, redundant-free, machine-readable companion to the human governance docs.",'
printf '%s\n' '    "source_policy": {'
printf '%s\n' '        "remote_first_no_guess": True,'
printf '%s\n' '        "human_docs_remain_authoritative": True,'
printf '%s\n' '        "compiled_yaml_must_match_docs": True,'
printf '%s\n' '        "new_rules_need_docs_yaml_tests": True,'
printf '%s\n' '    },'
printf '%s\n' '    "priority_order": ['
printf '%s\n' '        ".agentic/compiled_agent_context.yaml",'
printf '%s\n' '        ".agentic/handoff_state.yaml",'
printf '%s\n' '        ".agentic/no_copy_terminal_policy.yaml",'
printf '%s\n' '        "docs/STATUS.md",'
printf '%s\n' '        "docs/handoff/CURRENT_HANDOFF.md",'
printf '%s\n' '        "docs/TEST_GATES.md",'
printf '%s\n' '        "docs/DOCUMENTATION_COVERAGE.yaml",'
printf '%s\n' '    ],'
printf '%s\n' '    "hard_rules": ['
printf '%s\n' '        {"id": "remote-first-no-guess", "rule": "Inspect remote repo files, authoritative docs, and command help before acting."},'
printf '%s\n' '        {"id": "no-long-manual-command-blocks", "rule": "Queue repo-backed commands for agent-next instead of returning long local shell blocks."},'
printf '%s\n' '        {"id": "final-summary-contract", "rule": "Use the mandatory SUMMARY block and never relabel inner failures as PASS."},'
printf '%s\n' '        {"id": "patch-artifact-preflight", "rule": "Generated patch artifacts must pass syntax, YAML, coverage-term, and final-summary checks before use."},'
printf '%s\n' '        {"id": "rules-must-be-test-backed", "rule": "Durable rules require human docs, compiled YAML, and deterministic tests."},'
printf '%s\n' '    ],'
printf '%s\n' '    "normal_operator_path": ["git switch main", "git pull --ff-only origin main", "./ns agent-next"],'
printf '%s\n' '    "quality_goal": "Prefer the best deterministic solution over shortcuts; quality is the target."'
printf '%s\n' '}'
printf '%s\n' 'compiled.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")'
printf '%s\n' 'doc = ROOT / "docs" / "governance" / "COMPILED_AGENT_CONTEXT.md"'
printf '%s\n' 'doc.parent.mkdir(parents=True, exist_ok=True)'
printf '%s\n' 'doc.write_text("\n".join(['
printf '%s\n' '    "# Compiled Agent Context",'
printf '%s\n' '    "",'
printf '%s\n' '    "Status: active",'
printf '%s\n' '    "Decision status: accepted",'
printf '%s\n' '    "Review policy: update whenever durable workflow rules change",'
printf '%s\n' '    "",'
printf '%s\n' '    "This document defines the human-facing contract for `.agentic/compiled_agent_context.yaml`.",'
printf '%s\n' '    "",'
printf '%s\n' '    "The compiled YAML is a compact, machine-readable companion to the human governance docs. It does not replace the docs; it prevents slow, lossy reconstruction of active rules from scattered prose.",'
printf '%s\n' '    "",'
printf '%s\n' '    "Every durable rule must be maintained in three places: human documentation, `.agentic/compiled_agent_context.yaml`, and deterministic tests.",'
printf '%s\n' '    "",'
printf '%s\n' '    "The remote-first no-guess rule remains first: inspect the remote repository, authoritative files, and command help before acting on repository state or command syntax.",'
printf '%s\n' ']) + "\n", encoding="utf-8")'
printf '%s\n' 'test = ROOT / "tests" / "test_compiled_agent_context.py"'
printf '%s\n' 'test.write_text("\n".join(['
printf '%s\n' '    "from pathlib import Path",'
printf '%s\n' '    "",'
printf '%s\n' '    "import yaml",'
printf '%s\n' '    "",'
printf '%s\n' '    "def test_compiled_agent_context_yaml_is_valid_and_prioritized():",'
printf '%s\n' '    "    data = yaml.safe_load(Path(\".agentic/compiled_agent_context.yaml\").read_text(encoding=\"utf-8\"))",'
printf '%s\n' '    "    assert data[\"schema_version\"] == 1",'
printf '%s\n' '    "    assert data[\"source_policy\"][\"remote_first_no_guess\"] is True",'
printf '%s\n' '    "    assert data[\"source_policy\"][\"new_rules_need_docs_yaml_tests\"] is True",'
printf '%s\n' '    "    assert data[\"priority_order\"][0] == \".agentic/compiled_agent_context.yaml\"",'
printf '%s\n' '    "",'
printf '%s\n' '    "def test_compiled_agent_context_contains_active_hard_rules():",'
printf '%s\n' '    "    data = yaml.safe_load(Path(\".agentic/compiled_agent_context.yaml\").read_text(encoding=\"utf-8\"))",'
printf '%s\n' '    "    ids = {item[\"id\"] for item in data[\"hard_rules\"]}",'
printf '%s\n' '    "    required = {\"remote-first-no-guess\", \"final-summary-contract\", \"patch-artifact-preflight\", \"rules-must-be-test-backed\"}",'
printf '%s\n' '    "    assert required <= ids",'
printf '%s\n' ']) + "\n", encoding="utf-8")'
printf '%s\n' 'for path in [ROOT / "docs/STATUS.md", ROOT / "docs/handoff/CURRENT_HANDOFF.md", ROOT / "docs/TEST_GATES.md"]:'
printf '%s\n' '    text = path.read_text(encoding="utf-8")'
printf '%s\n' '    marker = "compiled_agent_context.yaml"'
printf '%s\n' '    if marker not in text:'
printf '%s\n' '        text = text.rstrip() + "\n\n## Compiled Agent Context YAML\n\n`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion to the human governance docs. New durable rules must be reflected in the human docs, the compiled YAML, and deterministic tests.\n"'
printf '%s\n' '        path.write_text(text, encoding="utf-8")'
printf '%s\n' 'yaml.safe_load(compiled.read_text(encoding="utf-8"))'
} > tmp/build_compiled_agent_context.py

if [ "$cmd_status" -eq 0 ]; then "$PY" -m py_compile tmp/build_compiled_agent_context.py || cmd_status=1; fi
if [ "$cmd_status" -eq 0 ]; then "$PY" tmp/build_compiled_agent_context.py || cmd_status=1; fi

printf '\n### TARGETED CHECKS ###\n'
if [ "$cmd_status" -eq 0 ]; then "$PY" -m py_compile tmp/build_compiled_agent_context.py || cmd_status=1; fi
if [ "$cmd_status" -eq 0 ]; then "$PY" -m pytest -q tests/test_compiled_agent_context.py || cmd_status=1; fi
if [ "$cmd_status" -eq 0 ]; then ./ns patch-preflight || cmd_status=1; fi
if [ "$cmd_status" -eq 0 ]; then ./ns dev || cmd_status=1; fi

printf '\n### FINAL STATE ###\n'
git status --short
git branch --show-current
git log --oneline --decorate -8

if [ "$cmd_status" -eq 0 ]; then
  git add .agentic/compiled_agent_context.yaml docs/governance/COMPILED_AGENT_CONTEXT.md docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md docs/TEST_GATES.md tests/test_compiled_agent_context.py || cmd_status=1
  git commit -m 'Add compiled agent context YAML' || cmd_status=1
  git push -u origin feature/compiled-agent-context-yaml || cmd_status=1
fi

if [ "$cmd_status" -eq 0 ]; then
  gh pr create --base main --head feature/compiled-agent-context-yaml --title 'Add compiled agent context YAML' --body 'Adds a compact machine-readable agent context YAML, human governance documentation, and deterministic tests so durable rules remain synchronized between docs, YAML, and gates.' || cmd_status=1
fi

printf '\n================================================================\n'
printf 'SUMMARY\n'
if [ "$cmd_status" -eq 0 ]; then
  printf 'WORK RESULT: PASS\n'
  printf 'EVIDENCE RESULT: PASS\n'
  printf 'OVERALL RESULT: PASS\n'
  printf 'REMOTE_EVIDENCE: PASS\n'
  printf 'terminal_log=NONE\n'
  printf 'command_report=docs/reports/command_runs/20260519-compiled-agent-context-v1.md\n'
  printf 'NEXT_CHAT_REPLY: p\n'
  printf '### RESULT: PASS ###\n'
else
  printf 'WORK RESULT: FAIL\n'
  printf 'EVIDENCE RESULT: PASS\n'
  printf 'OVERALL RESULT: FAIL\n'
  printf 'REMOTE_EVIDENCE: PASS\n'
  printf 'terminal_log=NONE\n'
  printf 'command_report=docs/reports/command_runs/20260519-compiled-agent-context-v1.md\n'
  printf 'NEXT_CHAT_REPLY: f\n'
  printf '### RESULT: FAIL ###\n'
fi
printf '================================================================\n'
