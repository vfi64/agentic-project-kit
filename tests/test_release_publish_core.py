from __future__ import annotations

import ast
import inspect
from pathlib import Path

import agentic_project_kit.release_publish_core as release_publish_core
from agentic_project_kit.release_publish_core import expected_confirmation, publish_release


def test_expected_confirmation_uses_release_tag() -> None:
    assert expected_confirmation("v0.4.9") == "publish-v0.4.9"


def test_publish_release_fails_closed_before_any_command(tmp_path: Path, capsys) -> None:
    assert publish_release("0.4.9", "publish-v0.4.9", tmp_path, sleep_seconds=0) == 2

    out = capsys.readouterr().out
    assert "direct release publish core is disabled after legacy ns removal" in out
    assert "No branch, tag, push, GitHub release, or DOI side effect was attempted." in out
    assert "agentic-kit release ready" in out
    assert "agentic-kit release prepare" in out
    assert "### RESULT: FAIL ###" in out


def test_publish_release_invalid_confirmation_fails_without_command(tmp_path: Path, capsys) -> None:
    assert publish_release("0.4.9", "wrong-token", tmp_path, sleep_seconds=0) == 2

    out = capsys.readouterr().out
    assert "refusing release publish without exact confirmation token" in out
    assert "agentic-kit release ready" in out
    assert "agentic-kit release prepare" in out


def test_publish_release_invalid_version_fails_without_command(tmp_path: Path, capsys) -> None:
    assert publish_release("not-a-version", "publish-vnot-a-version", tmp_path, sleep_seconds=0) == 2

    out = capsys.readouterr().out
    assert "release publish core is disabled after legacy ns removal" in out or "invalid semantic version" in out


def test_release_publish_module_has_no_unreachable_body() -> None:
    source = inspect.getsource(release_publish_core)
    tree = ast.parse(source)

    assert "subprocess" not in source
    assert "time.sleep" not in source
    assert "def run_command" not in source
    assert "def section" not in source
    assert "append_command" not in source

    publish = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "publish_release")
    assert len(publish.body) < 30
