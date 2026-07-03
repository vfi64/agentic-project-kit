from __future__ import annotations

from pathlib import Path

from agentic_project_kit.absolute_path_portability_audit import (
    audit_absolute_path_portability,
    render_absolute_path_portability_audit,
)


def test_absolute_path_audit_blocks_current_absolute_user_path(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "guide.md"
    doc.parent.mkdir()
    doc.write_text("Use /Users/hof/project/script.py now.\n", encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is False
    assert result.blockers
    assert result.blockers[0].classification == "absolute_path_blocker"


def test_absolute_path_audit_skips_tmp_tree(tmp_path: Path) -> None:
    log = tmp_path / "tmp" / "old.log"
    log.parent.mkdir()
    log.write_text("Use /Users/hof/project/script.py now.\n", encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is True
    assert result.references == ()


def test_absolute_path_audit_allows_repo_relative_agentic_tmp_path(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning.md"
    doc.parent.mkdir()
    doc.write_text("Lock path: .agentic/tmp/workspace.lock\n", encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is True
    assert result.references == ()


def test_absolute_path_audit_blocks_absolute_tmp_path(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "planning.md"
    doc.parent.mkdir()
    doc.write_text("Do not use /tmp/workspace.lock as a contract path.\n", encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is False
    assert result.blockers
    assert result.blockers[0].classification == "transient_path_reference"


def test_absolute_path_audit_allows_test_fixture(tmp_path: Path) -> None:
    test_file = tmp_path / "tests" / "test_example.py"
    test_file.parent.mkdir()
    test_file.write_text('PATH = "/Users/hof/project/script.py"\n', encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is True
    assert result.references
    assert result.references[0].classification in {
        "safe_generated_or_test_context",
        "test_fixture",
    }


def test_render_absolute_path_audit_reports_counts(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "guide.md"
    doc.parent.mkdir()
    doc.write_text("Use /home/user/project/script.py now.\n", encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)
    rendered = render_absolute_path_portability_audit(result)

    assert "ABSOLUTE_PATH_PORTABILITY_AUDIT" in rendered
    assert "STATUS=FAIL" in rendered
    assert "BLOCKER_COUNT=1" in rendered

def test_absolute_path_audit_skips_venv_like_trees(tmp_path: Path) -> None:
    sbom = tmp_path / ".venv313" / "lib" / "package.json"
    sbom.parent.mkdir(parents=True)
    sbom.write_text('{"url": "file:///Users/runner/work/pkg/pkg"}\n', encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is True
    assert result.references == ()


def test_absolute_path_audit_skips_generated_screen_output(tmp_path: Path) -> None:
    output = tmp_path / "Screen-Control_Output.txt"
    output.write_text("PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit\n", encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is True
    assert result.references == ()


def test_absolute_path_audit_classifies_audit_patterns_as_implementation(tmp_path: Path) -> None:
    module = tmp_path / "src" / "agentic_project_kit" / "absolute_path_portability_audit.py"
    module.parent.mkdir(parents=True)
    module.write_text('re.compile(r"/tmp/[^\\\\s]+")\n', encoding="utf-8")

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is True
    assert result.references
    assert result.references[0].classification == "audit_implementation"

def test_absolute_path_audit_blocks_source_path_even_with_historical_word(tmp_path: Path) -> None:
    module = tmp_path / "src" / "agentic_project_kit" / "leak.py"
    module.parent.mkdir(parents=True)
    module.write_text(
        '# used to test local dev setup at /Users/hof/project\n',
        encoding="utf-8",
    )

    result = audit_absolute_path_portability(tmp_path)

    assert result.ok is False
    assert result.blockers
    assert result.blockers[0].classification == "absolute_path_blocker"
