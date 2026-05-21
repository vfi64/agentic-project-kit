import pytest
from agentic_project_kit.communication_state import next_summary_header


def test_next_summary_header_rejects_empty_slice_name_when_writing(tmp_path):
    state = tmp_path / "communication_state.json"
    state.write_text('{"schema_version": 1, "last_summary_id": 0}', encoding="utf-8")
    with pytest.raises(ValueError, match="slice_name must not be empty"):
        next_summary_header(state, origin="local", branch="main", slice_name="", write=True)

def test_next_summary_header_allows_no_write_smoke_without_slice(tmp_path):
    state = tmp_path / "communication_state.json"
    state.write_text('{"schema_version": 1, "last_summary_id": 4}', encoding="utf-8")
    header = next_summary_header(state, origin="local", branch="main", slice_name="", write=False)
    assert "SUMMARY COMM-00005" in header
    assert "last_slice" not in state.read_text(encoding="utf-8")

def test_next_summary_header_records_explicit_slice_name(tmp_path):
    state = tmp_path / "communication_state.json"
    state.write_text('{"schema_version": 1, "last_summary_id": 0}', encoding="utf-8")
    header = next_summary_header(state, origin="local", branch="main", slice_name="TEST SLICE", write=True)
    assert "SUMMARY COMM-00001" in header
    assert "TEST SLICE" in state.read_text(encoding="utf-8")
