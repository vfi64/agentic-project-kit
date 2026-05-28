from agentic_project_kit.patch_artifact_preflight import check_required_slice_gate, run_preflight
from agentic_project_kit.slice_gate import DirtyState, SliceGateReport


def _report(result="PASS", dirty="CLEAN"):
    class Report(SliceGateReport):
        @property
        def slice_result(self):
            return result
    return Report(kind="planning-doc", step_results=(), dirty_state=DirtyState(dirty))


def test_required_slice_gate_passes_for_clean_pass():
    assert check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _report()) == []


def test_required_slice_gate_blocks_non_pass_result():
    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _report(result="BLOCKED"))
    assert "slice gate planning-doc: slice_result=BLOCKED" in errors


def test_required_slice_gate_blocks_dirty_state():
    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _report(dirty="DIRTY"))
    assert "slice gate planning-doc: dirty_state=DIRTY" in errors


def test_run_preflight_can_require_slice_gate():
    errors = run_preflight([], require_slice_gate="planning-doc", slice_gate_runner=lambda _kind, _root: _report())
    assert errors == []
