from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from agentic_project_kit import __version__ as PACKAGE_VERSION

from agentic_project_kit.gui_readiness_gate import (
    REQUIRED_CURRENT_DOCS,
    evaluate_gui_readiness,
    render_gui_readiness_gate,
)


def _write_required_docs(root: Path) -> None:
    for relative in REQUIRED_CURRENT_DOCS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")


def test_gui_readiness_gate_passes_when_required_docs_and_gates_pass(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        return 0, "PASS\n"

    result = evaluate_gui_readiness(tmp_path, version="9.9.9", runner=runner)

    assert result.ok is True
    assert result.status == "PASS"
    assert any("post-release-check" in args for args in seen)
    assert any("9.9.9" in args for args in seen)


def test_gui_readiness_gate_blocks_missing_required_doc(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        return 0, "PASS\n"

    result = evaluate_gui_readiness(tmp_path, runner=runner)

    assert result.ok is False
    assert any(item.name.startswith("required_doc:") for item in result.blockers)


def test_gui_readiness_gate_blocks_failed_gate(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "audit-doc-currency" in args:
            return 1, "FAIL doc currency\n"
        return 0, "PASS\n"

    result = evaluate_gui_readiness(tmp_path, runner=runner)

    assert result.ok is False
    assert any("audit-doc-currency" in item.name for item in result.blockers)


def test_render_gui_readiness_gate_reports_blockers(tmp_path: Path) -> None:
    result = evaluate_gui_readiness(tmp_path, runner=lambda args, cwd: (0, "PASS\n"))

    rendered = render_gui_readiness_gate(result)

    assert "GUI_READINESS_GATE" in rendered
    assert "STATUS=FAIL" in rendered
    assert "BLOCKER=" in rendered

def test_gui_readiness_gate_defers_post_merge_check_on_feature_branch(tmp_path: Path, monkeypatch) -> None:
    _write_required_docs(tmp_path)

    import agentic_project_kit.gui_readiness_gate as gate

    monkeypatch.setattr(gate, "_current_branch", lambda root: "feature/gui-work")

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if tuple(args[-2:]) == ("transfer", "post-merge-check"):
            return 2, "FAIL should have been deferred\n"
        return 0, "PASS\n"

    result = evaluate_gui_readiness(tmp_path, runner=runner)

    assert result.ok is True
    assert any(
        item.name == "gate:transfer post-merge-check"
        and "deferred on branch feature/gui-work" in item.detail
        for item in result.checks
    )

def test_gui_readiness_gate_default_version_follows_package_version(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        return 0, "PASS\n"

    result = evaluate_gui_readiness(tmp_path, runner=runner)

    assert result.ok is True
    assert result.version == PACKAGE_VERSION
    assert any("post-release-check" in args for args in seen)
    assert any(PACKAGE_VERSION in args for args in seen)

