from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_readonly_probe_execution import (
    CommandExecution,
    evaluate_dpa_readonly_probe_execution,
)

runner = CliRunner()


def _write_manifest(root: Path) -> Path:
    manifest = root / "docs/architecture/dpa/probes/fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "families": [
                    {
                        "id": "PROBE-001",
                        "title": "Registry compatibility",
                        "cases": [
                            {
                                "id": "P001-REG-001",
                                "title": "Existing manual registry entries remain accepted",
                                "mutation_scope": "READ_ONLY",
                                "authorization": "NOT_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-READONLY",
                                "expected_result": "existing entries parse",
                            },
                            {
                                "id": "P001-REG-002",
                                "title": "Valid optional ProjectionContract is accepted",
                                "mutation_scope": "TEMP_REPO_MUTATION",
                                "authorization": "MAINTAINER_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-TEMP-REPO",
                                "expected_result": "projection contract fixture validates",
                            },
                        ],
                    },
                    {
                        "id": "RENDERER",
                        "title": "Renderer identity and purity",
                        "cases": [
                            {
                                "id": "REN-001",
                                "title": "Renderer map identity is explicit",
                                "mutation_scope": "READ_ONLY",
                                "authorization": "NOT_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-READONLY",
                                "expected_result": "approved renderer identity resolves",
                            }
                        ],
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest


def _ok_runner(root: Path, argv: tuple[str, ...], timeout_seconds: int) -> CommandExecution:
    return CommandExecution(argv=argv, returncode=0, stdout="ok\n", stderr="")


def _failing_runner(root: Path, argv: tuple[str, ...], timeout_seconds: int) -> CommandExecution:
    return CommandExecution(argv=argv, returncode=1, stdout="", stderr="failed\n")


def test_readonly_probe_execution_runs_only_not_required_readonly_cases(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = evaluate_dpa_readonly_probe_execution(
        tmp_path,
        validation_ref="target-ref",
        command_runner=_ok_runner,
    )

    assert result.result_status == "READ_ONLY_EXECUTED_WITH_LIMITATIONS"
    payload = result.as_dict()
    assert payload["validation_ref"] == "target-ref"
    assert payload["summary"]["readonly_cases_selected"] == 2
    assert payload["summary"]["readonly_cases_executed"] == 1
    assert payload["summary"]["mutable_or_authorized_cases_blocked"] == 1
    assert payload["summary"]["context_dependent_readonly_cases_blocked"] == 1
    assert payload["full_probe_pass_satisfied"] is False
    assert payload["claims"]["production_mutation_performed"] is False


def test_readonly_probe_execution_reports_command_failures(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = evaluate_dpa_readonly_probe_execution(tmp_path, command_runner=_failing_runner)

    assert result.result_status == "READ_ONLY_FAIL"
    assert result.command_failures
    assert result.as_dict()["command_failure_count"] == 1


def test_readonly_probe_execution_plan_only_does_not_execute_commands(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    calls: list[tuple[str, ...]] = []

    def runner_that_should_not_run(root: Path, argv: tuple[str, ...], timeout_seconds: int) -> CommandExecution:
        calls.append(argv)
        return CommandExecution(argv=argv, returncode=0, stdout="", stderr="")

    result = evaluate_dpa_readonly_probe_execution(
        tmp_path,
        plan_only=True,
        command_runner=runner_that_should_not_run,
    )

    assert result.result_status == "READ_ONLY_PLAN_ONLY"
    assert calls == []


def test_readonly_probe_execution_blocks_missing_manifest(tmp_path: Path) -> None:
    result = evaluate_dpa_readonly_probe_execution(tmp_path)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert [finding.code for finding in result.findings] == ["fixture-manifest-missing"]


def test_readonly_probe_execution_cli_writes_plan_under_probe_root(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    output = "docs/architecture/evidence/dpa/probes/readonly-probe-current/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "readonly-probe-execution",
            "--root",
            str(tmp_path),
            "--plan-only",
            "--output",
            output,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / output).exists()
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["result_status"] == "READ_ONLY_PLAN_ONLY"


def test_readonly_probe_execution_cli_rejects_output_outside_probe_root(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "readonly-probe-execution",
            "--root",
            str(tmp_path),
            "--plan-only",
            "--output",
            "tmp/results.json",
            "--execute",
        ],
    )

    assert result.exit_code == 2
    assert "output_outside_dpa_probe_evidence_root" in result.stdout
    assert not (tmp_path / "tmp/results.json").exists()
