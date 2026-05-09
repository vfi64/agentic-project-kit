from pathlib import Path

from agentic_project_kit.checks import check_docs, check_todo


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
    (tmp_path / "README.md").write_text("# Title\n", encoding="utf-8")

    errors = check_docs(tmp_path)

    assert errors
    assert "missing required section" in errors[0]


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
