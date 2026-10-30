from __future__ import annotations

import copy
import json
import subprocess

import pytest

from agentic_project_kit import closeout_receipt as receipts
from agentic_project_kit.workspace import load_workspace


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", str(origin))
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Receipt fixture")
    (root / ".gitignore").write_text("docs/\n.agentic/\n")
    (root / "content").write_text("initial\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    git(root, "remote", "add", "origin", str(origin))
    git(root, "push", "-u", "origin", "main")
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    package = ws.handoff_packages_latest()
    package.mkdir(parents=True)
    for name in (
        "validation_report.json",
        "execution_contract.json",
        "source_manifest.json",
        "successor_context.yaml",
    ):
        (package / name).write_text(json.dumps({"status": "PASS"}))
    return root, origin, package


def payload_for(root):
    receipt = receipts.make_completion_receipt(
        root, after_pr=123, main_branch="main", lifecycle_state="COMPLETE"
    )
    assert receipt is not None
    return {"result_status": "PASS", "expected_head_sha": "a" * 40, "completion_receipt": receipt}


def valid(payload, root, **kwargs):
    return receipts.valid_completion_receipt(
        payload, root, after_pr=123, main_branch="main", **kwargs
    )


def test_same_state_is_reusable_and_does_not_mutate_repository(repo):
    root, _, _ = repo
    before = git(root, "status", "--porcelain=v1")
    payload = payload_for(root)
    assert valid(payload, root, source_head="a" * 40)
    assert valid(payload, root, source_head="a" * 40)
    assert git(root, "status", "--porcelain=v1") == before == ""


@pytest.mark.parametrize(
    "mutation",
    [
        "dirty",
        "index",
        "untracked",
        "branch",
        "head",
        "upstream",
        "operation",
        "evidence",
        "missing",
        "failed_evidence",
        "config",
    ],
)
def test_changed_local_inputs_decline_reuse(repo, mutation):
    root, _, package = repo
    payload = payload_for(root)
    if mutation in {"dirty", "index", "head"}:
        (root / "content").write_text("changed\n")
        if mutation in {"index", "head"}:
            git(root, "add", "content")
        if mutation == "head":
            git(root, "commit", "-m", "changed")
    elif mutation == "untracked":
        (root / "unknown").write_text("new")
    elif mutation == "branch":
        git(root, "switch", "-c", "feature")
    elif mutation == "upstream":
        git(root, "branch", "--unset-upstream")
    elif mutation == "operation":
        (root / ".git/MERGE_HEAD").write_text(git(root, "rev-parse", "HEAD"))
    elif mutation == "evidence":
        (package / "source_manifest.json").write_text("{}")
    elif mutation == "missing":
        (package / "execution_contract.json").unlink()
    elif mutation == "failed_evidence":
        (package / "validation_report.json").write_text('{"status":"FAIL"}')
    elif mutation == "config":
        git(root, "remote", "set-url", "origin", str(root / "absent"))
    assert not valid(payload, root)


def test_changed_remote_without_fetch_declines_reuse(repo, tmp_path):
    root, origin, _ = repo
    payload = payload_for(root)
    peer = tmp_path / "peer"
    git(tmp_path, "clone", "--branch", "main", str(origin), str(peer))
    git(peer, "config", "user.email", "fixture@example.invalid")
    git(peer, "config", "user.name", "Peer")
    (peer / "content").write_text("remote advance\n")
    git(peer, "commit", "-am", "advance")
    git(peer, "push", "origin", "main")
    assert git(root, "rev-parse", "HEAD") == git(root, "rev-parse", "origin/main")
    assert not valid(payload, root)


@pytest.mark.parametrize(
    "change",
    [
        None,
        {},
        {"result_status": "PASS"},
        {"result_status": "FAIL"},
        {"completion_receipt": True},
        {"returncode": 2},
    ],
)
def test_missing_or_failed_payload_declines_reuse(repo, change):
    root, _, _ = repo
    payload = payload_for(root)
    if change is None:
        payload = None
    elif not change or change == {"result_status": "PASS"}:
        payload = change
    else:
        payload.update(change)
    assert not valid(payload, root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("after_pr", True),
        ("after_pr", 124),
        ("schema_version", True),
        ("kind", "other"),
        ("lifecycle_state", "PENDING"),
        ("lifecycle_state", []),
        ("state", {}),
    ],
)
def test_malformed_or_mismatched_receipt_declines_reuse(repo, field, value):
    root, _, _ = repo
    payload = copy.deepcopy(payload_for(root))
    payload["completion_receipt"][field] = value
    assert not valid(payload, root)


def test_wrong_feature_head_repository_or_branch_declines_reuse(repo, tmp_path):
    root, _, _ = repo
    payload = payload_for(root)
    assert not valid(payload, root, source_head="b" * 40)
    assert not valid(payload, root, source_head=True)
    assert not valid(payload, tmp_path)
    assert not receipts.valid_completion_receipt(payload, root, after_pr=123, main_branch="other")


def test_observation_failure_or_race_declines_reuse(repo, monkeypatch):
    root, _, _ = repo
    payload = payload_for(root)
    original = receipts._git

    def unavailable(root, *args):
        if args[0] == "ls-remote":
            raise subprocess.TimeoutExpired("git", 15)
        return original(root, *args)

    monkeypatch.setattr(receipts, "_git", unavailable)
    assert not valid(payload, root)

    def race(root, *args):
        value = original(root, *args)
        if args[0] == "ls-remote":
            (root / "unknown").write_text("concurrent change")
        return value

    monkeypatch.setattr(receipts, "_git", race)
    assert not valid(payload, root)


@pytest.mark.parametrize("state", ["PENDING", "BLOCKED", "REFRESH_LOOP_DETECTED", []])
def test_nonterminal_state_does_not_issue_receipt(repo, state):
    root, _, _ = repo
    assert (
        receipts.make_completion_receipt(
            root, after_pr=123, main_branch="main", lifecycle_state=state
        )
        is None
    )
