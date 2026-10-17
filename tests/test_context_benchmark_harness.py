"""Context benchmark part 2: the harness, its prompts and its preregistration stay consistent.

The full self-test (`run_context_benchmark.py --self-test`) builds a sandbox and takes minutes;
its result is committed as CONTEXT_BENCHMARK_PART2_SELF_TEST.json. These checks are fast.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from agentic_project_kit.context_budget import SUCCESSOR_REQUIRED_READS

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH = REPO_ROOT / "docs/reports/context_budget_20261016"


def _harness():
    spec = importlib.util.spec_from_file_location("context_benchmark", BENCH / "run_context_benchmark.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["context_benchmark"] = module
    spec.loader.exec_module(module)
    return module


def test_prompts_differ_only_in_the_context_condition() -> None:
    harness = _harness()
    for task in harness.TASKS:
        b = harness.prompt_for(REPO_ROOT, task, "B")
        c = harness.prompt_for(REPO_ROOT, task, "C")
        assert task.prompt in b and task.prompt in c
        for path, _source in SUCCESSOR_REQUIRED_READS:
            assert f"- {path}" in b
        assert "Context packet:" in c and "COMMAND_MANIFEST_ACK" in c
        assert "Context packet:" not in b


def test_task_prompts_do_not_name_the_route_they_measure() -> None:
    harness = _harness()
    for task in harness.TASKS:
        for route in ("transfer commit", "sync-entrypoints", "doc-registry register", "remote-next", "push-current"):
            assert route not in task.prompt, (task.task_id, route)


def test_preregistration_and_self_test_cover_every_task() -> None:
    harness = _harness()
    ids = [task.task_id for task in harness.TASKS]
    prereg = (BENCH / "CONTEXT_BENCHMARK_PART2_20261016.md").read_text(encoding="utf-8")
    self_test = json.loads((BENCH / "CONTEXT_BENCHMARK_PART2_SELF_TEST.json").read_text(encoding="utf-8"))

    for task_id in ids:
        assert f"| {task_id} |" in prereg
    assert [r["task"] for r in self_test["results"]] == ids
    assert self_test["valid_count"] == len(ids)
    for result in self_test["results"]:
        assert result["fails_before_fix"] and result["success"] and result["method_ok"]
        assert not result["origin_main_moved"]
        if "shortcut_success" in result:
            assert result["shortcut_success"] and not result["shortcut_method_ok"]
