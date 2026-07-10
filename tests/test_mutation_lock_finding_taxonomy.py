from __future__ import annotations

from pathlib import Path

from agentic_project_kit.mutation_lock_audit import (
    MutationLockFinding,
    classify_mutation_lock_finding,
)


def _finding(
    *,
    path: str,
    symbol: str,
    reason: str = "git_history_mutation without nearby workspace mutation lock marker",
    category: str = "A",
    line: int = 1,
) -> MutationLockFinding:
    return MutationLockFinding(
        category=category,
        symbol=symbol,
        path=path,
        line=line,
        reason=reason,
    )


def test_command_manifest_module_command_strings_are_metadata_literals() -> None:
    finding = _finding(
        path="src/agentic_project_kit/command_manifest.py",
        symbol="<module>",
        reason="github_mutation without nearby workspace mutation lock marker",
        category="B",
        line=20,
    )

    classification = classify_mutation_lock_finding(finding)

    assert classification.kind == "metadata_literal"
    assert classification.counts_as_blocking is False
    assert "module-level command metadata" in classification.rationale


def test_command_taxonomy_keyword_matching_is_metadata_literal() -> None:
    finding = _finding(
        path="src/agentic_project_kit/command_taxonomy.py",
        symbol="_category_for",
        reason="git_history_mutation without nearby workspace mutation lock marker",
        category="A",
        line=138,
    )

    classification = classify_mutation_lock_finding(finding)

    assert classification.kind == "metadata_literal"
    assert classification.counts_as_blocking is False


def test_reference_renderers_are_generated_reference_findings() -> None:
    finding = _finding(
        path="src/agentic_project_kit/command_manifest.py",
        symbol="write_reference",
        reason="filesystem_mutation without nearby workspace mutation lock marker",
        category="C",
        line=350,
    )

    classification = classify_mutation_lock_finding(finding)

    assert classification.kind == "generated_reference"
    assert classification.counts_as_blocking is False


def test_tmp_and_evidence_report_writers_are_report_writers() -> None:
    finding = _finding(
        path="src/agentic_project_kit/terminal_logging.py",
        symbol="finalize_terminal_log",
        reason="filesystem_mutation without nearby workspace mutation lock marker",
        category="C",
        line=112,
    )

    classification = classify_mutation_lock_finding(finding)

    assert classification.kind == "report_writer"
    assert classification.counts_as_blocking is False


def test_core_branch_switch_remains_runtime_mutation() -> None:
    finding = _finding(
        path="src/agentic_project_kit/transfer_repo_actions.py",
        symbol="branch_switch",
        reason="git_branch_mutation without nearby workspace mutation lock marker",
        category="A",
        line=635,
    )

    classification = classify_mutation_lock_finding(finding)

    assert classification.kind == "runtime_mutation"
    assert classification.counts_as_blocking is True


def test_unknown_finding_stays_blocking() -> None:
    finding = _finding(
        path="src/agentic_project_kit/some_new_file.py",
        symbol="some_new_mutator",
        reason="filesystem_mutation without nearby workspace mutation lock marker",
        category="C",
        line=12,
    )

    classification = classify_mutation_lock_finding(finding)

    assert classification.kind == "unknown"
    assert classification.counts_as_blocking is True


def test_audit_payload_exposes_classification_summary(tmp_path: Path) -> None:
    result = classify_mutation_lock_finding(
        _finding(
            path="src/agentic_project_kit/command_manifest.py",
            symbol="<module>",
            reason="git_history_mutation without nearby workspace mutation lock marker",
            category="A",
            line=17,
        )
    )

    payload = result.to_dict()

    assert payload["kind"] == "metadata_literal"
    assert payload["counts_as_blocking"] is False
    assert payload["rationale"]
