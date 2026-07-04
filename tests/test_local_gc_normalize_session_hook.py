from __future__ import annotations

import ast
from pathlib import Path


def test_normalize_session_runs_local_gc_preflight() -> None:
    path = Path("src/agentic_project_kit/cli_commands/transfer_handoff_flow.py")
    text = path.read_text(encoding="utf-8")
    module = ast.parse(text)

    normalize = None
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if (
                isinstance(deco, ast.Call)
                and isinstance(deco.func, ast.Attribute)
                and deco.func.attr == "command"
                and deco.args
                and isinstance(deco.args[0], ast.Constant)
                and deco.args[0].value == "normalize-session"
            ):
                normalize = node
                break
        if normalize is not None:
            break

    assert normalize is not None
    calls = [
        node.func.id
        for node in ast.walk(normalize)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "_run_local_garbage_collector_preflight" in calls


def test_normalize_session_uses_python_command_stack_state_not_environment() -> None:
    path = Path("src/agentic_project_kit/cli_commands/transfer_shared.py")
    text = path.read_text(encoding="utf-8")
    helper_start = text.index("def _run_local_garbage_collector_preflight")
    helper_end = text.index("def _load_or_exit", helper_start)
    helper = text[helper_start:helper_end]
    assert "current_or_begin_local_command_stack_id" in helper
    assert "os.environ" not in helper
    assert "AGENTIC_LOCAL_COMMAND_STACK_ID" not in helper
