from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _function_source(path: str, function_name: str) -> str:
    source = _source(path)
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise AssertionError(f"function not found: {path}:{function_name}")


def test_workspace_lock_exposes_explicit_mutation_context() -> None:
    source = _source("src/agentic_project_kit/workspace_lock.py")

    assert "workspace_mutation_lock" in source
    assert "contextmanager" in source or "@contextlib.contextmanager" in source
    assert "acquire_workspace_lock" in source


def test_branch_mutators_require_workspace_mutation_lock_contract() -> None:
    source = _source("src/agentic_project_kit/transfer_repo_actions.py")

    for function_name in ["branch_create", "branch_switch", "ensure_remote_head"]:
        body = _function_source("src/agentic_project_kit/transfer_repo_actions.py", function_name)
        assert "workspace_mutation_lock" in body, function_name

    assert "workspace_mutation_lock" in source


def test_pr_flow_mutators_require_workspace_mutation_lock_contract() -> None:
    for path, functions in {
        "src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py": [
            "pr_create_complete_command",
        ],
        "src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py": [
            "pr_complete_command",
        ],
    }.items():
        for function_name in functions:
            body = _function_source(path, function_name)
            assert "workspace_mutation_lock" in body, f"{path}:{function_name}"


def test_mutation_lock_audit_prioritizes_enforced_core_paths() -> None:
    source = _source("src/agentic_project_kit/mutation_lock_audit.py")

    assert "workspace_mutation_lock" in source
    assert "transfer_repo_actions.py" in source
    assert "transfer_pr_create_flow.py" in source
    assert "transfer_pr_merge_flow.py" in source

def test_ensure_remote_head_does_not_wrap_push_current_with_outer_lock() -> None:
    body = _function_source("src/agentic_project_kit/transfer_repo_actions.py", "ensure_remote_head")

    assert "workspace_mutation_lock" in body
    assert "push_current(" in body
    assert 'with workspace_mutation_lock(Path("."),' not in body


def test_pr_existing_for_branch_uses_gh_pr_list_head_lookup() -> None:
    body = _function_source(
        "src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py",
        "pr_existing_for_branch_command",
    )

    assert '"pr"' in body
    assert '"list"' in body
    assert '"--head"' in body
    assert '"--base"' in body
    assert '"--state"' in body
    assert '"--json"' in body
    assert "json.loads" in body
    assert '"view"' not in body
