# Validate report schema usability start

Date: 2026-05-12
Branch: feature/validate-report-schema-usability

## Git status
?? docs/reports/validate_report_schema_usability_start_20260512.md

## Recent commits
399dd4f Document output transfer rule for agent workflows (#103)
6c27019 Finalize docs after v0.2.10 release (#102)
81ffe39 Update docs with v0.2.10 Zenodo DOI (#101)
4a9b91b Update docs after v0.2.10 GitHub release (#100)
bf12e6f Prepare v0.2.10 release metadata (#99)
6f6724c Update docs after validation report schema file (#98)
97055c5 Generate validation report JSON schema file (#97)
1e67524 Finalize docs after v0.2.9 release (#96)

## CLI references
src/agentic_project_kit/release.py:121:def build_release_state_report(
src/agentic_project_kit/release.py:281:def render_release_state_report(report: ReleaseStateReport) -> str:
src/agentic_project_kit/release.py:282:    lines = [f"Release state check for target v{report.version}", ""]
src/agentic_project_kit/release.py:283:    for check in report.checks:
src/agentic_project_kit/release.py:286:    lines.append("Overall: PASS" if report.ok else "Overall: FAIL")
src/agentic_project_kit/post_release.py:45:def build_post_release_report(
src/agentic_project_kit/post_release.py:182:def render_post_release_report(report: PostReleaseReport) -> str:
src/agentic_project_kit/post_release.py:183:    lines = [f"Post-release check for target v{report.version}", ""]
src/agentic_project_kit/post_release.py:184:    for check in report.checks:
src/agentic_project_kit/post_release.py:187:    lines.append("Overall: PASS" if report.ok else "Overall: FAIL")
src/agentic_project_kit/templates.py:8:BASE_FILES = {'README.md': '# $name\n\n$description\n\n## Purpose\n\nDescribe the purpose of the project here.\n\n## Quick Start\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\n```\n\n## Agentic Development\n\nThis project uses agent-facing documentation and local quality gates.\n\nStart with:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Status\n\nDo not store volatile status in this README. Use `docs/STATUS.md`.\n', 'AGENTS.md': '# AGENTS.md\n\n## Mission\n\nPreserve correctness, traceability, testability, and maintainability.\n\nDo not only satisfy the immediate request. Prefer the best technically sound solution within project constraints.\n\n## Source-of-truth hierarchy\n\n1. `.agentic/project.yaml`\n2. normative project specification, if present\n3. current code and tests\n4. `docs/STATUS.md`\n5. `docs/handoff/CURRENT_HANDOFF.md`\n6. historical archive files\n\nIf documentation, code, and tests disagree, report the discrepancy instead of guessing.\n\n## Agent read order\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `docs/PROJECT_START.md`\n4. `docs/STATUS.md`\n5. `docs/TEST_GATES.md`\n6. `docs/LOGGING_AND_EVIDENCE.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n8. relevant source files and tests\n\n## Work rules\n\n- Keep stable rules separate from volatile status.\n- Add or update tests for meaningful behavior changes.\n- Prefer outcome evidence over output claims.\n- Do not claim success without running the relevant gates.\n- Do not commit secrets, local credentials, or broad raw logs.\n- Use bounded diagnostic logs only when needed for troubleshooting.\n\n## Closeout template\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Changed files:\n- Tests run:\n- Tests not run:\n- Remaining risks:\n- Next safe step:\n```\n', 'docs/PROJECT_START.md': '# Project Start\n\n## Purpose\n\nThis file guides the initial setup after repository generation.\n\n## Generated Structure\n\nThis project was generated with agent-facing documentation, a machine-readable project contract, status and handoff files, a test-gate matrix, bootstrap task items, logging/evidence conventions, and optional GitHub workflow/pre-commit templates.\n\n## Required First Decisions\n\n- [ ] Review `.agentic/project.yaml` profiles and policy packs.\n- [ ] Choose or confirm project license.\n- [ ] Define the primary runtime entrypoint.\n- [ ] Define supported runtime versions.\n- [ ] Decide whether bounded diagnostic logs may be committed.\n- [ ] Define protected branches.\n- [ ] Define release strategy.\n- [ ] Review agent instructions.\n\n## First Local Commands\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate\npip install -e ".[dev]"\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## First GitHub Setup\n\n- [ ] Create GitHub repository.\n- [ ] Push initial commit.\n- [ ] Enable branch protection for `main`.\n- [ ] Enable GitHub Actions.\n- [ ] Enable secret scanning if available.\n- [ ] Review `.github/copilot-instructions.md`.\n\n## Agent Onboarding\n\nA new agent should read:\n\n1. `AGENTS.md`\n2. `.agentic/project.yaml`\n3. `.github/copilot-instructions.md`\n4. `docs/PROJECT_START.md`\n5. `docs/STATUS.md`\n6. `docs/TEST_GATES.md`\n7. `docs/handoff/CURRENT_HANDOFF.md`\n\n## Before First Feature\n\n- [ ] Update `README.md` with the real project goal.\n- [ ] Update `docs/STATUS.md`.\n- [ ] Update `docs/TEST_GATES.md`.\n- [ ] Add first meaningful tests.\n- [ ] Run all checks.\n', 'docs/STATUS.md': '# Project Status\n\nStatus-date: TODO\nProject: $name\nPrimary branch: main\nRuntime entrypoint: TODO\nProject contract: `.agentic/project.yaml`\n\n## Purpose\n\nThis is the compact current-state dashboard.\n\nIt must not become a long history file.\n\n## Current Goal\n\nTODO: define the current project goal.\n\n## Current Blockers\n\n- TODO\n\n## Live Status Commands\n\n```bash\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n```\n\n## Next Safe Step\n\nTODO\n', 'docs/TEST_GATES.md': '# Test Gates\n\n## Purpose\n\nThis file maps task types to required evidence.\n\n## Gate Matrix\n\n| Change type | Required evidence |\n|---|---|\n| Documentation only | `agentic-kit check-docs` |\n| task/status change | `agentic-kit check-todo` |\n| Project contract/profile change | `agentic-kit doctor` |\n| Python code | `pytest -q` and `ruff check .` if enabled |\n| CLI behavior | CLI tests plus local command smoke test |\n| Logging/evidence change | check generated logs for secrets and size |\n| GitHub workflow change | local syntax review and CI run |\n| Agent workflow change | docs check and handoff review |\n\n## Outcome Reporting\n\nUse this closeout shape:\n\n```text\n- Intended outcome:\n- Required evidence:\n- Outcome achieved: yes / no / partial\n- Evidence:\n- Remaining gap:\n- Tests run:\n- Tests not run:\n```\n', 'docs/LOGGING_AND_EVIDENCE.md': '# Logging and Evidence\n\n## Purpose\n\nLogs are diagnostic evidence, not automatic source material.\n\n## Recommended Layout\n\n```text\nLogs/\n  Audit/\n  ManualTests/\n  TestRuns/\ntmp/\n  agent-evidence/\n```\n\n## Rules\n\n- Do not commit secrets.\n- Do not commit broad raw logs by default.\n- Commit only bounded recent evidence when needed.\n- Inspect staged logs before committing.\n- Validation reports from `agentic-kit validate-output-contract --report` are bounded audit evidence when they are intentionally written to a reviewed path such as `tmp/agent-evidence/` or a PR-specific evidence folder.\n- Do not auto-stage validation reports by default; inspect them before committing.\n\n## Agent Use\n\nAgents should use logs to diagnose failures, not to infer undocumented project rules.\n', 'docs/handoff/CURRENT_HANDOFF.md': '# Current Handoff\n\nStatus-date: TODO\nProject: $name\nBranch: main\nProject contract: `.agentic/project.yaml`\n\n## Current goal\n\nTODO\n\n## Current source of truth\n\n1. `.agentic/project.yaml`\n2. `AGENTS.md`\n3. `docs/STATUS.md`\n4. current code and tests\n\n## Latest closeout\n\nNo closeout yet.\n\n## Next step\n\nTODO\n', 'docs/handoff/STANDARD_AGENT_PROMPT.md': '# Standard Agent Prompt\n\n```text\nYou are working in this repository.\n\nStart by reading:\n\n1. AGENTS.md\n2. .agentic/project.yaml\n3. docs/PROJECT_START.md\n4. docs/STATUS.md\n5. docs/TEST_GATES.md\n6. docs/handoff/CURRENT_HANDOFF.md\n\nDo not infer current state from memory.\nRun or request:\n\ngit status --short\npytest -q\nagentic-kit check\nagentic-kit doctor\n\nFor substantial work, close with:\n\n- Intended outcome:\n- Required evidence:\n- Outcome achieved:\n- Changed files:\n- Tests run:\n- Remaining risks:\n```\n', 'docs/TODO.md': '# TODO\n\nThis file is generated from `.agentic/todo.yaml`.\n\n## Bootstrap\n\n- [ ] **BOOT-001** Choose or confirm license  \n  Owner: human  \n  Priority: high  \n  Evidence required: `LICENSE` reviewed\n\n- [ ] **BOOT-002** Define runtime entrypoint  \n  Owner: human  \n  Priority: high  \n  Evidence required: `README.md` and `docs/STATUS.md` updated\n\n- [ ] **BOOT-003** Run initial local quality gate  \n  Owner: agent  \n  Priority: high  \n  Evidence required: `pytest -q` and `agentic-kit check` passed\n\n- [ ] **BOOT-004** Review project contract profiles and policy packs  \n  Owner: human  \n  Priority: high  \n  Evidence required: `.agentic/project.yaml` reviewed\n\n- [ ] **BOOT-005** Enable branch protection on GitHub  \n  Owner: human  \n  Priority: medium  \n  Evidence required: branch protection enabled\n', '.agentic/todo.yaml': 'items:\n  - id: BOOT-001\n    title: Choose or confirm license\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: LICENSE reviewed\n  - id: BOOT-002\n    title: Define runtime entrypoint\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: README.md and docs/STATUS.md updated\n  - id: BOOT-003\n    title: Run initial local quality gate\n    owner: agent\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: pytest -q and agentic-kit check passed\n  - id: BOOT-004\n    title: Review project contract profiles and policy packs\n    owner: human\n    priority: high\n    status: open\n    blocking: true\n    evidence_required: .agentic/project.yaml reviewed\n  - id: BOOT-005\n    title: Enable branch protection on GitHub\n    owner: human\n    priority: medium\n    status: open\n    blocking: false\n    evidence_required: branch protection enabled\n', 'sentinel.yaml': 'documents:\n  - path: README.md\n    required_sections:\n      - "## Purpose"\n      - "## Quick Start"\n    max_words: 2000\n  - path: AGENTS.md\n    required_sections:\n      - "## Mission"\n      - "## Agent read order"\n      - "## Closeout template"\n    max_words: 2500\n  - path: docs/STATUS.md\n    required_sections:\n      - "## Current Goal"\n      - "## Next Safe Step"\n    max_words: 1200\n  - path: docs/TEST_GATES.md\n    required_sections:\n      - "## Gate Matrix"\n      - "## Outcome Reporting"\n    max_words: 1600\ntodo:\n  path: .agentic/todo.yaml\n', '.github/copilot-instructions.md': '# Copilot Instructions\n\nFollow the repository rules in `AGENTS.md`.\n\nBefore claiming completion, run or request the relevant commands from `docs/TEST_GATES.md`.\n\nDo not commit secrets, broad raw logs, virtual environments, or local-only configuration.\n', '.github/pull_request_template.md': '## Intended outcome\n\n## Required evidence\n\n## Outcome achieved\n\n- [ ] yes\n- [ ] no\n- [ ] partial\n\n## Tests run\n\n## Risks / remaining gaps\n', '.github/ISSUE_TEMPLATE/agent_regression.yml': 'name: Agent regression\ndescription: Report an agent workflow or handoff regression\ntitle: "[Agent Regression]: "\nlabels: ["agent", "regression"]\nbody:\n  - type: textarea\n    id: observed\n    attributes:\n      label: Observed behavior\n    validations:\n      required: true\n  - type: textarea\n    id: expected\n    attributes:\n      label: Expected behavior\n    validations:\n      required: true\n  - type: textarea\n    id: evidence\n    attributes:\n      label: Evidence / logs\n    validations:\n      required: false\n', 'scripts/stage_recent_logs.py': 'from pathlib import Path\nimport shutil\n\nLOG_ROOTS = [Path("Logs/Audit"), Path("Logs/ManualTests"), Path("Logs/TestRuns")]\nTARGET = Path("tmp/agent-evidence")\n\n\ndef main(max_files: int = 10) -> None:\n    TARGET.mkdir(parents=True, exist_ok=True)\n    for root in LOG_ROOTS:\n        if not root.exists():\n            continue\n        files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.stat().st_mtime)\n        for src in files[-max_files:]:\n            rel = src.relative_to(root)\n            dst = TARGET / root.name / rel\n            dst.parent.mkdir(parents=True, exist_ok=True)\n            shutil.copy2(src, dst)\n    print(f"Staged bounded evidence in {TARGET}")\n\n\nif __name__ == "__main__":\n    main()\n'}
src/agentic_project_kit/templates.py:31:VALIDATION_REPORT_SCHEMA_JSON = '{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "additionalProperties": false,\n  "properties": {\n    "checked_file": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract": {\n      "minLength": 1,\n      "type": "string"\n    },\n    "contract_version": {\n      "minimum": 1,\n      "type": "integer"\n    },\n    "findings": {\n      "items": {\n        "additionalProperties": false,\n        "properties": {\n          "code": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "message": {\n            "minLength": 1,\n            "type": "string"\n          },\n          "severity": {\n            "enum": [\n              "info",\n              "warning",\n              "error"\n            ],\n            "type": "string"\n          }\n        },\n        "required": [\n          "severity",\n          "code",\n          "message"\n        ],\n        "type": "object"\n      },\n      "type": "array"\n    },\n    "ok": {\n      "type": "boolean"\n    }\n  },\n  "required": [\n    "ok",\n    "contract",\n    "contract_version",\n    "checked_file",\n    "findings"\n  ],\n  "title": "agentic-project-kit validation report",\n  "type": "object"\n}\n'
src/agentic_project_kit/templates.py:57:Use agentic-kit validate-output-contract when an output should be checked against a machine-readable output-contract YAML file.
src/agentic_project_kit/templates.py:61:    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml
src/agentic_project_kit/templates.py:63:For audit evidence, write a machine-readable JSON report:
src/agentic_project_kit/templates.py:65:    agentic-kit validate-output-contract output.md --contract docs/output-contracts/default-answer.yaml --report validation-report.json
src/agentic_project_kit/templates.py:67:The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`.
src/agentic_project_kit/templates.py:85:The report shape is intentionally small and structural so CI, wrappers, and review scripts can consume it without parsing human console output.
src/agentic_project_kit/templates.py:87:Generated governance-wrapper projects also include `docs/schemas/validation-report.schema.json` as the machine-readable schema for this report shape.
src/agentic_project_kit/templates.py:102:- If repair fails, report a clear contract failure.
src/agentic_project_kit/templates.py:234:        files["docs/schemas/validation-report.schema.json"] = VALIDATION_REPORT_SCHEMA_JSON
src/agentic_project_kit/cli.py:18:from agentic_project_kit.doctor import build_doctor_report, render_doctor_report
src/agentic_project_kit/cli.py:20:from agentic_project_kit.post_release import build_post_release_report, render_post_release_report
src/agentic_project_kit/cli.py:23:    build_release_state_report,
src/agentic_project_kit/cli.py:25:    render_release_state_report,
src/agentic_project_kit/cli.py:203:    report = build_doctor_report(project_root.resolve())
src/agentic_project_kit/cli.py:204:    console.print(render_doctor_report(report), markup=False)
src/agentic_project_kit/cli.py:205:    if not report.ok:
src/agentic_project_kit/cli.py:225:    report = build_release_state_report(project_root.resolve(), version=version)
src/agentic_project_kit/cli.py:226:    console.print(render_release_state_report(report), markup=False)
src/agentic_project_kit/cli.py:227:    if not report.ok:
src/agentic_project_kit/cli.py:237:    report = build_post_release_report(project_root.resolve(), version=version)
src/agentic_project_kit/cli.py:238:    console.print(render_post_release_report(report), markup=False)
src/agentic_project_kit/cli.py:239:    if not report.ok:
src/agentic_project_kit/cli.py:313:@app.command("validate-output-contract")
src/agentic_project_kit/cli.py:314:def validate_output_contract(
src/agentic_project_kit/cli.py:317:    report_path: Path | None = typer.Option(None, "--report", help="Write a JSON validation report."),
src/agentic_project_kit/cli.py:328:    report = validate_output_against_contract(output_path.read_text(encoding="utf-8"), contract)
src/agentic_project_kit/cli.py:329:    if report_path is not None:
src/agentic_project_kit/cli.py:331:            "ok": report.ok,
src/agentic_project_kit/cli.py:335:            "findings": report.to_dict()["findings"],
src/agentic_project_kit/cli.py:337:        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
src/agentic_project_kit/cli.py:339:    if report.ok:
src/agentic_project_kit/cli.py:343:    for finding in report.findings:
src/agentic_project_kit/cli.py:362:    report = validate_required_sections(path.read_text(encoding="utf-8"), tuple(required_section))
src/agentic_project_kit/cli.py:363:    if report.ok:
src/agentic_project_kit/cli.py:367:    for finding in report.findings:
src/agentic_project_kit/doctor.py:41:def build_doctor_report(project_root: Path) -> DoctorReport:
src/agentic_project_kit/doctor.py:42:    """Build a compact health report for an agentic project checkout."""
src/agentic_project_kit/doctor.py:59:def render_doctor_report(report: DoctorReport) -> str:
src/agentic_project_kit/doctor.py:60:    lines = [f"Agentic project doctor report for {report.project_root}", ""]
src/agentic_project_kit/doctor.py:61:    for check in report.checks:
src/agentic_project_kit/doctor.py:63:    lines.extend(["", f"Overall: {'PASS' if report.ok else 'FAIL'}"])
tests/test_release.py:8:    build_release_state_report,
tests/test_release.py:10:    render_release_state_report,
tests/test_release.py:63:def test_build_release_state_report_passes_for_unused_version(tmp_path: Path):
tests/test_release.py:66:    report = build_release_state_report(tmp_path, command_runner=_runner())
tests/test_release.py:68:    assert report.ok
tests/test_release.py:69:    assert [check.status for check in report.checks] == [ReleaseCheckStatus.PASS] * 7
tests/test_release.py:72:def test_build_release_state_report_warns_without_git_repo(tmp_path: Path):
tests/test_release.py:75:    report = build_release_state_report(tmp_path)
tests/test_release.py:77:    assert report.ok
tests/test_release.py:78:    assert report.checks[-3].status == ReleaseCheckStatus.WARN
tests/test_release.py:79:    assert report.checks[-3].detail
tests/test_release.py:80:    assert report.checks[-3].name == "local tag unused"
tests/test_release.py:83:def test_build_release_state_report_warns_when_remote_tag_check_is_unavailable(tmp_path: Path):
tests/test_release.py:86:    report = build_release_state_report(
tests/test_release.py:91:    assert report.ok
tests/test_release.py:92:    assert report.checks[-2].status == ReleaseCheckStatus.WARN
tests/test_release.py:93:    assert report.checks[-2].name == "remote tag unused"
tests/test_release.py:96:def test_build_release_state_report_warns_when_github_release_check_is_unavailable(tmp_path: Path):
tests/test_release.py:99:    report = build_release_state_report(
tests/test_release.py:104:    assert report.ok
tests/test_release.py:105:    assert report.checks[-1].status == ReleaseCheckStatus.WARN
tests/test_release.py:106:    assert report.checks[-1].name == "GitHub release unused"
tests/test_release.py:109:def test_build_release_state_report_fails_for_missing_changelog_version(tmp_path: Path):
tests/test_release.py:113:    report = build_release_state_report(tmp_path, command_runner=_runner())
tests/test_release.py:115:    assert not report.ok
tests/test_release.py:116:    assert report.checks[1].status == ReleaseCheckStatus.FAIL
tests/test_release.py:117:    assert "missing text: v1.2.3" in report.checks[1].detail
tests/test_release.py:120:def test_build_release_state_report_fails_for_existing_local_tag(tmp_path: Path):
tests/test_release.py:123:    report = build_release_state_report(tmp_path, command_runner=_runner(local_tag=CommandResult(0, "v1.2.3\n", "")))
tests/test_release.py:125:    assert not report.ok
tests/test_release.py:126:    assert report.checks[-3].status == ReleaseCheckStatus.FAIL
tests/test_release.py:127:    assert report.checks[-3].detail == "tag already exists: v1.2.3"
tests/test_release.py:130:def test_build_release_state_report_fails_for_existing_remote_tag(tmp_path: Path):
tests/test_release.py:133:    report = build_release_state_report(
tests/test_release.py:138:    assert not report.ok
tests/test_release.py:139:    assert report.checks[-2].status == ReleaseCheckStatus.FAIL
tests/test_release.py:140:    assert report.checks[-2].detail == "remote tag already exists: v1.2.3"
tests/test_release.py:143:def test_build_release_state_report_fails_for_existing_github_release(tmp_path: Path):
tests/test_release.py:146:    report = build_release_state_report(tmp_path, command_runner=_runner(github_release=CommandResult(0, "title: v1.2.3\n", "")))
tests/test_release.py:148:    assert not report.ok
tests/test_release.py:149:    assert report.checks[-1].status == ReleaseCheckStatus.FAIL
tests/test_release.py:150:    assert report.checks[-1].detail == "GitHub release already exists: v1.2.3"
tests/test_release.py:153:def test_render_release_state_report_shows_overall_status(tmp_path: Path):
tests/test_release.py:156:    rendered = render_release_state_report(build_release_state_report(tmp_path, command_runner=_runner()))
tests/test_generator.py:107:    from agentic_project_kit.doctor import build_doctor_report
tests/test_generator.py:130:    assert build_doctor_report(target).ok
tests/test_generator.py:151:    assert "Validation reports from `agentic-kit validate-output-contract --report`" in evidence
tests/test_generator.py:152:    assert "Do not auto-stage validation reports by default" in evidence
tests/test_generator.py:157:    schema_path = target / "docs/schemas/validation-report.schema.json"
tests/test_generator.py:160:    assert "agentic-project-kit validation report" in schema_text
tests/test_generator.py:169:    assert "Use agentic-kit validate-output-contract" in validation
tests/test_generator.py:171:    assert "--report validation-report.json" in validation
tests/test_generator.py:172:    assert "The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`." in validation
tests/test_generator.py:176:    assert "docs/schemas/validation-report.schema.json" in validation
tests/test_generator.py:177:    assert "machine-readable schema for this report shape" in validation
tests/test_doctor.py:4:from agentic_project_kit.doctor import DoctorStatus, build_doctor_report, render_doctor_report
tests/test_doctor.py:14:    (root / "docs/TEST_GATES.md").write_text("## Gate Matrix\npytest\n\n## Outcome Reporting\nreport exits\n", encoding="utf-8")
tests/test_doctor.py:83:def test_doctor_report_passes_with_minimal_state_docs(tmp_path: Path):
tests/test_doctor.py:87:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:89:    assert report.ok
tests/test_doctor.py:90:    assert [check.status for check in report.checks] == [
tests/test_doctor.py:101:    assert "Overall: PASS" in render_doctor_report(report)
tests/test_doctor.py:104:def test_doctor_report_fails_without_required_readme(tmp_path: Path):
tests/test_doctor.py:107:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:109:    assert not report.ok
tests/test_doctor.py:110:    assert report.checks[1].name == "README.md"
tests/test_doctor.py:111:    assert report.checks[1].status == DoctorStatus.FAIL
tests/test_doctor.py:112:    assert "Overall: FAIL" in render_doctor_report(report)
tests/test_doctor.py:115:def test_doctor_report_reports_valid_project_contract(tmp_path: Path):
tests/test_doctor.py:120:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:122:    contract_check = report.checks[4]
tests/test_doctor.py:139:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:141:    policy_check = report.checks[5]
tests/test_doctor.py:153:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:155:    assert not report.ok
tests/test_doctor.py:156:    policy_check = report.checks[5]
tests/test_doctor.py:164:def test_doctor_report_fails_on_invalid_project_contract(tmp_path: Path):
tests/test_doctor.py:173:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:175:    assert not report.ok
tests/test_doctor.py:176:    contract_check = report.checks[4]
tests/test_doctor.py:183:def test_doctor_report_passes_when_versions_match(tmp_path: Path):
tests/test_doctor.py:188:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:190:    assert report.ok
tests/test_doctor.py:191:    version_check = report.checks[-1]
tests/test_doctor.py:197:def test_doctor_report_accepts_quoted_citation_versions(tmp_path: Path):
tests/test_doctor.py:202:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:204:    assert report.ok
tests/test_doctor.py:205:    assert report.checks[-1].status == DoctorStatus.PASS
tests/test_doctor.py:208:def test_doctor_report_fails_on_version_drift(tmp_path: Path):
tests/test_doctor.py:213:    report = build_doctor_report(tmp_path)
tests/test_doctor.py:215:    assert not report.ok
tests/test_doctor.py:216:    version_check = report.checks[-1]
tests/test_runtime_validator.py:9:def test_validation_report_ok_when_no_findings() -> None:
tests/test_runtime_validator.py:10:    report = ValidationReport(findings=())
tests/test_runtime_validator.py:12:    assert report.ok is True
tests/test_runtime_validator.py:15:def test_validation_report_not_ok_when_error_finding_exists() -> None:
tests/test_runtime_validator.py:16:    report = ValidationReport(
tests/test_runtime_validator.py:25:    assert report.ok is False
tests/test_runtime_validator.py:28:def test_validation_report_ok_with_warning_only() -> None:
tests/test_runtime_validator.py:29:    report = ValidationReport(
tests/test_runtime_validator.py:39:    assert report.ok is True
tests/test_runtime_validator.py:43:    report = validate_required_sections(
tests/test_runtime_validator.py:48:    assert report.ok is True
tests/test_runtime_validator.py:49:    assert report.findings == ()
tests/test_runtime_validator.py:52:def test_validate_required_sections_reports_missing_sections_deterministically() -> None:
tests/test_runtime_validator.py:53:    report = validate_required_sections(
tests/test_runtime_validator.py:58:    assert report.ok is False
tests/test_runtime_validator.py:59:    assert [finding.code for finding in report.findings] == [
tests/test_runtime_validator.py:63:    assert [finding.message for finding in report.findings] == [
tests/test_runtime_validator.py:69:def test_validation_report_to_dict_is_json_safe_and_deterministic() -> None:
tests/test_runtime_validator.py:70:    report = ValidationReport(
tests/test_runtime_validator.py:80:    assert report.to_dict() == {
tests/test_output_contract.py:64:    report = validate_output_against_contract("Plan\nFinal Answer", contract)
tests/test_output_contract.py:66:    assert report.ok is False
tests/test_output_contract.py:67:    assert [finding.message for finding in report.findings] == [
tests/test_output_contract.py:80:    report = validate_output_against_contract("Plan\nSolution\nCheck", contract)
tests/test_output_contract.py:82:    assert report.ok is True
tests/test_output_contract.py:83:    assert report.findings == ()
tests/test_post_release.py:7:    build_post_release_report,
tests/test_post_release.py:9:    render_post_release_report,
tests/test_post_release.py:14:def test_post_release_report_passes_with_github_release_and_verified_zenodo_record(tmp_path: Path):
tests/test_post_release.py:17:    report = build_post_release_report(
tests/test_post_release.py:23:    assert report.ok
tests/test_post_release.py:24:    assert [check.status for check in report.checks] == [
tests/test_post_release.py:29:    assert "10.5281/zenodo.1001" in report.checks[-1].detail
tests/test_post_release.py:32:def test_post_release_report_waits_when_zenodo_record_is_not_available_yet(tmp_path: Path):
tests/test_post_release.py:35:    report = build_post_release_report(
tests/test_post_release.py:41:    assert report.ok
tests/test_post_release.py:42:    assert report.checks[-1].status == PostReleaseStatus.WAITING
tests/test_post_release.py:43:    assert "leave README/CITATION unchanged" in report.checks[-1].detail
tests/test_post_release.py:46:def test_post_release_report_fails_when_github_release_is_missing(tmp_path: Path):
tests/test_post_release.py:49:    report = build_post_release_report(
tests/test_post_release.py:55:    assert not report.ok
tests/test_post_release.py:56:    assert report.checks[0].status == PostReleaseStatus.FAIL
tests/test_post_release.py:57:    assert report.checks[0].detail == "GitHub release is absent: v1.2.3"
tests/test_post_release.py:60:def test_post_release_report_warns_and_skips_zenodo_without_citation_doi(tmp_path: Path):
tests/test_post_release.py:63:    report = build_post_release_report(
tests/test_post_release.py:69:    assert report.ok
tests/test_post_release.py:70:    assert report.checks[1].status == PostReleaseStatus.WARN
tests/test_post_release.py:71:    assert report.checks[2].status == PostReleaseStatus.WARN
tests/test_post_release.py:72:    assert "lookup skipped" in report.checks[2].detail
tests/test_post_release.py:96:def test_render_post_release_report_shows_waiting_as_non_failing(tmp_path: Path):
tests/test_post_release.py:98:    report = build_post_release_report(
tests/test_post_release.py:104:    rendered = render_post_release_report(report)
tests/test_post_release.py:151:def test_post_release_report_warns_when_zenodo_lookup_times_out(tmp_path: Path):
tests/test_post_release.py:157:    report = build_post_release_report(
tests/test_post_release.py:163:    assert report.ok
tests/test_post_release.py:164:    assert report.checks[-1].status == PostReleaseStatus.WARN
tests/test_post_release.py:165:    assert report.checks[-1].detail == "Zenodo lookup failed: read operation timed out"
tests/test_validate_output_contract_cli.py:22:def test_validate_output_contract_cli_passes_for_complete_output(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:30:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
tests/test_validate_output_contract_cli.py:37:def test_validate_output_contract_cli_fails_for_missing_required_sections(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:45:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
tests/test_validate_output_contract_cli.py:53:def test_validate_output_contract_cli_fails_for_invalid_contract(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:61:        ["validate-output-contract", str(output_path), "--contract", str(contract_path)],
tests/test_validate_output_contract_cli.py:68:def test_validate_output_contract_cli_writes_json_report_for_failure(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:71:    report_path = tmp_path / "validation-report.json"
tests/test_validate_output_contract_cli.py:78:            "validate-output-contract",
tests/test_validate_output_contract_cli.py:82:            "--report",
tests/test_validate_output_contract_cli.py:83:            str(report_path),
tests/test_validate_output_contract_cli.py:88:    payload = json.loads(report_path.read_text(encoding="utf-8"))
tests/test_validate_output_contract_cli.py:109:def test_validate_output_contract_cli_writes_json_report_for_success(tmp_path: Path) -> None:
tests/test_validate_output_contract_cli.py:112:    report_path = tmp_path / "validation-report.json"
tests/test_validate_output_contract_cli.py:119:            "validate-output-contract",
tests/test_validate_output_contract_cli.py:123:            "--report",
tests/test_validate_output_contract_cli.py:124:            str(report_path),
tests/test_validate_output_contract_cli.py:129:    assert json.loads(report_path.read_text(encoding="utf-8")) == {

## Candidate files
docs/examples/minimal-python-cli.md
docs/reports/validate_report_schema_usability_start_20260512.md
docs/reports/validation_report_schema_usability_inspection_20260512.md
src/agentic_project_kit/__pycache__/cli.cpython-314.pyc
src/agentic_project_kit/__pycache__/contract.cpython-314.pyc
src/agentic_project_kit/__pycache__/output_contract.cpython-314.pyc
src/agentic_project_kit/__pycache__/runtime_validator.cpython-314.pyc
src/agentic_project_kit/cli.py
src/agentic_project_kit/contract.py
src/agentic_project_kit/output_contract.py
src/agentic_project_kit/runtime_validator.py
tests/__pycache__/test_cli.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_contract.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_generator.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_output_contract.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_runtime_validator_cli.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_runtime_validator.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_validate_contract_cli.cpython-314-pytest-9.0.3.pyc
tests/__pycache__/test_validate_output_contract_cli.cpython-314-pytest-9.0.3.pyc
tests/test_cli.py
tests/test_contract.py
tests/test_generator.py
tests/test_output_contract.py
tests/test_runtime_validator_cli.py
tests/test_runtime_validator.py
tests/test_validate_contract_cli.py
tests/test_validate_output_contract_cli.py
