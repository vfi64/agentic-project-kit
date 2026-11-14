"""G2 (owner 2026-11-13): release checks that depend only on repository content run at the PR.

The release steps are derived from the source (syntax tree), not copied: every step of
``release ready``, ``release prepare`` and the ``--before-release`` part of
``transfer standard-error-scan`` must be listed under ``release_path`` in
reference/check-producers.json with a stage. ``pr`` steps must be steps of ``work finish``,
``work-start`` steps steps of ``work start``, and a ``release-only`` step names the directory entry
whose producer makes its content part pass at the PR. ``work finish`` runs the scan without
``--before-release``, so the PR scan is the release scan minus exactly those listed steps.
"""
from __future__ import annotations

import ast
import json
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_content_at_pr import CHECK_ID, release_run_covering_branch, scan_summary
from agentic_project_kit.workspace import load_workspace

SRC = Path(__file__).resolve().parents[1] / "src" / "agentic_project_kit"
HUMAN = SRC / "cli_commands" / "human_workflows.py"
SCAN = SRC / "cli_commands" / "transfer_diagnostics.py"
PRIMITIVES = {"_run_step", "step", "self_hosting_step", "_noop_step", "_failed_local_step"}
STAGES = {"pr", "work-start", "release-only", "release-input", "advisory", "action"}
HW = "agentic_project_kit.cli_commands.human_workflows"


def _directory() -> dict:
    return json.loads(files("agentic_project_kit.reference").joinpath("check-producers.json").read_text("utf-8"))


def _functions(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _literal(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _step_names(func: ast.FunctionDef, functions: dict[str, ast.FunctionDef], seen: set[str] | None = None) -> set[str]:
    """Literal step names a command builds, following module helpers named *_step or *_steps."""
    seen = set() if seen is None else seen
    names: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called = node.func.id
            if called in PRIMITIVES:
                if node.args and _literal(node.args[0]):
                    names.add(_literal(node.args[0]))
            elif called.endswith(("_step", "_steps")) and called in functions and called not in seen:
                seen.add(called)
                names |= _step_names(functions[called], functions, seen)
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if _literal(key) == "name" and _literal(value):
                    names.add(_literal(value))
    return names


def _before_release_only_steps(func: ast.FunctionDef) -> set[str]:
    """Steps the scan runs, or lets block, only with --before-release."""
    names: set[str] = set()

    def gated(call: ast.Call) -> bool:
        return any(
            keyword.arg == "allowed_returncodes" and isinstance(keyword.value, ast.IfExp)
            and isinstance(keyword.value.test, ast.Name) and keyword.value.test.id == "before_release"
            for keyword in call.keywords
        )

    def visit(node: ast.AST, release: bool) -> None:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "before_release":
            for child in node.body:
                visit(child, True)
            for child in node.orelse:
                visit(child, release)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in PRIMITIVES:
            if node.args and _literal(node.args[0]) and (release or gated(node)):
                names.add(_literal(node.args[0]))
        if isinstance(node, ast.Dict) and release:
            for key, value in zip(node.keys, node.values):
                if _literal(key) == "name" and _literal(value):
                    names.add(_literal(value))
        for child in ast.iter_child_nodes(node):
            visit(child, release)

    for statement in func.body:
        visit(statement, False)
    return names


def _derived_release_path() -> dict[str, set[str]]:
    human = _functions(HUMAN)
    return {
        "release ready": _step_names(human["release_ready_command"], human),
        "release prepare": _step_names(human["release_prepare_command"], human),
        "standard-error-scan --before-release": _before_release_only_steps(_functions(SCAN)["standard_error_scan_command"]),
    }


def _listed_release_path() -> dict[str, set[str]]:
    listed: dict[str, set[str]] = {}
    for item in _directory()["release_path"]:
        listed.setdefault(item["command"], set()).add(item["step"])
    return listed


def test_every_release_step_in_the_source_is_listed_with_a_stage():
    derived, listed = _derived_release_path(), _listed_release_path()
    assert set(listed) == set(derived)
    for command, steps in derived.items():
        missing = sorted(steps - listed[command])
        stale = sorted(listed[command] - steps)
        assert missing == [], f"G2: list these {command} steps under release_path in check-producers.json: {missing}"
        assert stale == [], f"G2: release_path lists {command} steps the source no longer has: {stale}"


def test_the_detector_sees_the_known_release_only_steps():
    # Self-test: the syntax-tree walk finds the steps that only the release runs or lets block.
    scan = _derived_release_path()["standard-error-scan --before-release"]
    assert {"release-notes-generate", "release-prep-dry-run", "post-merge-check",
            "fresh-context-clean-post-merge-allowance"} <= scan
    assert "docs-audit" not in scan and "standard-gates-audit-suite" not in scan


def test_every_release_path_entry_has_a_valid_stage_and_reason():
    directory = _directory()
    assert set(directory["release_path_stages"]) == STAGES
    entries = {entry["id"] for entry in directory["entries"]}
    human = _functions(HUMAN)
    finish = _step_names(human["work_finish_command"], human)
    start = _step_names(human["work_start_command"], human)
    for item in directory["release_path"]:
        label = f"{item['command']}: {item['step']}"
        assert item["stage"] in STAGES, label
        assert item.get("reason", "").strip(), f"{label} needs a reason"
        if item["stage"] == "pr":
            assert item["step"] in finish, f"{label} is stage pr but work finish has no such step"
        if item["stage"] == "work-start":
            assert item["step"] in start, f"{label} is stage work-start but work start has no such step"
        if item["stage"] == "release-only":
            assert item.get("check_id") in entries, f"{label} needs the check_id of a directory entry"


def _completed(argv, stdout='{"result_status": "PASS"}\n', returncode=0):
    return subprocess.CompletedProcess(list(argv), returncode, stdout, "")


def _finish(tmp_path, monkeypatch, fake_run, *extra):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(f"{HW}.subprocess.run", fake_run)
    return CliRunner().invoke(app, ["work", "finish", "--branch", "feat/x", "--title", "T", "--message", "T",
                                    "--path", "a.py", *extra, "--json"])


def test_work_finish_runs_the_scan_without_the_release_flag_before_the_commit(tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(argv)

    result = _finish(tmp_path, monkeypatch, fake_run)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    names = [step["name"] for step in payload["steps"]]
    assert names.index("kit-ci-pin-guard") < names.index("standard-error-scan") < names.index("remote-preflight")
    scans = [argv for argv in calls if argv[1:3] == ["transfer", "standard-error-scan"]]
    assert len(scans) == 1 and "--before-release" not in scans[0]


def test_a_blocked_scan_stops_work_finish_with_check_id_and_route(tmp_path, monkeypatch):
    blocked = json.dumps({"result_status": "BLOCKED", "blockers": ["docs-audit"], "warnings": []})

    def fake_run(argv, *args, **kwargs):
        if list(argv)[1:3] == ["transfer", "standard-error-scan"]:
            return _completed(argv, stdout=blocked, returncode=2)
        return _completed(argv)

    result = _finish(tmp_path, monkeypatch, fake_run, "--execute")
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["blockers"] == ["standard-error-scan"]
    assert payload["check_id"] == CHECK_ID
    assert payload["next_command_kind"] == "kit" and payload["next_command_autonomous"] is False
    assert "work finish" in payload["next_command"] and "--path a.py" in payload["next_command"]
    step = payload["steps"][-1]
    assert "BLOCKER=docs-audit" in step["stdout"] and "standard-error-scan --json" in step["stdout"]
    assert not any(s["name"] == "commit" for s in payload["steps"])


def test_a_kit_older_than_the_ci_pin_stops_work_finish_with_the_update_route(tmp_path, monkeypatch):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("run: pip install agentic-project-kit==99.0.0\n", encoding="utf-8")
    result = _finish(tmp_path, monkeypatch, lambda argv, *a, **k: _completed(argv))
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["blockers"] == ["kit-ci-pin-guard"]
    assert payload["check_id"] == CHECK_ID
    assert payload["next_command"] == "agentic-kit kit update --root . --version 99.0.0"


def _release_state(tmp_path: Path, *, finished: list[str]) -> None:
    # Same place the release run writes its state (ReleaseRun.state_path).
    tmp = load_workspace(tmp_path, suppress_legacy_profile_warning=True).tmp()
    tmp.mkdir(parents=True, exist_ok=True)
    state = {"kind": "release_run_state", "version": "1.4.0", "release_branch": "codex/release-1.4.0",
             "finished_steps": finished}
    (tmp / "release-run-1.4.0.json").write_text(json.dumps(state), encoding="utf-8")


@pytest.mark.parametrize("branch", ["codex/release-1.4.0", "codex/release-1.4.0-doi"])
def test_a_release_run_after_a2_owns_its_branches(tmp_path, branch):
    _release_state(tmp_path, finished=["A1", "A2", "A3", "B1", "B2"])
    assert release_run_covering_branch(tmp_path, branch) == "1.4.0"
    assert release_run_covering_branch(tmp_path, "feat/other") == ""


def test_a_release_run_before_a2_covers_nothing(tmp_path):
    _release_state(tmp_path, finished=["A1"])
    assert release_run_covering_branch(tmp_path, "codex/release-1.4.0") == ""


def test_scan_summary_reads_status_blockers_and_warnings():
    assert scan_summary('{"result_status": "WARN", "blockers": [], "warnings": ["w"]}') == ("WARN", [], ["w"])
    assert scan_summary("not json") == ("<no JSON>", [], [])
