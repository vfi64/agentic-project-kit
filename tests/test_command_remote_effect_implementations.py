import subprocess

import pytest
from typer import Typer

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import build_current_reference, build_reference_from_app, load_manifest
from tests.remote_effect_scan import scan_command_effects


def test_every_statically_observed_remote_command_has_a_non_none_declaration():
    declared = {c["qualified_name"]: set(c["remote_effects"]) for c in build_current_reference()["commands"]}
    observed = scan_command_effects(app)
    missing = {name: sorted(effects) for name, effects in observed.items() if effects and declared[name] == {"none"}}
    assert not missing, missing
    assert "merge" in observed["agentic-kit pr merge-if-green"]
    assert "fetch" in observed["agentic-kit transfer pull-current"]
    assert "delete_remote" in observed["agentic-kit remote-branch-hygiene-apply"]
    assert not observed["agentic-kit pr-closeout"]
    assert not observed["agentic-kit transfer publish-last-report"]


def test_static_scan_detects_a_future_remote_command_with_no_declaration():
    fixture = Typer()
    @fixture.command("future-action")
    def future_action():
        subprocess.run(["git", "push", "origin", "future"], check=True)
    declared = build_reference_from_app(fixture)["commands"][0]
    assert declared["remote_effects"] == ["none"]
    assert scan_command_effects(fixture)["agentic-kit future-action"] == {"push"}


@pytest.mark.parametrize("name,expected", [
    ("agentic-kit pr merge-if-green", {"merge", "delete_remote"}),
    ("agentic-kit remote-branch-hygiene-apply", {"push", "delete_remote"}),
    ("agentic-kit transfer pull-current", {"fetch"}),
    ("agentic-kit pr-closeout", {"none"}),
    ("agentic-kit transfer publish-last-report", {"none"}),
    ("agentic-kit post-release-doi-closeout", {"network_read"}),
])
def test_packaged_remote_effect_declarations_in_an_external_workspace(tmp_path, name, expected):
    commands = {c["qualified_name"]: c for c in load_manifest(tmp_path)["commands"]}
    assert expected <= set(commands[name]["remote_effects"])
