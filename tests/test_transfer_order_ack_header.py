"""Transfer orders start with the COMMAND_MANIFEST_ACK line; every reader must accept it.

Gate benchmark S04 (2026-10-16): the instruction lint requires the ACK as the first line at
apply time, but the remote-next guard, the report-path recovery and transfer continue read the
inbox as raw YAML and crashed with a ScannerError on every ACK-headed order. An order without the
ACK passed the readers and was then refused by the lint, so no order could complete remote-next.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from agentic_project_kit import transfer_continue as tc
from agentic_project_kit import transfer_remote_next as trn
from agentic_project_kit.transfer_runner import DEFAULT_INBOX

ORDER = {
    "schema_version": 1,
    "kind": trn.EXECUTABLE_TRANSFER_ORDER_KIND,
    "id": "ack-headed-order",
    "status": "active",
    "branch": "feature/order",
    "report_path": "docs/reports/command_runs/ack-headed-order.md",
}


def _write_order(root: Path) -> Path:
    path = root / DEFAULT_INBOX
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("COMMAND_MANIFEST_ACK 0123456789ab\n" + yaml.safe_dump(ORDER), encoding="utf-8")
    return path


def test_remote_next_guard_reads_ack_headed_orders(tmp_path: Path) -> None:
    path = _write_order(tmp_path)

    assert trn._read_transfer_order_data(path)["id"] == "ack-headed-order"
    assert trn._current_transfer_report_path(tmp_path) == "docs/reports/command_runs/ack-headed-order.md"


def test_remote_next_guard_reports_invalid_yaml_as_value_error(tmp_path: Path) -> None:
    path = tmp_path / DEFAULT_INBOX
    path.parent.mkdir(parents=True)
    path.write_text("COMMAND_MANIFEST_ACK 0123456789ab\nid: [unclosed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not valid YAML"):
        trn._read_transfer_order_data(path)


def test_transfer_continue_finds_ack_headed_active_orders(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    _write_order(root)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=kit@example.invalid", "-c", "user.name=Kit Test", "commit", "-q", "-m", "order"],
        cwd=root,
        check=True,
    )

    assert tc._current_order_is_active(root) is True
    assert tc._read_order_from_ref(root, "main")["id"] == "ack-headed-order"
