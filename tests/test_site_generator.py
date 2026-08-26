from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.command_manifest import manifest_sha
from agentic_project_kit.site_generator import (
    DOCS_PAGES_FALLBACK_KIND,
    SITE_KIND,
    SiteCommandEntry,
    build_docs_pages_fallback,
    build_site,
    collect_site_foundation_metadata,
    _guided_lifecycle_entries,
)


def test_site_foundation_metadata_uses_meta_manifest_sha(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)

    report = collect_site_foundation_metadata(root, build_commit="abc123")

    assert report.ok
    assert report.metadata is not None
    assert report.metadata.package_version == "1.2.3"
    assert report.metadata.requires_python == ">=3.11"
    assert report.metadata.repository_url == "https://example.invalid/repo"
    assert report.metadata.command_count == 3
    assert report.metadata.manifest_sha == report.metadata.reproduced_manifest_sha
    assert report.metadata.manifest_identity_verified is True


def test_site_foundation_build_writes_deterministic_static_artifact(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    output = tmp_path / "out"

    result = build_site(root, output_dir=output, build_commit="abc123")

    assert result.ok
    assert result.files == (
        "claims/claims.json",
        "claims/index.html",
        "commands/commands.json",
        "commands/diagnostics.html",
        "commands/guided.html",
        "commands/index.html",
        "index.html",
        "quickstart/index.html",
        "quickstart/quickstart.json",
        "site.json",
        "static/runtime-map.svg",
        "static/site.css",
        "workflows/index.html",
        "workflows/workflows.json",
    )
    html = (output / "index.html").read_text(encoding="utf-8")
    data = json.loads((output / "site.json").read_text(encoding="utf-8"))
    commands = json.loads((output / "commands" / "commands.json").read_text(encoding="utf-8"))
    claims = json.loads((output / "claims" / "claims.json").read_text(encoding="utf-8"))
    quickstart = json.loads((output / "quickstart" / "quickstart.json").read_text(encoding="utf-8"))
    workflows = json.loads((output / "workflows" / "workflows.json").read_text(encoding="utf-8"))
    assert "Agentic Execution Runtime" in html
    assert "Repository Memory" in html
    assert "Choose How You Want To Work" in html
    assert "Verified now" in html
    assert "1.2.3" in html
    assert "abc123" in html
    assert "v1.2.3" in html
    assert "pip install agentic-project-kit" in html
    assert "https://example.invalid/repo" in html
    assert data["kind"] == SITE_KIND
    assert data["metadata"]["package_version"] == "1.2.3"
    assert data["metadata"]["repository_url"] == "https://example.invalid/repo"
    assert data["metadata"]["manifest_identity_verified"] is True
    assert data["metadata"]["surface_counts"] == {
        "diagnostic": 1,
        "orchestrator": 1,
        "primitive": 1,
    }
    assert data["status_projection"]["current_release_tag"] == "v1.2.3"
    assert data["roadmap_projection"]["status"] == "active"
    assert commands["guided_count"] == 1
    assert commands["diagnostic_count"] == 1
    assert commands["entries"][0]["diagnostic_priority"] == "common_blocker"
    assert claims["claim_count"] == 0
    assert quickstart["kind"] == "site_quickstart_projection"
    assert quickstart["docs"][0]["path"] == "docs/ONBOARDING.md"
    assert quickstart["flows"][0]["commands"][0]["qualified_name"] == "agentic-kit init"
    assert workflows["kind"] == "site_workflow_projection"
    assert [mode["id"] for mode in workflows["modes"]] == [
        "file-transfer",
        "copy-paste",
        "agent-direct",
        "gui",
    ]
    assert workflows["brownfield"]["status"] == "not_recorded"
    assert "First-chat onboarding" in (output / "quickstart" / "index.html").read_text(encoding="utf-8")
    assert "Executor Is Replaceable; Repository Governance Persists" in (
        output / "workflows" / "index.html"
    ).read_text(encoding="utf-8")
    assert "Docker" in (output / "quickstart" / "index.html").read_text(encoding="utf-8")
    assert "agentic-kit workspace init" in (
        output / "commands" / "guided.html"
    ).read_text(encoding="utf-8")
    assert "agentic-kit check-docs" in (
        output / "commands" / "diagnostics.html"
    ).read_text(encoding="utf-8")
    command_html = (output / "commands" / "index.html").read_text(encoding="utf-8")
    assert 'id="command-search"' in command_html
    assert 'data-safety="BOUNDED"' in command_html
    assert "default=" in command_html


def test_docs_pages_fallback_writes_redirect_and_generated_site(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)

    result = build_docs_pages_fallback(root)

    assert result.ok
    assert result.as_dict()["kind"] == DOCS_PAGES_FALLBACK_KIND
    assert result.files == (
        ".nojekyll",
        "index.html",
        "site/claims/claims.json",
        "site/claims/index.html",
        "site/commands/commands.json",
        "site/commands/diagnostics.html",
        "site/commands/guided.html",
        "site/commands/index.html",
        "site/index.html",
        "site/quickstart/index.html",
        "site/quickstart/quickstart.json",
        "site/site.json",
        "site/static/runtime-map.svg",
        "site/static/site.css",
        "site/workflows/index.html",
        "site/workflows/workflows.json",
    )
    redirect = (root / "docs" / "index.html").read_text(encoding="utf-8")
    generated_site = (root / "docs" / "site" / "site.json").read_text(encoding="utf-8")
    assert 'url=site/index.html' in redirect
    assert 'href="site/index.html"' in redirect
    assert "docs-pages-fallback" in generated_site
    assert "See docs/STATUS.md" in generated_site
    assert (root / "docs" / ".nojekyll").read_text(encoding="utf-8")
    assert (root / "docs" / "site" / "index.html").exists()
    assert (root / "docs" / "STATUS.md").read_text(encoding="utf-8").startswith(
        "## Current State"
    )


def test_docs_pages_fallback_ignores_volatile_status_refresh(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)

    build_docs_pages_fallback(root)
    first_site_json = (root / "docs" / "site" / "site.json").read_text(encoding="utf-8")
    status_path = root / "docs" / "STATUS.md"
    status_path.write_text(
        status_path.read_text(encoding="utf-8")
        .replace("Current verified main: `abc123`.", "Current verified main: `def456`.")
        .replace("Latest substantive work: PR #1.", "Latest substantive work: PR #2."),
        encoding="utf-8",
    )

    build_docs_pages_fallback(root)

    assert (root / "docs" / "site" / "site.json").read_text(encoding="utf-8") == first_site_json


def test_guided_lifecycle_entries_use_manifest_rank_before_alphabetical_order() -> None:
    entries = (
        _entry("agentic-kit artifact-gc", rank=100),
        _entry("agentic-kit workspace init", rank=20),
        _entry("agentic-kit init", rank=0),
        _entry("agentic-kit work start", rank=30),
    )

    assert [entry.qualified_name for entry in _guided_lifecycle_entries(entries)] == [
        "agentic-kit init",
        "agentic-kit workspace init",
        "agentic-kit work start",
        "agentic-kit artifact-gc",
    ]


def test_site_foundation_blocks_manifest_identity_mismatch(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path, manifest_identity="not-current")

    report = collect_site_foundation_metadata(root, build_commit="abc123")

    assert not report.ok
    assert report.metadata is None
    assert report.blockers == (
        "command manifest meta.manifest_sha does not match the reproduced command manifest hash",
    )


def test_site_foundation_blocks_missing_orchestrator_surface(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path, surfaces=("diagnostic", "primitive"))

    report = collect_site_foundation_metadata(root, build_commit="abc123")

    assert not report.ok
    assert "guided command view has no orchestrator commands" in report.blockers


def test_site_foundation_blocks_invalid_command_surface(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path, surfaces=("diagnostic", "unknown", "primitive"))

    report = collect_site_foundation_metadata(root, build_commit="abc123")

    assert not report.ok
    assert "agentic-kit workspace init: invalid surface 'unknown'" in report.blockers


def test_public_site_templates_name_remote_target_ci_limitation() -> None:
    limitation = "Remote target-CI validation is not claimed"

    assert limitation in Path("site/templates/index.html").read_text(encoding="utf-8")
    assert limitation in Path("site/templates/claims.html").read_text(encoding="utf-8")


def test_workflow_projection_reads_brownfield_closeout_evidence(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    report_path = root / "docs" / "reports" / "POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(
            {
                "status": "B1_EVALUABLE",
                "rule_ack_evidence_type": "kit_main_external_retest_not_released_package",
                "public_summary": "Five cycles.",
                "generalization_boundary": "one repo only",
                "cycle_totals": {
                    "real_cycles": 5,
                    "merge_boundary_cycles": 4,
                    "administrative_refresh_prs": 6,
                    "admin_refresh_rate": "6/4 = 1.5",
                    "observable_admin_refresh_share": "6/11",
                },
                "seam_metric": {
                    "definition": "legacy_seams_remaining",
                    "start": 72,
                    "end": 58,
                },
                "tests": {
                    "full_suite_min": 1483,
                    "full_suite_max": 1490,
                    "cycle_005_test_boundary": "remote CI only",
                },
                "defects": [
                    {"id": "B1-KIT-002"},
                    {"id": "B1-KIT-004-005"},
                    {"id": "B1-KIT-006"},
                    {"id": "B1-KIT-009"},
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_site(root, output_dir=tmp_path / "out", build_commit="abc123")

    assert result.ok
    workflows = json.loads(
        (tmp_path / "out" / "workflows" / "workflows.json").read_text(encoding="utf-8")
    )
    assert workflows["brownfield"]["status"] == "B1_EVALUABLE"
    assert workflows["brownfield"]["real_cycles"] == 5
    assert workflows["brownfield"]["legacy_seams_end"] == 58
    assert (
        workflows["brownfield"]["rule_ack_evidence_type"]
        == "kit_main_external_retest_not_released_package"
    )


def _write_site_fixture(
    root: Path,
    *,
    manifest_identity: str | None = None,
    surfaces: tuple[str, ...] = ("diagnostic", "orchestrator", "primitive"),
) -> Path:
    (root / "docs" / "reference").mkdir(parents=True)
    (root / "site" / "templates").mkdir(parents=True)
    (root / "site" / "static").mkdir(parents=True)
    (root / "docs" / "planning").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "agentic-project-kit"',
                'version = "1.2.3"',
                'requires-python = ">=3.11"',
                "",
                "[project.urls]",
                'Repository = "https://example.invalid/repo"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    command_names = [
        ("agentic-kit check-docs", "root", "READ_ONLY"),
        ("agentic-kit workspace init", "workspace", "BOUNDED"),
        ("agentic-kit transfer commit", "transfer", "BOUNDED"),
    ]
    commands = [
        {
            "qualified_name": qualified_name,
            "group": group,
            "surface": surface,
            "safety": safety,
            "dry_run_available": False,
            "when_to_use": f"Run {qualified_name}.",
            "help": "",
            "params": [
                {
                    "name": "root",
                    "required": False,
                    "opts": ["--root"],
                    "default": ".",
                    "help": "Repository root.",
                }
            ],
        }
        for (qualified_name, group, safety), surface in zip(command_names, surfaces, strict=False)
    ]
    identity = manifest_identity or manifest_sha(commands)
    (root / "docs" / "reference" / "agentic-kit-commands.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": "agentic_kit_command_reference",
                "source": "test",
                "meta": {
                    "schema_version": 1,
                    "manifest_sha": identity,
                    "generated_md": "docs/reference/AGENTIC_KIT_COMMANDS.md",
                },
                "commands": commands,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "index.html").write_text(
        (
            "<html>${product_name} ${package_version} ${build_commit} "
            "${orchestrator_count} ${release_tag} Repository Memory Verified now "
            "Choose How You Want To Work ${workflow_mode_count} ${brownfield_status} "
            "pip install ${package_name} ${repository_url} "
            "${guided_command_items} ${common_diagnostic_items}</html>\n"
        ),
        encoding="utf-8",
    )
    (root / "site" / "templates" / "commands.html").write_text(
        '<html>${title} <input id="command-search"> ${rows}</html>\n',
        encoding="utf-8",
    )
    (root / "site" / "templates" / "quickstart.html").write_text(
        "<html>${product_name} ${package_name} Docker ${new_repo_command_items} ${existing_repo_command_items} ${docs_link_items}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "templates" / "workflows.html").write_text(
        (
            "<html>${product_name} Executor Is Replaceable; Repository Governance Persists "
            "${mode_cards} ${core_workflow_items} ${boundary_items} ${brownfield_items}</html>\n"
        ),
        encoding="utf-8",
    )
    (root / "site" / "templates" / "claims.html").write_text(
        "<html>${claim_count} ${rows}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "static" / "site.css").write_text("body { color: black; }\n", encoding="utf-8")
    (root / "site" / "static" / "runtime-map.svg").write_text(
        "<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>\n",
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
        "\n".join(
            [
                "schema_version: 1",
                "meta:",
                "  status: active",
                "  updated_after_pr: 1",
                "  updated_after_pr_semantics: strategic_direction_refresh",
                "  updated_after_pr_current_main_claimed: false",
                "strategy:",
                "  - id: one",
                "    status: active",
                "roadmap:",
                "  - id: one",
                "    status: done",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root


def _entry(qualified_name: str, *, rank: int | None) -> SiteCommandEntry:
    return SiteCommandEntry(
        qualified_name=qualified_name,
        group=qualified_name.removeprefix("agentic-kit ").split()[0],
        surface="orchestrator",
        safety="BOUNDED",
        dry_run_available=False,
        diagnostic_priority="normal",
        when_to_use=f"Use {qualified_name}.",
        help=f"Use {qualified_name}.",
        lifecycle_rank=rank,
        params=(),
    )
