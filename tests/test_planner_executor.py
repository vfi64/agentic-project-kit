from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cockpit import BOUNDED, READ_ONLY, CockpitAction
from agentic_project_kit.planner_executor import (
    RESULT_PASS,
    RESULT_PENDING,
    build_planner_executor_plan,
    parse_planner_executor_intent,
    run_planner_executor_intent,
)


def _intent_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": 1,
        "id": "demo-intent",
        "title": "Demo intent",
        "executor_adapter": "hermes",
        "block_dirty_worktree": False,
        "steps": [
            {
                "id": "docs",
                "kind": "cockpit_action",
                "action_id": "gate.check-docs",
            }
        ],
    }
    data.update(overrides)
    return data


def test_parse_intent_accepts_hermes_adapter_without_making_it_authority() -> None:
    intent = parse_planner_executor_intent(_intent_data())

    assert intent.executor_adapter == "hermes"
    assert intent.steps[0].action_id == "gate.check-docs"


def test_parse_intent_rejects_non_kit_command_step() -> None:
    data = _intent_data(
        steps=[
            {
                "id": "raw",
                "kind": "command",
                "argv": ["python", "-m", "pytest"],
            }
        ]
    )

    try:
        parse_planner_executor_intent(data)
    except ValueError as exc:
        assert "must start with agentic-kit" in str(exc)
    else:
        raise AssertionError("non-Kit command step should fail")


def test_plan_resolves_cockpit_action_safety() -> None:
    intent = parse_planner_executor_intent(_intent_data())
    plan = build_planner_executor_plan(intent)

    assert plan.result_status == RESULT_PASS
    assert plan.steps[0].authority == "cockpit"
    assert plan.steps[0].safety == "READ_ONLY"
    assert plan.steps[0].executable_by_default is True


def test_plan_blocks_unknown_manifest_command() -> None:
    intent = parse_planner_executor_intent(
        _intent_data(
            steps=[
                {
                    "id": "unknown",
                    "kind": "command",
                    "argv": ["agentic-kit", "missing-command"],
                }
            ]
        )
    )

    plan = build_planner_executor_plan(intent)

    assert plan.result_status == RESULT_PENDING
    assert "command not found" in plan.blockers[0]


def test_run_is_dry_run_by_default(tmp_path: Path) -> None:
    intent = parse_planner_executor_intent(_intent_data())

    result = run_planner_executor_intent(intent, tmp_path)

    assert result.result_status == RESULT_PENDING
    assert result.executed is False
    assert (tmp_path / result.evidence_path).exists()


def test_run_executes_read_only_manifest_command_with_runner(tmp_path: Path) -> None:
    intent = parse_planner_executor_intent(
        _intent_data(
            steps=[
                {
                    "id": "manifest-docs",
                    "kind": "command",
                    "argv": ["agentic-kit", "check-docs"],
                }
            ]
        )
    )
    calls: list[tuple[str, ...]] = []

    def runner(argv: tuple[str, ...], _root: Path) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(list(argv), 0, "ok", "")

    result = run_planner_executor_intent(intent, tmp_path, execute=True, runner=runner)

    assert result.result_status == RESULT_PASS
    assert result.executed is True
    assert calls


def test_bounded_cockpit_action_requires_intent_and_cli_allow(tmp_path: Path, monkeypatch) -> None:
    import agentic_project_kit.planner_executor as planner_executor

    actions = [
        CockpitAction(
            "demo.bounded",
            "Bounded",
            "demo",
            ("demo", "go"),
            BOUNDED,
            "Run bounded demo.",
            "Run bounded demo",
        ),
        CockpitAction(
            "demo.status",
            "Status",
            "demo",
            ("demo", "status"),
            READ_ONLY,
            "Read demo.",
            "Read demo",
        ),
    ]
    monkeypatch.setattr(planner_executor, "cockpit_actions", lambda: actions)
    intent = parse_planner_executor_intent(
        _intent_data(
            steps=[
                {
                    "id": "bounded",
                    "kind": "cockpit_action",
                    "action_id": "demo.bounded",
                    "allow_bounded": True,
                }
            ]
        )
    )

    result = run_planner_executor_intent(intent, tmp_path, execute=True)

    assert result.result_status == RESULT_PENDING
    assert "requires intent allow_bounded and CLI --allow-bounded" in result.message


def test_executor_plan_cli_outputs_json(tmp_path: Path) -> None:
    intent = tmp_path / "intent.yaml"
    intent.write_text(
        "schema_version: 1\n"
        "id: cli-demo\n"
        "title: CLI demo\n"
        "executor_adapter: hermes\n"
        "block_dirty_worktree: false\n"
        "steps:\n"
        "  - id: docs\n"
        "    kind: cockpit_action\n"
        "    action_id: gate.check-docs\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["executor", "plan", str(intent), "--json"])

    assert result.exit_code == 0
    assert '"executor_adapter": "hermes"' in result.output
    assert '"authority": "cockpit"' in result.output
