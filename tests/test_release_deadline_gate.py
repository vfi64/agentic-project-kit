"""Release-count deadlines for open Kit Greenfield findings."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_deadline_gate import deadline_blockers


def _kit_root(tmp_path: Path, *, state: str = "OPEN", deadline: dict | None = None) -> Path:
    (tmp_path / "src/agentic_project_kit").mkdir(parents=True)
    planning = tmp_path / "docs/planning"
    planning.mkdir(parents=True)
    value = deadline if deadline is not None else {
        "kind": "release_count_after", "anchor_release": "1.2.0", "max_releases": 2,
    }
    import yaml

    (planning / "PROJECT_DIRECTION.yaml").write_text(yaml.safe_dump({
        "plans": [{"id": "external-v1-acceptance-removal", "finding": "KIT-GF-096", "deadline": value}],
    }))
    catalog = tmp_path / ".agentic/greenfield_findings.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(json.dumps({"findings": [{"id": "KIT-GF-096", "kit_state": state}]}))
    return tmp_path


def test_second_release_blocks_open_finding(tmp_path):
    root = _kit_root(tmp_path)
    assert deadline_blockers(root, "1.2.1", release_tags=["v1.2.0"]) == []
    assert deadline_blockers(root, "1.2.2", release_tags=["v1.2.0", "v1.2.1"]) == [
        "KIT-GF-096: release deadline reached at 1.2.2 (second release after 1.2.0)"
    ]


def test_closed_finding_and_unrelated_workspace_do_not_block(tmp_path):
    root = _kit_root(tmp_path, state="CLOSED")
    assert deadline_blockers(root, "1.2.2", release_tags=["v1.2.0", "v1.2.1"]) == []
    assert deadline_blockers(tmp_path / "external", "1.2.2", release_tags=[]) == []


def test_absent_deadline_does_not_block_and_missing_anchor_fails_closed(tmp_path):
    root = _kit_root(tmp_path)
    with pytest.raises(ValueError, match="anchor tag"):
        deadline_blockers(root, "1.2.2", release_tags=["v1.2.1"])
    import yaml

    path = root / "docs/planning/PROJECT_DIRECTION.yaml"
    data = yaml.safe_load(path.read_text())
    del data["plans"][0]["deadline"]
    path.write_text(yaml.safe_dump(data))
    assert deadline_blockers(root, "1.2.2", release_tags=[]) == []


@pytest.mark.parametrize("deadline", [
    {"kind": "release_count_after", "anchor_release": "1.2.0", "max_releases": 0},
    {"kind": "unknown", "anchor_release": "1.2.0", "max_releases": 2},
])
def test_invalid_deadline_fails_closed(tmp_path, deadline):
    root = _kit_root(tmp_path, deadline=deadline)
    with pytest.raises(ValueError, match="release deadline"):
        deadline_blockers(root, "1.2.2", release_tags=["v1.2.0", "v1.2.1"])


@pytest.mark.parametrize("entry", ["ready", "prepare"])
def test_both_release_entries_block_before_subprocess(monkeypatch, tmp_path, entry):
    _kit_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.human_workflows.deadline_blockers",
        lambda root, version: ["KIT-GF-096: release deadline reached"],
        raising=False,
    )
    calls = []
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.human_workflows.subprocess.run",
        lambda *args, **kwargs: calls.append(args),
    )
    result = CliRunner().invoke(app, ["release", entry, "--version", "1.2.2", "--json"])
    assert result.exit_code == 2
    assert "KIT-GF-096" in result.stdout
    assert calls == []
