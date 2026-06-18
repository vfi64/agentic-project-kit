from __future__ import annotations

from pathlib import Path
import os

from agentic_project_kit.patch_failure_discipline_audit import (
    audit_patch_failure_discipline,
    render_patch_failure_discipline,
)


def _write(path: Path, text: str, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_patch_failure_discipline_passes_without_failures(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-ok-20260101-000001.log", "RESULT=PASS\n", 1)

    result = audit_patch_failure_discipline(tmp_path, include_tmp=True)

    assert result.ok is True
    assert result.violations == ()


def test_patch_failure_discipline_allows_single_patch_failure(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-a-20260101-000001.log", "block not found\n", 1)

    result = audit_patch_failure_discipline(tmp_path, include_tmp=True)

    assert result.ok is True
    assert len([s for s in result.signals if s.kind == "patch_failure"]) == 1


def test_patch_failure_discipline_fails_two_failures_without_later_diagnosis(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-a-20260101-000001.log", "block not found\n", 1)
    _write(tmp_path / "tmp" / "slice1-b-20260101-000002.log", "function not found\n", 2)

    result = audit_patch_failure_discipline(tmp_path, include_tmp=True)

    assert result.ok is False
    assert result.violations
    assert result.violations[0].kind == "missing_diagnosis_after_repeated_patch_failure"


def test_patch_failure_discipline_passes_when_diagnosis_follows_two_failures(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-a-20260101-000001.log", "block not found\n", 1)
    _write(tmp_path / "tmp" / "slice1-b-20260101-000002.log", "function not found\n", 2)
    _write(
        tmp_path / "tmp" / "slice1-diagnose-20260101-000003.log",
        "exact next_turn test functions\nRESULT=SLICE1_DIAGNOSE_NEXT_TURN_DONE\n",
        3,
    )

    result = audit_patch_failure_discipline(tmp_path, include_tmp=True)

    assert result.ok is True
    assert result.violations == ()


def test_patch_failure_discipline_requires_new_diagnosis_after_new_repeated_failures(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-a-20260101-000001.log", "block not found\n", 1)
    _write(tmp_path / "tmp" / "slice1-b-20260101-000002.log", "function not found\n", 2)
    _write(tmp_path / "tmp" / "slice1-diagnose-20260101-000003.log", "RESULT=PATCH_FAILURE_DIAGNOSIS_DONE\n", 3)
    _write(tmp_path / "tmp" / "slice1-c-20260101-000004.log", "assertion block not found\n", 4)
    _write(tmp_path / "tmp" / "slice1-d-20260101-000005.log", "not uniquely replaced\n", 5)

    result = audit_patch_failure_discipline(tmp_path, include_tmp=True)

    assert result.ok is False
    assert result.violations[0].group == "slice1"


def test_patch_failure_discipline_default_ignores_tmp_until_requested(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-a-20260101-000001.log", "block not found\n", 1)
    _write(tmp_path / "tmp" / "slice1-b-20260101-000002.log", "function not found\n", 2)

    assert audit_patch_failure_discipline(tmp_path).ok is True
    assert audit_patch_failure_discipline(tmp_path, include_tmp=True).ok is False


def test_render_patch_failure_discipline_lists_violations(tmp_path: Path) -> None:
    _write(tmp_path / "tmp" / "slice1-a-20260101-000001.log", "block not found\n", 1)
    _write(tmp_path / "tmp" / "slice1-b-20260101-000002.log", "function not found\n", 2)

    rendered = render_patch_failure_discipline(
        audit_patch_failure_discipline(tmp_path, include_tmp=True)
    )

    assert "PATCH_FAILURE_DISCIPLINE_AUDIT" in rendered
    assert "STATUS=FAIL" in rendered
    assert "VIOLATION=slice1" in rendered

def test_patch_failure_discipline_default_ignores_historical_terminal_reports(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs" / "reports" / "terminal" / "old-a-20260101-000001.log",
        "block not found\n",
        1,
    )
    _write(
        tmp_path / "docs" / "reports" / "terminal" / "old-b-20260101-000002.log",
        "function not found\n",
        2,
    )

    result = audit_patch_failure_discipline(tmp_path)

    assert result.ok is True
    assert result.signals == ()

