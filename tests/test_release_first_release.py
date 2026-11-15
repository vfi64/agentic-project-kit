"""KIT-GF-118: the first release of a project without a previous v* tag.

Owner decision 2026-11-15: no previous tag = first release; its notes start at the root commit, a
product commit without a PR number is listed as a direct commit instead of blocking (only in the first
release), and the B4 gate carries ``first_release``, which the approval signature binds. Before the fix
``release run`` blocked in A2 (standard-error-scan: release-from-tag) and the notes blocked every
direct commit.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_notes import build_release_notes_report, render_release_notes_markdown
from agentic_project_kit.release_range import ReleaseRange, first_release_gate, resolve


@pytest.fixture(autouse=True)
def _git_identity(tmp_path_factory, monkeypatch):
    # CI runners have no Git identity; a global identity on the developer machine must not hide that.
    config = tmp_path_factory.mktemp("gitconfig") / "gitconfig"
    config.write_text("[user]\n\tname = First Release\n\temail = first@example.invalid\n"
                      "[init]\n\tdefaultBranch = main\n[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def _git(root: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def _project(tmp_path: Path, *, origin_tags: tuple[str, ...] = ()) -> Path:
    origin = tmp_path / "origin.git"
    root = tmp_path / "project"
    root.mkdir(parents=True)
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(root, "init", "-q", "-b", "main")
    _git(root, "remote", "add", "origin", str(origin))
    (root / "README.md").write_text("demo\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-q", "-m", "Update README documentation")
    (root / "gate.txt").write_text("gate\n")
    _git(root, "add", "gate.txt")
    _git(root, "commit", "-q", "-m", "Add pytest gate")
    _git(root, "push", "-q", "origin", "main")
    for tag in origin_tags:  # a tag only the origin has (a clone that did not fetch tags)
        _git(root, "tag", tag)
        _git(root, "push", "-q", "origin", f"refs/tags/{tag}")
        _git(root, "tag", "-d", tag)
    return root


def _notes(root: Path, **kwargs):
    return build_release_notes_report(root, version="0.1.1", to_ref="HEAD",
                                      private_unclassified_fallback=False, **kwargs)


def test_first_release_notes_start_at_the_root_and_list_direct_commits_under_the_standard_policy(tmp_path):
    root = _project(tmp_path)
    report = _notes(root, from_tag="", first_release=True)
    assert report.validation.status == "PASS", report.validation.reasons
    assert [item.title for item in report.items] == ["Update README documentation", "Add pytest gate"]
    assert all(item.pr_number is None for item in report.items)
    assert all({"type": "direct_commit", "range": "root"} in item.evidence for item in report.items)
    assert not [e for e in report.missing_evidence if e.get("type") == "missing_pr_number"]
    assert report.as_dict()["first_release"] is True
    markdown = render_release_notes_markdown(report)
    assert "(direct commit, `" in markdown and "PR <missing>" not in markdown
    assert "first release, from the root commit" in markdown


def test_a_second_release_keeps_the_pr_evidence_mandatory(tmp_path):
    root = _project(tmp_path)
    _git(root, "tag", "v0.1.1", "HEAD~1")
    report = _notes(root, from_tag="v0.1.1")
    assert report.validation.status == "BLOCK"
    assert any("missing PR evidence" in reason for reason in report.validation.reasons)
    assert "first_release" not in report.as_dict()


def test_first_release_notes_refuse_an_existing_release_tag(tmp_path):
    root = _project(tmp_path)
    _git(root, "tag", "v0.1.0")
    report = _notes(root, from_tag="", first_release=True)
    assert report.validation.status == "BLOCK"
    assert [e["type"] for e in report.missing_evidence] == ["first_release_with_release_tag"]
    with pytest.raises(ValueError, match="exclude each other"):
        _notes(root, from_tag="v0.1.0", first_release=True)


def test_the_range_is_the_tag_else_the_first_release_and_never_with_unfetched_tags(tmp_path):
    root = _project(tmp_path)
    assert resolve(root) == ReleaseRange(from_tag="", first_release=True)
    assert resolve(root).notes_args() == ["--first-release"]
    assert resolve(root, "v9.9.9") == ReleaseRange(from_tag="v9.9.9", first_release=False)
    _git(root, "tag", "v0.1.0")
    assert resolve(root).notes_args() == ["--from-tag", "v0.1.0"]

    unfetched = _project(tmp_path / "second", origin_tags=("v0.1.0",))
    blocked = resolve(unfetched)
    assert blocked.first_release and blocked.blockers
    assert blocked.blockers[0].startswith("release-tags-not-fetched")

    _git(root, "tag", "-d", "v0.1.0")
    _git(root, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    assert resolve(root).blockers[0].startswith("first-release-origin-tags-unreadable")


def test_the_b4_gate_field_names_root_and_direct_commits_only_without_a_tag(tmp_path):
    root = _project(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    first = _git(root, "rev-list", "--max-parents=0", "HEAD")
    assert first_release_gate(root, head) == {
        "range": "root", "root_commit": first, "direct_commits": [first, head]}
    _git(root, "tag", "v0.1.0")
    assert first_release_gate(root, head) is None


def test_release_run_b4_gate_binds_the_first_release_field(tmp_path, monkeypatch):
    from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions, _approval_signature

    root = _project(tmp_path)
    monkeypatch.setattr("agentic_project_kit.release_run.load_workspace", lambda *a, **k: _Workspace(root))
    run = ReleaseRun(ReleaseRunOptions(root=root, version="0.1.1"))
    gate = run._gate_details("B4")
    assert gate["first_release"]["range"] == "root"
    changed = json.loads(json.dumps(gate))
    changed["first_release"]["direct_commits"] = []
    assert _approval_signature(changed) != _approval_signature(gate)


class _Workspace:
    def __init__(self, root: Path):
        self.root = root

    def tmp_file(self, name: str) -> Path:
        return self.root / ".agentic/tmp" / name

    def tmp(self) -> Path:
        return self.root / ".agentic/tmp"


@pytest.mark.parametrize("args", [[], ["--from-tag", "v0.1.0", "--first-release"]])
def test_release_notes_generate_needs_exactly_one_lower_bound(tmp_path, monkeypatch, args):
    root = _project(tmp_path)
    monkeypatch.chdir(root)
    result = CliRunner().invoke(app, ["release-notes-generate", "--version", "0.1.1", *args, "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["status"] == "BLOCK"


def test_release_notes_generate_first_release_passes(tmp_path, monkeypatch):
    root = _project(tmp_path)
    monkeypatch.chdir(root)
    result = CliRunner().invoke(app, ["release-notes-generate", "--version", "0.1.1", "--first-release",
                                      "--to-ref", "HEAD", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["first_release"] is True


def _release_ready(monkeypatch, release_range):
    from agentic_project_kit.cli_commands import human_workflows

    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(list(argv), 0, '{"result_status": "PASS"}\n', "")

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)
    monkeypatch.setattr(human_workflows, "_latest_release_tag", lambda: "")
    monkeypatch.setattr(human_workflows, "resolve_release_range", lambda root, tag: release_range)
    monkeypatch.setattr(human_workflows, "_doc_lifecycle_release_review_step", lambda version: {
        "name": "doc-lifecycle-release-review", "argv": [], "returncode": 0, "ok": True,
        "allowed_returncodes": [0], "stdout": "", "stderr": ""})
    result = CliRunner().invoke(app, ["release", "ready", "--version", "0.1.1", "--json"])
    return result, calls


def test_release_ready_passes_the_first_release_to_scan_and_notes(monkeypatch):
    result, calls = _release_ready(monkeypatch, ReleaseRange("", True))
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["first_release"] is True and payload["from_tag"] == ""
    scan = next(call for call in calls if "standard-error-scan" in call)
    notes = next(call for call in calls if "release-notes-generate" in call)
    assert "--first-release" in scan and "--from-tag" not in scan
    assert "--first-release" in notes and "--from-tag" not in notes


def test_release_ready_blocks_on_unfetched_origin_tags_before_the_scan(monkeypatch):
    blocked = ReleaseRange("", True, ("release-tags-not-fetched: origin lists v0.1.0; run git fetch --tags origin",))
    result, calls = _release_ready(monkeypatch, blocked)
    assert result.exit_code == 2
    steps = json.loads(result.stdout)["steps"]
    assert [s["name"] for s in steps if not s["ok"]] == ["release-range"]
    assert not [call for call in calls if "standard-error-scan" in call or "release-notes-generate" in call]


def test_first_release_lists_unclassified_direct_commits_under_changed_with_a_warning(tmp_path):
    """KIT-GF-119: the init and adoption commits match no heuristic and have no PR to carry a category."""
    root = _project(tmp_path)
    (root / "x.txt").write_text("x\n")
    _git(root, "add", "x.txt")
    _git(root, "commit", "-q", "-m", "Initialize agentic project")
    report = _notes(root, from_tag="", first_release=True)
    assert report.validation.status == "PASS", report.validation.reasons
    item = report.items[-1]
    assert (item.title, item.category, item.confidence) == ("Initialize agentic project", "Changed", "fallback")
    assert item.evidence[-1]["type"] == "unclassified_first_release_direct_commit"
    assert report.warnings and "first release" in report.warnings[0] and item.commit_sha[:8] in report.warnings[0]
    assert not report.unclassified_items


def test_a_second_release_still_blocks_an_unclassified_commit(tmp_path):
    root = _project(tmp_path)
    _git(root, "tag", "v0.1.0")
    (root / "x.txt").write_text("x\n")
    _git(root, "add", "x.txt")
    _git(root, "commit", "-q", "-m", "Initialize agentic project (#7)")
    report = _notes(root, from_tag="v0.1.0")
    assert report.validation.status == "BLOCK"
    assert any("Unclassified" in reason for reason in report.validation.reasons)
