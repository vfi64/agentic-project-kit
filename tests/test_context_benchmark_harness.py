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


def test_preregistration_and_historical_self_test_cover_every_task() -> None:
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


def test_direction_fault_hits_validator_and_preserves_nested_metadata(tmp_path):
    import yaml
    from agentic_project_kit.project_direction import validate_project_direction_data

    harness = _harness()
    original = (REPO_ROOT / "docs/planning/PROJECT_DIRECTION.yaml").read_text()
    target = tmp_path / "direction.yaml"
    target.write_text(original)
    before = yaml.safe_load(original)
    assert validate_project_direction_data(before, root=REPO_ROOT).ok
    harness.support.set_direction_fault(target)
    injected = yaml.safe_load(target.read_text())
    assert injected["meta"] == before["meta"]
    result = validate_project_direction_data(injected, root=REPO_ROOT)
    assert [f.code for f in result.findings] == ["invalid-status"]
    harness.support.set_direction_fault(target, repair=True)
    assert target.read_text() == original
    assert validate_project_direction_data(yaml.safe_load(target.read_text()), root=REPO_ROOT).ok


def test_composite_failure_cannot_substitute_for_target_gate_failure():
    support = _harness().support
    fields = dict(outcome_failed_before=True, gate_failed_before=False,
                  gate_passed_after=True, success=True, method_ok=True,
                  origin_main_moved=False, reference_error="", shortcut={})
    assert not support.self_test_valid(**fields)
    assert support.self_test_valid(**{**fields, "gate_failed_before": True})
    assert not support.self_test_valid(**{**fields, "gate_failed_before": True,
                                         "origin_main_moved": True})


def test_sanitized_snapshot_has_neither_reference_contents_nor_old_objects(tmp_path):
    support = _harness().support
    source = tmp_path / "source"
    source.mkdir()
    support._git(source, "init", "-q", "-b", "main")
    hidden = source / "docs/reports/context_budget_example/reference.py"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("SECRET_REFERENCE = 'gold-solution'\n")
    (source / "product.py").write_text("answer = 42\n")
    support._git(source, "add", ".")
    support._git(source, "-c", "commit.gpgsign=false", "commit", "-qm", "original")
    old = support._git(source, "rev-parse", "HEAD")
    base = tmp_path / "fixture"
    base.mkdir()
    work, provenance = support.build_agent_snapshot(source, base, old)
    assert "gold-solution" not in (work / hidden.relative_to(source)).read_text()
    assert support._git(work, "rev-list", "--count", "--all") == "1"
    import subprocess
    assert subprocess.run(["git", "cat-file", "-e", old], cwd=work,
                          capture_output=True).returncode != 0
    assert (work / "product.py").read_text() == "answer = 42\n"
    assert provenance["source_commit"] == old


def test_native_isolation_denies_evaluator_reads_in_child_process(tmp_path):
    import subprocess
    import pytest
    support = _harness().support
    try:
        prefix = support.agent_isolation_prefix([tmp_path / "private"])
    except RuntimeError:
        pytest.skip("macOS sandbox-exec unavailable; real-agent mode fails closed")
    private = tmp_path / "private"
    private.mkdir()
    (private / "secret").write_text("reference solution")
    public = tmp_path / "public"
    public.write_text("visible")
    allowed = subprocess.run([*prefix, "/bin/cat", str(public)], capture_output=True, text=True)
    assert allowed.returncode == 0 and allowed.stdout == "visible"
    denied = subprocess.run([*prefix, "/bin/sh", "-c", '/bin/cat "$1"',
                             "probe", str(private / "secret")], capture_output=True, text=True)
    assert denied.returncode != 0 and "reference solution" not in denied.stdout


def test_timeout_stops_descendants_and_retains_output(tmp_path):
    import os
    import subprocess
    import time
    import pytest

    support = _harness().support
    marker = tmp_path / "should-not-exist"
    child = "import time; from pathlib import Path; time.sleep(1); Path(" + repr(str(marker)) + ").touch()"
    parent = ("import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', "
              + repr(child) + "]); print('started', flush=True); time.sleep(30)")
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        support.run_agent_process([sys.executable, "-c", parent], cwd=tmp_path,
                                  env=dict(os.environ), timeout=0.2)
    assert "started" in caught.value.stdout
    time.sleep(1)
    assert not marker.exists()


def test_empty_or_unknown_experiment_cannot_pass(monkeypatch):
    import pytest
    harness = _harness()
    for extra in (["--tasks", "TYPO"], ["--repetitions", "0"], ["--conditions"]):
        monkeypatch.setattr(sys, "argv", ["benchmark", "--self-test", "--out", "/tmp/unused.json", *extra])
        with pytest.raises(SystemExit) as caught:
            harness.main()
        assert caught.value.code == 2


def test_agent_is_not_started_when_fault_misses_target(monkeypatch, tmp_path):
    from dataclasses import replace
    import pytest
    harness = _harness()
    task = replace(harness.TASKS[0], gate_check=lambda root: True)
    monkeypatch.setattr(harness, "prepare", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="Target gate passed"):
        harness.run_agent(tmp_path, task, "C", "must-never-start", 1, tmp_path)
