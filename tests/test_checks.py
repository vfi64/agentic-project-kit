from pathlib import Path

from agentic_project_kit.checks import (
    check_docs,
    check_document_quality,
    check_documentation_coverage,
    check_state_gate_docs,
    check_todo,
)


def test_check_docs_reports_missing_section(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
documents:
  - path: README.md
    required_sections:
      - "## Purpose"
''',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Title\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    errors = check_docs(tmp_path)

    assert errors
    assert "missing required section" in errors[0]


def test_check_docs_accepts_state_gate_docs_without_sentinel(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    assert check_docs(tmp_path) == []


def test_check_docs_reports_unresolved_placeholder_markers(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
documents:
  - path: README.md
    required_sections:
      - "# Demo"
''',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n\nTODO: finish this.\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    errors = check_docs(tmp_path)

    assert "README.md: unresolved placeholder marker 'TODO'" in errors


def test_check_docs_can_disable_quality_checks_per_document(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
documents:
  - path: README.md
    required_sections:
      - "# Demo"
    quality_checks: false
''',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n\nTODO: accepted fixture text.\nrequired-term\n", encoding="utf-8")
    _write_valid_state_gate_docs(tmp_path)

    assert check_docs(tmp_path) == []


def test_check_document_quality_reports_placeholder_markers():
    errors = check_document_quality("README.md", "# Demo\n\nFIXME later\n")

    assert errors == ["README.md: unresolved placeholder marker 'FIXME'"]


def test_check_todo_accepts_valid_items(tmp_path: Path):
    (tmp_path / "sentinel.yaml").write_text(
        '''
todo:
  path: .agentic/todo.yaml
''',
        encoding="utf-8",
    )
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/todo.yaml").write_text(
        '''
items:
  - id: BOOT-001
    title: Choose license
    owner: human
    priority: high
    status: open
    evidence_required: LICENSE reviewed
''',
        encoding="utf-8",
    )

    assert check_todo(tmp_path) == []


def test_check_state_gate_docs_accepts_valid_docs(tmp_path: Path):
    _write_valid_state_gate_docs(tmp_path)

    assert check_state_gate_docs(tmp_path) == []


def test_check_state_gate_docs_reports_missing_file(tmp_path: Path):
    (tmp_path / "docs/handoff").mkdir(parents=True)
    (tmp_path / "docs/STATUS.md").write_text(
        "# Project Status\n\n## Current State\n\n## Current Goal\n\n## Next Safe Step\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/TEST_GATES.md").write_text(
        "# Test Gates\n\n## Gate Matrix\n\n## Outcome Reporting\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        "# Current Handoff\n\n## Current Repository State\n\n## Source of Truth\n\n## Next Safe Step\n",
        encoding="utf-8",
    )

    errors = check_state_gate_docs(tmp_path)

    assert "Missing state gate document: docs/architecture/ARCHITECTURE_CONTRACT.md" in errors
    assert "Missing state gate document: docs/DOCUMENTATION_COVERAGE.yaml" in errors


def test_check_state_gate_docs_reports_missing_architecture_contract_section(tmp_path: Path):
    _write_valid_state_gate_docs(tmp_path)
    contract_path = tmp_path / "docs/architecture/ARCHITECTURE_CONTRACT.md"
    contract_path.write_text(
        "# Architecture Contract and Roadmap\n\n## 1. Executive Summary\n",
        encoding="utf-8",
    )

    errors = check_state_gate_docs(tmp_path)

    assert (
        "docs/architecture/ARCHITECTURE_CONTRACT.md: missing state gate section "
        "'## 7. Architectural Contract'"
    ) in errors


def test_check_state_gate_docs_reports_stale_handoff_marker(tmp_path: Path):
    _write_valid_state_gate_docs(tmp_path)
    handoff_path = tmp_path / "docs/handoff/CURRENT_HANDOFF.md"
    handoff_path.write_text(
        handoff_path.read_text(encoding="utf-8")
        + "\nRun the local gate, inspect the diff, then commit the documentation-state update.\n",
        encoding="utf-8",
    )

    errors = check_state_gate_docs(tmp_path)

    assert errors == [
        "docs/handoff/CURRENT_HANDOFF.md: stale handoff marker "
        "'Run the local gate, inspect the diff, then commit the documentation-state update'"
    ]


def test_check_documentation_coverage_accepts_valid_matrix(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\nrequired-term\n", encoding="utf-8")
    _write_valid_coverage_matrix(tmp_path)

    assert check_documentation_coverage(tmp_path) == []


def test_check_documentation_coverage_reports_missing_term(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    _write_valid_coverage_matrix(tmp_path)

    errors = check_documentation_coverage(tmp_path)

    assert errors == [
        "documentation coverage demo-rule: README.md missing term 'required-term'",
    ]


def test_check_documentation_coverage_reports_missing_matrix(tmp_path: Path):
    errors = check_documentation_coverage(tmp_path)

    assert errors == ["Missing state gate document: docs/DOCUMENTATION_COVERAGE.yaml"]


def _write_valid_state_gate_docs(project_root: Path) -> None:
    (project_root / "docs/handoff").mkdir(parents=True)
    (project_root / "docs/architecture").mkdir(parents=True)
    (project_root / "docs/STATUS.md").write_text(
        "# Project Status\n\n## Current State\n\n## Current Goal\n\n## Next Safe Step\n",
        encoding="utf-8",
    )
    (project_root / "docs/TEST_GATES.md").write_text(
        "# Test Gates\n\n## Gate Matrix\n\n## Standard Local Gate\n\n## Maintenance Rule\n\n## Outcome Reporting\n",
        encoding="utf-8",
    )
    (project_root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        "# Current Handoff\n\n## Current Repository State\n\n## Source of Truth\n\n## Next Safe Step\n",
        encoding="utf-8",
    )
    (project_root / "docs/architecture/ARCHITECTURE_CONTRACT.md").write_text(
        "# Architecture Contract and Roadmap\n\n"
        "## 1. Executive Summary\n\n"
        "## 2. How to Use This Document\n\n"
        "## 4. Decision Rules\n\n"
        "## 7. Architectural Contract\n\n"
        "## 16. Acceptance Criteria for Future Work\n",
        encoding="utf-8",
    )
    _write_valid_coverage_matrix(project_root)


def _write_valid_coverage_matrix(project_root: Path) -> None:
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "docs/DOCUMENTATION_COVERAGE.yaml").write_text(
        '''
version: 1
rules:
  - id: demo-rule
    documents:
      - path: README.md
        terms:
          - required-term
''',
        encoding="utf-8",
    )
