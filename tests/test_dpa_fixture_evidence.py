from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_fixture_evidence import (
    AUTHORIZATION_TOKEN,
    evaluate_dpa_fixture_evidence,
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
                        "id": "PROBE-002",
                        "title": "Lifecycle, acceptance and writer routing",
                        "cases": [
                            {
                                "id": "P002-LIFE-001",
                                "title": "Immutable lifecycle plan capture",
                                "mutation_scope": "TEMP_REPO_MUTATION",
                                "authorization": "MAINTAINER_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-TEMP-REPO",
                                "expected_result": "plan records fingerprints",
                            },
                            {
                                "id": "P002-WRT-001",
                                "title": "Administrative handoff refresh writer routing",
                                "mutation_scope": "DISPOSABLE_BRANCH_MUTATION",
                                "authorization": "MAINTAINER_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-DISPOSABLE-BRANCH",
                                "expected_result": "writer is bounded",
                                "writer_id": "WRT-CH-001",
                            },
                        ],
                    },
                    {
                        "id": "RENDERER",
                        "title": "Renderer identity and purity",
                        "cases": [
                            {
                                "id": "REN-003",
                                "title": "Renderer deterministic repeat output",
                                "mutation_scope": "TEMP_REPO_MUTATION",
                                "authorization": "MAINTAINER_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-TEMP-REPO",
                                "expected_result": "deterministic output",
                            }
                        ],
                    },
                    {
                        "id": "PROBE-003",
                        "title": "Workflow serialization",
                        "cases": [
                            {
                                "id": "P003-WF-002",
                                "title": "Branch switch or rebase rejects stale plan",
                                "mutation_scope": "DISPOSABLE_BRANCH_MUTATION",
                                "authorization": "MAINTAINER_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-DISPOSABLE-BRANCH",
                                "expected_result": "branch movement invalidates stale plan",
                            }
                        ],
                    },
                    {
                        "id": "PROBE-004",
                        "title": "Migration and rollback",
                        "cases": [
                            {
                                "id": "P004-MIG-003",
                                "title": "Exact-byte rollback after Write",
                                "mutation_scope": "TEMP_REPO_MUTATION",
                                "authorization": "MAINTAINER_REQUIRED",
                                "cleanup_plan_id": "CLEANUP-TEMP-REPO",
                                "expected_result": "rollback restores bytes",
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


def test_fixture_evidence_blocks_mutating_cases_without_authorization(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = evaluate_dpa_fixture_evidence(tmp_path, validation_ref="target-ref")

    assert result.result_status == "AUTHORIZATION_BLOCK"
    assert result.blocked_cases
    assert result.full_evidence_by_family["PROBE-002"] is False


def test_fixture_evidence_executes_authorized_non_production_cases(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = evaluate_dpa_fixture_evidence(
        tmp_path,
        validation_ref="target-ref",
        authorized_by="Maintainer",
        authorization_token=AUTHORIZATION_TOKEN,
    )

    payload = result.as_dict()
    assert result.result_status == "FULL_FIXTURE_EVIDENCE_RECORDED"
    assert payload["validation_ref"] == "target-ref"
    assert payload["summary"]["case_count"] == 5
    assert payload["summary"]["pass_count"] == 5
    assert payload["claims"]["production_mutation_performed"] is False
    assert payload["claims"]["generated_outputs_manually_patched"] is False
    assert payload["rollback_cleanup_proven"] is True
    assert all(payload["full_evidence_by_family"].values())
    rendered = json.dumps(payload, sort_keys=True)
    assert "<DPA_FIXTURE_TEMP_ROOT>" in rendered
    assert tempfile.gettempdir() not in rendered
    assert "/private/var/" not in rendered


def test_fixture_evidence_plan_only_does_not_satisfy_full_evidence(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = evaluate_dpa_fixture_evidence(
        tmp_path,
        authorized_by="Maintainer",
        authorization_token=AUTHORIZATION_TOKEN,
        plan_only=True,
    )

    assert result.result_status == "FIXTURE_PLAN_ONLY"
    assert result.rollback_cleanup_proven is False


def test_fixture_evidence_cli_writes_under_probe_root(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    output = "docs/architecture/evidence/dpa/probes/fixture-evidence/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "fixture-evidence",
            "--root",
            str(tmp_path),
            "--authorized-by",
            "Maintainer",
            "--authorization-token",
            AUTHORIZATION_TOKEN,
            "--output",
            output,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["result_status"] == "FULL_FIXTURE_EVIDENCE_RECORDED"


def test_fixture_evidence_cli_rejects_output_outside_probe_root(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "fixture-evidence",
            "--root",
            str(tmp_path),
            "--authorized-by",
            "Maintainer",
            "--authorization-token",
            AUTHORIZATION_TOKEN,
            "--output",
            "tmp/results.json",
            "--execute",
        ],
    )

    assert result.exit_code == 2
    assert "output_outside_dpa_probe_evidence_root" in result.stdout
    assert not (tmp_path / "tmp/results.json").exists()
