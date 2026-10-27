"""Release preparation refreshes the design projection after manifest changes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.release_review_projection import review_projection_command

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/task_selection_design_check.py"
OUTPUT = "docs/reports/task_selection_design_20261026/README.md"


def make_checkout(root):
    for relative in (SCRIPT, OUTPUT, "docs/reference/TASK_COMMAND_SELECTION_PROPOSAL.yaml",
                     "docs/reference/agentic-kit-commands.json", "pyproject.toml"):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (root / "src/agentic_project_kit").mkdir(parents=True)


def test_projection_command_uses_checkout_identity_not_script_presence(tmp_path):
    assert review_projection_command(tmp_path, sys.executable) is None
    make_checkout(tmp_path)
    (tmp_path / SCRIPT).unlink()
    assert review_projection_command(tmp_path, sys.executable) == [sys.executable, SCRIPT, "--out", OUTPUT]


@pytest.mark.parametrize("mode", ["write", "generator_failure", "missing_generator", "external", "dry_run"])
def test_release_projection_order_failure_and_isolation(tmp_path, monkeypatch, mode):
    make_checkout(tmp_path)
    if mode == "external":
        (tmp_path / "src/agentic_project_kit").rmdir()
    if mode == "generator_failure":
        (tmp_path / "docs/reference/TASK_COMMAND_SELECTION_PROPOSAL.yaml").write_text("{}")
    if mode == "missing_generator":
        (tmp_path / SCRIPT).unlink()
    before = (tmp_path / OUTPUT).read_bytes()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(human_workflows, "default_python", lambda root: sys.executable)
    original_run = subprocess.run
    calls = []

    def run_step(name, argv, **kwargs):
        calls.append(name)
        if name == "commands-sync-entrypoints":
            path = tmp_path / "docs/reference/agentic-kit-commands.json"
            manifest = json.loads(path.read_text())
            manifest["meta"]["manifest_sha"] = "new-release-manifest"
            path.write_text(json.dumps(manifest))
        if name == "task-selection-review-refresh":
            done = original_run(argv, text=True, capture_output=True)
            return {"name": name, "argv": argv, "returncode": done.returncode,
                    "ok": done.returncode == 0, "stdout": done.stdout, "stderr": done.stderr}
        return {"name": name, "argv": argv, "returncode": 0, "ok": True, "stdout": "", "stderr": ""}

    monkeypatch.setattr(human_workflows, "_run_step", run_step)
    monkeypatch.setattr(human_workflows, "_dpa_readiness_ack_refresh_step",
                        lambda: run_step("dpa-readiness-ack-refresh", []))
    monkeypatch.setattr(human_workflows, "_write_release_prepare_report_step",
                        lambda **kwargs: run_step("release-prepare-report", []))
    args = ["release", "prepare", "--version", "1.1.7", "--from-tag", "v1.1.6", "--json"]
    if mode != "dry_run":
        args.append("--write")
    result = CliRunner().invoke(app, args)
    payload = json.loads(result.stdout)
    if mode in {"generator_failure", "missing_generator"}:
        assert result.exit_code == 2, result.output
        assert payload["blockers"] == ["task-selection-review-refresh"]
        assert "successor-handoff-refresh" not in calls
        assert "docs-pages-fallback-refresh" not in calls
        assert not list((tmp_path / "docs/reports/release").glob("release-prepare-*.json"))
        assert (tmp_path / OUTPUT).read_bytes() == before
    elif mode == "write":
        assert result.exit_code == 0, result.output
        assert calls.index("commands-sync-entrypoints") < calls.index("task-selection-review-refresh")
        assert calls.index("task-selection-review-refresh") < calls.index("successor-handoff-refresh")
        rendered = (tmp_path / OUTPUT).read_text()
        assert "current manifest `new-release-manifest`" in rendered
        again = original_run([sys.executable, SCRIPT, "--out", OUTPUT], capture_output=True, text=True)
        assert again.returncode == 0, again.stderr
        assert (tmp_path / OUTPUT).read_text() == rendered
    else:
        assert result.exit_code == 0, result.output
        assert "task-selection-review-refresh" not in calls
        assert (tmp_path / OUTPUT).read_bytes() == before
