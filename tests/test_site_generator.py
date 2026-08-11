from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.command_manifest import manifest_sha
from agentic_project_kit.site_generator import (
    DOCS_PAGES_FALLBACK_KIND,
    SITE_KIND,
    build_docs_pages_fallback,
    build_site,
    collect_site_foundation_metadata,
)


def test_site_foundation_metadata_uses_meta_manifest_sha(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)

    report = collect_site_foundation_metadata(root, build_commit="abc123")

    assert report.ok
    assert report.metadata is not None
    assert report.metadata.package_version == "1.2.3"
    assert report.metadata.requires_python == ">=3.11"
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
        "site.json",
        "static/runtime-map.svg",
        "static/site.css",
    )
    html = (output / "index.html").read_text(encoding="utf-8")
    data = json.loads((output / "site.json").read_text(encoding="utf-8"))
    commands = json.loads((output / "commands" / "commands.json").read_text(encoding="utf-8"))
    claims = json.loads((output / "claims" / "claims.json").read_text(encoding="utf-8"))
    assert "Agentic Execution Runtime" in html
    assert "Repository Memory" in html
    assert "Verified now" in html
    assert "1.2.3" in html
    assert "abc123" in html
    assert "v1.2.3" in html
    assert data["kind"] == SITE_KIND
    assert data["metadata"]["package_version"] == "1.2.3"
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
    assert "agentic-kit workspace init" in (
        output / "commands" / "guided.html"
    ).read_text(encoding="utf-8")
    assert "agentic-kit check-docs" in (
        output / "commands" / "diagnostics.html"
    ).read_text(encoding="utf-8")


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
        "site/site.json",
        "site/static/runtime-map.svg",
        "site/static/site.css",
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
            "params": [],
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
            "${guided_command_items} ${common_diagnostic_items}</html>\n"
        ),
        encoding="utf-8",
    )
    (root / "site" / "templates" / "commands.html").write_text(
        "<html>${title} ${rows}</html>\n",
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
