from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer

from agentic_project_kit.cli_commands import release as release_cli
from agentic_project_kit.release_metadata_authority_gate import (
    evaluate_release_metadata_authority_gate,
    is_release_anchor_path,
    release_metadata_anchor_changes_from_diff,
)


def test_release_anchor_path_classification() -> None:
    assert is_release_anchor_path("pyproject.toml")
    assert is_release_anchor_path("src/agentic_project_kit/__init__.py")
    assert is_release_anchor_path("docs/releases/VERIFIED_RELEASES.md")
    assert is_release_anchor_path("docs/releases/notes/v1.md")
    assert not is_release_anchor_path("src/agentic_project_kit/release.py")
    assert not is_release_anchor_path("tests/test_release.py")


def test_gate_passes_when_no_release_anchor_changed(tmp_path: Path) -> None:
    result = evaluate_release_metadata_authority_gate(
        tmp_path,
        version="0.4.9",
        changed_paths=["src/agentic_project_kit/release.py"],
    )

    assert result.ok is True
    assert result.status == "PASS"
    assert result.changed_release_anchor_paths == []


def test_gate_blocks_release_anchor_changes_without_evidence(tmp_path: Path) -> None:
    result = evaluate_release_metadata_authority_gate(
        tmp_path,
        version="0.4.9",
        changed_paths=["pyproject.toml", "README.md"],
    )

    assert result.ok is False
    assert result.status == "BLOCK"
    assert result.changed_release_anchor_paths == ["README.md", "pyproject.toml"]
    assert "without authoritative release-prepare evidence" in result.message


def test_release_metadata_diff_filter_ignores_non_release_readme_hunks() -> None:
    diff_text = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -10,0 +11,3 @@
+`agentic-kit workspace upgrade --root PATH` is a dry-run by default.
+It prints a manifest diff and writes `.agentic/config.yaml.bak.v<N>`.
+It tells newer-schema repositories to upgrade the kit instead of guessing.
"""

    changed = release_metadata_anchor_changes_from_diff(diff_text, ["README.md"])

    assert changed == []


def test_release_metadata_diff_filter_keeps_release_readme_hunks() -> None:
    diff_text = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -10,0 +11,2 @@
+Current verified release: `0.4.13`.
+Verified Zenodo version DOI: `10.5281/zenodo.29999999`.
"""

    changed = release_metadata_anchor_changes_from_diff(diff_text, ["README.md"])

    assert changed == ["README.md"]


def test_gate_accepts_authoritative_json_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "release-prep-evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "command": "agentic-kit release-prep --version 0.4.9 --summary-line 'Prepare release metadata.' --json",
                "version": "0.4.9",
                "changed_paths": ["README.md", "pyproject.toml"],
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_release_metadata_authority_gate(
        tmp_path,
        version="0.4.9",
        evidence_paths=[evidence],
        changed_paths=["pyproject.toml", "README.md"],
    )

    assert result.ok is True
    assert result.status == "PASS"
    assert result.evidence_paths == [evidence.as_posix()]


def test_gate_rejects_evidence_for_wrong_version(tmp_path: Path) -> None:
    evidence = tmp_path / "release-prep-evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "command": "agentic-kit release-prep --version 0.4.8 --summary-line 'Prepare release metadata.' --json",
                "version": "0.4.8",
                "changed_paths": ["README.md", "pyproject.toml"],
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_release_metadata_authority_gate(
        tmp_path,
        version="0.4.9",
        evidence_paths=[evidence],
        changed_paths=["pyproject.toml", "README.md"],
    )

    assert result.ok is False
    assert result.status == "BLOCK"


def test_release_metadata_authority_gate_command_blocks(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(
        release_cli,
        "evaluate_release_metadata_authority_gate",
        lambda *args, **kwargs: evaluate_release_metadata_authority_gate(
            tmp_path,
            version="0.4.9",
            changed_paths=["pyproject.toml"],
        ),
    )

    with pytest.raises(typer.Exit) as excinfo:
        release_cli.release_metadata_authority_gate_command(
            project_root=tmp_path,
            base_ref="origin/main",
            version="0.4.9",
            evidence=None,
            json_output=False,
        )

    assert excinfo.value.exit_code == 1
    assert "RELEASE_METADATA_AUTHORITY_GATE" in capsys.readouterr().out


def test_release_metadata_authority_gate_is_registered() -> None:
    import inspect

    source = inspect.getsource(release_cli.register_release_commands)
    assert 'app.command("release-metadata-authority-gate")(release_metadata_authority_gate_command)' in source
