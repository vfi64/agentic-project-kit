# Current workflow output

Date: 2026-05-12
Branch: feature/plan-v0.3.0-output-repair

## Purpose

Start v0.3.0 planning for a bounded output-repair pipeline.

## Current main
ac7699f Update docs with v0.2.11 Zenodo DOI (#112)
e5f33b4 Fix v0.2.11 citation version drift (#111)
8fa1e8f Prepare v0.2.11 release metadata (#110)
4a50e30 Clean up transient workflow reports (#109)
cc57509 Document current workflow output handoff file (#108)
ee6d088 Document report schema option in generated wrapper docs (#107)
89b7408 Record status roadmap after PR 105 (#106)
92a0a02 Document collaboration rules and report schema E2E (#105)
6b61956 Validate output reports against generated schema (#104)
399dd4f Document output transfer rule for agent workflows (#103)
6c27019 Finalize docs after v0.2.10 release (#102)
81ffe39 Update docs with v0.2.10 Zenodo DOI (#101)

## Existing output-contract and validation code
docs/reports/report_schema_docs_slice_20260512.md
docs/reports/report_schema_e2e_and_collab_rules_20260512.md
src/agentic_project_kit/__pycache__/checks.cpython-314.pyc
src/agentic_project_kit/__pycache__/contract.cpython-314.pyc
src/agentic_project_kit/__pycache__/doctor.cpython-314.pyc
src/agentic_project_kit/__pycache__/output_contract.cpython-314.pyc
src/agentic_project_kit/__pycache__/runtime_validator.cpython-314.pyc
src/agentic_project_kit/checks.py
src/agentic_project_kit/contract.py
src/agentic_project_kit/doctor.py
src/agentic_project_kit/output_contract.py
src/agentic_project_kit/runtime_validator.py
tests/__pycache__/test_checks.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_contract.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_doctor.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_output_contract.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_runtime_validator_cli.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_runtime_validator.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_validate_contract_cli.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_validate_output_contract_cli.cpython-314-pytest-9.0.3.pyc
tests/test_checks.py
tests/test_contract.py
tests/test_doctor.py
tests/test_output_contract.py
tests/test_runtime_validator_cli.py
tests/test_runtime_validator.py
tests/test_validate_contract_cli.py
tests/test_validate_output_contract_cli.py

## Existing repair/validation references
src/agentic_project_kit/output_contract.py:1:"""Machine-readable output contract primitives.
src/agentic_project_kit/output_contract.py:21:    """Minimal machine-readable output contract."""
src/agentic_project_kit/output_contract.py:29:    """Load a minimal output contract from YAML."""
src/agentic_project_kit/output_contract.py:40:        raise ValueError("output contract must be a mapping")
src/agentic_project_kit/output_contract.py:47:        raise ValueError("output contract version must be 1")
src/agentic_project_kit/output_contract.py:49:        raise ValueError("output contract name is required")
src/agentic_project_kit/templates.py:8:BASE_FILES = {'README.md': '# $name\n\n$description\n\n## Purpose\n\nDescribe the purpose of the project here.\n\n## Quick Start\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\n```\n\n## Agentic Development\n\nThis project uses agent-facing documentation and local quality gates.\n\nStart with:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Status\n\nDo not store volatile status in this README. Use `docs/STATUS.md`.\n', 'AGENTS.md': '# AGENTS.md\n\n## Mission\n\nPreserve correctness, traceability, testability, and maintainability.\n\nDo not only satisfy the immediate request. Prefer the best technically sound solution within project constraints.\n\n## Source-of-truth hierarchy\n\n1. `.agentic/project.yaml`\n2. normative project specification, if present\n3. current code and tests\n4. `docs/STATUS.md`\n5. `docs/handoff/CURRENT_HANDOFF.md`\n6. historical archive files\n\nIf documentation, code, and tests disagree, report the discrepancy instead of guessing.\n\n## Agent read order\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/LOGGING_AND_EVIDENCE.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n8. relevant source files and tests\n\n## Work rules\n\n- Keep stable rules separate from volatile status.\n- Add or update tests for meaningful behavior changes.\n- Prefer outcome evidence over output claims.\n- Do not claim success without running the relevant gates.\n- Do not commit secrets, local credentials, or broad raw logs.\n- Use bounded diagnostic logs only when needed for troubleshooting.\n\n## Closeout template\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Changed files:\n- Tests run:\n- Tests not run:\n- Remaining risks:\n- Next safe step:\n```\n', 'docs/PROJECT_START.md': '# Project Start\n\n## Purpose\n\nThis file guides the initial setup after repository generation.\n\n## Generated Structure\n\nThis project was generated with agent-facing documentation, a machine-readable project contract, status and handoff files, a test-gate matrix, bootstrap task items, logging/evidence conventions, and optional GitHub workflow/pre-commit templates.\n\n## Required First Decisions\n\n- [ ] Review `.agentic/project.yaml` profiles and policy packs.\n- [ ] Choose or confirm project license.\n- [ ] Define the primary runtime entrypoint.\n- [ ] Define supported runtime versions.\n- [ ] Decide whether bounded diagnostic logs may be committed.\n- [ ] Define protected branches.\n- [ ] Define release strategy.\n- [ ] Review agent instructions.\n\n## First Local Commands\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## First GitHub Setup\n\n- [ ] Create GitHub repository.\n- [ ] Push initial commit.\n- [ ] Enable branch protection for `main`.\n- [ ] Enable GitHub Actions.\n- [ ] Enable secret scanning if available.\n- [ ] Review `.github/copilot-instructions.md`.\n\n## Agent Onboarding\n\nA new agent should read:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `.github/copilot-instructions.md`\n4. `docs/PROJECT_START.md`\n5. `docs/STATUS.md`\n6. `docs/TEST_GATES.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Before First Feature\n\n- [ ] Update `README.md` with the real project goal.\n- [ ] Update `docs/STATUS.md`.\n- [ ] Update `docs/TEST_GATES.md`.\n- [ ] Add first meaningful tests.\n- [ ] Run all checks.\n', 'docs/STATUS.md': '# Project Status\n\nStatus-date: TODO\nProject: $name\nPrimary branch: main\nRuntime entrypoint: TODO\nProject contract: `.agentic/project.yaml`\n\n## Purpose\n\nThis is the compact current-state dashboard.\n\nIt must not become a long history file.\n\n## Current Goal\n\nTODO: define the current project goal.\n\n## Current Blockers\n\n- TODO\n\n## Live Status Commands\n\n```bash\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## Next Safe Step\n\nTODO\n', 'docs/TEST_GATES.md': '# Test Gates\n\n## Purpose\n\nThis file maps task types to required evidence.\n\n## Gate Matrix\n\n| Change type | Required evidence |\n|---|---|\n| Documentation only | `agentic-kit check-docs` |\n| task/status change | `agentic-kit check-todo` |\n| Project contract/profile change | `agentic-kit doctor` |\n| Python code | `pytest -q` and `ruff check .` if enabled |\n| CLI behavior | CLI tests plus local command smoke test |\n| Logging/evidence change | check generated logs for secrets and size |\n| GitHub workflow change | local syntax review and CI run |\n| Agent workflow change | docs check and handoff review |\n\n## Outcome Reporting\n\nUse this closeout shape:\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Evidence:\n- Remaining gap:\n- Tests run:\n- Tests not run:\n```\n', 'docs/LOGGING_AND_EVIDENCE.md': '# Logging and Evidence\n\n## Purpose\n\nLogs are diagnostic evidence, not automatic source material.\n\n## Recommended Layout\n\n```text\nLogs/\n  Audit/\n  ManualTests/\n  TestRuns/\ntmp/\n  agent-evidence/\n```\n\n## Rules\n\n- Do not commit secrets.\n- Do not commit broad raw logs by default.\n- Commit only bounded recent evidence when needed.\n- Inspect staged logs before committing.\n- Validation reports from `agentic-kit validate-output-contract --report` are bounded audit evidence when they are intentionally written to a reviewed path such as `tmp/agent-evidence/` or a PR-specific evidence folder.\n- Do not auto-stage validation reports by default; inspect them before committing.\n\n## Agent Use\n\nAgents should use logs to diagnose failures, not to infer undocumented project rules.\n', 'docs/handoff/CURRENT_HANDOFF.md': '# Current Handoff\n\nStatus-date: TODO\nProject: $name\nBranch: main\nProject contract: `.agentic/project.yaml`\n\n## Current goal\n\nTODO\n\n## Current source of truth\n\n1. `.agentic/project.yaml`\n2. `AGENTS.md`\n3. `docs/STATUS.md`\n4. current code and tests\n\n## Latest closeout\n\nNo closeout yet.\n\n## Next step\n\nTODO\n', 'docs/handoff/STANDARD_AGENT_PROMPT.md': '# Standard Agent Prompt\n\n```text\nYou are working in this repository.\n\nStart by reading:\n\n1. AGENTS.md\n2. .agentic/project.yaml\n3. docs/PROJECT_START.md\n4. docs/STATUS.md\n5. docs/TEST_GATES.md\n6. docs/handoff/CURRENT_HANDOFF.md\n\nDo not infer current state from memory.\nRun or request:\n\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n\nFor substantial work, close with:\n\n- Intended outcome:\n- Required evidence:\n- Outcome achieved:\n- Changed files:\n- Tests run:\n- Remaining risks:\n```\n', 'docs/TODO.md': '# TODO\n\nThis file is generated from `.agentic/todo.yaml`.\n\n## Bootstrap\n\n- [ ] **BOOT-001** Choose or confirm license  \n  Owner: human  \n  Priority: high  \n  Evidence required: `LICENSE` reviewed\n\n- [ ] **BOOT-002** Define runtime entrypoint  \n  Owner: human  \n  Priority: high  \n  Evidence required: `README.md` and `docs/STATUS.md` updated\n\n- [ ] **BOOT-003** Run initial local quality gate  \n  Owner: agent  \n  Priority: high  \n  Evidence required: `pytest -q` and `agentic-kit check` passed\n\n- [ ] **BOOT-004** Review project contract profiles and policy packs  \n  Owner: human  \n  Priority: high  \n  Evidence required: `.agentic/project.yaml` reviewed\n\n- [ ] **BOOT-005** Enable branch protection on GitHub  \n  Owner: human  \n  Priority: medium  \n  Evidence required: branch protection enabled\n', '.agentic/todo.yaml': 'items:\n  - id: BOOT-001\n    title: Choose or confirm license\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: LICENSE reviewed\n  - id: BOOT-002\n    title: Define runtime entrypoint\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: README.md and docs/STATUS.md updated\n  - id: BOOT-003\n    title: Run initial local quality gate\n    owner: agent\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: pytest -q and agentic-kit check passed\n  - id: BOOT-004\n    title: Review project contract profiles and policy packs\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: .agentic/project.yaml reviewed\n  - id: BOOT-005\n    title: Enable branch protection on GitHub\n    owner: human\n    priority: medium\n    status: open\n    blocking: false\n    evidence_required: branch protection enabled\n', 'sentinel.yaml': 'documents:\n  - path: README.md\n    required_sections:\n      - "## Purpose"\n      - "## Quick Start"\n    max_words: 2000\n  - path: AGENTS.md\n    required_sections:\n      - "## Mission"\n      - "## Agent read order"\n      - "## Closeout template"\n    max_words: 2500\n  - path: docs/STATUS.md\n    required_sections:\n      - "## Current Goal"\n      - "## Next Safe Step"\n    max_words: 1200\n  - path: docs/TEST_GATES.md\n    required_sections:\n      - "## Gate Matrix"\n      - "## Outcome Reporting"\n    max_words: 1600\ntodo:\n  path: .agentic/todo.yaml\n', '.github/copilot-instructions.md': '# Copilot Instructions\n\nFollow the repository rules in `AGENTS.md`.\n\nBefore claiming completion, run or request the relevant commands from `docs/TEST_GATES.md`.\n\nDo not commit secrets, broad raw logs, virtual environments, or local-only configuration.\n', '.github/pull_request_template.md': '## Intended outcome\n\n## Required evidence\n\n## Outcome achieved\n\n- [ ] yes\n- [ ] no\n- [ ] partial\n\n## Tests run\n\n## Risks / remaining gaps\n', '.github/ISSUE_TEMPLATE/agent_regression.yml': 'name: Agent regression\ndescription: Report an agent workflow or handoff regression\ntitle: "[Agent Regression]: "\nlabels: ["agent", "regression"]\nbody:\n  - type: textarea\n    id: observed\n    attributes:\n      label: Observed behavior\n    validations:\n      required: true\n  - type: textarea\n    id: expected\n    attributes:\n      label: Expected behavior\n    validations:\n      required: true\n  - type: textarea\n    id: evidence\n    attributes:\n      label: Evidence / logs\n    validations:\n      required: false\n', 'scripts/stage_recent_logs.py': 'from pathlib import Path\nimport shutil\n\nLOG_ROOTS = [Path("Logs/Audit"), Path("Logs/ManualTests"), Path("Logs/TestRuns")]\nTARGET = Path("tmp/agent-evidence")\n\n\ndef main(max_files: int = 10) -> None:\n    TARGET.mkdir(parents=True, exist_ok=True)\n    for root in LOG_ROOTS:\n        if not root.exists():\n            continue\n        files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.stat().st_mtime)\n        for src in files[-max_files:]:\n            rel = src.relative_to(root)\n            dst = TARGET / root.name / rel\n            dst.parent.mkdir(parents=True, exist_ok=True)\n            shutil.copy2(src, dst)\n    print(f"Staged bounded evidence in {TARGET}")\n\n\nif __name__ == "__main__":\n    main()\n'}
src/agentic_project_kit/templates.py:18:- Define explicit output schemas before relying on generated content.
src/agentic_project_kit/templates.py:21:- Do not silently repair meaning-changing output errors.
src/agentic_project_kit/templates.py:31:VALIDATION_REPORT_SCHEMA_JSON = '{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "additionalProperties": false,\n  "properties": {\n    "checked_file": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract_version": {\n      "minimum": 1,\n      "type": "integer"\n    },\n    "findings": {\n      "items": {\n        "additionalProperties": false,\n        "properties": {\n          "code": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "message": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "severity": {\n            "enum": [\n              "info",\n              "warning",\n              "error"\n            ],\n            "type": "string"\n          }\n        },\n        "required": [\n          "severity",\n          "code",\n          "message"\n        ],\n        "type": "object"\n      },\n      "type": "array"\n    },\n    "ok": {\n      "type": "boolean"\n    }\n  },\n  "required": [\n    "ok",\n    "contract",\n    "contract_version",\n    "checked_file",\n    "findings"\n  ],\n  "title": "agentic-project-kit validation report",\n  "type": "object"\n}\n'
src/agentic_project_kit/templates.py:42:VALIDATION_AND_REPAIR = """# Validation and Repair
src/agentic_project_kit/templates.py:46:This document records validation and bounded repair rules for governance-wrapper projects.
src/agentic_project_kit/templates.py:57:Use agentic-kit validate-output-contract when an output should be checked against a machine-readable output-contract YAML file.
src/agentic_project_kit/templates.py:61:    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml
src/agentic_project_kit/templates.py:65:    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --report validation-report.json --report-schema docs/schemas/validation-report.schema.json
src/agentic_project_kit/templates.py:67:The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`. Use `--report-schema docs/schemas/validation-report.schema.json` to validate the generated report shape before the report file is written.
src/agentic_project_kit/templates.py:87:Generated governance-wrapper projects also include `docs/schemas/validation-report.schema.json` as the machine-readable schema for this report shape.
src/agentic_project_kit/templates.py:95:Both commands only check required literal sections. They do not repair content, infer missing facts, or validate semantic correctness.
src/agentic_project_kit/templates.py:97:## Repair rules
src/agentic_project_kit/templates.py:99:- Repair attempts must be bounded and auditable.
src/agentic_project_kit/templates.py:100:- Repairs must not invent missing domain facts.
src/agentic_project_kit/templates.py:101:- Repairs must not rewrite valid final content unnecessarily.
src/agentic_project_kit/templates.py:102:- If repair fails, report a clear contract failure.
src/agentic_project_kit/templates.py:107:- [ ] Define allowed repair scope.
src/agentic_project_kit/templates.py:108:- [ ] Add regression tests for repair boundaries.
src/agentic_project_kit/templates.py:234:        files["docs/schemas/validation-report.schema.json"] = VALIDATION_REPORT_SCHEMA_JSON
src/agentic_project_kit/cli.py:314:@app.command("validate-output-contract")
src/agentic_project_kit/cli.py:317:    contract_path: Path = typer.Option(..., "--contract", "-c", help="Output contract YAML file."),
src/agentic_project_kit/cli.py:318:    report_path: Path | None = typer.Option(None, "--report", help="Write a JSON validation report."),
src/agentic_project_kit/cli.py:319:    report_schema_path: Path | None = typer.Option(
src/agentic_project_kit/cli.py:321:        "--report-schema",
src/agentic_project_kit/cli.py:322:        help="Validate the JSON report against a generated validation-report.schema.json file.",
src/agentic_project_kit/cli.py:325:    """Validate an output file against a machine-readable output contract."""
src/agentic_project_kit/cli.py:331:        typer.echo(f"Output contract invalid: {exc}", err=True)
src/agentic_project_kit/cli.py:342:    if report_schema_path is not None:
src/agentic_project_kit/cli.py:344:            typer.echo("--report-schema requires --report.", err=True)
src/agentic_project_kit/cli.py:346:        schema_payload = json.loads(report_schema_path.read_text(encoding="utf-8"))
src/agentic_project_kit/cli.py:347:        schema_errors = _validate_report_payload_against_schema(payload, schema_payload)
src/agentic_project_kit/cli.py:348:        if schema_errors:
src/agentic_project_kit/cli.py:349:            typer.echo("Validation report schema check failed:", err=True)
src/agentic_project_kit/cli.py:350:            for error in schema_errors:
src/agentic_project_kit/cli.py:358:        typer.echo("Output contract validation passed.")
src/agentic_project_kit/cli.py:369:def _validate_report_payload_against_schema(
src/agentic_project_kit/cli.py:371:    schema_payload: dict[str, Any],
src/agentic_project_kit/cli.py:374:    if schema_payload.get("type") != "object":
src/agentic_project_kit/cli.py:375:        errors.append("report schema root type must be object")
src/agentic_project_kit/cli.py:377:    required = schema_payload.get("required", [])
src/agentic_project_kit/cli.py:379:        errors.append("report schema required field must be a list")
src/agentic_project_kit/cli.py:383:            errors.append("report schema required entries must be strings")
src/agentic_project_kit/cli.py:386:    properties = schema_payload.get("properties", {})
src/agentic_project_kit/cli.py:388:        errors.append("report schema properties field must be an object")
src/agentic_project_kit/cli.py:390:    if schema_payload.get("additionalProperties") is False:
src/agentic_project_kit/cli.py:398:            if expected_type and not _json_schema_type_matches(value, expected_type):
src/agentic_project_kit/cli.py:403:def _json_schema_type_matches(value: Any, expected_type: Any) -> bool:
src/agentic_project_kit/cli.py:405:        return any(_json_schema_type_matches(value, item) for item in expected_type)
src/agentic_project_kit/contract.py:78:        description="Strict human-AI wrapper project with output contracts, validation, repair boundaries, and auditability.",
src/agentic_project_kit/contract.py:130:        title="Output contracts",
src/agentic_project_kit/contract.py:131:        description="Strict response/output governance with schemas, validators, bounded repair, and evidence-oriented failure handling.",
src/agentic_project_kit/runtime_validator.py:4:validation results without performing repair or invoking any model.
src/agentic_project_kit/runtime_validator.py:56:    as a first runtime skeleton for generated output contracts and governance
tests/test_generator.py:151:    assert "Validation reports from `agentic-kit validate-output-contract --report`" in evidence
tests/test_generator.py:152:    assert "Do not auto-stage validation reports by default" in evidence
tests/test_generator.py:157:    schema_path = target / "docs/schemas/validation-report.schema.json"
tests/test_generator.py:158:    assert schema_path.exists()
tests/test_generator.py:159:    schema_text = schema_path.read_text(encoding="utf-8")
tests/test_generator.py:160:    assert "agentic-project-kit validation report" in schema_text
tests/test_generator.py:161:    assert "checked_file" in schema_text
tests/test_generator.py:162:    assert "missing_required_section" not in schema_text
tests/test_generator.py:169:    assert "Use agentic-kit validate-output-contract" in validation
tests/test_generator.py:176:    assert "docs/schemas/validation-report.schema.json" in validation
tests/test_generator.py:177:    assert "machine-readable schema for this report shape" in validation
tests/test_generator.py:180:    assert "Repair attempts must be bounded" in validation
tests/test_output_contract.py:45:        ([], "output contract must be a mapping"),
tests/test_output_contract.py:46:        ({"version": 2, "name": "x", "required_sections": ["A"]}, "output contract version must be 1"),
tests/test_output_contract.py:47:        ({"version": 1, "name": "", "required_sections": ["A"]}, "output contract name is required"),
tests/test_validate_output_contract_cli.py:30:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
tests/test_validate_output_contract_cli.py:34:    assert "Output contract validation passed." in result.output
tests/test_validate_output_contract_cli.py:45:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
tests/test_validate_output_contract_cli.py:61:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
tests/test_validate_output_contract_cli.py:65:    assert "Output contract invalid: output contract version must be 1" in result.output
tests/test_validate_output_contract_cli.py:78:            "validate-output-contract",
tests/test_validate_output_contract_cli.py:119:            "validate-output-contract",
tests/test_validate_output_contract_cli.py:139:def test_validate_output_contract_cli_validates_json_report_against_schema(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:143:    schema_path = tmp_path / "validation-report.schema.json"
tests/test_validate_output_contract_cli.py:146:    schema_path.write_text(json.dumps({"type": "object", "additionalProperties": False, "required": ["checked_file", "contract", "contract_version", "findings", "ok"], "properties": {"checked_file": {"type": "string"}, "contract": {"type": "string"}, "contract_version": {"type": "integer"}, "findings": {"type": "array"}, "ok": {"type": "boolean"}}}), encoding="utf-8")
tests/test_validate_output_contract_cli.py:147:    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report", str(report_path), "--report-schema", str(schema_path)])
tests/test_validate_output_contract_cli.py:152:def test_validate_output_contract_cli_report_schema_requires_report(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:155:    schema_path = tmp_path / "validation-report.schema.json"
tests/test_validate_output_contract_cli.py:158:    schema_path.write_text(json.dumps({"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}), encoding="utf-8")
tests/test_validate_output_contract_cli.py:159:    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report-schema", str(schema_path)])
tests/test_validate_output_contract_cli.py:161:    assert "--report-schema requires --report." in result.output
tests/test_validate_output_contract_cli.py:164:def test_validate_output_contract_cli_fails_when_report_schema_rejects_payload(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:168:    schema_path = tmp_path / "validation-report.schema.json"
tests/test_validate_output_contract_cli.py:171:    schema_path.write_text(json.dumps({"type": "object", "required": ["ok", "missing"], "properties": {"ok": {"type": "boolean"}, "missing": {"type": "string"}}}), encoding="utf-8")
tests/test_validate_output_contract_cli.py:172:    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report", str(report_path), "--report-schema", str(schema_path)])
tests/test_validate_output_contract_cli.py:174:    assert "Validation report schema check failed:" in result.output
docs/handoff/CURRENT_HANDOFF.md:67:   - Prefer generic names such as `structured-output`, `governed-output`, `response-contracts`, `repairable-output`, and `audit-evidence`.
docs/handoff/CURRENT_HANDOFF.md:91:For this repository, assistants and coding agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.
docs/handoff/CURRENT_HANDOFF.md:204:- PR #54 tightened generated validation/repair guidance so repair wording is singular, bounded, and auditable.
docs/handoff/CURRENT_HANDOFF.md:209:- Decision: do not add `validate-output-contract` yet because generated `docs/OUTPUT_CONTRACTS.md` is still a Markdown skeleton, not a machine-readable contract format.
docs/handoff/CURRENT_HANDOFF.md:213:- PR #70 added `agentic-kit validate-output-contract`, which loads an output-contract YAML file and validates an output text file using existing required-section semantics.
docs/handoff/CURRENT_HANDOFF.md:214:- PR #72 updated generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` guidance so `validate-output-contract` is shown next to the lower-level `validate-sections` command.
docs/handoff/CURRENT_HANDOFF.md:215:- PR #74 documented the runtime validation workflow in `README.md` and `CHANGELOG.md`, including `validate-sections`, `validate-contract`, and `validate-output-contract`.
docs/handoff/CURRENT_HANDOFF.md:220:- PR #81 added deterministic JSON report export for `agentic-kit validate-output-contract --report`, including `ok`, `contract`, `contract_version`, `checked_file`, and `findings`.
docs/handoff/CURRENT_HANDOFF.md:221:- PR #83 documented the `validate-output-contract --report` workflow in `README.md` and generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` guidance.
docs/handoff/CURRENT_HANDOFF.md:222:- PR #85 documented validation reports from `validate-output-contract --report` as bounded audit evidence in generated `docs/LOGGING_AND_EVIDENCE.md` guidance, while keeping report creation explicit and warning against auto-staging by default.
docs/handoff/CURRENT_HANDOFF.md:226:- PR #91 documented the validation-report JSON schema in `README.md` and generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` guidance.
docs/handoff/CURRENT_HANDOFF.md:227:- v0.2.9 GitHub Release has been created for the validation-report JSON schema documentation / contract-stability slice.
docs/handoff/CURRENT_HANDOFF.md:230:- PR #97 added generated governance-wrapper support for `docs/schemas/validation-report.schema.json`, making the validation-report JSON shape available as a machine-readable schema file.
docs/handoff/CURRENT_HANDOFF.md:231:- v0.2.11 GitHub Release has been created for the validation-report schema-file contract-stability slice.
docs/TEST_GATES.md:85:Agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.
docs/STATUS.md:83:   - Prefer generic names such as `structured-output`, `governed-output`, `response-contracts`, `repairable-output`, and `audit-evidence`.
docs/STATUS.md:158:- `output-contracts` is available as a policy pack for schema/validator/repair-boundary oriented projects.
docs/STATUS.md:166:- PR #54 tightened generated validation/repair guidance so repair wording is singular, bounded, and auditable.
docs/STATUS.md:171:- Decision: do not add `validate-output-contract` yet because generated `docs/OUTPUT_CONTRACTS.md` is still a Markdown skeleton, not a machine-readable contract format.
docs/STATUS.md:175:- PR #70 added `agentic-kit validate-output-contract`, which loads an output-contract YAML file and validates an output text file using existing required-section semantics.
docs/STATUS.md:176:- PR #72 updated generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` guidance so `validate-output-contract` is shown next to the lower-level `validate-sections` command.
docs/STATUS.md:177:- PR #74 documented the runtime validation workflow in `README.md` and `CHANGELOG.md`, including `validate-sections`, `validate-contract`, and `validate-output-contract`.
docs/STATUS.md:182:- PR #81 added deterministic JSON report export for `agentic-kit validate-output-contract --report`, including `ok`, `contract`, `contract_version`, `checked_file`, and `findings`.
docs/STATUS.md:183:- PR #83 documented the `validate-output-contract --report` workflow in `README.md` and generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` guidance.
docs/STATUS.md:184:- PR #85 documented validation reports from `validate-output-contract --report` as bounded audit evidence in generated `docs/LOGGING_AND_EVIDENCE.md` guidance, while keeping report creation explicit and warning against auto-staging by default.
docs/STATUS.md:188:- PR #91 documented the validation-report JSON schema in `README.md` and generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` guidance.
docs/STATUS.md:189:- v0.2.9 GitHub Release has been created for the validation-report JSON schema documentation / contract-stability slice.
docs/STATUS.md:192:- PR #97 added generated governance-wrapper support for `docs/schemas/validation-report.schema.json`, making the validation-report JSON shape available as a machine-readable schema file.
docs/STATUS.md:193:- v0.2.11 GitHub Release has been created for the validation-report schema-file contract-stability slice.
docs/DESIGN.md:23:- TODO schema
docs/reports/report_schema_docs_slice_20260512.md:1:# Report schema docs slice
docs/reports/report_schema_docs_slice_20260512.md:7:Make the `--report-schema` option discoverable in user-facing documentation after PR #104 added schema validation support and PR #105 verified it end-to-end.
docs/reports/report_schema_docs_slice_20260512.md:11:- Update documentation examples from `--report validation-report.json` to `--report validation-report.json --report-schema docs/schemas/validation-report.schema.json` where the generated schema is already discussed.
docs/reports/report_schema_docs_slice_20260512.md:12:- Explain that the schema check validates the report shape before the report file is written.
docs/reports/report_schema_docs_slice_20260512.md:24:feature/document-report-schema-option
docs/reports/report_schema_docs_slice_20260512.md:28:?? docs/reports/report_schema_docs_slice_20260512.md
docs/reports/report_schema_docs_slice_20260512.md:32:92a0a02 Document collaboration rules and report schema E2E (#105)
docs/reports/report_schema_docs_slice_20260512.md:33:6b61956 Validate output reports against generated schema (#104)
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:1:# Report schema E2E and collaboration rules
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:4:Branch: feature/report-schema-e2e-and-collab-rules
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:8:?? docs/reports/report_schema_e2e_and_collab_rules_20260512.md
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:11:Initialized empty Git repository in /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/tmp/report-schema-e2e-demo/.git/
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:12:Created project: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/tmp/report-schema-e2e-demo
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:39: create mode 100644 docs/schemas/validation-report.schema.json
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:43:  cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/tmp/report-schema-e2e-demo
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:48:## Generated schema and contract files
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:49:-rw-r--r--@ 1 hof  staff  1180 12 Mai  12:36 tmp/report-schema-e2e-demo/docs/schemas/validation-report.schema.json
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:50:-rw-r--r--@ 1 hof  staff  100 12 Mai  12:36 tmp/report-schema-e2e-demo/docs/output-contracts/default-answer.yaml
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:54:## Validate output, write report, validate report against schema
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:55:Output contract validation passed.
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:59:  "checked_file": "tmp/report-schema-e2e-demo/sample-output.md",
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:66:## Negative check: --report-schema without --report must fail
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:83:feature/report-schema-e2e-and-collab-rules
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:87:?? docs/reports/report_schema_e2e_and_collab_rules_20260512.md
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:90:6b61956 Validate output reports against generated schema (#104)
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:96:6f6724c Update docs after validation report schema file (#98)
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:97:97055c5 Generate validation report JSON schema file (#97)
docs/reports/report_schema_e2e_and_collab_rules_20260512.md:141:?? docs/reports/report_schema_e2e_and_collab_rules_20260512.md
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:4:Branch: feature/plan-v0.3.0-output-repair
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:8:Start v0.3.0 planning for a bounded output-repair pipeline.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:16:ee6d088 Document report schema option in generated wrapper docs (#107)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:18:92a0a02 Document collaboration rules and report schema E2E (#105)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:19:6b61956 Validate output reports against generated schema (#104)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:25:docs/reports/report_schema_docs_slice_20260512.md
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:26:docs/reports/report_schema_e2e_and_collab_rules_20260512.md
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:54:## Existing repair/validation references
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:55:src/agentic_project_kit/output_contract.py:1:"""Machine-readable output contract primitives.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:56:src/agentic_project_kit/output_contract.py:21:    """Minimal machine-readable output contract."""
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:57:src/agentic_project_kit/output_contract.py:29:    """Load a minimal output contract from YAML."""
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:58:src/agentic_project_kit/output_contract.py:40:        raise ValueError("output contract must be a mapping")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:59:src/agentic_project_kit/output_contract.py:47:        raise ValueError("output contract version must be 1")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:60:src/agentic_project_kit/output_contract.py:49:        raise ValueError("output contract name is required")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:61:src/agentic_project_kit/templates.py:8:BASE_FILES = {'README.md': '# $name\n\n$description\n\n## Purpose\n\nDescribe the purpose of the project here.\n\n## Quick Start\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\n```\n\n## Agentic Development\n\nThis project uses agent-facing documentation and local quality gates.\n\nStart with:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Status\n\nDo not store volatile status in this README. Use `docs/STATUS.md`.\n', 'AGENTS.md': '# AGENTS.md\n\n## Mission\n\nPreserve correctness, traceability, testability, and maintainability.\n\nDo not only satisfy the immediate request. Prefer the best technically sound solution within project constraints.\n\n## Source-of-truth hierarchy\n\n1. `.agentic/project.yaml`\n2. normative project specification, if present\n3. current code and tests\n4. `docs/STATUS.md`\n5. `docs/handoff/CURRENT_HANDOFF.md`\n6. historical archive files\n\nIf documentation, code, and tests disagree, report the discrepancy instead of guessing.\n\n## Agent read order\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/LOGGING_AND_EVIDENCE.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n8. relevant source files and tests\n\n## Work rules\n\n- Keep stable rules separate from volatile status.\n- Add or update tests for meaningful behavior changes.\n- Prefer outcome evidence over output claims.\n- Do not claim success without running the relevant gates.\n- Do not commit secrets, local credentials, or broad raw logs.\n- Use bounded diagnostic logs only when needed for troubleshooting.\n\n## Closeout template\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Changed files:\n- Tests run:\n- Tests not run:\n- Remaining risks:\n- Next safe step:\n```\n', 'docs/PROJECT_START.md': '# Project Start\n\n## Purpose\n\nThis file guides the initial setup after repository generation.\n\n## Generated Structure\n\nThis project was generated with agent-facing documentation, a machine-readable project contract, status and handoff files, a test-gate matrix, bootstrap task items, logging/evidence conventions, and optional GitHub workflow/pre-commit templates.\n\n## Required First Decisions\n\n- [ ] Review `.agentic/project.yaml` profiles and policy packs.\n- [ ] Choose or confirm project license.\n- [ ] Define the primary runtime entrypoint.\n- [ ] Define supported runtime versions.\n- [ ] Decide whether bounded diagnostic logs may be committed.\n- [ ] Define protected branches.\n- [ ] Define release strategy.\n- [ ] Review agent instructions.\n\n## First Local Commands\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## First GitHub Setup\n\n- [ ] Create GitHub repository.\n- [ ] Push initial commit.\n- [ ] Enable branch protection for `main`.\n- [ ] Enable GitHub Actions.\n- [ ] Enable secret scanning if available.\n- [ ] Review `.github/copilot-instructions.md`.\n\n## Agent Onboarding\n\nA new agent should read:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `.github/copilot-instructions.md`\n4. `docs/PROJECT_START.md`\n5. `docs/STATUS.md`\n6. `docs/TEST_GATES.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Before First Feature\n\n- [ ] Update `README.md` with the real project goal.\n- [ ] Update `docs/STATUS.md`.\n- [ ] Update `docs/TEST_GATES.md`.\n- [ ] Add first meaningful tests.\n- [ ] Run all checks.\n', 'docs/STATUS.md': '# Project Status\n\nStatus-date: TODO\nProject: $name\nPrimary branch: main\nRuntime entrypoint: TODO\nProject contract: `.agentic/project.yaml`\n\n## Purpose\n\nThis is the compact current-state dashboard.\n\nIt must not become a long history file.\n\n## Current Goal\n\nTODO: define the current project goal.\n\n## Current Blockers\n\n- TODO\n\n## Live Status Commands\n\n```bash\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## Next Safe Step\n\nTODO\n', 'docs/TEST_GATES.md': '# Test Gates\n\n## Purpose\n\nThis file maps task types to required evidence.\n\n## Gate Matrix\n\n| Change type | Required evidence |\n|---|---|\n| Documentation only | `agentic-kit check-docs` |\n| task/status change | `agentic-kit check-todo` |\n| Project contract/profile change | `agentic-kit doctor` |\n| Python code | `pytest -q` and `ruff check .` if enabled |\n| CLI behavior | CLI tests plus local command smoke test |\n| Logging/evidence change | check generated logs for secrets and size |\n| GitHub workflow change | local syntax review and CI run |\n| Agent workflow change | docs check and handoff review |\n\n## Outcome Reporting\n\nUse this closeout shape:\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Evidence:\n- Remaining gap:\n- Tests run:\n- Tests not run:\n```\n', 'docs/LOGGING_AND_EVIDENCE.md': '# Logging and Evidence\n\n## Purpose\n\nLogs are diagnostic evidence, not automatic source material.\n\n## Recommended Layout\n\n```text\nLogs/\n  Audit/\n  ManualTests/\n  TestRuns/\ntmp/\n  agent-evidence/\n```\n\n## Rules\n\n- Do not commit secrets.\n- Do not commit broad raw logs by default.\n- Commit only bounded recent evidence when needed.\n- Inspect staged logs before committing.\n- Validation reports from `agentic-kit validate-output-contract --report` are bounded audit evidence when they are intentionally written to a reviewed path such as `tmp/agent-evidence/` or a PR-specific evidence folder.\n- Do not auto-stage validation reports by default; inspect them before committing.\n\n## Agent Use\n\nAgents should use logs to diagnose failures, not to infer undocumented project rules.\n', 'docs/handoff/CURRENT_HANDOFF.md': '# Current Handoff\n\nStatus-date: TODO\nProject: $name\nBranch: main\nProject contract: `.agentic/project.yaml`\n\n## Current goal\n\nTODO\n\n## Current source of truth\n\n1. `.agentic/project.yaml`\n2. `AGENTS.md`\n3. `docs/STATUS.md`\n4. current code and tests\n\n## Latest closeout\n\nNo closeout yet.\n\n## Next step\n\nTODO\n', 'docs/handoff/STANDARD_AGENT_PROMPT.md': '# Standard Agent Prompt\n\n```text\nYou are working in this repository.\n\nStart by reading:\n\n1. AGENTS.md\n2. .agentic/project.yaml\n3. docs/PROJECT_START.md\n4. docs/STATUS.md\n5. docs/TEST_GATES.md\n6. docs/handoff/CURRENT_HANDOFF.md\n\nDo not infer current state from memory.\nRun or request:\n\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n\nFor substantial work, close with:\n\n- Intended outcome:\n- Required evidence:\n- Outcome achieved:\n- Changed files:\n- Tests run:\n- Remaining risks:\n```\n', 'docs/TODO.md': '# TODO\n\nThis file is generated from `.agentic/todo.yaml`.\n\n## Bootstrap\n\n- [ ] **BOOT-001** Choose or confirm license  \n  Owner: human  \n  Priority: high  \n  Evidence required: `LICENSE` reviewed\n\n- [ ] **BOOT-002** Define runtime entrypoint  \n  Owner: human  \n  Priority: high  \n  Evidence required: `README.md` and `docs/STATUS.md` updated\n\n- [ ] **BOOT-003** Run initial local quality gate  \n  Owner: agent  \n  Priority: high  \n  Evidence required: `pytest -q` and `agentic-kit check` passed\n\n- [ ] **BOOT-004** Review project contract profiles and policy packs  \n  Owner: human  \n  Priority: high  \n  Evidence required: `.agentic/project.yaml` reviewed\n\n- [ ] **BOOT-005** Enable branch protection on GitHub  \n  Owner: human  \n  Priority: medium  \n  Evidence required: branch protection enabled\n', '.agentic/todo.yaml': 'items:\n  - id: BOOT-001\n    title: Choose or confirm license\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: LICENSE reviewed\n  - id: BOOT-002\n    title: Define runtime entrypoint\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: README.md and docs/STATUS.md updated\n  - id: BOOT-003\n    title: Run initial local quality gate\n    owner: agent\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: pytest -q and agentic-kit check passed\n  - id: BOOT-004\n    title: Review project contract profiles and policy packs\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: .agentic/project.yaml reviewed\n  - id: BOOT-005\n    title: Enable branch protection on GitHub\n    owner: human\n    priority: medium\n    status: open\n    blocking: false\n    evidence_required: branch protection enabled\n', 'sentinel.yaml': 'documents:\n  - path: README.md\n    required_sections:\n      - "## Purpose"\n      - "## Quick Start"\n    max_words: 2000\n  - path: AGENTS.md\n    required_sections:\n      - "## Mission"\n      - "## Agent read order"\n      - "## Closeout template"\n    max_words: 2500\n  - path: docs/STATUS.md\n    required_sections:\n      - "## Current Goal"\n      - "## Next Safe Step"\n    max_words: 1200\n  - path: docs/TEST_GATES.md\n    required_sections:\n      - "## Gate Matrix"\n      - "## Outcome Reporting"\n    max_words: 1600\ntodo:\n  path: .agentic/todo.yaml\n', '.github/copilot-instructions.md': '# Copilot Instructions\n\nFollow the repository rules in `AGENTS.md`.\n\nBefore claiming completion, run or request the relevant commands from `docs/TEST_GATES.md`.\n\nDo not commit secrets, broad raw logs, virtual environments, or local-only configuration.\n', '.github/pull_request_template.md': '## Intended outcome\n\n## Required evidence\n\n## Outcome achieved\n\n- [ ] yes\n- [ ] no\n- [ ] partial\n\n## Tests run\n\n## Risks / remaining gaps\n', '.github/ISSUE_TEMPLATE/agent_regression.yml': 'name: Agent regression\ndescription: Report an agent workflow or handoff regression\ntitle: "[Agent Regression]: "\nlabels: ["agent", "regression"]\nbody:\n  - type: textarea\n    id: observed\n    attributes:\n      label: Observed behavior\n    validations:\n      required: true\n  - type: textarea\n    id: expected\n    attributes:\n      label: Expected behavior\n    validations:\n      required: true\n  - type: textarea\n    id: evidence\n    attributes:\n      label: Evidence / logs\n    validations:\n      required: false\n', 'scripts/stage_recent_logs.py': 'from pathlib import Path\nimport shutil\n\nLOG_ROOTS = [Path("Logs/Audit"), Path("Logs/ManualTests"), Path("Logs/TestRuns")]\nTARGET = Path("tmp/agent-evidence")\n\n\ndef main(max_files: int = 10) -> None:\n    TARGET.mkdir(parents=True, exist_ok=True)\n    for root in LOG_ROOTS:\n        if not root.exists():\n            continue\n        files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.stat().st_mtime)\n        for src in files[-max_files:]:\n            rel = src.relative_to(root)\n            dst = TARGET / root.name / rel\n            dst.parent.mkdir(parents=True, exist_ok=True)\n            shutil.copy2(src, dst)\n    print(f"Staged bounded evidence in {TARGET}")\n\n\nif __name__ == "__main__":\n    main()\n'}
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:62:src/agentic_project_kit/templates.py:18:- Define explicit output schemas before relying on generated content.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:63:src/agentic_project_kit/templates.py:21:- Do not silently repair meaning-changing output errors.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:64:src/agentic_project_kit/templates.py:31:VALIDATION_REPORT_SCHEMA_JSON = '{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "additionalProperties": false,\n  "properties": {\n    "checked_file": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract_version": {\n      "minimum": 1,\n      "type": "integer"\n    },\n    "findings": {\n      "items": {\n        "additionalProperties": false,\n        "properties": {\n          "code": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "message": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "severity": {\n            "enum": [\n              "info",\n              "warning",\n              "error"\n            ],\n            "type": "string"\n          }\n        },\n        "required": [\n          "severity",\n          "code",\n          "message"\n        ],\n        "type": "object"\n      },\n      "type": "array"\n    },\n    "ok": {\n      "type": "boolean"\n    }\n  },\n  "required": [\n    "ok",\n    "contract",\n    "contract_version",\n    "checked_file",\n    "findings"\n  ],\n  "title": "agentic-project-kit validation report",\n  "type": "object"\n}\n'
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:65:src/agentic_project_kit/templates.py:42:VALIDATION_AND_REPAIR = """# Validation and Repair
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:66:src/agentic_project_kit/templates.py:46:This document records validation and bounded repair rules for governance-wrapper projects.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:67:src/agentic_project_kit/templates.py:57:Use agentic-kit validate-output-contract when an output should be checked against a machine-readable output-contract YAML file.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:68:src/agentic_project_kit/templates.py:61:    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:69:src/agentic_project_kit/templates.py:65:    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --report validation-report.json --report-schema docs/schemas/validation-report.schema.json
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:70:src/agentic_project_kit/templates.py:67:The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`. Use `--report-schema docs/schemas/validation-report.schema.json` to validate the generated report shape before the report file is written.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:71:src/agentic_project_kit/templates.py:87:Generated governance-wrapper projects also include `docs/schemas/validation-report.schema.json` as the machine-readable schema for this report shape.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:72:src/agentic_project_kit/templates.py:95:Both commands only check required literal sections. They do not repair content, infer missing facts, or validate semantic correctness.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:73:src/agentic_project_kit/templates.py:97:## Repair rules
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:74:src/agentic_project_kit/templates.py:99:- Repair attempts must be bounded and auditable.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:75:src/agentic_project_kit/templates.py:100:- Repairs must not invent missing domain facts.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:76:src/agentic_project_kit/templates.py:101:- Repairs must not rewrite valid final content unnecessarily.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:77:src/agentic_project_kit/templates.py:102:- If repair fails, report a clear contract failure.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:78:src/agentic_project_kit/templates.py:107:- [ ] Define allowed repair scope.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:79:src/agentic_project_kit/templates.py:108:- [ ] Add regression tests for repair boundaries.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:80:src/agentic_project_kit/templates.py:234:        files["docs/schemas/validation-report.schema.json"] = VALIDATION_REPORT_SCHEMA_JSON
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:81:src/agentic_project_kit/cli.py:314:@app.command("validate-output-contract")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:82:src/agentic_project_kit/cli.py:317:    contract_path: Path = typer.Option(..., "--contract", "-c", help="Output contract YAML file."),
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:83:src/agentic_project_kit/cli.py:318:    report_path: Path | None = typer.Option(None, "--report", help="Write a JSON validation report."),
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:84:src/agentic_project_kit/cli.py:319:    report_schema_path: Path | None = typer.Option(
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:85:src/agentic_project_kit/cli.py:321:        "--report-schema",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:86:src/agentic_project_kit/cli.py:322:        help="Validate the JSON report against a generated validation-report.schema.json file.",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:87:src/agentic_project_kit/cli.py:325:    """Validate an output file against a machine-readable output contract."""
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:88:src/agentic_project_kit/cli.py:331:        typer.echo(f"Output contract invalid: {exc}", err=True)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:89:src/agentic_project_kit/cli.py:342:    if report_schema_path is not None:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:90:src/agentic_project_kit/cli.py:344:            typer.echo("--report-schema requires --report.", err=True)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:91:src/agentic_project_kit/cli.py:346:        schema_payload = json.loads(report_schema_path.read_text(encoding="utf-8"))
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:92:src/agentic_project_kit/cli.py:347:        schema_errors = _validate_report_payload_against_schema(payload, schema_payload)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:93:src/agentic_project_kit/cli.py:348:        if schema_errors:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:94:src/agentic_project_kit/cli.py:349:            typer.echo("Validation report schema check failed:", err=True)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:95:src/agentic_project_kit/cli.py:350:            for error in schema_errors:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:96:src/agentic_project_kit/cli.py:358:        typer.echo("Output contract validation passed.")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:97:src/agentic_project_kit/cli.py:369:def _validate_report_payload_against_schema(
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:98:src/agentic_project_kit/cli.py:371:    schema_payload: dict[str, Any],
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:99:src/agentic_project_kit/cli.py:374:    if schema_payload.get("type") != "object":
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:100:src/agentic_project_kit/cli.py:375:        errors.append("report schema root type must be object")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:101:src/agentic_project_kit/cli.py:377:    required = schema_payload.get("required", [])
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:102:src/agentic_project_kit/cli.py:379:        errors.append("report schema required field must be a list")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:103:src/agentic_project_kit/cli.py:383:            errors.append("report schema required entries must be strings")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:104:src/agentic_project_kit/cli.py:386:    properties = schema_payload.get("properties", {})
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:105:src/agentic_project_kit/cli.py:388:        errors.append("report schema properties field must be an object")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:106:src/agentic_project_kit/cli.py:390:    if schema_payload.get("additionalProperties") is False:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:107:src/agentic_project_kit/cli.py:398:            if expected_type and not _json_schema_type_matches(value, expected_type):
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:108:src/agentic_project_kit/cli.py:403:def _json_schema_type_matches(value: Any, expected_type: Any) -> bool:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:109:src/agentic_project_kit/cli.py:405:        return any(_json_schema_type_matches(value, item) for item in expected_type)
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:110:src/agentic_project_kit/contract.py:78:        description="Strict human-AI wrapper project with output contracts, validation, repair boundaries, and auditability.",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:111:src/agentic_project_kit/contract.py:130:        title="Output contracts",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:112:src/agentic_project_kit/contract.py:131:        description="Strict response/output governance with schemas, validators, bounded repair, and evidence-oriented failure handling.",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:113:src/agentic_project_kit/runtime_validator.py:4:validation results without performing repair or invoking any model.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:114:src/agentic_project_kit/runtime_validator.py:56:    as a first runtime skeleton for generated output contracts and governance
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:115:tests/test_generator.py:151:    assert "Validation reports from `agentic-kit validate-output-contract --report`" in evidence
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:116:tests/test_generator.py:152:    assert "Do not auto-stage validation reports by default" in evidence
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:117:tests/test_generator.py:157:    schema_path = target / "docs/schemas/validation-report.schema.json"
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:118:tests/test_generator.py:158:    assert schema_path.exists()
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:119:tests/test_generator.py:159:    schema_text = schema_path.read_text(encoding="utf-8")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:120:tests/test_generator.py:160:    assert "agentic-project-kit validation report" in schema_text
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:121:tests/test_generator.py:161:    assert "checked_file" in schema_text
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:122:tests/test_generator.py:162:    assert "missing_required_section" not in schema_text
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:123:tests/test_generator.py:169:    assert "Use agentic-kit validate-output-contract" in validation
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:124:tests/test_generator.py:176:    assert "docs/schemas/validation-report.schema.json" in validation
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:125:tests/test_generator.py:177:    assert "machine-readable schema for this report shape" in validation
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:126:tests/test_generator.py:180:    assert "Repair attempts must be bounded" in validation
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:127:tests/test_output_contract.py:45:        ([], "output contract must be a mapping"),
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:128:tests/test_output_contract.py:46:        ({"version": 2, "name": "x", "required_sections": ["A"]}, "output contract version must be 1"),
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:129:tests/test_output_contract.py:47:        ({"version": 1, "name": "", "required_sections": ["A"]}, "output contract name is required"),
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:130:tests/test_validate_output_contract_cli.py:30:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:131:tests/test_validate_output_contract_cli.py:34:    assert "Output contract validation passed." in result.output
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:132:tests/test_validate_output_contract_cli.py:45:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:133:tests/test_validate_output_contract_cli.py:61:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:134:tests/test_validate_output_contract_cli.py:65:    assert "Output contract invalid: output contract version must be 1" in result.output
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:135:tests/test_validate_output_contract_cli.py:78:            "validate-output-contract",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:136:tests/test_validate_output_contract_cli.py:119:            "validate-output-contract",
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:137:tests/test_validate_output_contract_cli.py:139:def test_validate_output_contract_cli_validates_json_report_against_schema(tmp_path: Path) -> None:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:138:tests/test_validate_output_contract_cli.py:143:    schema_path = tmp_path / "validation-report.schema.json"
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:139:tests/test_validate_output_contract_cli.py:146:    schema_path.write_text(json.dumps({"type": "object", "additionalProperties": False, "required": ["checked_file", "contract", "contract_version", "findings", "ok"], "properties": {"checked_file": {"type": "string"}, "contract": {"type": "string"}, "contract_version": {"type": "integer"}, "findings": {"type": "array"}, "ok": {"type": "boolean"}}}), encoding="utf-8")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:140:tests/test_validate_output_contract_cli.py:147:    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report", str(report_path), "--report-schema", str(schema_path)])
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:141:tests/test_validate_output_contract_cli.py:152:def test_validate_output_contract_cli_report_schema_requires_report(tmp_path: Path) -> None:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:142:tests/test_validate_output_contract_cli.py:155:    schema_path = tmp_path / "validation-report.schema.json"
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:143:tests/test_validate_output_contract_cli.py:158:    schema_path.write_text(json.dumps({"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}), encoding="utf-8")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:144:tests/test_validate_output_contract_cli.py:159:    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report-schema", str(schema_path)])
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:145:tests/test_validate_output_contract_cli.py:161:    assert "--report-schema requires --report." in result.output
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:146:tests/test_validate_output_contract_cli.py:164:def test_validate_output_contract_cli_fails_when_report_schema_rejects_payload(tmp_path: Path) -> None:
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:147:tests/test_validate_output_contract_cli.py:168:    schema_path = tmp_path / "validation-report.schema.json"
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:148:tests/test_validate_output_contract_cli.py:171:    schema_path.write_text(json.dumps({"type": "object", "required": ["ok", "missing"], "properties": {"ok": {"type": "boolean"}, "missing": {"type": "string"}}}), encoding="utf-8")
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:149:tests/test_validate_output_contract_cli.py:172:    result = runner.invoke(app, ["validate-output-contract", str(output_path), "--contract", str(contract_path), "--report", str(report_path), "--report-schema", str(schema_path)])
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:150:tests/test_validate_output_contract_cli.py:174:    assert "Validation report schema check failed:" in result.output
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:151:docs/handoff/CURRENT_HANDOFF.md:67:   - Prefer generic names such as `structured-output`, `governed-output`, `response-contracts`, `repairable-output`, and `audit-evidence`.
docs/reports/CURRENT_WORKFLOW_OUTPUT.md:152:docs/handoff/CURRENT_HANDOFF.md:91:For this repository, assistants and coding agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.

## Current gates
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 16:21:31
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/plan-v0.3.0-output-repair

=== git status --short ===
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md

=== git log --oneline -8 ===
ac7699f Update docs with v0.2.11 Zenodo DOI (#112)
e5f33b4 Fix v0.2.11 citation version drift (#111)
8fa1e8f Prepare v0.2.11 release metadata (#110)
4a50e30 Clean up transient workflow reports (#109)
cc57509 Document current workflow output handoff file (#108)
ee6d088 Document report schema option in generated wrapper docs (#107)
89b7408 Record status roadmap after PR 105 (#106)
92a0a02 Document collaboration rules and report schema E2E (#105)

=== python -m pytest -q ===
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.83s
pytest exit code: 0

=== ruff check . ===
All checks passed!
ruff exit code: 0

=== agentic-kit check-docs ===
Agentic project check passed
check-docs exit code: 0

=== agentic-kit doctor ===
Agentic project doctor report for /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

[PASS] pyproject.toml: present
[PASS] README.md: present
[PASS] sentinel.yaml: present
[PASS] .github/workflows/ci.yml: present
[PASS] project contract: agentic-project-kit; profiles: generic-git-repo, markdown-docs, python-cli, git-github, 
release-managed; policy packs: solo-maintainer, agentic-development, release-managed, documentation-governed
[PASS] policy pack checks: active: solo-maintainer, agentic-development, release-managed, documentation-governed
[PASS] documentation gates: passed
[PASS] todo gates: passed
[PASS] version drift: project state matches version 0.2.11

Overall: PASS
doctor exit code: 0


=== Summary ===
pytest:      0
ruff:        0
check-docs:  0
doctor:      0
extra:       0
OVERALL: PASS

## Git status
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md
