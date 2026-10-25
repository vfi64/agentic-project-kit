"""KIT-GF-086: release prepare must stop at the first guard step."""
import json
from types import SimpleNamespace
import pytest
from typer.testing import CliRunner
from agentic_project_kit.cli import app
import agentic_project_kit.cli_commands.human_workflows as workflows


@pytest.mark.parametrize("mode", ["--dry-run", "--write"])
def test_release_prepare_blocks_before_any_later_step(tmp_path, monkeypatch, mode):
    workflow = tmp_path / ".github/workflows/gate.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("steps:\n  - run: pip install agentic-project-kit==99.0.0\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(workflows, "load_workspace", lambda _: SimpleNamespace(
        tmp_file=lambda name: tmp_path / name))
    def no_later_step(*args, **kwargs):
        raise AssertionError("release prepare executed a step after the CI pin guard")
    monkeypatch.setattr(workflows, "_run_step", no_later_step)
    before = {str(p.relative_to(tmp_path)): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    response = CliRunner().invoke(app, ["release", "prepare", "--version", "1.1.6",
        "--from-tag", "v1.1.5", "--to-ref", "main", mode, "--json"])
    assert response.exit_code != 0, response.output
    result = json.loads(response.stdout)
    assert result["result_status"] in {"BLOCKED", "FAIL"}
    assert len(result["steps"]) == 1
    step = result["steps"][0]
    assert step["name"] == "kit-ci-pin-guard"
    assert not step["ok"]
    assert "installed_kit_older_than_ci_pin" in step["stdout"]
    after = {str(p.relative_to(tmp_path)): p.read_bytes()
             for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before
