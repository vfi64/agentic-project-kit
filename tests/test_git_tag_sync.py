"""KIT-GF-090: real local origins; no network or maintainer checkout."""
import subprocess
from types import SimpleNamespace

import pytest

from agentic_project_kit import transfer_repo_actions as actions
from agentic_project_kit import pr_closeout_complete as closeout
from agentic_project_kit.release_state import build_release_lifecycle_status


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, text=True, capture_output=True).stdout.strip()


def repositories(tmp_path):
    origin, seed, clone = (tmp_path / name for name in ("origin.git", "seed", "clone"))
    git(tmp_path, "init", "--bare", str(origin))
    git(tmp_path, "init", "-b", "main", str(seed))
    git(seed, "config", "user.email", "fixture@example.invalid")
    git(seed, "config", "user.name", "Fixture")
    (seed / "file.txt").write_text("base")
    git(seed, "add", "file.txt")
    git(seed, "commit", "-m", "base")
    git(seed, "remote", "add", "origin", str(origin))
    git(seed, "push", "-u", "origin", "main")
    git(origin, "symbolic-ref", "HEAD", "refs/heads/main")
    git(tmp_path, "clone", str(origin), str(clone))
    git(clone, "config", "user.email", "fixture@example.invalid")
    git(clone, "config", "user.name", "Fixture")
    return seed, clone


@pytest.mark.parametrize("route", ["fetch", "branch_pull", "closeout_pull", "observed", "remote_next", "transfer_next", "release_prep"])
@pytest.mark.parametrize("new_commit", [False, True])
def test_sync_routes_fetch_new_annotated_tags(tmp_path, monkeypatch, route, new_commit):
    seed, clone = repositories(tmp_path)
    if new_commit:
        (seed / "file.txt").write_text("release")
        git(seed, "commit", "-am", "release")
        git(seed, "push", "origin", "main")
    git(seed, "tag", "-a", "v9.9.9", "-m", "release")
    git(seed, "push", "origin", "refs/tags/v9.9.9")
    monkeypatch.chdir(clone)
    monkeypatch.setattr(actions, "guard_branch", lambda **kwargs: SimpleNamespace(decision="ALLOW"))
    if route == "fetch":
        result = actions.fetch_origin("main")
    elif route == "branch_pull":
        result = actions.branch_switch("main", pull=True)
    elif route == "closeout_pull":
        result = closeout._run_command(["git", "pull", "--ff-only", "origin", "main"], cwd=clone)
    elif route == "observed":
        from agentic_project_kit.transfer_observed_subprocess import run_observed_subprocess
        result = SimpleNamespace(**run_observed_subprocess("main-pull", ["git", "pull", "--ff-only", "origin", "main"], timeout_seconds=30))
    elif route == "remote_next":
        from agentic_project_kit.remote_next import _run_git
        result = _run_git(clone, ["git", "pull", "--ff-only", "origin", "main"])
    elif route == "transfer_next":
        from agentic_project_kit.transfer_remote_next import _command
        result = _command(["git", "pull", "--ff-only", "origin", "main"], clone)
    else:
        from agentic_project_kit.release_prep_core import run_command
        result = run_command(clone, ["git", "pull", "--ff-only", "origin", "main"])
    assert result.returncode == 0, result
    assert git(clone, "rev-parse", "v9.9.9^{commit}") == git(seed, "rev-parse", "HEAD")
    assert git(clone, "cat-file", "-t", "v9.9.9") == "tag"


def test_tag_conflict_blocks_without_overwriting_or_partial_tag_updates(tmp_path, monkeypatch):
    seed, clone = repositories(tmp_path)
    git(clone, "tag", "-a", "v9.9.9", "-m", "local tag")
    local = git(clone, "rev-parse", "v9.9.9")
    local_commit = git(clone, "rev-parse", "HEAD")
    (seed / "file.txt").write_text("different")
    git(seed, "commit", "-am", "different")
    remote_commit = git(seed, "rev-parse", "HEAD")
    for tag in ("v9.9.9", "v9.9.10"):
        git(seed, "tag", "-a", tag, "-m", "remote tag")
        git(seed, "push", "origin", "refs/tags/" + tag)
    monkeypatch.chdir(clone)
    result = actions.fetch_origin("main")
    assert result.result_status == "BLOCKED", result
    assert result.returncode != 0
    assert "v9.9.9" in result.stderr and local_commit in result.stderr and remote_commit in result.stderr
    assert git(clone, "rev-parse", "v9.9.9") == local
    assert git(clone, "tag", "-l", "v9.9.10") == ""


def test_common_primitive_is_idempotent_and_does_not_force(tmp_path):
    from agentic_project_kit.git_tag_sync import sync_remote_tags

    seed, clone = repositories(tmp_path)
    git(seed, "tag", "-a", "v9.9.9", "-m", "release")
    git(seed, "push", "origin", "refs/tags/v9.9.9")
    assert sync_remote_tags(clone).returncode == 0
    before = git(clone, "show-ref", "--tags")
    assert sync_remote_tags(clone).returncode == 0
    assert git(clone, "show-ref", "--tags") == before


@pytest.mark.parametrize("version", ["1.1.7", "9.9.9"])
def test_missing_closeout_tag_reports_blocker_then_sync_restores_verified(tmp_path, monkeypatch, version):
    seed, clone = repositories(tmp_path)
    doi = "10.5281/zenodo.22222222"
    concept = "10.5281/zenodo.11111111"
    status = (f"Current version: {version}\nCurrent verified release: {version}.\n"
              f"Current release tag: v{version}.\nVerified Zenodo version DOI: `{doi}`.\n")
    # The fixture owns all metadata: live checkout files may already prepare the next release.
    files = {
        "pyproject.toml": f'[project]\nname = "agentic-project-kit"\nversion = "{version}"\n',
        "src/agentic_project_kit/__init__.py": f'__version__ = "{version}"\n',
        "README.md": (f"Version `{version}` is the current release line.\n"
                      f"Current verified release: `v{version}` with Zenodo version DOI `{doi}`.\n"),
        "CHANGELOG.md": f"## v{version} - 2026-10-29\n\nDOI {doi}\n",
        "CITATION.cff": f"version: {version}\ndoi: {concept}\n# Verified v{version} version DOI: {doi}\n",
        "docs/STATUS.md": status,
        "docs/handoff/CURRENT_HANDOFF.md": status,
        "docs/releases/VERIFIED_RELEASES.md": f"# Verified releases\n\n## v{version}\n\nVersion DOI: {doi}\nConcept DOI: {concept}\n",
        f"docs/reports/release/post-release-doi-closeout-{version}.json": "{}\n",
    }
    for relative, content in files.items():
        target = seed / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    git(seed, "add", ".")
    git(seed, "commit", "-m", "verified release files")
    git(seed, "push", "origin", "main")
    git(clone, "pull", "--ff-only", "origin", "main")
    git(seed, "tag", "-a", f"v{version}", "-m", "release")
    git(seed, "push", "origin", f"refs/tags/v{version}")
    before = build_release_lifecycle_status(clone, version=version)
    assert "local_release_tag_missing" in before.blockers
    assert before.next_action == "agentic-kit transfer sync-main"
    monkeypatch.chdir(clone)
    assert actions.fetch_origin("main").returncode == 0
    after = build_release_lifecycle_status(clone, version=version)
    assert after.current_state == "current_verified" and not after.blockers


def test_rebase_does_not_fallback_or_rebase_after_tag_conflict(tmp_path, monkeypatch):
    from agentic_project_kit.transfer_rebase import rebase_on_upstream

    seed, clone = repositories(tmp_path)
    git(seed, "push", "origin", "HEAD:refs/heads/work")
    git(clone, "switch", "-c", "work")
    git(clone, "tag", "-a", "v9.9.9", "-m", "local")
    git(seed, "tag", "-a", "v9.9.9", "-m", "different annotation")
    git(seed, "push", "origin", "refs/tags/v9.9.9")
    monkeypatch.chdir(clone)
    original = subprocess.run
    calls = []

    def run(argv, *args, **kwargs):
        calls.append(list(argv))
        if list(argv)[-3:] == ["transfer", "conflict-status", "--json"]:
            return subprocess.CompletedProcess(argv, 0, '{"conflict_present":false}', "")
        return original(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    result = rebase_on_upstream()
    assert result["result_status"] == "BLOCKED"
    assert not any(argv[:2] == ["git", "rebase"] for argv in calls)
    assert ["git", "fetch", "origin", "main"] not in calls
    assert any("TAG_SYNC_BLOCKED" in step["stderr"] for step in result["steps"])


def test_failed_branch_fetch_is_not_promoted_to_tag_success(monkeypatch):
    from agentic_project_kit.git_tag_sync import run_with_tag_sync

    calls = []

    def run(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 1, "", "branch fetch failed")

    monkeypatch.setattr(subprocess, "run", run)
    result = run_with_tag_sync(["git", "fetch", "origin", "main"])
    assert result.returncode == 1 and len(calls) == 1
