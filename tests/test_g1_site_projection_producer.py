"""G1 producer for KIT-CHK-SITE-PROJECTION-FRESH (lesson of PR #2774, CI test-shard 2).

work finish rebuilds the docs-pages projection after the handoff commit and commits a change
before the PR is created, so tests/test_site_fallback_staleness.py has a producer on the
standard path.
"""
from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app

HW = "agentic_project_kit.cli_commands.human_workflows.subprocess.run"
ARGS = ["work", "finish", "--branch", "fix/demo", "--title", "Demo", "--message", "Demo",
        "--path", "src/x.py", "--execute", "--json"]
BUILD = ["site/scripts/build.py", "--docs-pages-fallback", "--json"]


def _fake(calls, *, site_porcelain="", build_rc=0):
    def run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:2] == ["git", "status"]:
            out = site_porcelain if "docs/site" in command else ""
            return subprocess.CompletedProcess(command, 0, out, "")
        if command[-3:] == BUILD:
            return subprocess.CompletedProcess(command, build_rc, "{}\n", "" if build_rc == 0 else "boom\n")
        if command[1:3] == ["transfer", "pr-create-complete"]:
            out = '{"result_status":"PASS","pr_number":7,"post_merge_complete_verified_by_inner_pr_complete":true}\n'
            return subprocess.CompletedProcess(command, 0, out, "")
        return subprocess.CompletedProcess(command, 0, '{"result_status": "PASS"}\n', "")
    return run


def _names(payload):
    return [step["name"] for step in payload["steps"]]


def _index(calls, predicate):
    return next(i for i, call in enumerate(calls) if predicate(call))


def test_changed_projection_is_committed_after_the_handoff_and_before_the_pr(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls, site_porcelain=" M docs/site/site.json\n"))
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    names = _names(payload)
    assert names.index("handoff-commit") < names.index("docs-pages-fallback-refresh") \
        < names.index("docs-pages-projection-commit")
    commit = next(step for step in payload["steps"] if step["name"] == "docs-pages-projection-commit")
    argv = commit["argv"]
    assert argv[1:3] == ["transfer", "commit"]
    assert argv[argv.index("--branch") + 1] == "fix/demo"
    paths = [argv[i + 1] for i, word in enumerate(argv) if word == "--path"]
    assert paths == ["docs/.nojekyll", "docs/index.html", "docs/site"]
    site_commit = _index(calls, lambda c: c[1:3] == ["transfer", "commit"] and "docs/site" in c)
    assert site_commit < _index(calls, lambda c: c[1:3] == ["transfer", "pr-create-complete"])


def test_unchanged_projection_commits_nothing(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls))
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 0, result.output
    step = next(s for s in json.loads(result.stdout)["steps"] if s["name"] == "docs-pages-projection-commit")
    assert step["argv"] == [] and "No docs-pages projection changes" in step["stdout"]
    assert not any(c[1:3] == ["transfer", "commit"] and "docs/site" in c for c in calls)


def test_failed_rebuild_blocks_before_the_pr_and_names_the_check(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls, build_rc=1))
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["blockers"] == ["docs-pages-fallback-refresh"]
    assert payload["check_id"] == "KIT-CHK-SITE-PROJECTION-FRESH"
    assert payload["next_command_autonomous"] is False
    assert not any(c[1:3] == ["transfer", "pr-create-complete"] for c in calls)


def test_workspace_without_site_build_script_skips_the_projection(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls, site_porcelain=" M docs/site/site.json\n"))
    monkeypatch.setattr("agentic_project_kit.docs_pages_projection.docs_pages_projection_paths", lambda root: ())
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "docs-pages-projection" in _names(payload)
    assert "docs-pages-fallback-refresh" not in _names(payload)
    assert not any(c[-3:] == BUILD for c in calls)


def test_dry_run_does_not_rebuild_the_projection(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls))
    result = CliRunner().invoke(app, [arg for arg in ARGS if arg != "--execute"])
    assert result.exit_code == 0, result.output
    assert not any(c[-3:] == BUILD for c in calls)
