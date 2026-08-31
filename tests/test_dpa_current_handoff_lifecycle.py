from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from agentic_project_kit.dpa_current_handoff_lifecycle import (
    DEFAULT_ACCEPTANCE_STATE_PATH,
    evaluate_current_handoff_lifecycle,
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo(root: Path) -> str:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test User")
    _write(
        root / ".agentic/operational_handoff_state.yaml",
        """
schema_version: 1
current_head:
  full: 1111111111111111111111111111111111111111
  short: "11111111"
  subject: Initial handoff state
last_substantive_work_state:
  full: 1111111111111111111111111111111111111111
  short: "11111111"
  subject: Initial handoff state
administrative_context:
- Admin context.
freshness_policy:
  text: Freshness policy.
next_safe_substantive_slice:
  text: Next slice.
""".lstrip(),
    )
    _write(root / "docs/handoff/CURRENT_HANDOFF.md", "Curated handoff text.\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "Initial test repo")
    return _git(root, "rev-parse", "HEAD")


def _commit_all(root: Path, message: str) -> str:
    _git(root, "add", ".")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def test_current_handoff_refresh_requires_explicit_initial_acceptance(tmp_path: Path) -> None:
    _repo(tmp_path)

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=False,
        require_dp2_authorized=False,
    )

    assert result.result_status == "BLOCKED"
    assert [finding.code for finding in result.findings] == ["acceptance-state-missing"]
    assert not (tmp_path / DEFAULT_ACCEPTANCE_STATE_PATH).exists()


def test_current_handoff_refresh_records_acceptance_state_after_verify(tmp_path: Path) -> None:
    head = _repo(tmp_path)

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )

    assert result.result_status == "ACCEPTED"
    assert result.wrote_target is True
    assert result.wrote_acceptance_state is True
    target_text = (tmp_path / "docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "Current Operational Handoff State" in target_text
    state = json.loads((tmp_path / DEFAULT_ACCEPTANCE_STATE_PATH).read_text(encoding="utf-8"))
    assert state["status"] == "accepted"
    assert state["validation_ref"] == head
    assert state["target"]["path"] == "docs/handoff/CURRENT_HANDOFF.md"
    assert state["target"]["complete_target_fingerprint"] == result.plan.projected_complete_target_fingerprint
    assert state["claims"]["generated_outputs_manually_patched"] is False

    fresh = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=False,
        require_dp2_authorized=False,
        validation_ref=head,
    )
    assert fresh.result_status == "FRESH"
    assert fresh.plan.freshness == "fresh"


def test_current_handoff_refresh_blocks_target_drift_before_write(tmp_path: Path) -> None:
    head = _repo(tmp_path)
    accepted = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )
    assert accepted.result_status == "ACCEPTED"
    target = tmp_path / "docs/handoff/CURRENT_HANDOFF.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nmanual tamper\n", encoding="utf-8")

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )

    assert result.result_status == "BLOCKED"
    assert [finding.code for finding in result.findings] == ["target-drift"]
    assert "manual tamper" in target.read_text(encoding="utf-8")


def test_current_handoff_refresh_blocks_committed_target_drift_by_default(tmp_path: Path) -> None:
    head = _repo(tmp_path)
    accepted = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )
    assert accepted.result_status == "ACCEPTED"
    _commit_all(tmp_path, "Accept handoff state")

    target = tmp_path / "docs/handoff/CURRENT_HANDOFF.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nmerged handoff note\n", encoding="utf-8")
    merged_head = _commit_all(tmp_path, "Merge handoff note")

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        require_dp2_authorized=False,
        validation_ref=merged_head,
    )

    assert result.result_status == "BLOCKED"
    assert [finding.code for finding in result.findings] == ["target-drift"]


def test_current_handoff_refresh_accepts_opt_in_committed_target_drift(tmp_path: Path) -> None:
    head = _repo(tmp_path)
    accepted = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )
    assert accepted.result_status == "ACCEPTED"
    old_target_fingerprint = accepted.plan.projected_complete_target_fingerprint
    _commit_all(tmp_path, "Accept handoff state")

    target = tmp_path / "docs/handoff/CURRENT_HANDOFF.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nmerged handoff note\n", encoding="utf-8")
    merged_head = _commit_all(tmp_path, "Merge handoff note")

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        require_dp2_authorized=False,
        validation_ref=merged_head,
        allow_committed_target_drift=True,
    )

    assert result.result_status == "ACCEPTED"
    assert result.plan.freshness == "stale"
    assert result.plan.target_before_fingerprint != old_target_fingerprint
    state = json.loads((tmp_path / DEFAULT_ACCEPTANCE_STATE_PATH).read_text(encoding="utf-8"))
    assert state["validation_ref"] == merged_head
    assert state["target"]["pre_write_fingerprint"] == result.plan.target_before_fingerprint
    assert state["target"]["complete_target_fingerprint"] == result.plan.projected_complete_target_fingerprint


def test_current_handoff_refresh_opt_in_still_blocks_uncommitted_target_drift(tmp_path: Path) -> None:
    head = _repo(tmp_path)
    accepted = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )
    assert accepted.result_status == "ACCEPTED"
    committed_head = _commit_all(tmp_path, "Accept handoff state")

    target = tmp_path / "docs/handoff/CURRENT_HANDOFF.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nuncommitted handoff note\n", encoding="utf-8")

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        require_dp2_authorized=False,
        validation_ref=committed_head,
        allow_committed_target_drift=True,
    )

    assert result.result_status == "BLOCKED"
    assert [finding.code for finding in result.findings] == ["target-drift"]
    assert "uncommitted handoff note" in target.read_text(encoding="utf-8")


def test_current_handoff_refresh_blocks_stale_validation_ref(tmp_path: Path) -> None:
    _repo(tmp_path)

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=False,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref="0000000000000000000000000000000000000000",
    )

    assert result.result_status == "BLOCKED"
    assert [finding.code for finding in result.findings] == ["stale-validation-ref"]


def test_current_handoff_refresh_blocks_when_workspace_lock_is_busy(tmp_path: Path) -> None:
    head = _repo(tmp_path)
    lock = tmp_path / ".agentic/tmp/workspace.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(
        json.dumps({"pid": os.getpid(), "command": "other dpa writer", "acquired_at": "now"}),
        encoding="utf-8",
    )

    result = evaluate_current_handoff_lifecycle(
        tmp_path,
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
        validation_ref=head,
    )

    assert result.result_status == "BLOCKED"
    assert [finding.code for finding in result.findings] == ["workspace-lock-busy"]
    assert not (tmp_path / DEFAULT_ACCEPTANCE_STATE_PATH).exists()
