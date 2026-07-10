from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.path_literal_audit import (
    audit_path_literals,
    render_path_literal_audit,
    render_path_literal_evidence_report,
)


def test_audit_path_literals_counts_known_fixture(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo" / "paths.py"
    module.parent.mkdir(parents=True)
    module.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                'DOC = "docs/guide.md"',
                'TMP = "tmp/cache"',
                'DOC_PATH = Path("docs") / "guide.md"',
                'TMP_PATH = Path("tmp") / "cache"',
                'BOTH = "docs/a.md" + "docs/b.md"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = audit_path_literals(tmp_path)

    assert result.status == "REPORT"
    assert result.returncode == 0
    assert result.affected_module_count == 1
    assert result.literal_count == 6
    assert result.modules[0].path == "src/demo/paths.py"
    assert result.modules[0].patterns == {
        "path_docs": 1,
        "path_tmp": 1,
        "quoted_docs": 3,
        "quoted_tmp": 1,
    }
    assert result.modules[0].classification.kind == "active_path_literal"
    assert result.active_path_literal_count == 6


def test_audit_path_literals_json_shape(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text('DOC = "docs/readme.md"\n', encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["audit-path-literals", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["kind"] == "path_literal_audit"
    assert payload["status"] == "REPORT"
    assert payload["affected_module_count"] == 1
    assert payload["literal_count"] == 1
    assert payload["active_path_literal_count"] == 0
    assert payload["classification_summary"]["reference_or_message"]["literal_count"] == 1
    assert payload["modules"][0]["path"] == "src/demo.py"
    assert payload["modules"][0]["classification"]["kind"] == "reference_or_message"


def test_audit_path_literals_always_exit_zero(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text('TMP = "tmp/cache"\n', encoding="utf-8")

    result = CliRunner().invoke(app, ["audit-path-literals", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "STATUS=REPORT" in result.output
    assert "LITERAL_COUNT=1" in result.output
    assert "ACTIVE_PATH_LITERAL_COUNT=0" in result.output


def test_render_path_literal_audit_lists_modules(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text('DOC = "docs/readme.md"\n', encoding="utf-8")

    rendered = render_path_literal_audit(audit_path_literals(tmp_path))

    assert "PATH_LITERAL_AUDIT" in rendered
    assert "MODULE=1|src/demo.py" in rendered
    assert "classification=reference_or_message" in rendered


def test_audit_path_literals_declares_template_data_exception(tmp_path: Path) -> None:
    module = tmp_path / "src" / "agentic_project_kit" / "templates.py"
    module.parent.mkdir(parents=True)
    module.write_text(
        'from pathlib import Path\nTEMPLATE = "docs/STATUS.md"\nTMP = Path("tmp") / "cache"\n',
        encoding="utf-8",
    )

    result = audit_path_literals(tmp_path)

    assert result.literal_count == 2
    assert result.active_path_literal_count == 0
    assert result.modules[0].classification.kind == "template_data"
    assert result.declared_exception_modules[0].path == "src/agentic_project_kit/templates.py"


def test_audit_path_literals_reports_repo_identity_literals(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text(
        'REPO = "vfi64/agentic-project-kit"\nURL = "https://github.com/vfi64/agentic-project-kit"\n',
        encoding="utf-8",
    )

    result = audit_path_literals(tmp_path)
    rendered = render_path_literal_audit(result)

    assert result.literal_count == 0
    assert result.repo_identity_literal_count == 3
    assert result.repo_identity_modules[0].patterns == {
        "github_url": 1,
        "repo_slug_prefix": 2,
    }
    assert "REPO_IDENTITY_LITERALS:" in rendered
    assert "REPO_IDENTITY=3|src/demo.py" in rendered


def test_path_literal_evidence_report_includes_classification_and_repo_identity(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text(
        'DOC = "docs/readme.md"\nREPO = "vfi64/agentic-project-kit"\n',
        encoding="utf-8",
    )

    report = render_path_literal_evidence_report(audit_path_literals(tmp_path))

    assert "## Path Literal Classifications" in report
    assert "reference_or_message" in report
    assert "## Repo Identity Literals" in report
    assert "Repo identity literal count: 1" in report
