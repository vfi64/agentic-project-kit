import json
from pathlib import Path

from agentic_project_kit.communication_state import check_state, format_summary_id, next_summary_header


def write_state(path: Path, last_summary_id: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "last_summary_id": last_summary_id,
            "updated_at": None,
            "last_origin": None,
            "last_branch": None,
            "last_slice": None,
        }) + chr(10),
        encoding="utf-8",
    )


def test_summary_id_format_is_stable() -> None:
    assert format_summary_id(0) == "COMM-00000"
    assert format_summary_id(123) == "COMM-00123"


def test_next_summary_increments_state(tmp_path: Path) -> None:
    state = tmp_path / "communication_state.json"
    write_state(state, 41)
    header = next_summary_header(state, origin="local", branch="feature/test", slice_name="unit")
    assert header.startswith("SUMMARY COMM-00042 | ")
    assert " | local | " not in header
    assert "feature/test" not in header
    data = json.loads(state.read_text(encoding="utf-8"))
    assert data["last_summary_id"] == 42
    assert data["last_origin"] == "local"
    assert data["last_branch"] == "feature/test"
    assert data["last_slice"] == "unit"


def test_comm_check_accepts_initial_repo_state() -> None:
    result = check_state(Path(".agentic/communication_state.json"))
    assert result.ok


def test_ns_shortcuts_are_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "comm-check" in text
    assert "comm-next-summary" in text
    assert "agentic_project_kit.communication_state check" in text
    assert "agentic_project_kit.communication_state next-summary" in text


def test_summary_contract_documents_communication_id() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "Communication summary id contract" in text
    assert "SUMMARY COMM-xxxxx | YYYY-MM-DD HH:MM:SS +ZZZZ" in text
    assert "must not repeat branch, origin, or mode" in text
    assert ".agentic/communication_state.json" in text
