from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.command_manifest import manifest_sha
from agentic_project_kit.site_generator import (
    SITE_KIND,
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
    assert report.metadata.command_count == 2
    assert report.metadata.manifest_sha == report.metadata.reproduced_manifest_sha
    assert report.metadata.manifest_identity_verified is True


def test_site_foundation_build_writes_deterministic_static_artifact(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path)
    output = tmp_path / "out"

    result = build_site(root, output_dir=output, build_commit="abc123")

    assert result.ok
    assert result.files == ("index.html", "site.json", "static/site.css")
    html = (output / "index.html").read_text(encoding="utf-8")
    data = json.loads((output / "site.json").read_text(encoding="utf-8"))
    assert "Agentic Execution Runtime" in html
    assert "1.2.3" in html
    assert "abc123" in html
    assert data["kind"] == SITE_KIND
    assert data["metadata"]["package_version"] == "1.2.3"
    assert data["metadata"]["manifest_identity_verified"] is True


def test_site_foundation_blocks_manifest_identity_mismatch(tmp_path: Path) -> None:
    root = _write_site_fixture(tmp_path, manifest_identity="not-current")

    report = collect_site_foundation_metadata(root, build_commit="abc123")

    assert not report.ok
    assert report.metadata is None
    assert report.blockers == (
        "command manifest meta.manifest_sha does not match the reproduced command manifest hash",
    )


def _write_site_fixture(root: Path, *, manifest_identity: str | None = None) -> Path:
    (root / "docs" / "reference").mkdir(parents=True)
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
        {
            "qualified_name": "agentic-kit check-docs",
            "surface": "diagnostic",
            "safety": "READ_ONLY",
        },
        {
            "qualified_name": "agentic-kit workspace init",
            "surface": "orchestrator",
            "safety": "BOUNDED",
        },
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
        "<html>${product_name} ${package_version} ${build_commit}</html>\n",
        encoding="utf-8",
    )
    (root / "site" / "static" / "site.css").write_text("body { color: black; }\n", encoding="utf-8")
    return root
