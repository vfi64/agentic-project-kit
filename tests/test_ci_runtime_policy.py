from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.ci_runtime_policy import (
    ADMIN_REFRESH_LIGHT,
    BUILD_REQUIRED,
    BUILD_SKIPPED,
    DIAGNOSTIC_ONLY,
    FULL_CI,
    TREE_PROOF,
    admin_refresh_current_handoff_paths,
    admin_refresh_expected_paths,
    admin_refresh_expected_path_variants,
    admin_refresh_post_merge_settle_paths,
    build_failure_record,
    classify_admin_refresh_light,
    classify_failure_class,
    classify_main_push_tree_proof,
    classify_pages_build,
    load_pages_input_manifest,
    main,
    receipt_store_decision,
    validate_pages_input_manifest,
)


def _pages_manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "site_input_paths": [
            "site/",
            "src/agentic_project_kit/site_generator.py",
            "src/agentic_project_kit/site_claims.py",
        ],
        "release_state_paths": ["pyproject.toml", "CHANGELOG.md"],
        "workflow_paths": [".github/workflows/pages.yml", "site/pages_input_manifest.json"],
        "required_pull_request_test_paths": [
            "tests/test_site_generator.py",
            "tests/test_site_claims.py",
            "tests/test_ci_runtime_policy.py",
        ],
    }


def test_admin_refresh_light_accepts_exact_successor_package_refresh_path_set() -> None:
    changed_paths = admin_refresh_expected_paths(2195)

    decision = classify_admin_refresh_light(
        changed_paths,
        branch="docs/post-pr2195-successor-package-refresh",
        validation_status="PASS",
    )

    assert decision.status == "PASS"
    assert decision.mode == ADMIN_REFRESH_LIGHT
    assert decision.changed_paths == changed_paths
    assert decision.missing_paths == ()
    assert decision.unexpected_paths == ()
    assert decision.mutation == "successor-package-refresh"
    assert "exact successor-package-refresh path set for PR 2195" in decision.reasons


def test_admin_refresh_light_accepts_exact_current_handoff_refresh_path_set() -> None:
    changed_paths = admin_refresh_current_handoff_paths()

    decision = classify_admin_refresh_light(
        changed_paths,
        branch="docs/post-pr2197-handoff-refresh",
        validation_status="PASS",
    )

    assert decision.status == "PASS"
    assert decision.mode == ADMIN_REFRESH_LIGHT
    assert decision.changed_paths == changed_paths
    assert decision.missing_paths == ()
    assert decision.unexpected_paths == ()
    assert decision.mutation == "current-handoff-refresh"
    assert "exact current-handoff-refresh path set for PR 2197" in decision.reasons


def test_admin_refresh_light_accepts_exact_post_merge_settle_refresh_path_set() -> None:
    changed_paths = admin_refresh_post_merge_settle_paths(2200)

    decision = classify_admin_refresh_light(
        changed_paths,
        branch="docs/post-pr2200-handoff-refresh",
        validation_status="PASS",
    )

    assert decision.status == "PASS"
    assert decision.mode == ADMIN_REFRESH_LIGHT
    assert decision.changed_paths == changed_paths
    assert decision.missing_paths == ()
    assert decision.unexpected_paths == ()
    assert decision.mutation == "post-merge-settle-refresh"
    assert "exact post-merge-settle-refresh path set for PR 2200" in decision.reasons


def test_admin_refresh_light_rejects_extra_product_path() -> None:
    changed_paths = (*admin_refresh_expected_paths(2195), "src/agentic_project_kit/demo.py")

    decision = classify_admin_refresh_light(
        changed_paths,
        branch="docs/post-pr2195-handoff-refresh",
        validation_status="PASS",
    )

    assert decision.mode == FULL_CI
    assert decision.unexpected_paths == ("src/agentic_project_kit/demo.py",)
    assert "admin refresh changed-path set contains non-allowlisted paths" in decision.reasons


def test_admin_refresh_light_rejects_missing_generated_path() -> None:
    changed_paths = tuple(
        path
        for path in admin_refresh_expected_paths(2195)
        if path != "docs/reports/handoff-packages/latest/validation_report.json"
    )

    decision = classify_admin_refresh_light(
        changed_paths,
        branch="docs/post-pr2195-handoff-refresh",
        validation_status="PASS",
    )

    assert decision.mode == FULL_CI
    assert "admin refresh path set does not match exact" in decision.reasons[0]
    assert decision.missing_paths or decision.unexpected_paths


def test_admin_refresh_light_rejects_non_pass_validation_status() -> None:
    decision = classify_admin_refresh_light(
        admin_refresh_expected_paths(2195),
        branch="docs/post-pr2195-handoff-refresh",
        validation_status="FAIL",
    )

    assert decision.mode == FULL_CI
    assert "successor package validation is not PASS" in decision.reasons


def test_admin_refresh_light_report_path_can_prove_source_pr_but_not_path_variant() -> None:
    changed_paths = (*admin_refresh_expected_paths(2195), "docs/reports/terminal/post-pr2195-successor-chat-handoff.md")

    decision = classify_admin_refresh_light(changed_paths, validation_status="PASS")

    assert decision.mode == FULL_CI
    assert decision.unexpected_paths == ("docs/reports/terminal/post-pr2195-successor-chat-handoff.md",)


def test_admin_refresh_light_path_variants_include_combined_settle_set() -> None:
    variants = dict(admin_refresh_expected_path_variants(2198))

    assert set(variants) == {
        "successor-package-refresh",
        "current-handoff-refresh",
        "post-merge-settle-refresh",
    }
    assert "docs/reports/handoff-packages/latest/validation_report.json" in variants["successor-package-refresh"]
    assert ".agentic/dpa/acceptance/current_handoff_operational_state.json" in variants["current-handoff-refresh"]
    combined = set(variants["post-merge-settle-refresh"])
    assert set(variants["successor-package-refresh"]) < combined
    assert set(variants["current-handoff-refresh"]) < combined
    assert "docs/handoff/START_NEW_CHAT_PROMPT.md" in combined
    assert "docs/reports/terminal/post-pr2198-successor-chat-handoff.md" in combined


def test_admin_refresh_light_invalid_path_falls_back_to_full_ci() -> None:
    decision = classify_admin_refresh_light(
        (*admin_refresh_expected_paths(2195), "../outside.md"),
        branch="docs/post-pr2195-handoff-refresh",
        validation_status="PASS",
    )

    assert decision.mode == FULL_CI
    assert decision.invalid_paths == ("../outside.md",)


def test_pages_manifest_schema_is_deterministic() -> None:
    assert validate_pages_input_manifest(_pages_manifest()) == ()

    findings = validate_pages_input_manifest({"schema_version": 1, "site_input_paths": []})

    assert "site_input_paths must be a non-empty string list" in findings
    assert "release_state_paths must be a non-empty string list" in findings


def test_checked_in_pages_input_manifest_is_valid() -> None:
    manifest_path = Path("site/pages_input_manifest.json")
    manifest = load_pages_input_manifest(manifest_path)

    assert validate_pages_input_manifest(manifest) == ()
    for key in (
        "site_input_paths",
        "release_state_paths",
        "workflow_paths",
        "required_pull_request_test_paths",
    ):
        for item in manifest[key]:
            path = Path(str(item).rstrip("/"))
            assert path.exists(), f"{key} points to missing path: {item}"


def test_pages_path_gate_skips_unrelated_push_change() -> None:
    decision = classify_pages_build(
        ["README.md"],
        event_name="push",
        manifest=_pages_manifest(),
    )

    assert decision.status == "PASS"
    assert decision.mode == BUILD_SKIPPED
    assert decision.matched_paths == ()


def test_pages_path_gate_requires_build_for_site_release_workflow_or_manual_changes() -> None:
    manifest = _pages_manifest()

    assert classify_pages_build(
        ["site/templates/index.html"],
        event_name="push",
        manifest=manifest,
    ).mode == BUILD_REQUIRED
    assert classify_pages_build(["pyproject.toml"], event_name="push", manifest=manifest).mode == BUILD_REQUIRED
    assert classify_pages_build(
        [".github/workflows/pages.yml"],
        event_name="push",
        manifest=manifest,
    ).mode == BUILD_REQUIRED
    assert classify_pages_build([], event_name="workflow_dispatch", manifest=manifest).mode == BUILD_REQUIRED


def test_pages_path_gate_fails_closed_when_paths_or_manifest_are_unverifiable() -> None:
    assert classify_pages_build(
        ["../outside.md"],
        event_name="push",
        manifest=_pages_manifest(),
    ).mode == BUILD_REQUIRED
    assert classify_pages_build(
        ["README.md"],
        event_name="push",
        manifest={"schema_version": 1},
    ).mode == BUILD_REQUIRED


def test_pages_manifest_loader_fails_closed_for_missing_manifest(tmp_path: Path) -> None:
    manifest = load_pages_input_manifest(tmp_path / "missing.json")
    decision = classify_pages_build(["README.md"], event_name="push", manifest=manifest)

    assert decision.mode == BUILD_REQUIRED
    assert "cannot load Pages input manifest:" in decision.reasons[0]


def test_main_push_tree_proof_accepts_only_safe_equivalent_tree() -> None:
    decision = classify_main_push_tree_proof(
        ["src/agentic_project_kit/demo.py", "tests/test_demo.py"],
        event_name="push",
        final_tree_sha="tree123",
        tested_tree_sha="tree123",
        pr_checks_passed=True,
    )

    assert decision.status == "PASS"
    assert decision.mode == TREE_PROOF


def test_main_push_tree_proof_falls_back_without_complete_proof_or_workflow_change() -> None:
    assert classify_main_push_tree_proof(
        ["docs/handoff/CURRENT_HANDOFF.md"],
        event_name="pull_request",
        final_tree_sha="tree123",
        tested_tree_sha="tree123",
        pr_checks_passed=True,
    ).mode == FULL_CI
    assert classify_main_push_tree_proof(
        ["docs/handoff/CURRENT_HANDOFF.md"],
        event_name="push",
        final_tree_sha="tree123",
        tested_tree_sha="other",
        pr_checks_passed=True,
    ).mode == FULL_CI
    assert classify_main_push_tree_proof(
        ["docs/handoff/CURRENT_HANDOFF.md"],
        event_name="push",
        final_tree_sha="",
        tested_tree_sha="",
        pr_checks_passed=True,
    ).mode == FULL_CI
    assert classify_main_push_tree_proof(
        ["docs/handoff/CURRENT_HANDOFF.md"],
        event_name="push",
        final_tree_sha="tree123",
        tested_tree_sha="tree123",
        pr_checks_passed=None,
    ).mode == FULL_CI
    workflow_change = classify_main_push_tree_proof(
        [".github/workflows/ci.yml"],
        event_name="push",
        final_tree_sha="tree123",
        tested_tree_sha="tree123",
        pr_checks_passed=True,
    )
    assert workflow_change.mode == FULL_CI
    assert "workflow or GitHub Actions helper paths changed" in workflow_change.reasons


def test_failure_registry_classifies_known_diagnostic_failures() -> None:
    cases = {
        "scope_decision projection drift": "registry-counter-drift",
        "COMMAND_MANIFEST_ACK stale in successor package": "stale-llm-context-carrier",
        "dirty volatile carrier found": "dirty-volatile-carrier",
        "expected check missing: CI": "missing-checks",
        "queued run has no-job evidence": "queued-stuck-run",
        "deploy-pages failed": "pages-deploy-issue",
        "pytest timed out at deadline": "timeout",
        "pytest AssertionError": "test-failure",
    }

    for message, expected_class in cases.items():
        assert classify_failure_class(message)[0] == expected_class


def test_failure_record_is_diagnostic_only_and_blocks_incomplete_evidence() -> None:
    complete = build_failure_record(
        workflow_run_id="33097945702",
        failing_job="test",
        message="expected check missing: CI",
        evidence_pointers=["https://github.com/vfi64/agentic-project-kit/actions/runs/33097945702"],
    )

    assert complete["status"] == "PASS"
    assert complete["mode"] == DIAGNOSTIC_ONLY
    assert complete["diagnostic_only"] is True
    assert complete["mutation"] == "none"
    assert complete["failure_class"] == "missing-checks"
    assert complete["blockers"] == []

    incomplete = build_failure_record(
        workflow_run_id="33097945702",
        failing_job="",
        message="pytest failed",
        evidence_pointers=[],
    )

    assert incomplete["status"] == "BLOCK"
    assert incomplete["blockers"] == ["failing_job", "evidence_pointers"]


def test_receipt_store_decision_keeps_current_refresh_mechanism() -> None:
    decision = receipt_store_decision()

    assert decision["status"] == "PASS"
    assert decision["decision"] == "defer_replacement_keep_current_refresh_pr_mechanism"
    assert decision["exactly_one_receipt"] == "not_proven"
    assert decision["append_only_enforcement"] == "not_proven"
    assert decision["successor_read_path_discovery"] == "not_proven"
    assert decision["current_refresh_mechanism_removed"] is False


def test_ci_runtime_policy_cli_writes_json(tmp_path: Path, capsys) -> None:
    changed_paths = tmp_path / "changed-paths.txt"
    changed_paths.write_text("README.md\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_pages_manifest()), encoding="utf-8")
    output = tmp_path / "policy.json"

    assert main(
        [
            "pages",
            "--changed-paths-file",
            str(changed_paths),
            "--event-name",
            "push",
            "--manifest",
            str(manifest),
            "--output",
            str(output),
        ]
    ) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == BUILD_SKIPPED
    assert payload["reasons"]
    assert json.loads(capsys.readouterr().out)["mode"] == BUILD_SKIPPED
