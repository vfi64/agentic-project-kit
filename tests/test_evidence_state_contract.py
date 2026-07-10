from pathlib import Path

from agentic_project_kit.evidence_state_contract import (
    EVIDENCE_LOCAL_TMP_ONLY,
    EVIDENCE_MISSING,
    EVIDENCE_REMOTE_PRESENT,
    EVIDENCE_STALE_LATEST_POINTER,
    evidence_state_as_json_data,
    inspect_evidence_state,
)


def _write_manifest(root: Path) -> None:
    manifest = root / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "kit_schema_version: 1\n"
        "project:\n"
        "  name: fixture\n"
        "  type: generic\n"
        "profile: generic\n",
        encoding="utf-8",
    )


def _write(root: Path, rel: str, text: str = "log") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

def test_remote_evidence_present_from_latest_pointer(tmp_path: Path) -> None:
    rel = "docs/reports/terminal/run.log"
    _write(tmp_path, rel)
    _write(tmp_path, "docs/reports/terminal/LATEST_TERMINAL_LOG.txt", rel)
    state = inspect_evidence_state(tmp_path)
    assert state.evidence_state == EVIDENCE_REMOTE_PRESENT
    assert state.remote_evidence_present is True
    data = evidence_state_as_json_data(state)
    assert data["schema_version"] == 1
    assert data["next_allowed_actions"] == ["d", "f"]

def test_local_tmp_only_evidence(tmp_path: Path) -> None:
    local = tmp_path / "local-tmp.log"
    local.write_text("tmp", encoding="utf-8")
    state = inspect_evidence_state(tmp_path, terminal_log=str(local))
    assert state.evidence_state == EVIDENCE_LOCAL_TMP_ONLY
    assert state.local_tmp_only is True
    assert "paste-output" in state.next_allowed_actions

def test_missing_evidence_without_pointer(tmp_path: Path) -> None:
    state = inspect_evidence_state(tmp_path)
    assert state.evidence_state == EVIDENCE_MISSING
    assert state.missing_evidence is True
    assert state.next_allowed_actions == ("paste-output",)

def test_missing_evidence_for_nonexistent_repo_path(tmp_path: Path) -> None:
    state = inspect_evidence_state(tmp_path, terminal_log="docs/reports/terminal/missing.log")
    assert state.evidence_state == EVIDENCE_MISSING
    assert state.missing_evidence is True

def test_stale_latest_pointer(tmp_path: Path) -> None:
    latest_rel = "docs/reports/terminal/latest.log"
    requested_rel = "docs/reports/terminal/requested.log"
    _write(tmp_path, latest_rel)
    _write(tmp_path, requested_rel)
    _write(tmp_path, "docs/reports/terminal/LATEST_TERMINAL_LOG.txt", latest_rel)
    state = inspect_evidence_state(tmp_path, terminal_log=requested_rel)
    assert state.evidence_state == EVIDENCE_STALE_LATEST_POINTER
    assert state.stale_latest_pointer is True

def test_command_report_availability_from_latest_pointer(tmp_path: Path) -> None:
    terminal_rel = "docs/reports/terminal/run.log"
    report_rel = "docs/reports/command_runs/run.md"
    _write(tmp_path, terminal_rel)
    _write(tmp_path, report_rel)
    _write(tmp_path, "docs/reports/terminal/LATEST_TERMINAL_LOG.txt", terminal_rel)
    _write(tmp_path, "docs/reports/command_runs/LATEST_COMMAND_RUN.txt", report_rel)
    state = inspect_evidence_state(tmp_path)
    assert state.evidence_state == EVIDENCE_REMOTE_PRESENT
    assert state.command_report_available is True
    assert state.command_report == report_rel


def test_evidence_state_uses_manifest_terminal_and_command_namespaces(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    terminal_rel = ".agentic/state/handoff/terminal/run.log"
    report_rel = ".agentic/state/handoff/command_runs/run.md"
    _write(tmp_path, terminal_rel)
    _write(tmp_path, report_rel)
    _write(tmp_path, ".agentic/state/handoff/terminal/LATEST_TERMINAL_LOG.txt", terminal_rel)
    _write(tmp_path, ".agentic/state/handoff/command_runs/LATEST_COMMAND_RUN.txt", report_rel)

    state = inspect_evidence_state(tmp_path)

    assert state.evidence_state == EVIDENCE_REMOTE_PRESENT
    assert state.remote_evidence_present is True
    assert state.command_report_available is True
    assert state.command_report == report_rel
