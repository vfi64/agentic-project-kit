from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.mutation_lock_audit import (
    MutationLockCoverageAuditResult,
    MutationLockFinding,
    audit_mutation_lock_coverage,
    render_mutation_lock_coverage_audit,
)


def test_mutation_lock_audit_command_passes_after_lc3_remediation() -> None:
    result = CliRunner().invoke(app, ["audit-mutation-lock-coverage", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)

    assert payload["kind"] == "mutation_lock_coverage_audit"
    assert payload["result_status"] == "PASS"
    assert payload["finding_count"] == len(payload["findings"])
    assert payload["blocking_finding_count"] == len(payload["blocking_findings"])
    assert payload["non_blocking_finding_count"] == len(payload["non_blocking_findings"])
    assert payload["blocking_finding_count"] == 0
    assert "findings" in payload
    assert "classification_summary" in payload
    assert any(finding["category"] in {"A", "B", "C"} for finding in payload["findings"])
    assert any(
        finding["classification"]["counts_as_blocking"] is False
        for finding in payload["non_blocking_findings"]
    )


def test_mutation_lock_audit_has_text_summary() -> None:
    result = CliRunner().invoke(app, ["audit-mutation-lock-coverage"])

    assert result.exit_code == 0
    assert "MUTATION_LOCK_COVERAGE_AUDIT" in result.output
    assert "RESULT: PASS" in result.output
    assert "BLOCKING_FINDINGS:" in result.output
    assert "NON_BLOCKING_FINDINGS:" in result.output
    assert "disposition=non-blocking" in result.output


def test_non_blocking_false_positive_findings_do_not_block() -> None:
    result = MutationLockCoverageAuditResult(
        kind="mutation_lock_coverage_audit",
        findings=[
            MutationLockFinding(
                category="A",
                symbol="<module>",
                path="src/agentic_project_kit/command_manifest.py",
                line=17,
                reason="git_history_mutation without nearby workspace mutation lock marker",
            )
        ],
    )

    payload = result.to_dict()

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert payload["blocking_finding_count"] == 0
    assert payload["non_blocking_finding_count"] == 1
    assert payload["non_blocking_findings"][0]["classification"]["kind"] == "metadata_literal"
    assert "NON_BLOCKING:" in render_mutation_lock_coverage_audit(result)


def test_runtime_mutation_findings_stay_blocking() -> None:
    result = MutationLockCoverageAuditResult(
        kind="mutation_lock_coverage_audit",
        findings=[
            MutationLockFinding(
                category="A",
                symbol="branch_create",
                path="src/agentic_project_kit/transfer_repo_actions.py",
                line=561,
                reason="git_branch_mutation without nearby workspace mutation lock marker",
            )
        ],
    )

    payload = result.to_dict()

    assert result.result_status == "BLOCK"
    assert result.returncode == 1
    assert payload["blocking_finding_count"] == 1
    assert payload["non_blocking_finding_count"] == 0
    assert payload["blocking_findings"][0]["classification"]["kind"] == "runtime_mutation"


def test_core_runtime_mutation_without_lock_still_blocks(tmp_path) -> None:
    source = tmp_path / "src" / "agentic_project_kit" / "transfer_repo_actions.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "def branch_switch(branch):\n"
        "    command = ['git', 'switch', branch]\n"
        "    return command\n",
        encoding="utf-8",
    )

    result = audit_mutation_lock_coverage(tmp_path)
    payload = result.to_dict()

    assert result.result_status == "BLOCK"
    assert result.returncode == 1
    assert payload["blocking_finding_count"] == 1
    assert payload["blocking_findings"][0]["symbol"] == "branch_switch"
    assert payload["blocking_findings"][0]["classification"]["kind"] == "runtime_mutation"
