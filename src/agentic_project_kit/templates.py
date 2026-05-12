from dataclasses import asdict
import subprocess

from agentic_project_kit.contract import build_contract_data, render_contract_yaml
from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.rendering import render_template_string, write_file

BASE_FILES = {'README.md': '# $name\n\n$description\n\n## Purpose\n\nDescribe the purpose of the project here.\n\n## Quick Start\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\n```\n\n## Agentic Development\n\nThis project uses agent-facing documentation and local quality gates.\n\nStart with:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Status\n\nDo not store volatile status in this README. Use `docs/STATUS.md`.\n', 'AGENTS.md': '# AGENTS.md\n\n## Mission\n\nPreserve correctness, traceability, testability, and maintainability.\n\nDo not only satisfy the immediate request. Prefer the best technically sound solution within project constraints.\n\n## Source-of-truth hierarchy\n\n1. `.agentic/project.yaml`\n2. normative project specification, if present\n3. current code and tests\n4. `docs/STATUS.md`\n5. `docs/handoff/CURRENT_HANDOFF.md`\n6. historical archive files\n\nIf documentation, code, and tests disagree, report the discrepancy instead of guessing.\n\n## Agent read order\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/LOGGING_AND_EVIDENCE.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n8. relevant source files and tests\n\n## Work rules\n\n- Keep stable rules separate from volatile status.\n- Add or update tests for meaningful behavior changes.\n- Prefer outcome evidence over output claims.\n- Do not claim success without running the relevant gates.\n- Do not commit secrets, local credentials, or broad raw logs.\n- Use bounded diagnostic logs only when needed for troubleshooting.\n\n## Closeout template\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Changed files:\n- Tests run:\n- Tests not run:\n- Remaining risks:\n- Next safe step:\n```\n', 'docs/PROJECT_START.md': '# Project Start\n\n## Purpose\n\nThis file guides the initial setup after repository generation.\n\n## Generated Structure\n\nThis project was generated with agent-facing documentation, a machine-readable project contract, status and handoff files, a test-gate matrix, bootstrap task items, logging/evidence conventions, and optional GitHub workflow/pre-commit templates.\n\n## Required First Decisions\n\n- [ ] Review `.agentic/project.yaml` profiles and policy packs.\n- [ ] Choose or confirm project license.\n- [ ] Define the primary runtime entrypoint.\n- [ ] Define supported runtime versions.\n- [ ] Decide whether bounded diagnostic logs may be committed.\n- [ ] Define protected branches.\n- [ ] Define release strategy.\n- [ ] Review agent instructions.\n\n## First Local Commands\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## First GitHub Setup\n\n- [ ] Create GitHub repository.\n- [ ] Push initial commit.\n- [ ] Enable branch protection for `main`.\n- [ ] Enable GitHub Actions.\n- [ ] Enable secret scanning if available.\n- [ ] Review `.github/copilot-instructions.md`.\n\n## Agent Onboarding\n\nA new agent should read:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `.github/copilot-instructions.md`\n4. `docs/PROJECT_START.md`\n5. `docs/STATUS.md`\n6. `docs/TEST_GATES.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Before First Feature\n\n- [ ] Update `README.md` with the real project goal.\n- [ ] Update `docs/STATUS.md`.\n- [ ] Update `docs/TEST_GATES.md`.\n- [ ] Add first meaningful tests.\n- [ ] Run all checks.\n', 'docs/STATUS.md': '# Project Status\n\nStatus-date: TODO\nProject: $name\nPrimary branch: main\nRuntime entrypoint: TODO\nProject contract: `.agentic/project.yaml`\n\n## Purpose\n\nThis is the compact current-state dashboard.\n\nIt must not become a long history file.\n\n## Current Goal\n\nTODO: define the current project goal.\n\n## Current Blockers\n\n- TODO\n\n## Live Status Commands\n\n```bash\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## Next Safe Step\n\nTODO\n', 'docs/TEST_GATES.md': '# Test Gates\n\n## Purpose\n\nThis file maps task types to required evidence.\n\n## Gate Matrix\n\n| Change type | Required evidence |\n|---|---|\n| Documentation only | `agentic-kit check-docs` |\n| task/status change | `agentic-kit check-todo` |\n| Project contract/profile change | `agentic-kit doctor` |\n| Python code | `pytest -q` and `ruff check .` if enabled |\n| CLI behavior | CLI tests plus local command smoke test |\n| Logging/evidence change | check generated logs for secrets and size |\n| GitHub workflow change | local syntax review and CI run |\n| Agent workflow change | docs check and handoff review |\n\n## Outcome Reporting\n\nUse this closeout shape:\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Evidence:\n- Remaining gap:\n- Tests run:\n- Tests not run:\n```\n', 'docs/LOGGING_AND_EVIDENCE.md': '# Logging and Evidence\n\n## Purpose\n\nLogs are diagnostic evidence, not automatic source material.\n\n## Recommended Layout\n\n```text\nLogs/\n  Audit/\n  ManualTests/\n  TestRuns/\ntmp/\n  agent-evidence/\n```\n\n## Rules\n\n- Do not commit secrets.\n- Do not commit broad raw logs by default.\n- Commit only bounded recent evidence when needed.\n- Inspect staged logs before committing.\n- Validation reports from `agentic-kit validate-output-contract --report` are bounded audit evidence when they are intentionally written to a reviewed path such as `tmp/agent-evidence/` or a PR-specific evidence folder.\n- Do not auto-stage validation reports by default; inspect them before committing.\n\n## Agent Use\n\nAgents should use logs to diagnose failures, not to infer undocumented project rules.\n', 'docs/handoff/CURRENT_HANDOFF.md': '# Current Handoff\n\nStatus-date: TODO\nProject: $name\nBranch: main\nProject contract: `.agentic/project.yaml`\n\n## Current goal\n\nTODO\n\n## Current source of truth\n\n1. `.agentic/project.yaml`\n2. `AGENTS.md`\n3. `docs/STATUS.md`\n4. current code and tests\n\n## Latest closeout\n\nNo closeout yet.\n\n## Next step\n\nTODO\n', 'docs/handoff/STANDARD_AGENT_PROMPT.md': '# Standard Agent Prompt\n\n```text\nYou are working in this repository.\n\nStart by reading:\n\n1. AGENTS.md\n2. .agentic/project.yaml\n3. docs/PROJECT_START.md\n4. docs/STATUS.md\n5. docs/TEST_GATES.md\n6. docs/handoff/CURRENT_HANDOFF.md\n\nDo not infer current state from memory.\nRun or request:\n\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n\nFor substantial work, close with:\n\n- Intended outcome:\n- Required evidence:\n- Outcome achieved:\n- Changed files:\n- Tests run:\n- Remaining risks:\n```\n', 'docs/TODO.md': '# TODO\n\nThis file is generated from `.agentic/todo.yaml`.\n\n## Bootstrap\n\n- [ ] **BOOT-001** Choose or confirm license  \n  Owner: human  \n  Priority: high  \n  Evidence required: `LICENSE` reviewed\n\n- [ ] **BOOT-002** Define runtime entrypoint  \n  Owner: human  \n  Priority: high  \n  Evidence required: `README.md` and `docs/STATUS.md` updated\n\n- [ ] **BOOT-003** Run initial local quality gate  \n  Owner: agent  \n  Priority: high  \n  Evidence required: `pytest -q` and `agentic-kit check` passed\n\n- [ ] **BOOT-004** Review project contract profiles and policy packs  \n  Owner: human  \n  Priority: high  \n  Evidence required: `.agentic/project.yaml` reviewed\n\n- [ ] **BOOT-005** Enable branch protection on GitHub  \n  Owner: human  \n  Priority: medium  \n  Evidence required: branch protection enabled\n', '.agentic/todo.yaml': 'items:\n  - id: BOOT-001\n    title: Choose or confirm license\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: LICENSE reviewed\n  - id: BOOT-002\n    title: Define runtime entrypoint\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: README.md and docs/STATUS.md updated\n  - id: BOOT-003\n    title: Run initial local quality gate\n    owner: agent\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: pytest -q and agentic-kit check passed\n  - id: BOOT-004\n    title: Review project contract profiles and policy packs\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: .agentic/project.yaml reviewed\n  - id: BOOT-005\n    title: Enable branch protection on GitHub\n    owner: human\n    priority: medium\n    status: open\n    blocking: false\n    evidence_required: branch protection enabled\n', 'sentinel.yaml': 'documents:\n  - path: README.md\n    required_sections:\n      - "## Purpose"\n      - "## Quick Start"\n    max_words: 2000\n  - path: AGENTS.md\n    required_sections:\n      - "## Mission"\n      - "## Agent read order"\n      - "## Closeout template"\n    max_words: 2500\n  - path: docs/STATUS.md\n    required_sections:\n      - "## Current Goal"\n      - "## Next Safe Step"\n    max_words: 1200\n  - path: docs/TEST_GATES.md\n    required_sections:\n      - "## Gate Matrix"\n      - "## Outcome Reporting"\n    max_words: 1600\ntodo:\n  path: .agentic/todo.yaml\n', '.github/copilot-instructions.md': '# Copilot Instructions\n\nFollow the repository rules in `AGENTS.md`.\n\nBefore claiming completion, run or request the relevant commands from `docs/TEST_GATES.md`.\n\nDo not commit secrets, broad raw logs, virtual environments, or local-only configuration.\n', '.github/pull_request_template.md': '## Intended outcome\n\n## Required evidence\n\n## Outcome achieved\n\n- [ ] yes\n- [ ] no\n- [ ] partial\n\n## Tests run\n\n## Risks / remaining gaps\n', '.github/ISSUE_TEMPLATE/agent_regression.yml': 'name: Agent regression\ndescription: Report an agent workflow or handoff regression\ntitle: "[Agent Regression]: "\nlabels: ["agent", "regression"]\nbody:\n  - type: textarea\n    id: observed\n    attributes:\n      label: Observed behavior\n    validations:\n      required: true\n  - type: textarea\n    id: expected\n    attributes:\n      label: Expected behavior\n    validations:\n      required: true\n  - type: textarea\n    id: evidence\n    attributes:\n      label: Evidence / logs\n    validations:\n      required: false\n', 'scripts/stage_recent_logs.py': 'from pathlib import Path\nimport shutil\n\nLOG_ROOTS = [Path("Logs/Audit"), Path("Logs/ManualTests"), Path("Logs/TestRuns")]\nTARGET = Path("tmp/agent-evidence")\n\n\ndef main(max_files: int = 10) -> None:\n    TARGET.mkdir(parents=True, exist_ok=True)\n    for root in LOG_ROOTS:\n        if not root.exists():\n            continue\n        files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.stat().st_mtime)\n        for src in files[-max_files:]:\n            rel = src.relative_to(root)\n            dst = TARGET / root.name / rel\n            dst.parent.mkdir(parents=True, exist_ok=True)\n            shutil.copy2(src, dst)\n    print(f"Staged bounded evidence in {TARGET}")\n\n\nif __name__ == "__main__":\n    main()\n'}

REPAIR_REPORT_SCHEMA_JSON = '{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "title": "agentic-project-kit repair report",\n  "type": "object",\n  "additionalProperties": false,\n  "required": [\n    "ok",\n    "repair_attempted",\n    "original_findings",\n    "operations",\n    "skipped_operations",\n    "final_validation"\n  ],\n  "properties": {\n    "ok": {\n      "type": "boolean"\n    },\n    "repair_attempted": {\n      "type": "boolean"\n    },\n    "original_findings": {\n      "type": "array",\n      "items": {\n        "type": "object"\n      }\n    },\n    "operations": {\n      "type": "array",\n      "items": {\n        "type": "object",\n        "additionalProperties": false,\n        "required": [\n          "kind",\n          "status",\n          "target"\n        ],\n        "properties": {\n          "kind": {\n            "type": "string",\n            "minLength": 1\n          },\n          "status": {\n            "type": "string",\n            "enum": [\n              "applied",\n              "planned",\n              "failed"\n            ]\n          },\n          "target": {\n            "type": "string",\n            "minLength": 1\n          },\n          "message": {\n            "type": "string"\n          }\n        }\n      }\n    },\n    "skipped_operations": {\n      "type": "array",\n      "items": {\n        "type": "object",\n        "additionalProperties": false,\n        "required": [\n          "kind",\n          "target",\n          "reason"\n        ],\n        "properties": {\n          "kind": {\n            "type": "string",\n            "minLength": 1\n          },\n          "target": {\n            "type": "string",\n            "minLength": 1\n          },\n          "reason": {\n            "type": "string",\n            "minLength": 1\n          }\n        }\n      }\n    },\n    "final_validation": {\n      "type": "object",\n      "additionalProperties": false,\n      "required": [\n        "ok",\n        "findings"\n      ],\n      "properties": {\n        "ok": {\n          "type": "boolean"\n        },\n        "findings": {\n          "type": "array",\n          "items": {\n            "type": "object"\n          }\n        }\n      }\n    }\n  }\n}\n'
OUTPUT_CONTRACTS = """# Output Contracts

## Purpose

This document defines the expected structure of generated or model-produced outputs.

## Contract rules

- Define explicit output schemas before relying on generated content.
- Validate outputs before using them in downstream steps.
- Keep failures visible and reproducible.
- Do not silently repair meaning-changing output errors.

## Initial checklist

- [ ] Define the primary output types.
- [ ] Define validators for required fields and sections.
- [ ] Define failure behavior for invalid outputs.
- [ ] Add tests for accepted and rejected outputs.
"""

VALIDATION_REPORT_SCHEMA_JSON = '{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "additionalProperties": false,\n  "properties": {\n    "checked_file": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract_version": {\n      "minimum": 1,\n      "type": "integer"\n    },\n    "findings": {\n      "items": {\n        "additionalProperties": false,\n        "properties": {\n          "code": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "message": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "severity": {\n            "enum": [\n              "info",\n              "warning",\n              "error"\n            ],\n            "type": "string"\n          }\n        },\n        "required": [\n          "severity",\n          "code",\n          "message"\n        ],\n        "type": "object"\n      },\n      "type": "array"\n    },\n    "ok": {\n      "type": "boolean"\n    }\n  },\n  "required": [\n    "ok",\n    "contract",\n    "contract_version",\n    "checked_file",\n    "findings"\n  ],\n  "title": "agentic-project-kit validation report",\n  "type": "object"\n}\n'

OUTPUT_CONTRACT_SAMPLE_YAML = """version: 1
name: default-answer
required_sections:
  - Plan
  - Solution
  - Check
  - Final Answer
"""

VALIDATION_AND_REPAIR = """# Validation and Repair

## Purpose

This document records validation and bounded repair rules for governance-wrapper projects.

## Validation rules

- Validate outputs against explicit contracts.
- Treat missing required sections as failures.
- Keep validation deterministic where possible.
- Record evidence for failed validations.

## Runtime output-contract validation

Use agentic-kit validate-output-contract when an output should be checked against a machine-readable output-contract YAML file.

Example:

    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml

For audit evidence, write a machine-readable JSON report:

    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --report validation-report.json --report-schema docs/schemas/validation-report.schema.json

Use deterministic repair only for missing required section markers:

```bash
agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --repair-output output.repaired.md --repair-report repair-report.json
```

The repair output is structural only. It appends missing section markers with explicit TODO text and records the operation in `repair-report.json`; it does not create or infer the missing substantive content.

The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`. Use `--report-schema docs/schemas/validation-report.schema.json` to validate the generated report shape before the report file is written.

Report shape:

    {
      "ok": false,
      "contract": "default-answer",
      "contract_version": 1,
      "checked_file": "output.md",
      "findings": [
        {
          "severity": "error",
          "code": "missing_required_section",
          "message": "Missing required section: Solution"
        }
      ]
    }

The report shape is intentionally small and structural so CI, wrappers, and review scripts can consume it without parsing human console output.

Generated governance-wrapper projects also include `docs/schemas/validation-report.schema.json` as the machine-readable schema for this report shape. They also include `docs/schemas/repair-report.schema.json` as the planned machine-readable shape for future bounded repair reports.

Use agentic-kit validate-sections as a lower-level check when you only need to verify literal section markers directly.

Example:

    agentic-kit validate-sections output.md -s "Plan" -s "Solution" -s "Check" -s "Final Answer"

Both commands only check required literal sections. They do not repair content, infer missing facts, or validate semantic correctness.

## Repair rules

- Repair attempts must be bounded and auditable.
- Repairs must not invent missing domain facts.
- Repairs must not rewrite valid final content unnecessarily.
- If repair fails, report a clear contract failure.

## Initial checklist

- [ ] Define validation entry points.
- [ ] Define allowed repair scope.
- [ ] Add regression tests for repair boundaries.
- [ ] Add evidence capture for validation failures.
"""

GENERATED_STATUS = '# Project Status\n\nCurrent version: 0.1.0\nProject: $name\nPrimary branch: main\nRuntime entrypoint: Python package import\nProject contract: `.agentic/project.yaml`\n\n## Purpose\n\nThis is the compact current-state dashboard.\n\nIt must not become a long history file.\n\n## Current Goal\n\nEstablish the initial generated repository state and run the first local quality gate.\n\n## Current Blockers\n\n- No blockers recorded at generation time.\n\n## Live Status Commands\n\n```bash\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## Next Safe Step\n\nRun the generated local quality gate, review the initial project contract, and replace bootstrap decisions with project-specific decisions.\n'
GENERATED_HANDOFF = '# Current Handoff\n\nCurrent version: 0.1.0\nProject: $name\nBranch: main\nProject contract: `.agentic/project.yaml`\n\n## Current\n\nThe repository has just been generated. The project contract, agent instructions, status file, test gates, task file, and local health checks are the current source of truth.\n\n## Current source of truth\n\n1. `.agentic/project.yaml`\n2. `AGENTS.md`\n3. `docs/STATUS.md`\n4. `docs/TEST_GATES.md`\n5. current code and tests\n\n## Latest closeout\n\nInitial generated project skeleton was created.\n\n## Next\n\nRun the local gate, review bootstrap task items, and replace generated assumptions with project-specific decisions where needed.\n'
ARCHITECTURE_CONTRACT = '# Architecture Contract\n\n## 1. Executive Summary\n\nThis generated project starts with a compact architecture contract so future work has an explicit governance document.\n\n## 2. How to Use This Document\n\nRead this file before architecture-relevant changes. Keep decisions small, documented, and testable.\n\n## 4. Decision Rules\n\nPrefer simple, local, testable changes. Update tests and documentation when behavior or project structure changes.\n\n## 7. Architectural Contract\n\nThe generated repository separates project contract data, status documents, tests, and implementation code. Do not hide durable rules only in chat history.\n\n## 17. Acceptance Criteria for Future Work\n\nArchitecture-relevant changes should state the intended outcome, changed files, evidence run, and remaining risks.\n'
DOCUMENTATION_COVERAGE = "rules:\n  - id: generated-core-docs\n    description: Generated projects must keep core onboarding and gate documents discoverable.\n    documents:\n      - path: README.md\n        terms:\n          - Agentic Development\n          - docs/STATUS.md\n      - path: docs/STATUS.md\n        terms:\n          - 'Current version: 0.1.0'\n          - Next Safe Step\n      - path: docs/handoff/CURRENT_HANDOFF.md\n        terms:\n          - 'Current version: 0.1.0'\n          - Next\n      - path: docs/architecture/ARCHITECTURE_CONTRACT.md\n        terms:\n          - Architectural Contract\n          - Acceptance Criteria for Future Work\n"
CHANGELOG = '# Changelog\n\n## v0.1.0\n\n- Initial generated project skeleton.\n'


PYPROJECT_PYTHON = '''
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "$name"
version = "0.1.0"
description = "$description"
readme = "README.md"
requires-python = ">=3.10"
license = "$license_name"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py310"
'''

CI = '''
name: CI

on:
  push:
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install project
        run: |
          python -m pip install --upgrade pip
          if [ -f pyproject.toml ]; then pip install -e ".[dev]" || pip install -e .; fi
$kit_install_command
      - name: Run tests
        run: |
          if [ -d tests ]; then pytest -q; fi
      - name: Run agentic checks
        run: |
          agentic-kit check
'''

KIT_INSTALL_COMMANDS = {
    "pypi": "          pip install agentic-project-kit",
    "testpypi": (
        "          pip install "
        "--index-url https://test.pypi.org/simple/ "
        "--extra-index-url https://pypi.org/simple/ "
        "agentic-project-kit"
    ),
    "none": "          # agentic-project-kit install intentionally skipped",
}


PRECOMMIT = '''
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files

  - repo: local
    hooks:
      - id: agentic-kit-check
        name: Agentic Kit check
        entry: agentic-kit check
        language: system
        pass_filenames: false
'''


def create_project(options: ProjectOptions, overwrite: bool = False) -> None:
    target = options.target_dir
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Target directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)

    context = {k: str(v) for k, v in asdict(options).items()}
    context["kit_install_command"] = KIT_INSTALL_COMMANDS[options.kit_source]
    files = dict(BASE_FILES)
    files[".agentic/project.yaml"] = render_contract_yaml(
        build_contract_data(
            name=options.name,
            description=options.description,
            project_type=options.project_type,
            profiles=options.profiles,
            policy_packs=options.policy_packs,
        )
    )
    files["docs/STATUS.md"] = GENERATED_STATUS
    files["docs/handoff/CURRENT_HANDOFF.md"] = GENERATED_HANDOFF
    files["docs/architecture/ARCHITECTURE_CONTRACT.md"] = ARCHITECTURE_CONTRACT
    files["docs/DOCUMENTATION_COVERAGE.yaml"] = DOCUMENTATION_COVERAGE
    files["CHANGELOG.md"] = CHANGELOG

    if options.project_type == "governance-wrapper":
        files["docs/OUTPUT_CONTRACTS.md"] = OUTPUT_CONTRACTS
        files["docs/VALIDATION_AND_REPAIR.md"] = VALIDATION_AND_REPAIR
        files["docs/output-contracts/default-answer.yaml"] = OUTPUT_CONTRACT_SAMPLE_YAML
        files["docs/schemas/validation-report.schema.json"] = VALIDATION_REPORT_SCHEMA_JSON
        files["docs/schemas/repair-report.schema.json"] = REPAIR_REPORT_SCHEMA_JSON

    if options.project_type in {"python-cli", "python-lib"}:
        files["pyproject.toml"] = PYPROJECT_PYTHON
        package_name = options.name.replace("-", "_")
        files[f"src/{package_name}/__init__.py"] = '__version__ = "0.1.0"\n'
        files["tests/test_smoke.py"] = "def test_smoke():\n    assert True\n"

    if options.github_actions:
        files[".github/workflows/ci.yml"] = CI

    if options.pre_commit:
        files[".pre-commit-config.yaml"] = PRECOMMIT

    for rel_path, template in files.items():
        content = render_template_string(template, context)
        write_file(target / rel_path, content, overwrite=overwrite)

    subprocess.run(["git", "init"], cwd=target, check=False)
