from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_wrt_ch001_evidence import (
    evaluate_wrt_ch001_admin_refresh_observation,
)

runner = CliRunner()


EXPECTED_FILES = (
    ".agentic/handoff_state.yaml",
    ".agentic/operational_handoff_state.yaml",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/reports/handoff-packages/latest/execution_contract.json",
    "docs/reports/handoff-packages/latest/source_manifest.json",
    "docs/reports/handoff-packages/latest/successor_context.yaml",
    "docs/reports/handoff-packages/latest/successor_prompt.md",
    "docs/reports/handoff-packages/latest/validation_report.json",
    "docs/reports/terminal/post-pr1901-successor-chat-handoff.md",
)


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _root_with_admin_refresh_files(root: Path) -> None:
    for path in EXPECTED_FILES:
        _touch(root, path)


def _pr_data(*, files: tuple[str, ...] = EXPECTED_FILES) -> dict[str, object]:
    return {
        "number": 1902,
        "state": "MERGED",
        "title": "Refresh handoff state after PR1901",
        "baseRefName": "main",
        "headRefName": "docs/post-pr1901-handoff-refresh",
        "headRefOid": "e" * 40,
        "mergeCommit": {"oid": "d" * 40},
        "files": [{"path": path} for path in files],
        "commits": [{"messageHeadline": "Refresh handoff state after PR1901"}],
        "statusCheckRollup": [
            {
                "name": "test",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "workflowName": "CI",
            }
        ],
    }


def test_wrt_ch001_observation_accepts_merged_admin_refresh_pr(tmp_path: Path) -> None:
    _root_with_admin_refresh_files(tmp_path)

    result = evaluate_wrt_ch001_admin_refresh_observation(
        tmp_path,
        source_pr=1901,
        admin_pr=1902,
        pr_data=_pr_data(),
    )

    assert result.structural_ok
    assert result.result_status == "OBSERVED_ADMIN_REFRESH_NOT_DISPOSABLE_FIXTURE"
    assert not result.full_wrt_ch001_fixture_satisfied
    payload = result.as_dict()
    assert payload["validation_ref"] == "d" * 40
    assert payload["claims"]["admin_refresh_observed"] is True
    assert payload["claims"]["disposable_fixture_claimed"] is False


def test_wrt_ch001_observation_blocks_unexpected_admin_refresh_file(tmp_path: Path) -> None:
    _root_with_admin_refresh_files(tmp_path)
    _touch(tmp_path, "docs/unexpected.md")

    result = evaluate_wrt_ch001_admin_refresh_observation(
        tmp_path,
        source_pr=1901,
        admin_pr=1902,
        pr_data=_pr_data(files=(*EXPECTED_FILES, "docs/unexpected.md")),
    )

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert [finding.code for finding in result.findings] == ["admin-refresh-file-unexpected"]


def test_wrt_ch001_observation_cli_writes_evidence_under_probe_root(tmp_path: Path) -> None:
    _root_with_admin_refresh_files(tmp_path)
    input_path = tmp_path / "pr1902.json"
    input_path.write_text(json.dumps(_pr_data()), encoding="utf-8")
    output = "docs/architecture/evidence/dpa/probes/wrt-ch001-observation/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "wrt-ch001-evidence",
            "--source-pr",
            "1901",
            "--admin-pr",
            "1902",
            "--root",
            str(tmp_path),
            "--input",
            str(input_path),
            "--output",
            output,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / output).exists()
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["result_status"] == "OBSERVED_ADMIN_REFRESH_NOT_DISPOSABLE_FIXTURE"


def test_wrt_ch001_observation_cli_can_require_disposable_fixture(tmp_path: Path) -> None:
    _root_with_admin_refresh_files(tmp_path)
    input_path = tmp_path / "pr1902.json"
    input_path.write_text(json.dumps(_pr_data()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "dpa",
            "wrt-ch001-evidence",
            "--source-pr",
            "1901",
            "--admin-pr",
            "1902",
            "--root",
            str(tmp_path),
            "--input",
            str(input_path),
            "--require-disposable-fixture",
        ],
    )

    assert result.exit_code == 1
    assert "FULL_WRT_CH001_FIXTURE_SATISFIED=false" in result.stdout
