from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.remote_branch_hygiene import (
    OpenPullRequestHead,
    RemoteBranchInfo,
    analyze_remote_branch_hygiene,
    render_remote_branch_hygiene_report,
    report_as_json_data,
)


def test_remote_branch_hygiene_skips_main_head_and_bare_origin() -> None:
    report = analyze_remote_branch_hygiene(
        [
            RemoteBranchInfo("origin", merged_to_origin_main=False),
            RemoteBranchInfo("origin/HEAD", merged_to_origin_main=True),
            RemoteBranchInfo("origin/main", merged_to_origin_main=True),
            RemoteBranchInfo("origin/feature/done", merged_to_origin_main=True),
        ],
        [],
    )

    assert report.summary["remote_branches"] == 1
    assert report.findings[0].branch == "origin/feature/done"


def test_remote_branch_hygiene_keeps_open_pr_heads() -> None:
    report = analyze_remote_branch_hygiene(
        [RemoteBranchInfo("origin/feature/active", merged_to_origin_main=False)],
        [OpenPullRequestHead("feature/active", 17, "Active PR", "https://example.invalid/pr/17")],
    )

    finding = report.findings[0]
    assert finding.proposed_action == "keep"
    assert finding.reason == "has open PR"
    assert finding.open_pr_number == 17


def test_remote_branch_hygiene_marks_merged_no_open_pr_as_candidate_only() -> None:
    report = analyze_remote_branch_hygiene(
        [RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True)],
        [],
    )

    finding = report.findings[0]
    assert finding.proposed_action == "candidate-delete-merged-remote-branch"
    assert finding.safety_class == "dry-run-candidate"
    assert finding.delete_command is None


def test_remote_branch_hygiene_not_merged_requires_manual_review() -> None:
    report = analyze_remote_branch_hygiene(
        [RemoteBranchInfo("origin/feature/not-merged", merged_to_origin_main=False)],
        [],
    )

    finding = report.findings[0]
    assert finding.proposed_action == "manual-review"
    assert finding.reason == "not merged into origin/main"


def test_remote_branch_hygiene_json_schema_is_stable() -> None:
    report = analyze_remote_branch_hygiene(
        [
            RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True),
            RemoteBranchInfo("origin/feature/not-merged", merged_to_origin_main=False),
        ],
        [],
    )
    data = report_as_json_data(report)

    assert data["schema_version"] == 1
    assert data["kind"] == "k3_remote_branch_hygiene_report"
    assert data["mode"] == "dry-run"
    assert data["mutation"] == "none"
    assert data["result_status"] == "PASS"
    assert data["summary"]["candidate_delete_merged_remote_branch"] == 1
    assert data["summary"]["manual_review"] == 1


def test_remote_branch_hygiene_text_is_explicitly_read_only() -> None:
    report = analyze_remote_branch_hygiene(
        [RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True)],
        [],
    )
    text = render_remote_branch_hygiene_report(report)

    assert "K3_REMOTE_BRANCH_HYGIENE" in text
    assert "MODE: dry-run" in text
    assert "MUTATION: none" in text
    assert "DELETE: disabled" in text
    assert "candidate-delete-merged-remote-branch" in text


def test_remote_branch_hygiene_cli_json_uses_collectors(monkeypatch) -> None:
    def fake_collect(root):
        return (
            [RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True)],
            [],
        )

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_branch_hygiene.collect_remote_branch_hygiene_inputs",
        fake_collect,
    )

    result = CliRunner().invoke(app, ["remote-branch-hygiene", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["kind"] == "k3_remote_branch_hygiene_report"
    assert data["summary"]["candidate_delete_merged_remote_branch"] == 1


def test_remote_branch_hygiene_evidence_report_payload_embeds_inventory() -> None:
    from agentic_project_kit.remote_branch_hygiene import build_remote_branch_hygiene_evidence_report_payload

    report = analyze_remote_branch_hygiene(
        [
            RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True),
            RemoteBranchInfo("origin/feature/not-merged", merged_to_origin_main=False),
        ],
        [],
    )

    payload = build_remote_branch_hygiene_evidence_report_payload(report)

    assert payload["schema_version"] == 1
    assert payload["kind"] == "k3_remote_branch_hygiene_evidence_report"
    assert payload["mode"] == "dry-run"
    assert payload["mutation"] == "none"
    assert payload["result_status"] == "PASS"
    assert payload["inventory"]["kind"] == "k3_remote_branch_hygiene_report"
    assert payload["inventory"]["summary"]["candidate_delete_merged_remote_branch"] == 1


def test_remote_branch_hygiene_report_command_requires_execute_to_write(monkeypatch, tmp_path) -> None:
    def fake_collect(root):
        return ([RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True)], [])

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_branch_hygiene.collect_remote_branch_hygiene_inputs",
        fake_collect,
    )

    output = tmp_path / "tmp" / "report.json"
    result = CliRunner().invoke(
        app,
        [
            "remote-branch-hygiene-report",
            "--root",
            str(tmp_path),
            "--output",
            str(output),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["kind"] == "k3_remote_branch_hygiene_report_write_result"
    assert data["mode"] == "dry-run"
    assert data["mutation"] == "none"
    assert data["written"] is False
    assert not output.exists()


def test_remote_branch_hygiene_report_command_writes_only_with_execute(monkeypatch, tmp_path) -> None:
    def fake_collect(root):
        return ([RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True)], [])

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_branch_hygiene.collect_remote_branch_hygiene_inputs",
        fake_collect,
    )

    output = tmp_path / "tmp" / "report.json"
    result = CliRunner().invoke(
        app,
        [
            "remote-branch-hygiene-report",
            "--root",
            str(tmp_path),
            "--output",
            str(output),
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["kind"] == "k3_remote_branch_hygiene_report_write_result"
    assert data["mode"] == "execute"
    assert data["mutation"] == "evidence-report-write"
    assert data["written"] is True
    assert data["output_path"] == str(output)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["kind"] == "k3_remote_branch_hygiene_evidence_report"
    assert written["inventory"]["summary"]["candidate_delete_merged_remote_branch"] == 1


def test_remote_branch_hygiene_report_command_blocks_output_outside_safe_roots(monkeypatch, tmp_path) -> None:
    def fake_collect(root):
        return ([RemoteBranchInfo("origin/feature/merged", merged_to_origin_main=True)], [])

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_branch_hygiene.collect_remote_branch_hygiene_inputs",
        fake_collect,
    )

    output = tmp_path.parent / "unsafe-report.json"
    result = CliRunner().invoke(
        app,
        [
            "remote-branch-hygiene-report",
            "--root",
            str(tmp_path),
            "--output",
            str(output),
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code != 0
    assert "output path must be below" in result.output
