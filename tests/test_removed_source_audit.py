from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.removed_source_audit import build_removed_source_audit


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_project(root: Path) -> None:
    _write(
        root / "docs/planning/PROJECT_DIRECTION.yaml",
        """
plans:
  - id: cleanup
    preserved_information:
      removed_source:
        path: docs/planning/OLD_NOTE.md
        status: removed_source
        central_target: docs/planning/PROJECT_DIRECTION.yaml
    source_files:
      - docs/planning/PROJECT_DIRECTION.yaml
""".lstrip(),
    )
    _write(root / "docs/DOCUMENTATION_REGISTRY.yaml", "documents: []\n")
    _write(root / "docs/DOCUMENTATION_COVERAGE.yaml", "documents: []\n")
    _write(root / "docs/DOC_REGISTRY_SCOPE.yaml", "required_paths: []\n")


def test_removed_source_audit_passes_when_only_central_removed_source_metadata_remains(tmp_path: Path) -> None:
    _minimal_project(tmp_path)

    result = build_removed_source_audit(tmp_path)

    assert result.result_status == "PASS"
    assert result.audited_count == 1
    assert result.findings[0].path == "docs/planning/OLD_NOTE.md"
    assert result.findings[0].ok


def test_removed_source_audit_fails_on_existing_removed_file(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    _write(tmp_path / "docs/planning/OLD_NOTE.md", "# Old\n")

    result = build_removed_source_audit(tmp_path)

    assert result.result_status == "FAIL"
    assert result.findings[0].exists is True


def test_removed_source_audit_fails_on_live_ref_outside_central_target(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    _write(tmp_path / "docs/planning/LIVE.md", "See docs/planning/OLD_NOTE.md\n")

    result = build_removed_source_audit(tmp_path)

    assert result.result_status == "FAIL"
    assert result.findings[0].live_refs == [
        "docs/planning/LIVE.md:1:See docs/planning/OLD_NOTE.md"
    ]


def test_removed_source_audit_fails_on_source_files_style_ref(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    p = tmp_path / "docs/planning/PROJECT_DIRECTION.yaml"
    p.write_text(
        p.read_text(encoding="utf-8")
        + "\nextra:\n  source_files:\n      - docs/planning/OLD_NOTE.md\n",
        encoding="utf-8",
    )

    result = build_removed_source_audit(tmp_path)

    assert result.result_status == "FAIL"
    refs = result.findings[0].source_file_style_refs
    assert len(refs) == 1
    assert refs[0].startswith("docs/planning/PROJECT_DIRECTION.yaml:")
    assert refs[0].endswith(":- docs/planning/OLD_NOTE.md")


def test_removed_source_audit_cli_json(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["docs", "removed-source-audit", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["audited_count"] == 1


def test_removed_source_audit_cli_fails_for_specific_path(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    _write(tmp_path / "tests/test_old_note.py", 'OLD = "docs/planning/OLD_NOTE.md"\n')
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "docs",
            "removed-source-audit",
            "--root",
            str(tmp_path),
            "--path",
            "docs/planning/OLD_NOTE.md",
        ],
    )

    assert result.exit_code == 1
    assert "LIVE_REF tests/test_old_note.py:1:OLD = \"docs/planning/OLD_NOTE.md\"" in result.output
