"""KIT-GF-120: agentic-kit init starts the new repository on main, whatever init.defaultBranch says.

The Kit's workflows (work start --from-ref main, sync-main, release run) assume main. Before the fix
init ran a plain ``git init``, so on a machine without init.defaultBranch=main the project and its
first push (init --github) landed on master.
"""
from __future__ import annotations

import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app


@pytest.mark.parametrize("default_branch", ["master", "trunk", None])
def test_init_starts_on_main_whatever_the_git_default_branch(tmp_path, monkeypatch, default_branch):
    config = tmp_path / "gitconfig"
    text = "[user]\n\tname = Init Main\n\temail = init@example.invalid\n[commit]\n\tgpgsign = false\n"
    if default_branch:
        text += f"[init]\n\tdefaultBranch = {default_branch}\n"
    config.write_text(text)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init", "demo", "--type", "python-lib", "--no-pre-commit", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS" and payload["initial_commit"] is True
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=tmp_path / "demo",
                            capture_output=True, text=True, check=True).stdout.strip()
    assert branch == "main"
    heads = subprocess.run(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"], cwd=tmp_path / "demo",
                           capture_output=True, text=True, check=True).stdout.split()
    assert heads == ["main"]
