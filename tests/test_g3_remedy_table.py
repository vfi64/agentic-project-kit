"""G3 remedy table (owner decision 2026-11-15): every listed cause names its resolving Kit command.

Ratchet: each entry of ``g3_remedies.REMEDIES`` has a case here that drives its emitter and checks
the emitted ``next_command``; an entry without a case fails. KIT-GF-114 (workspace init over an
``init`` project), KIT-GF-115 (recovery with injection flags) and KIT-GF-116 (release run B4 stop)
ended with the human marker although a Kit command resolves them.
"""
from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems
from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import workspace as workspace_cli
from agentic_project_kit.cli_commands.routed_output import kit_command
from agentic_project_kit.g3_remedies import CONDITIONS, REMEDIES, routes_for
from agentic_project_kit.greenfield_retest import check_route
from agentic_project_kit.release_run import ReleaseRun
from agentic_project_kit.workspace_upgrade import WorkspaceUpgradeError
from agentic_project_kit.workspace_remove import WorkspaceRemoveError

runner = CliRunner()


def _json(args: list[str], code: int) -> dict:
    result = runner.invoke(app, [*args, "--json"])
    assert result.exit_code == code, result.output
    return json.loads(result.output)


def _generated_project(tmp_path: Path) -> Path:
    previous = Path.cwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["init", "demo", "--type", "python-lib", "--no-pre-commit", "--json"])
    finally:
        os.chdir(previous)
    assert result.exit_code == 0, result.output
    root = tmp_path / "demo"
    assert (root / ".agentic/project.yaml").is_file() and not (root / ".agentic/config.yaml").exists()
    return root


def _kit(payload: dict, words: tuple[str, ...], root: Path | None = None) -> None:
    assert payload["next_command_kind"] == KIND_KIT, payload
    assert payload["next_command"] == kit_command(*words, root=root)
    assert payload["next_command_autonomous"] is True and route_problems(payload) == []


def case_already_initialized(tmp_path: Path) -> None:
    assert runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"]).exit_code == 0
    payload = _json(["workspace", "init", "--root", str(tmp_path)], 1)
    assert payload["code"] == "ALREADY_INITIALIZED"
    _kit(payload, REMEDIES[("workspace init", "ALREADY_INITIALIZED")], tmp_path)


def case_foreign_agentic(tmp_path: Path) -> None:
    root = _generated_project(tmp_path)
    payload = _json(["workspace", "init", "--root", str(root), "--name", "demo", "--inject-ci"], 1)
    assert payload["result_status"] == "FAIL" and payload["code"] == "FOREIGN_AGENTIC"
    _kit(payload, REMEDIES[("workspace init", "FOREIGN_AGENTIC")], root)
    assert "workspace ci-update --inject-ci --execute" in payload["next_action"]
    # The route leads to a plan: the recovery offers its signature.
    plan = _json(shlex.split(payload["next_command"])[1:], 0)
    assert plan["result_status"] == "AWAITING_APPROVAL" and plan["approval_signature"]
    # Condition: a foreign .agentic/ without a generated contract stays with the person.
    foreign = tmp_path / "foreign"
    (foreign / ".agentic").mkdir(parents=True)
    other = _json(["workspace", "init", "--root", str(foreign)], 1)
    assert other["code"] == "FOREIGN_AGENTIC" and other["next_command_kind"] == KIND_HUMAN
    assert route_problems(other) == []


def case_recovery_no_injection(tmp_path: Path) -> None:
    root = _generated_project(tmp_path)
    for flag in ("--inject-ci", "--inject-pre-commit"):
        payload = _json(["workspace", "init", "--root", str(root), "--recover-partial", flag], 2)
        assert payload["result_status"] == "BLOCKED" and payload["code"] == "RECOVERY_NO_INJECTION"
        assert payload["written"] is False and "workspace ci-update --inject-ci --execute" in payload["next_action"]
        _kit(payload, REMEDIES[("workspace init", "RECOVERY_NO_INJECTION")], root)
        assert "next_command_reason" not in payload or not payload["next_command_reason"]


def _emitted(kind: str, exc: Exception, routes: dict, root: Path) -> dict:
    return workspace_cli._error_payload(kind, exc, routes, root)


def case_no_manifest(tmp_path: Path) -> None:
    payload = _json(["workspace", "upgrade", "--root", str(tmp_path)], 1)
    assert payload["code"] == "NO_MANIFEST"
    _kit(payload, REMEDIES[("workspace upgrade", "NO_MANIFEST")], tmp_path)


def case_manifest_changed(tmp_path: Path) -> None:
    exc = WorkspaceUpgradeError("workspace manifest changed after the upgrade plan was built", code="MANIFEST_CHANGED")
    payload = _emitted("workspace_upgrade_result", exc, workspace_cli.UPGRADE_ERROR_ROUTES, tmp_path)
    _kit(payload, REMEDIES[("workspace upgrade", "MANIFEST_CHANGED")], tmp_path)


def case_plan_changed(tmp_path: Path) -> None:
    exc = WorkspaceRemoveError("plan changed", code="PLAN_CHANGED")
    payload = _emitted("workspace_remove_result", exc, workspace_cli.REMOVE_ERROR_ROUTES, tmp_path)
    _kit(payload, REMEDIES[("workspace remove", "PLAN_CHANGED")], tmp_path)


def _b4(result: dict, root: Path = Path(".")) -> dict:
    run = SimpleNamespace(version="0.1.1", options=SimpleNamespace(root=root))
    return ReleaseRun._b4_route(run, result)  # type: ignore[arg-type]


def case_release_b4(tmp_path: Path) -> None:
    words = ("agentic-kit", *REMEDIES[("release run", "B4")], "--version", "0.1.1")
    pushed = _b4({"step_id": "B4", "result_status": "BLOCKED", "blockers": ["returncode"],
                  "next_action": "Inspect release-run-0.1.1.log and fix step B4."})
    assert pushed["next_command"] == shlex.join(words) and pushed["next_command_kind"] == KIND_KIT
    assert pushed["next_command_autonomous"] is True and "resume" in pushed["next_action"]
    drift = _b4({"step_id": "B4", "result_status": "BLOCKED", "blockers": ["changed-paths-drift"]}, tmp_path)
    assert drift["next_command"] == shlex.join([*words, "--root", str(tmp_path)])
    # K6: a route the failed step brought wins; PASS stays untouched.
    own = _b4({"step_id": "B4", "result_status": "BLOCKED", "next_command": "agentic-kit ci status --json",
               "next_command_kind": KIND_KIT, "next_command_autonomous": True})
    assert own["next_command"] == "agentic-kit ci status --json"
    assert "next_command" not in _b4({"step_id": "B4", "result_status": "PASS"})


CASES = {
    ("workspace init", "ALREADY_INITIALIZED"): case_already_initialized,
    ("workspace init", "FOREIGN_AGENTIC"): case_foreign_agentic,
    ("workspace init", "RECOVERY_NO_INJECTION"): case_recovery_no_injection,
    ("workspace upgrade", "NO_MANIFEST"): case_no_manifest,
    ("workspace upgrade", "MANIFEST_CHANGED"): case_manifest_changed,
    ("workspace remove", "PLAN_CHANGED"): case_plan_changed,
    ("release run", "B4"): case_release_b4,
}


def test_every_remedy_has_a_case_and_every_case_a_remedy():
    assert set(CASES) == set(REMEDIES)
    assert set(CONDITIONS) <= set(REMEDIES)


def test_every_remedy_is_a_manifest_route_of_an_existing_orchestrator():
    for (owner, _code), words in REMEDIES.items():
        assert check_route(["agentic-kit", *owner.split()])["path"] == owner.split()
        commands = [word for word in words if not word.startswith("-")]
        assert check_route(["agentic-kit", *words])["path"] == commands


def test_routes_for_lists_one_orchestrator():
    assert set(routes_for("workspace init")) == {"ALREADY_INITIALIZED", "FOREIGN_AGENTIC", "RECOVERY_NO_INJECTION"}
    assert routes_for("release run") == {"B4": ("release", "run")}


def test_already_initialized(tmp_path: Path):
    case_already_initialized(tmp_path)


def test_foreign_agentic_over_a_generated_project(tmp_path: Path):
    case_foreign_agentic(tmp_path)


def test_recovery_with_injection_flags(tmp_path: Path):
    case_recovery_no_injection(tmp_path)


def test_no_manifest(tmp_path: Path):
    case_no_manifest(tmp_path)


def test_manifest_changed(tmp_path: Path):
    case_manifest_changed(tmp_path)


def test_plan_changed(tmp_path: Path):
    case_plan_changed(tmp_path)


def test_release_b4(tmp_path: Path):
    case_release_b4(tmp_path)


def test_foreign_agentic_text_mode_names_the_recovery(tmp_path: Path):
    root = _generated_project(tmp_path)
    result = runner.invoke(app, ["workspace", "init", "--root", str(root), "--name", "demo"])
    assert result.exit_code == 1
    assert f"NEXT_COMMAND={kit_command('workspace', 'init', '--recover-partial', root=root)}" in result.output
