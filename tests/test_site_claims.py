from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from agentic_project_kit.command_manifest import manifest_sha
from agentic_project_kit.site_claims import CommandExecution, evaluate_site_claims
from agentic_project_kit.site_generator import SiteCommandCatalog, SiteCommandEntry, build_site


def test_claim_evaluator_computes_verified_pyproject_entrypoint(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: cli
    text: CLI exists.
    required: true
    evidence:
      type: pyproject-entrypoint
      script: agentic-kit
      target: agentic_project_kit.cli:app
""",
    )
    _add_pyproject_scripts(root)

    report = evaluate_site_claims(root)

    assert report.ok
    assert report.status_counts()["verified"] == 1
    assert report.claims[0].status == "verified"


def test_claim_evaluator_rejects_stored_verified_status(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: bad
    text: Bad claim.
    required: false
    status: verified
    evidence:
      type: pyproject-value
      key: project.version
""",
    )

    report = evaluate_site_claims(root)

    assert not report.ok
    assert report.schema_blockers == (
        "bad: stored derived status fields are forbidden: status",
    )


def test_optional_unverified_claim_does_not_block_site_build(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: optional
    text: Optional command claim.
    required: false
    evidence:
      type: command-manifest
      qualified_name: agentic-kit missing
""",
    )

    result = build_site(root, output_dir=tmp_path / "out", build_commit="abc123")

    assert result.ok
    assert result.report.claim_report.claims[0].status == "unverified"


def test_required_unverified_claim_blocks_site_build(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: required
    text: Required command claim.
    required: true
    evidence:
      type: command-manifest
      qualified_name: agentic-kit missing
""",
    )

    result = build_site(root, output_dir=tmp_path / "out", build_commit="abc123")

    assert not result.ok
    assert result.report.claim_report.blockers == (
        "required claim is not verified: required",
    )


def test_pytest_node_evidence_runs_the_named_node(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    calls: list[Sequence[str]] = []
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: test-node
    text: Test node claim.
    required: true
    evidence:
      type: pytest-node
      node_id: tests/test_example.py::test_example
""",
    )

    def runner(_root: Path, command: Sequence[str], _timeout: int) -> CommandExecution:
        calls.append(command)
        return CommandExecution(0, ".")

    report = evaluate_site_claims(root, command_runner=runner)

    assert report.ok
    assert calls
    assert list(calls[0][-4:]) == ["-m", "pytest", "-q", "tests/test_example.py::test_example"]


def test_generated_artifact_evidence_checks_manifest_coverage(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: catalog
    text: Catalog is complete.
    required: true
    evidence:
      type: generated-artifact
      assertion: manifest-command-coverage
""",
    )
    incomplete_catalog = SiteCommandCatalog(
        entries=(
            SiteCommandEntry(
                qualified_name="agentic-kit check-docs",
                group="root",
                surface="diagnostic",
                safety="READ_ONLY",
                dry_run_available=False,
                diagnostic_priority="common_blocker",
                when_to_use="Run agentic-kit check-docs.",
                help="",
                params=(),
            ),
        )
    )

    report = evaluate_site_claims(root, command_catalog=incomplete_catalog)

    assert not report.ok
    assert report.claims[0].status == "unverified"
    assert "catalog coverage mismatch" in report.claims[0].blockers[0]


def test_command_probe_evidence_checks_json_assertion(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: probe
    text: Probe claim.
    required: true
    evidence:
      type: command-probe
      command:
        - agentic-kit
        - audit-command-manifest
        - --json
      assertion:
        json_path: $.status
        equals: PASS
""",
    )

    def runner(_root: Path, _command: Sequence[str], _timeout: int) -> CommandExecution:
        return CommandExecution(0, json.dumps({"status": "PASS"}))

    report = evaluate_site_claims(root, command_runner=runner)

    assert report.ok
    assert report.claims[0].status == "verified"


def test_file_contains_evidence_checks_repository_text(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    (root / "README.md").write_text("Install from source: git+https://example.invalid/repo.git@main\n", encoding="utf-8")
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: source-install
    text: Source install path is documented.
    required: true
    evidence:
      type: file-contains
      path: README.md
      contains: git+https://example.invalid/repo.git@main
""",
    )

    report = evaluate_site_claims(root)

    assert report.ok
    assert report.claims[0].status == "verified"


def test_file_contains_evidence_rejects_root_escape(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    _write_claims(
        root,
        """
schema_version: 1
claims:
  - id: escape
    text: Root escape is invalid.
    required: false
    evidence:
      type: file-contains
      path: ../outside.md
      contains: nope
""",
    )

    report = evaluate_site_claims(root)

    assert report.claims[0].status == "unverified"
    assert "path escapes root" in report.claims[0].blockers[0]


def _write_claims(root: Path, text: str) -> None:
    (root / "site" / "content").mkdir(parents=True, exist_ok=True)
    (root / "site" / "content" / "claims.yaml").write_text(text.strip() + "\n", encoding="utf-8")


def _add_pyproject_scripts(root: Path) -> None:
    path = root / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text
        + "\n[project.scripts]\n"
        + 'agentic-kit = "agentic_project_kit.cli:app"\n',
        encoding="utf-8",
    )


def _write_site_fixture(root: Path) -> Path:
    (root / "docs" / "reference").mkdir(parents=True)
    (root / "docs" / "planning").mkdir(parents=True)
    (root / "site" / "content").mkdir(parents=True)
    (root / "site" / "templates").mkdir(parents=True)
    (root / "site" / "static").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "agentic-project-kit"',
                'version = "1.2.3"',
                'requires-python = ">=3.11"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    commands = [
        _command("agentic-kit check-docs", "root", "diagnostic", "READ_ONLY"),
        _command("agentic-kit workspace init", "workspace", "orchestrator", "BOUNDED"),
        _command("agentic-kit transfer commit", "transfer", "primitive", "BOUNDED"),
    ]
    (root / "docs" / "reference" / "agentic-kit-commands.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": "agentic_kit_command_reference",
                "source": "test",
                "meta": {
                    "schema_version": 1,
                    "manifest_sha": manifest_sha(commands),
                    "generated_md": "docs/reference/AGENTIC_KIT_COMMANDS.md",
                },
                "commands": commands,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "docs" / "STATUS.md").write_text(
        "\n".join(
            [
                "## Current State",
                "",
                "Current version: 1.2.3",
                "Current verified release: 1.2.3.",
                "Current release tag: v1.2.3.",
                "Zenodo concept DOI: `10.5281/zenodo.1`.",
                "Verified Zenodo version DOI: `10.5281/zenodo.2`.",
                "Current verified main: `abc123`.",
                "Latest substantive work: PR #1.",
                "Next safe step: continue.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "docs" / "planning" / "PROJECT_DIRECTION.yaml").write_text(
        "schema_version: 1\nmeta:\n  status: active\nstrategy: []\nroadmap: []\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "index.html").write_text(
        "<html>${product_name} ${claim_verified_count}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "commands.html").write_text(
        "<html>${title} ${rows}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "quickstart.html").write_text(
        "<html>${product_name} ${new_repo_command_items} ${existing_repo_command_items} ${docs_link_items}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "workflows.html").write_text(
        "<html>${product_name} ${mode_cards} ${core_workflow_items} ${boundary_items} ${brownfield_items}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "claims.html").write_text(
        "<html>${claim_count} ${rows}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "static" / "site.css").write_text("body { color: black; }\n", encoding="utf-8")
    return root


def _command(qualified_name: str, group: str, surface: str, safety: str) -> dict[str, object]:
    return {
        "qualified_name": qualified_name,
        "group": group,
        "surface": surface,
        "safety": safety,
        "dry_run_available": False,
        "when_to_use": f"Run {qualified_name}.",
        "help": "",
        "params": [],
    }
