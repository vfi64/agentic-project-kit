from __future__ import annotations

from pathlib import Path

from agentic_project_kit.program_redundancy_audit import (
    audit_program_redundancy,
    render_program_redundancy_audit,
)


def test_program_redundancy_audit_blocks_shell_true(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "bad.py"
    src.parent.mkdir(parents=True)
    src.write_text("import subprocess\nsubprocess.run('x', shell=True)\n", encoding="utf-8")

    result = audit_program_redundancy(tmp_path)

    assert result.ok is False
    assert result.blockers
    assert result.blockers[0].kind == "shell_true"


def test_program_redundancy_audit_blocks_duplicate_cli_command(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "cli.py"
    src.parent.mkdir(parents=True)
    src.write_text(
        'app.command("same")(one)\napp.command("same")(two)\n',
        encoding="utf-8",
    )

    result = audit_program_redundancy(tmp_path)

    assert result.ok is False
    assert any(item.kind == "duplicate_cli_command_name" for item in result.blockers)


def test_program_redundancy_audit_allows_clean_source(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "ok.py"
    src.parent.mkdir(parents=True)
    src.write_text("def ok() -> int:\n    return 1\n", encoding="utf-8")

    result = audit_program_redundancy(tmp_path)

    assert result.ok is True


def test_render_program_redundancy_audit_reports_counts(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "bad.py"
    src.parent.mkdir(parents=True)
    src.write_text("eval('1')\n", encoding="utf-8")

    rendered = render_program_redundancy_audit(audit_program_redundancy(tmp_path))

    assert "PROGRAM_REDUNDANCY_AUDIT" in rendered
    assert "STATUS=FAIL" in rendered
    assert "BLOCKER_COUNT=1" in rendered

def test_program_redundancy_audit_allows_same_command_name_on_different_apps(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "cli.py"
    src.parent.mkdir(parents=True)
    src.write_text(
        'first_app.command("list")(one)\nsecond_app.command("list")(two)\n',
        encoding="utf-8",
    )

    result = audit_program_redundancy(tmp_path)

    assert result.ok is True


def test_program_redundancy_audit_reviews_own_patterns_without_blocking(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "program_redundancy_audit.py"
    src.parent.mkdir(parents=True)
    src.write_text(
        '("shell_true", re.compile(r"shell=True"), "pattern")\n',
        encoding="utf-8",
    )

    result = audit_program_redundancy(tmp_path)

    assert result.ok is True
    assert result.findings
    assert result.findings[0].severity == "review"


def test_program_redundancy_audit_reviews_validator_pattern_lists_without_blocking(tmp_path: Path) -> None:
    src = tmp_path / "src" / "agentic_project_kit" / "work_order_validator.py"
    src.parent.mkdir(parents=True)
    src.write_text(
        'BANNED = ["os.system(", "shell=True", "eval(", "exec("]\n',
        encoding="utf-8",
    )

    result = audit_program_redundancy(tmp_path)

    assert result.ok is True
    assert {item.kind for item in result.findings} >= {"os_system", "shell_true", "eval_exec"}

