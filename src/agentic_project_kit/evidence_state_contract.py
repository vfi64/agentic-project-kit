"""Machine-readable evidence state contract for GUI readiness.

The contract is read-only. It classifies whether a terminal or command-run
result has durable repo-backed evidence, only local tmp evidence, missing
evidence, a stale latest pointer, and/or a command report.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.workspace import LEGACY_DEFAULTS, Workspace, load_workspace

EVIDENCE_REMOTE_PRESENT = "REMOTE_EVIDENCE_PRESENT"
EVIDENCE_LOCAL_TMP_ONLY = "LOCAL_TMP_ONLY"
EVIDENCE_MISSING = "MISSING_EVIDENCE"
EVIDENCE_STALE_LATEST_POINTER = "STALE_LATEST_POINTER"

TERMINAL_DIR = Path(LEGACY_DEFAULTS.terminal_reports_root)
COMMAND_RUN_DIR = Path(LEGACY_DEFAULTS.command_runs_root)
LATEST_TERMINAL_LOG = TERMINAL_DIR / "LATEST_TERMINAL_LOG.txt"
LATEST_COMMAND_RUN = COMMAND_RUN_DIR / "LATEST_COMMAND_RUN.txt"

@dataclass(frozen=True)
class EvidenceState:
    schema_version: int
    evidence_state: str
    remote_evidence_present: bool
    local_tmp_only: bool
    missing_evidence: bool
    stale_latest_pointer: bool
    terminal_log: str | None
    latest_terminal_log: str | None
    command_report: str | None
    command_report_available: bool
    reason: str
    next_allowed_actions: tuple[str, ...]

def _root(root: Path) -> Path:
    return root.resolve()

def _read_pointer(path: Path) -> str | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None

def _is_repo_evidence_path(value: str | None, workspace: Workspace) -> bool:
    if value is None:
        return False
    return value.startswith(workspace.path_text(workspace.terminal_reports_dir()) + "/") or value.startswith(
        workspace.path_text(workspace.command_runs_dir()) + "/"
    )

def _exists(root: Path, value: str | None) -> bool:
    if value is None:
        return False
    path = Path(value)
    if path.is_absolute():
        return path.exists()
    return (_root(root) / path).exists()

def inspect_evidence_state(root: Path = Path("."), terminal_log: str | None = None, command_report: str | None = None) -> EvidenceState:
    root = _root(root)
    workspace = load_workspace(root)
    latest = _read_pointer(workspace.latest_terminal_log_pointer())
    latest_command_report = _read_pointer(workspace.latest_command_run_pointer())
    effective_report = command_report or latest_command_report
    effective_terminal = terminal_log or latest
    command_report_available = _exists(root, effective_report)
    if effective_terminal is None:
        return EvidenceState(1, EVIDENCE_MISSING, False, False, True, False, None, latest, effective_report, command_report_available, "no terminal evidence path is available", ("paste-output",))
    terminal_exists = _exists(root, effective_terminal)
    repo_path = _is_repo_evidence_path(effective_terminal, workspace)
    stale = latest is not None and terminal_log is not None and latest != terminal_log
    if stale:
        return EvidenceState(1, EVIDENCE_STALE_LATEST_POINTER, repo_path and terminal_exists, False, not terminal_exists, True, effective_terminal, latest, effective_report, command_report_available, "latest terminal pointer does not match requested terminal log", ("terminal-upload", "paste-output"))
    if repo_path and terminal_exists:
        return EvidenceState(1, EVIDENCE_REMOTE_PRESENT, True, False, False, False, effective_terminal, latest, effective_report, command_report_available, "repo-backed evidence is present", ("d", "f"))
    if Path(effective_terminal).is_absolute() and terminal_exists:
        return EvidenceState(1, EVIDENCE_LOCAL_TMP_ONLY, False, True, False, False, effective_terminal, latest, effective_report, command_report_available, "only local tmp evidence is available", ("terminal-upload", "paste-output"))
    return EvidenceState(1, EVIDENCE_MISSING, False, False, True, False, effective_terminal, latest, effective_report, command_report_available, "evidence path is missing or not repo-backed", ("paste-output",))

def evidence_state_as_json_data(state: EvidenceState) -> dict[str, object]:
    return {
        "schema_version": state.schema_version,
        "evidence_state": state.evidence_state,
        "remote_evidence_present": state.remote_evidence_present,
        "local_tmp_only": state.local_tmp_only,
        "missing_evidence": state.missing_evidence,
        "stale_latest_pointer": state.stale_latest_pointer,
        "terminal_log": state.terminal_log,
        "latest_terminal_log": state.latest_terminal_log,
        "command_report": state.command_report,
        "command_report_available": state.command_report_available,
        "reason": state.reason,
        "next_allowed_actions": list(state.next_allowed_actions),
    }
