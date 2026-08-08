from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.cli_commands import transfer_context_helpers


def _write_context_carriers(root: Path, ctx: dict[str, object]) -> None:
    payload = {"llm_execution_context": ctx}
    for relative_path in (
        ".agentic/transfer/outbox/last_result.txt",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")


def _context(*, source_hashes: dict[str, str], generated_at: str) -> dict[str, object]:
    return {
        "source_hashes": source_hashes,
        "context_quality": {"source_hashes_complete": True},
        "running_chat_refresh_contract": {"refresh_required_for_running_chats": True},
        "shell_placeholder_policy": "no placeholders",
        "terminal_resilience": {
            "required_commands": [
                "agentic-kit transfer pr-create-complete --post-merge-complete",
                "verify-llm-context-refresh",
            ]
        },
        "patch_generation_policy": {"bounded": True},
        "command_reference": {"manifest": "test"},
        "generated_at_utc": generated_at,
    }


def test_fresh_llm_context_treats_age_only_staleness_as_warning(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_hashes = {"docs/STATUS.md": "abc"}
    _write_context_carriers(
        tmp_path,
        _context(source_hashes=source_hashes, generated_at="2026-01-01T00:00:00+00:00"),
    )
    monkeypatch.setattr(
        "agentic_project_kit.llm_execution_context.build_llm_execution_context",
        lambda root: {"source_hashes": source_hashes},
    )

    payload = transfer_context_helpers._evaluate_llm_context_freshness(
        tmp_path,
        max_age_minutes=60,
    )

    assert payload["result_status"] == "PASS"
    assert set(payload["valid_contexts"]) == {"outbox", "latest_handoff_report"}
    assert payload["blockers"] == []
    assert payload["warnings"] == [
        "outbox_age_exceeds_max_but_source_hashes_match",
        "latest_handoff_report_age_exceeds_max_but_source_hashes_match",
    ]


def test_fresh_llm_context_still_blocks_stale_hash_mismatch(tmp_path: Path, monkeypatch) -> None:
    _write_context_carriers(
        tmp_path,
        _context(
            source_hashes={"docs/STATUS.md": "old"},
            generated_at="2026-01-01T00:00:00+00:00",
        ),
    )
    monkeypatch.setattr(
        "agentic_project_kit.llm_execution_context.build_llm_execution_context",
        lambda root: {"source_hashes": {"docs/STATUS.md": "current"}},
    )

    payload = transfer_context_helpers._evaluate_llm_context_freshness(
        tmp_path,
        max_age_minutes=60,
    )

    assert payload["result_status"] == "BLOCKED"
    assert "outbox_source_hashes_mismatch" in payload["blockers"]
    assert "outbox_stale_or_not_fresh" in payload["blockers"]
