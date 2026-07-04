from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_project_kit.release_process_guardrails import (
    assert_uploadable_artifact,
    command_reference_paths_are_current,
    dump_structured_like_existing,
    git_status_paths,
    load_structured_text,
    parse_git_status_short,
    rc_from_result_payload,
    reject_invalid_pr_complete_args,
    release_and_handoff_paths_are_mixed,
    require_no_release_handoff_mix,
    require_pending_doi_marker,
    require_release_date_contract,
    require_release_notes_from_tag,
    require_successor_package_mentions_version,
    safe_compact_findings,
    split_known_volatile_paths,
)


def test_git_status_short_parser_preserves_modified_paths_with_leading_worktree_column() -> None:
    status = " M docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log\n"
    assert git_status_paths(status) == [
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log"
    ]


def test_git_status_short_parser_preserves_added_paths_and_renames() -> None:
    entries = parse_git_status_short("A  src/new.py\nR  old.py -> src/new_name.py\n")
    assert entries[0].path == "src/new.py"
    assert entries[1].original_path == "old.py"
    assert entries[1].path == "src/new_name.py"


def test_known_volatile_handoff_paths_are_split_from_unexpected_dirty_paths() -> None:
    volatile, unexpected = split_known_volatile_paths([
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        "src/agentic_project_kit/release_prepare.py",
    ])
    assert volatile == ["docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"]
    assert unexpected == ["src/agentic_project_kit/release_prepare.py"]


def test_structured_loader_uses_json_content_even_for_yaml_named_files() -> None:
    payload = load_structured_text('{"release_prep_current_version": "0.4.11"}', path="successor_context.yaml")
    assert payload == {"release_prep_current_version": "0.4.11"}
    rendered = dump_structured_like_existing(payload, existing_text='{"old": true}\n')
    assert json.loads(rendered)["release_prep_current_version"] == "0.4.11"


def test_pr_complete_rejects_post_merge_complete_flag() -> None:
    with pytest.raises(ValueError, match="post-merge-complete"):
        reject_invalid_pr_complete_args([
            "./.venv/bin/agentic-kit",
            "transfer",
            "pr-complete",
            "1545",
            "--post-merge-complete",
        ])


def test_release_notes_from_tag_is_required_and_must_be_previous_release() -> None:
    with pytest.raises(ValueError, match="requires --from-tag"):
        require_release_notes_from_tag("0.4.11", "")
    with pytest.raises(ValueError, match="previous release"):
        require_release_notes_from_tag("0.4.11", "v0.4.11")
    require_release_notes_from_tag("0.4.11", "v0.4.10")


def test_outer_rc_maps_blocked_inner_result_to_rc2() -> None:
    assert rc_from_result_payload({"result_status": "PASS"}) == 0
    assert rc_from_result_payload({"result_status": "BLOCKED", "blockers": ["pr-complete_failed"]}) == 2
    assert rc_from_result_payload({"result_status": "FAIL"}) == 1


def test_command_reference_current_paths_are_required() -> None:
    assert command_reference_paths_are_current([
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
        "docs/reference/agentic-kit-commands.json",
    ])
    assert not command_reference_paths_are_current([
        "docs/generated/agentic-kit-command-reference.json",
    ])


def test_release_and_handoff_paths_must_not_be_committed_together() -> None:
    paths = [
        "CHANGELOG.md",
        "docs/reports/handoff-packages/latest/successor_context.yaml",
    ]
    assert release_and_handoff_paths_are_mixed(paths)
    with pytest.raises(ValueError, match="must not be committed in one release-prep PR"):
        require_no_release_handoff_mix(paths)


def test_successor_package_must_mention_current_release_version() -> None:
    with pytest.raises(ValueError, match="0.4.11"):
        require_successor_package_mentions_version(["project direction only"], "0.4.11")
    require_successor_package_mentions_version(["release_prep_current_version: 0.4.11"], "0.4.11")


def test_changelog_pending_doi_marker_required_until_current_version_verified() -> None:
    with pytest.raises(ValueError, match="Zenodo DOI verification pending"):
        require_pending_doi_marker("## 0.4.11\n- Release prep.", version="0.4.11", verified_version="0.4.10")
    require_pending_doi_marker(
        "## 0.4.11\n- Zenodo DOI verification pending for v0.4.11.",
        version="0.4.11",
        verified_version="0.4.10",
    )


def test_citation_release_date_contract_detects_drift() -> None:
    citation = 'version: 0.4.11\ndate-released: "2026-06-21"\n'
    with pytest.raises(ValueError, match="expected 2026-06-20"):
        require_release_date_contract(citation, "2026-06-20")


def test_large_plan_findings_are_compacted_and_upload_guard_blocks_large_artifacts(tmp_path: Path) -> None:
    compact = safe_compact_findings({"term": ["x" * 1000 for _ in range(20)]}, per_term=2, max_line=10)
    assert compact == {"term": ["x" * 10, "x" * 10]}

    big = tmp_path / "big.json"
    big.write_text("x" * 101, encoding="utf-8")
    with pytest.raises(ValueError, match="too large"):
        assert_uploadable_artifact(big, max_bytes=100)


def test_pr_create_complete_payload_guard_detects_blocked_json() -> None:
    from agentic_project_kit.release_process_guardrails import rc_from_result_payload

    assert rc_from_result_payload({"result_status": "BLOCKED", "blockers": ["inner"]}) == 2


def test_pr_complete_invalid_post_merge_complete_message_is_present() -> None:
    source = Path("src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py").read_text(encoding="utf-8")
    assert "invalid_argument_post_merge_complete" in source
    assert "--post-merge-complete is not valid for transfer pr-complete" in source


def test_payload_guard_ignores_unrelated_json() -> None:
    from agentic_project_kit.release_process_guardrails import is_transfer_result_payload

    assert not is_transfer_result_payload({"state": "OPEN", "number": 1547})
    assert is_transfer_result_payload({
        "kind": "transfer_pr_complete_result",
        "result_status": "BLOCKED",
        "blockers": ["x"],
    })
