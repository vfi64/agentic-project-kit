from pathlib import Path

from agentic_project_kit import slice_gate
from agentic_project_kit.patch_artifact_preflight import check_required_slice_gate, run_preflight


def _slice_report(*, slice_pass: bool = True, dirty_state: str = "CLEAN") -> slice_gate.SliceGateReport:
    step = slice_gate.SliceGateStepResult(
        name="unit-gate",
        command=("agentic-kit", "unit"),
        status="PASS" if slice_pass else "FAIL",
        exit_code=0 if slice_pass else 1,
    )
    dirty_files = () if dirty_state == "CLEAN" else (" M docs/example.md",)
    return slice_gate.SliceGateReport(
        kind="planning-doc",
        step_results=(step,),
        dirty_state=slice_gate.DirtyState(dirty_state, dirty_files),
    )


def test_preflight_slice_gate_requirement_passes_with_clean_passing_gate() -> None:
    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _slice_report())
    assert errors == []


def test_preflight_slice_gate_requirement_blocks_failed_slice_gate() -> None:
    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _slice_report(slice_pass=False))
    assert any("slice_result=BLOCKED" in error for error in errors)


def test_preflight_slice_gate_requirement_blocks_dirty_slice_gate() -> None:
    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _slice_report(dirty_state="DIRTY"))
    assert any("dirty_state=DIRTY" in error for error in errors)


def test_run_preflight_can_require_slice_gate() -> None:
    errors = run_preflight([], require_slice_gate="planning-doc", slice_gate_runner=lambda _kind, _root: _slice_report())
    assert errors == []


def test_slice_gate_requirement_uses_repository_root() -> None:
    seen_roots: list[Path] = []

    def runner(_kind: str, root: Path) -> slice_gate.SliceGateReport:
        seen_roots.append(root)
        return _slice_report()

    assert check_required_slice_gate("planning-doc", project_root=Path("."), runner=runner) == []
    assert seen_roots == [Path(".")]
