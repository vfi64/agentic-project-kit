from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path("src/agentic_project_kit")
SAFE_PUSH_IMPLEMENTATION = Path("src/agentic_project_kit/safe_push.py")
TAG_PUSH_EXCEPTIONS = {
    Path("src/agentic_project_kit/release_publish_orchestration.py"),
}


def _constant_strings(node: ast.AST) -> list[str] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    values: list[str] = []
    for element in node.elts:
        if isinstance(element, ast.Constant) and isinstance(element.value, str):
            values.append(element.value)
        else:
            values.append("")
    return values


def _starts_with_git_push(node: ast.AST) -> bool:
    values = _constant_strings(node)
    return bool(values and len(values) >= 2 and values[0] == "git" and values[1] == "push")


def _starts_with_helper_push(node: ast.AST) -> bool:
    values = _constant_strings(node)
    return bool(values and values[0] == "push")


def _is_delete_push(node: ast.AST) -> bool:
    values = _constant_strings(node) or []
    return "--delete" in values


def _is_authorized_push(path: Path, node: ast.AST) -> bool:
    if path == SAFE_PUSH_IMPLEMENTATION:
        return True
    if _is_delete_push(node):
        return True
    if path in TAG_PUSH_EXCEPTIONS:
        return True
    return False


def _called_function_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def test_direct_git_push_calls_go_through_safe_push_gatekeeper() -> None:
    findings: list[str] = []
    helper_names = {"_run_git", "run_git", "_command", "_run", "runner"}
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Tuple)) and _starts_with_git_push(node):
                if not _is_authorized_push(path, node):
                    findings.append(f"{path}:{node.lineno}: {ast.unparse(node)}")
            if isinstance(node, ast.Call) and _called_function_name(node) in helper_names:
                candidates = list(node.args)
                if len(candidates) >= 2:
                    candidates.append(candidates[1])
                for candidate in candidates[:2]:
                    if _starts_with_helper_push(candidate) and not _is_authorized_push(path, candidate):
                        findings.append(f"{path}:{node.lineno}: {_called_function_name(node)}({ast.unparse(candidate)})")

    assert findings == []


def test_normal_callers_do_not_enable_protected_branch_push_override() -> None:
    findings: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        if path == SAFE_PUSH_IMPLEMENTATION:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _called_function_name(node) != "safe_push":
                continue
            for keyword in node.keywords:
                if keyword.arg == "allow_protected":
                    findings.append(f"{path}:{node.lineno}: {ast.unparse(node)}")

    assert findings == []
