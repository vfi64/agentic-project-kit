from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from agentic_project_kit.ci_runtime_policy import ADMIN_REFRESH_LIGHT, FULL_CI, main
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_ci_policy import (
    classify_workspace_refresh,
    evaluate_workspace_refresh,
)
from agentic_project_kit.workspace_ci_template import render_workspace_ci


BRANCH = "docs/post-pr42-handoff-refresh"


@pytest.fixture
def ws(tmp_path):
    manifest = tmp_path / ".agentic/config.yaml"
    manifest.parent.mkdir()
    manifest.write_text(
        "kit_schema_version: 2\nproject: {name: consumer, type: generic}\nhygiene: {doc_lifecycle: 'off'}\n"
    )
    return load_workspace(tmp_path)


def classify(ws, paths, branch=BRANCH, event_name="pull_request"):
    return classify_workspace_refresh(ws, paths, branch=branch, event_name=event_name)


def test_consumer_refresh_accepts_reserved_state_and_resolved_handoff(ws):
    paths = [
        ".agentic/state/status.md",
        ".agentic/state/handoff/packages/latest/validation_report.json",
    ]
    result = classify(ws, paths)
    assert result.mode == ADMIN_REFRESH_LIGHT
    assert result.matched_paths == tuple(sorted(paths))
    assert result.mutation == "none"


def test_exact_projection_overrides_do_not_allow_adjacent_product_files(ws):
    path = ws.root / ".agentic/config.yaml"
    path.write_text(
        path.read_text()
        + "paths:\n  status_path: docs/PROJECT_STATUS.md\n  handoff_root: docs/project-handoff\n"
    )
    ws = load_workspace(ws.root)
    assert (
        classify(ws, ["docs/PROJECT_STATUS.md", "docs/project-handoff/CURRENT_HANDOFF.md"]).mode
        == ADMIN_REFRESH_LIGHT
    )
    assert classify(ws, ["docs/project-handoff/PRODUCT.md"]).mode == FULL_CI


@pytest.mark.parametrize(
    "extra",
    [
        "src/app.py",
        ".agentic/config.yaml",
        ".agentic/ci/agentic-gate.yaml",
        ".github/workflows/agentic-gate.yaml",
        ".agentic/rules/owner.md",
        "pyproject.toml",
    ],
)
def test_one_non_refresh_file_requires_full_suite(ws, extra):
    assert classify(ws, [".agentic/state/status.md", extra]).mode == FULL_CI


@pytest.mark.parametrize(
    "branch,event",
    [
        ("codex/fix-product", "pull_request"),
        (BRANCH + "-extra", "pull_request"),
        (BRANCH, "push"),
        (BRANCH, "workflow_dispatch"),
        ("", "pull_request"),
    ],
)
def test_wrong_branch_or_event_requires_full_suite(ws, branch, event):
    assert classify(ws, [".agentic/state/status.md"], branch, event).mode == FULL_CI


@pytest.mark.parametrize(
    "path",
    [
        "",
        "../outside.md",
        "/etc/file",
        "C:/file",
        ".agentic//state/a.md",
        ".agentic/state/../a",
        ".agentic/state/a\nb.md",
        ".agentic/state/a\\b.md",
    ],
)
def test_ambiguous_paths_require_full_suite(ws, path):
    assert classify(ws, [path]).mode == FULL_CI


def test_empty_diff_requires_full_suite(ws):
    assert classify(ws, []).mode == FULL_CI


def test_symlink_projection_and_parent_require_full_suite(ws):
    state = ws.root / ".agentic/state"
    state.mkdir()
    product = ws.root / "product.md"
    product.write_text("product")
    (state / "status.md").symlink_to(product)
    assert classify(ws, [".agentic/state/status.md"]).mode == FULL_CI
    (state / "link").symlink_to(ws.root, target_is_directory=True)
    assert classify(ws, [".agentic/state/link/product.md"]).mode == FULL_CI


@pytest.mark.parametrize("override", ["../escape", "src", ".github", ".git"])
def test_unsafe_operating_root_requires_full_suite(ws, override):
    manifest = ws.root / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text() + f"paths:\n  agentic_root: {override}\n")
    assert classify(load_workspace(ws.root), [".agentic/state/status.md"]).mode == FULL_CI


def test_changed_manifest_cannot_expand_own_allowlist(ws):
    manifest = ws.root / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text() + "paths:\n  status_path: docs/product.md\n")
    assert (
        classify(load_workspace(ws.root), ["docs/product.md", ".agentic/config.yaml"]).mode
        == FULL_CI
    )


def test_file_adapter_and_cli_are_pure_json_and_fail_closed(ws, capsys):
    paths = ws.root / "diff"
    paths.write_bytes(b".agentic/state/status.md\0")
    assert (
        main(
            [
                "workspace-refresh",
                "--root",
                str(ws.root),
                "--changed-paths-file",
                str(paths),
                "--branch",
                BRANCH,
                "--event-name",
                "pull_request",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["mode"] == ADMIN_REFRESH_LIGHT
    for content in (b".agentic/state/status.md\n", b"\xff\0", b""):
        paths.write_bytes(content)
        assert (
            evaluate_workspace_refresh(ws.root, paths, branch=BRANCH, event_name="pull_request")[
                "mode"
            ]
            == FULL_CI
        )
    paths.unlink()
    assert (
        evaluate_workspace_refresh(ws.root, paths, branch=BRANCH, event_name="pull_request")["mode"]
        == FULL_CI
    )
    paths.write_bytes(b".agentic/state/status.md\0")
    (ws.root / ".agentic/config.yaml").write_text("kit_schema_version: [bad]\n")
    assert (
        evaluate_workspace_refresh(ws.root, paths, branch=BRANCH, event_name="pull_request")["mode"]
        == FULL_CI
    )


@pytest.mark.parametrize(
    "fetch_rc,diff_rc,paths,expected",
    [
        (0, 0, b".agentic/state/status.md\0", ADMIN_REFRESH_LIGHT),
        (0, 0, b".agentic/state/status.md\0src/app.py\0", FULL_CI),
        (1, 0, b".agentic/state/status.md\0", FULL_CI),
        (0, 1, b".agentic/state/status.md\0", FULL_CI),
    ],
)
def test_rendered_classifier_script_uses_complete_nul_diff_or_full(
    ws, fetch_rc, diff_rc, paths, expected
):
    steps = yaml.safe_load(render_workspace_ci("1.0.22"))["jobs"]["agentic-gate"]["steps"]
    policy = next(step for step in steps if step.get("id") == "ci-policy")
    bins = ws.root / "bin"
    bins.mkdir()
    (bins / "python").write_text('#!/bin/sh\nexec "' + sys.executable + '" "$@"\n')
    (bins / "python").chmod(0o755)
    fake = bins / "git"
    fake.write_text(
        '#!/bin/sh\nif [ "$1" = fetch ]; then exit '
        + str(fetch_rc)
        + '; fi\ncat "$DIFF_FIXTURE"\nexit '
        + str(diff_rc)
        + "\n"
    )
    fake.chmod(0o755)
    fixture = ws.root / "fixture"
    fixture.write_bytes(paths)
    output = ws.root / "github-output"
    env = {
        **os.environ,
        "PATH": str(bins) + os.pathsep + os.environ["PATH"],
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        "EVENT_NAME": "pull_request",
        "REFRESH_BRANCH": BRANCH,
        "BASE_SHA": "a" * 40,
        "HEAD_SHA": "b" * 40,
        "RUNNER_TEMP": str(ws.root),
        "GITHUB_OUTPUT": str(output),
        "DIFF_FIXTURE": str(fixture),
    }
    result = subprocess.run(
        ["bash", "-e", "-c", policy["run"]], cwd=ws.root, env=env, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text() == f"mode={expected}\n"
    light = next(step for step in steps if step.get("name") == "Check workspace refresh")
    full = next(step for step in steps if step.get("name") == "Full workspace audit suite")
    assert light["run"] == "agentic-kit check --root . --json"
    assert light["if"] == "steps.ci-policy.outputs.mode == 'ADMIN_REFRESH_LIGHT'"
    assert full["run"] == "agentic-kit standard-gates-audit-suite"
    assert full["if"] == "steps.ci-policy.outputs.mode != 'ADMIN_REFRESH_LIGHT'"
    assert policy["env"]["REFRESH_BRANCH"] == "${{ github.head_ref }}"
    assert 'git diff --no-renames --name-only -z "$BASE_SHA" "$HEAD_SHA"' in policy["run"]


@pytest.mark.parametrize(
    "projection",
    [
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        ".agentic/rules/owner.yaml",
        ".agentic/registries/documentation.yaml",
        ".agentic/rule_ack/current.json",
    ],
)
def test_governance_files_cannot_be_mapped_into_light_lane(ws, projection):
    manifest = ws.root / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text() + f"paths:\n  status_path: {projection}\n")
    assert classify(load_workspace(ws.root), [projection]).mode == FULL_CI


def test_malformed_yaml_requires_full_suite(ws):
    paths = ws.root / "diff"
    paths.write_bytes(b".agentic/state/status.md\0")
    (ws.root / ".agentic/config.yaml").write_text("kit_schema_version: [\n")
    assert (
        evaluate_workspace_refresh(ws.root, paths, branch=BRANCH, event_name="pull_request")["mode"]
        == FULL_CI
    )
