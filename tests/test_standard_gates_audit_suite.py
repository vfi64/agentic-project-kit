from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.standard_gates_audit_suite import (
    REQUIRED_STANDARD_GATE_COMMANDS,
    evaluate_standard_gates_audit_suite,
    render_standard_gates_audit_suite,
)


REQUIRED_NAMES = {
    "audit-patch-failure-discipline",
    "audit-path-literals",
    "command-taxonomy-check",
    "direction",
    "doc-registry",
    "audit-ns-legacy-references",
    "audit-absolute-path-portability",
    "audit-doc-currency",
    "audit-status-current-state",
    "audit-planning-docs-consolidation",
    "audit-program-redundancy",
    "release-publish",
}


STRICT_SCOPE_COMMAND = ("doc-registry", "check-unregistered", "--strict-scope")
PATH_LITERAL_ENFORCE_COMMAND = ("audit-path-literals", "--enforce-active")


def test_standard_gates_audit_suite_contains_required_gates() -> None:
    command_names = {command[0] for command in REQUIRED_STANDARD_GATE_COMMANDS}

    assert REQUIRED_NAMES <= command_names


def test_suite_contains_strict_scope_step() -> None:
    assert STRICT_SCOPE_COMMAND in REQUIRED_STANDARD_GATE_COMMANDS


def test_path_literal_enforce_is_standard_gate() -> None:
    assert PATH_LITERAL_ENFORCE_COMMAND in REQUIRED_STANDARD_GATE_COMMANDS


def test_standard_gates_suite_blocks_active_path_literal_failure(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if args[-2:] == PATH_LITERAL_ENFORCE_COMMAND:
            return (
                1,
                "PATH_LITERAL_ACTIVE_CLASS_ENFORCEMENT\n"
                "STATUS=FAIL\n"
                "BLOCKER=active_path_literal|src/demo.py|literals=1\n",
            )
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, runner=runner)

    assert result.ok is False
    blocker = next(
        check
        for check in result.blockers
        if check.name == "audit-path-literals --enforce-active"
    )
    assert blocker.detail.startswith("BLOCKER=active_path_literal")


def test_standard_gates_audit_suite_passes_when_commands_pass(tmp_path: Path) -> None:
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, version="9.9.9", runner=runner)

    assert result.ok is True
    assert result.version == "9.9.9"
    assert any("release-publish" in args for args in seen)
    assert any("9.9.9" in args for args in seen)


def test_standard_gates_audit_suite_fails_when_required_gate_fails(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "audit-doc-currency" in args:
            return 1, "BLOCKER_COUNT=1\n"
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, runner=runner)

    assert result.ok is False
    assert any(check.name == "audit-doc-currency" for check in result.blockers)


def test_standard_gates_audit_suite_blocks_invalid_project_direction(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if args[-2:] == ("direction", "validate"):
            return (
                1,
                "PROJECT_DIRECTION_VALIDATE\n"
                "STATUS=FAIL\n"
                "FINDING=duplicate-id|docs/planning/PROJECT_DIRECTION.yaml|duplicate id\n",
            )
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, runner=runner)

    assert result.ok is False
    blocker = next(check for check in result.blockers if check.name == "direction validate")
    assert blocker.detail == "STATUS=FAIL"


def test_strict_scope_violation_fails_suite(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if args[-3:] == STRICT_SCOPE_COMMAND:
            return (
                1,
                "DOC_REGISTRY_UNREGISTERED\n"
                "STATUS=FAIL\n"
                "CANDIDATES=1\n"
                "- docs/governance/MISSING.md\n"
                "STRICT_SCOPE=True\n"
                "EXEMPTED=0\n"
                "SCOPE_VIOLATIONS=1\n"
                "SCOPE-VIOLATION docs/governance/MISSING.md\n",
            )
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, runner=runner)

    assert result.ok is False
    blocker = next(
        check
        for check in result.blockers
        if check.name == "doc-registry check-unregistered --strict-scope"
    )
    assert blocker.returncode == 1
    assert blocker.detail == "STATUS=FAIL"


def test_standard_gates_audit_suite_default_version_follows_package_version(tmp_path: Path) -> None:
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, runner=runner)

    assert result.version == PACKAGE_VERSION
    assert any(PACKAGE_VERSION in args for args in seen)


def test_render_standard_gates_audit_suite_lists_blockers(tmp_path: Path) -> None:
    result = evaluate_standard_gates_audit_suite(
        tmp_path,
        runner=lambda args, cwd: (1, "FAIL\n"),
    )

    rendered = render_standard_gates_audit_suite(result)

    assert "STANDARD_GATES_AUDIT_SUITE" in rendered
    assert "STATUS=FAIL" in rendered
    assert "BLOCKER=" in rendered


def test_standard_gates_audit_suite_prefers_blocker_line_in_failure_detail(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "audit-program-redundancy" in args:
            return 1, "PROGRAM_REDUNDANCY_AUDIT\nBLOCKER=pass_in_exception|file.py:1|pass|reason\nFINDING=review|later\n"
        return 0, "PASS\n"

    result = evaluate_standard_gates_audit_suite(tmp_path, runner=runner)

    blocker = next(check for check in result.blockers if check.name == "audit-program-redundancy")
    assert blocker.detail.startswith("BLOCKER=pass_in_exception")
