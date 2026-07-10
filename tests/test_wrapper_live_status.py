from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_project_kit.wrapper_live_status import (
    WRAPPER_PHASES,
    default_safe_to_interrupt,
    read_wrapper_live_status,
    wrapper_status_path,
    write_wrapper_live_status,
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


def test_write_wrapper_live_status_uses_canonical_tmp_path(tmp_path: Path) -> None:
    payload = write_wrapper_live_status(
        tmp_path,
        wrapper="pr-create-complete",
        phase="creating_pr",
        base="main",
        head="codex/demo",
        expected_head_sha="0123456789abcdef0123456789abcdef01234567",
        pr_number=123,
        blockers=["none"],
        step="pr-create",
    )

    path = wrapper_status_path(tmp_path)
    assert path == tmp_path / "tmp/current-wrapper-status.json"
    assert json.loads(path.read_text(encoding="utf-8")) == payload
    assert payload["kind"] == "wrapper_live_status"
    assert payload["phase"] == "creating_pr"
    assert payload["safe_to_interrupt"] is False
    assert payload["known_phases"] == list(WRAPPER_PHASES)


def test_write_wrapper_live_status_uses_manifest_tmp_namespace(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    payload = write_wrapper_live_status(
        tmp_path,
        wrapper="pr-create-complete",
        phase="starting",
    )

    path = wrapper_status_path(tmp_path)
    assert path == tmp_path / ".agentic/tmp/current-wrapper-status.json"
    assert payload["status_path"] == ".agentic/tmp/current-wrapper-status.json"
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_read_wrapper_live_status_round_trips(tmp_path: Path) -> None:
    written = write_wrapper_live_status(
        tmp_path,
        wrapper="pr-create-complete",
        phase="done",
        result_status="PASS",
    )

    assert read_wrapper_live_status(tmp_path) == written


def test_wrapper_live_status_rejects_unknown_phase(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_wrapper_live_status(
            tmp_path,
            wrapper="pr-create-complete",
            phase="not_a_phase",  # type: ignore[arg-type]
        )


def test_default_safe_to_interrupt_allows_only_ci_waiting_phase() -> None:
    assert default_safe_to_interrupt("starting") is False
    assert default_safe_to_interrupt("creating_pr") is False
    assert default_safe_to_interrupt("waiting_ci") is True
    assert default_safe_to_interrupt("merging") is False
    assert default_safe_to_interrupt("post_merge") is False
    assert default_safe_to_interrupt("done") is False
    assert default_safe_to_interrupt("blocked") is False
