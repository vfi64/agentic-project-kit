"""Known drift classes and repeated-failure detection (plan step drift-and-repeated-failure-checks)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit import invocation_ledger as ledger
from agentic_project_kit.cli import app
from agentic_project_kit.drift_signals import (
    consumer_status_signal,
    drift_signals,
    refresh_chain_signal,
    release_projection_signal,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _commit(root: Path, subject: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=kit@example.invalid", "-c", "user.name=Kit Test", "commit", "-q", "--allow-empty", "-m", subject],
        cwd=root,
        check=True,
    )


def test_refresh_chains_count_refreshes_after_each_product_merge(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    for subject in [
        "Product A (#1)",
        "Refresh handoff state after PR1 (#2)",
        "Product B (#3)",
        "Refresh handoff state after PR3 (#4)",
        "Refresh handoff state after PR4 (#5)",
        "Product C (#6)",
    ]:
        _commit(root, subject)

    signal = refresh_chain_signal(root)

    assert signal["status"] == "drift"
    assert (signal["product_merges"], signal["chain_0"], signal["chain_1"], signal["chain_2"]) == (3, 1, 1, 1)
    assert signal["chain_2plus_share"] == round(1 / 3, 4)
    assert signal["recent_long_chains"][0]["product_subject"] == "Product B (#3)"


def test_release_projection_detects_a_stale_handoff_release_block(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    evidence = root / "docs/reports/release"
    evidence.mkdir(parents=True)
    (evidence / "post-release-doi-closeout-1.0.25.json").write_text(
        json.dumps({"result_status": "PASS", "version": "1.0.25", "tag": "v1.0.25"}), encoding="utf-8"
    )
    (root / ".agentic").mkdir()
    (root / ".agentic/handoff_state.yaml").write_text(
        "release:\n  current_version: 0.4.13\n  tag: v0.4.13\n", encoding="utf-8"
    )

    signal = release_projection_signal(root)

    assert signal["status"] == "drift"
    assert signal["drifted_keys"] == ["current_version", "tag"]


def test_release_projection_reports_a_synced_handoff_release_block_as_consistent(tmp_path: Path) -> None:
    # Fixture instead of the live repository: between the DOI closeout PR and the administrative
    # handoff refresh that syncs the release block (HD-08), the Kit repository drifts by design.
    # The signal is report-only; asserting the live state failed CI on the 1.1.0 DOI PR #2540.
    root = tmp_path / "repo"
    evidence = root / "docs/reports/release"
    evidence.mkdir(parents=True)
    (evidence / "post-release-doi-closeout-1.0.25.json").write_text(
        json.dumps({"result_status": "PASS", "version": "1.0.25", "tag": "v1.0.25"}), encoding="utf-8"
    )
    (root / ".agentic").mkdir()
    (root / ".agentic/handoff_state.yaml").write_text(
        "release:\n  current_version: 1.0.25\n  tag: v1.0.25\n", encoding="utf-8"
    )

    signal = release_projection_signal(root)

    assert signal["status"] == "consistent"
    assert signal["drifted_keys"] == []


def test_no_test_asserts_the_live_release_projection() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    assert "release_projection_signal(" + "REPO_ROOT)" not in source


def test_consumer_status_lists_kit_closed_consumer_open_and_needs_an_explicit_ledger(tmp_path: Path) -> None:
    assert consumer_status_signal(None)["status"] == "not_measured"
    from agentic_project_kit.greenfield_status import read_status

    closed = next(f["id"] for f in read_status()["findings"] if f["kit_state"] == "CLOSED")
    consumer = tmp_path / "ledger.json"
    consumer.write_text(json.dumps({"families": [{"id": closed, "status": "OPEN"}, {"id": "OTHER", "status": "OPEN"}]}), encoding="utf-8")

    signal = consumer_status_signal(consumer)

    assert signal["status"] == "drift"
    assert (signal["shared_findings"], signal["kit_closed_consumer_open"]) == (1, [closed])


def test_drift_signals_are_report_only_and_the_command_exits_zero() -> None:
    report = drift_signals(REPO_ROOT)
    assert report["report_only"] is True
    assert report["result_status"] == "PASS"
    assert set(report["signals"]) == {"release_projection", "refresh_chains", "consumer_status"}

    result = CliRunner().invoke(app, ["audit-drift-signals", "--root", str(REPO_ROOT), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["kind"] == "drift_signals"


def _record(command: str, returncode: int, started: str, *, branch: str = "feature/x", root_id: str = "r1", kind: str = "cli"):
    return {"command": command, "returncode": returncode, "started_at": started, "branch": branch, "root_id": root_id, "kind": kind}


def test_repeated_failures_need_three_consecutive_failures_without_success() -> None:
    records = [
        _record("agentic-kit doctor", 1, "2026-10-16T10:00:00+00:00", root_id="a"),
        _record("agentic-kit doctor", 1, "2026-10-16T10:01:00+00:00", root_id="b"),
        _record("agentic-kit doctor", 0, "2026-10-16T10:02:00+00:00"),
        _record("agentic-kit doctor", 1, "2026-10-16T10:03:00+00:00", root_id="c"),
        _record("agentic-kit doctor", 1, "2026-10-16T10:04:00+00:00", root_id="d"),
        _record("agentic-kit work finish", 2, "2026-10-16T11:00:00+00:00", root_id="e"),
        _record("agentic-kit work finish", 2, "2026-10-16T11:01:00+00:00", root_id="e"),
        _record("agentic-kit work finish", 2, "2026-10-16T11:02:00+00:00", root_id="f"),
        _record("agentic-kit work finish", 2, "2026-10-16T11:03:00+00:00", branch="other", root_id="g"),
    ]

    [signal] = ledger.repeated_failures(records)

    assert (signal["command"], signal["returncode"], signal["branch"], signal["count"], signal["work_cycles"]) == (
        "agentic-kit work finish",
        2,
        "feature/x",
        3,
        2,
    )


def test_finding_drafts_are_written_once_and_never_overwritten(tmp_path: Path) -> None:
    signal = {
        "fingerprint": "abc123def456",
        "command": "agentic-kit work finish",
        "returncode": 2,
        "branch": "feature/x",
        "count": 3,
        "work_cycles": 2,
        "first_seen": "2026-10-16T11:00:00+00:00",
        "last_seen": "2026-10-16T11:02:00+00:00",
    }

    assert ledger.write_finding_drafts(tmp_path, [signal]) == [
        ".agentic/tmp/invocation-ledger/finding-drafts/abc123def456.md"
    ]
    draft = tmp_path / ".agentic/tmp/invocation-ledger/finding-drafts/abc123def456.md"
    draft.write_text("edited by a human\n", encoding="utf-8")

    assert ledger.write_finding_drafts(tmp_path, [signal]) == []
    assert draft.read_text(encoding="utf-8") == "edited by a human\n"


def test_tests_do_not_write_to_the_developer_ledger() -> None:
    import os

    assert os.environ.get(ledger.LEDGER_ENV) == "0"
