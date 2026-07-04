from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.path_literal_audit import (
    audit_path_literals,
    render_path_literal_audit,
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
    assert payload["modules"][0]["path"] == "src/demo.py"


def test_audit_path_literals_always_exit_zero(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text('TMP = "tmp/cache"\n', encoding="utf-8")

    result = CliRunner().invoke(app, ["audit-path-literals", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "STATUS=REPORT" in result.output
    assert "LITERAL_COUNT=1" in result.output


def test_render_path_literal_audit_lists_modules(tmp_path: Path) -> None:
    module = tmp_path / "src" / "demo.py"
    module.parent.mkdir()
    module.write_text('DOC = "docs/readme.md"\n', encoding="utf-8")

    rendered = render_path_literal_audit(audit_path_literals(tmp_path))

    assert "PATH_LITERAL_AUDIT" in rendered
    assert "MODULE=1|src/demo.py" in rendered
