from __future__ import annotations

import inspect
from pathlib import Path

import typer

from agentic_project_kit.cli_commands import release as release_cli
from agentic_project_kit.release_prepare import prepare_release_state
import agentic_project_kit.release_prep_core as release_prep_core
import agentic_project_kit.release_publish_core as release_publish_core


def test_release_prep_is_registered_once_on_public_agentic_kit_surface() -> None:
    source = inspect.getsource(release_cli.register_release_commands)
    assert 'app.command("release-prep")(release_prep_command)' in source
    assert "release_metadata_prep_command" not in source


def test_release_prep_command_uses_python_core_not_ns_or_tools() -> None:
    source = inspect.getsource(release_cli.release_prep_command)
    assert "prepare_release_state" in source
    assert "./ns" not in source
    assert "tools/ns_" not in source
    assert "post-release-doi-closeout" not in source
    assert "git tag" not in source
    assert "gh release create" not in source


def test_release_prepare_core_is_still_deterministic_metadata_authority(tmp_path: Path) -> None:
    for relative, content in {
        "pyproject.toml": 'version = "0.4.8"\n',
        "src/agentic_project_kit/__init__.py": '__version__ = "0.4.8"\n',
        "README.md": "Current version: 0.4.8\n",
        "CITATION.cff": 'version: 0.4.8\ndate-released: "2026-06-01"\n',
        "docs/STATUS.md": "Current version: 0.4.8\n",
        "docs/handoff/CURRENT_HANDOFF.md": "Current version: 0.4.8\n",
        "CHANGELOG.md": "## v0.4.8 - 2026-06-01\n\n- Existing.\n",
    }.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    result = prepare_release_state(
        tmp_path,
        version="0.4.9",
        date="2026-06-18",
        summary_lines=["Release metadata prepared through explicit changelog summary input."],
        dry_run=True,
    )

    assert result.ok is True
    assert result.dry_run is True
    assert result.version == "0.4.9"
    assert sorted(result.changed_paths) == [
        "CHANGELOG.md",
        "CITATION.cff",
        "README.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "pyproject.toml",
        "src/agentic_project_kit/__init__.py",
    ]


def test_release_prep_core_no_longer_advertises_ns_route() -> None:
    source = inspect.getsource(release_prep_core)
    assert "./ns release-prep" not in source
    assert "NS RELEASE PREP CYCLE" not in source
    assert "agentic-kit release-prep --version" in source
    assert "AGENTIC-KIT RELEASE PREP CYCLE" in source


def test_release_publish_core_is_fail_closed_after_ns_removal() -> None:
    source = inspect.getsource(release_publish_core)
    assert "./ns" not in source
    assert "NS RELEASE PUBLISH CYCLE" not in source
    assert "direct release publish core is disabled after legacy ns removal" in source
    assert "No branch, tag, push, GitHub release, or DOI side effect was attempted." in source


def test_release_prep_rejects_invalid_version_without_side_effect(monkeypatch, capsys) -> None:
    calls: list[object] = []

    def fake_prepare_release_state(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("prepare_release_state must not be called for malformed versions")

    monkeypatch.setattr(release_cli, "prepare_release_state", fake_prepare_release_state)

    try:
        release_cli.release_prep_command(
            project_root=Path("."),
            version="not-a-version",
            release_date="2026-06-18",
            dry_run=True,
            json_output=False,
        )
    except typer.Exit as exc:
        assert exc.exit_code == 2

    assert calls == []
    assert "Invalid release version" in capsys.readouterr().out
