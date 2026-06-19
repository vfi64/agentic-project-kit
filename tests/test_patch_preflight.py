from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from agentic_project_kit.patch_preflight import build_patch_preflight_report, render_patch_preflight_report


def test_patch_preflight_passes_small_non_protected_diff(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "--numstat" in args:
            return 0, "2\t1\tsrc/example.py\n"
        return 0, " M src/example.py\n"

    report = build_patch_preflight_report(tmp_path, runner=runner, strict=True)

    assert report.ok
    assert report.status == "PASS"


def test_patch_preflight_warns_for_protected_paths(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "--numstat" in args:
            return 0, "2\t1\tdocs/reference/AGENTIC_KIT_COMMANDS.md\n"
        return 0, " M docs/reference/AGENTIC_KIT_COMMANDS.md\n"

    report = build_patch_preflight_report(tmp_path, runner=runner)

    assert report.status == "WARN"
    assert any(finding.code == "protected_paths_touched" for finding in report.findings)


def test_patch_preflight_strict_blocks_large_diff(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "--numstat" in args:
            return 0, "401\t0\tsrc/large.py\n"
        return 0, " M src/large.py\n"

    report = build_patch_preflight_report(tmp_path, runner=runner, strict=True, max_diff_lines=400)

    assert report.ok is False
    assert any(finding.code == "diff_size" and finding.severity == "BLOCK" for finding in report.findings)


def test_render_patch_preflight_report(tmp_path: Path) -> None:
    report = build_patch_preflight_report(
        tmp_path,
        runner=lambda args, cwd: (0, ""),
    )

    rendered = render_patch_preflight_report(report)

    assert "PATCH_PREFLIGHT" in rendered
    assert "CHANGED_FILE_COUNT=" in rendered
