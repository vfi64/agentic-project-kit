"""Bounded static check of literal remote argv and reachable package helpers."""
from __future__ import annotations

import ast
from functools import lru_cache
import inspect
import textwrap
from types import ModuleType

from typer.main import get_command


def _argv_effects(values: list[str]) -> set[str]:
    effects = set()
    if values[:1] == ["git"] and len(values) > 1:
        if values[1] in {"fetch", "pull"}:
            effects.add("fetch")
        if values[1] == "push":
            effects.add("push")
            if "--delete" in values:
                effects.add("delete_remote")
    # gh adapters sometimes prepend "gh" to a helper's argv.
    gh = values[1:] if values[:1] == ["gh"] else values
    if gh[:1] == ["pr"] and len(gh) > 1:
        effects.add("network_read")
        if gh[1] == "merge":
            effects.add("merge")
            if "--delete-branch" in gh:
                effects.add("delete_remote")
        elif gh[1] in {"create", "close", "edit", "comment", "review", "reopen", "ready"}:
            effects.add("pull_request")
    if gh[:1] == ["release"] and len(gh) > 1:
        effects.add("network_read")
        if gh[1] in {"create", "upload", "edit", "delete"}:
            effects.add("release_publish")
    return effects


def _resolve(node, namespace):
    if isinstance(node, ast.Name):
        return namespace.get(node.id)
    if isinstance(node, ast.Attribute):
        parent = _resolve(node.value, namespace)
        if isinstance(parent, ModuleType):
            return getattr(parent, node.attr, None)
    return None


@lru_cache(maxsize=None)
def _function_summary(function):
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    except (TypeError, OSError, SyntaxError):
        return set(), ()
    effects = set()
    helpers = set()
    namespace = getattr(function, "__globals__", {})
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)) and not isinstance(parents.get(node), ast.Compare):
            prefix = []
            for item in node.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    prefix.append(item.value)
                else:
                    # Keep leading argv tokens; later dynamic args do not change them.
                    if len(prefix) < 2:
                        break
            effects.update(_argv_effects(prefix))
        if isinstance(node, ast.Call):
            dry_run = any(k.arg == "dry_run" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords)
            for reference in [node.func, *node.args, *(k.value for k in node.keywords)]:
                value = _resolve(reference, namespace)
                if inspect.isfunction(value) and value.__module__.startswith("agentic_project_kit"):
                    helpers.add((inspect.unwrap(value), dry_run))
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            if name in {"create_release", "publish_release", "publish_deposition"}:
                effects.add("release_publish")
    return effects, tuple(helpers)


def scan_command_effects(app):
    observed = {}

    def scan(function, seen, dry_run=False):
        function = inspect.unwrap(function)
        key = (function, dry_run)
        if key in seen:
            return set()
        seen.add(key)
        effects, helpers = _function_summary(function)
        result = set(effects)
        for helper, helper_dry_run in helpers:
            result.update(scan(helper, seen, dry_run or helper_dry_run))
        if dry_run:
            result -= {"push", "merge", "pull_request", "delete_remote", "release_publish"}
        return result

    def walk(command, path):
        if hasattr(command, "commands"):
            for name, child in command.commands.items():
                walk(child, [*path, name])
        elif command.callback:
            observed["agentic-kit " + " ".join(path)] = scan(command.callback, set())

    root = get_command(app)
    walk(root, [] if hasattr(root, "commands") else [root.name])
    return observed
