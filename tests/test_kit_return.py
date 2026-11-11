"""Bounded return from a v2 adoption, with real local Git history."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess

import pytest


def _git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _fixture(root, *, crlf=False, bind_adoption=True, previous="1.1.10", adopted="1.1.11", previous_sha=""):
    from agentic_project_kit.kit_return import record_adoption, bind_adoption_pr
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.workspace_init import CI_TEMPLATE_PATH, CI_INJECTION_TARGET, MANAGED_CI_HEADER

    seed = runpy.run_path(str(Path(__file__).with_name("test_external_handoff_projection.py")))["_external_workspace"]
    ws = seed(root)
    (root / ".gitignore").write_text("/.agentic/tmp/\n/.agentic/rule_ack/\n")
    pin = b'jobs:\n  gate:\n    steps:\n      - run: python -m pip install "agentic-project-kit==1.1.10"\n'
    pin = pin.replace(b"==1.1.10", f"=={previous}".encode())
    if crlf:
        pin = pin.replace(b"\n", b"\r\n")
    for name, content in {CI_TEMPLATE_PATH: pin, CI_INJECTION_TARGET: MANAGED_CI_HEADER.encode() + b"\n" + pin}.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    ws.package_file("validation_report.json").parent.mkdir(parents=True, exist_ok=True)
    ws.package_file("validation_report.json").write_text(json.dumps({"status": "PASS", "generated_head": _git(root, "rev-parse", "HEAD")}))
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Original pinned v1 state")
    baseline = {name: (root / name).read_bytes() for name in _git(root, "ls-files").splitlines()}
    base_head = _git(root, "rev-parse", "HEAD")
    _git(root, "switch", "-c", "adoption")
    write_successor_handoff_package(root)
    for name in (CI_TEMPLATE_PATH, CI_INJECTION_TARGET):
        path = root / name
        path.write_bytes(path.read_bytes().replace(f"=={previous}".encode(), f"=={adopted}".encode()))
    paths = sorted(set(_git(root, "ls-files").splitlines()) | {
        path.relative_to(root).as_posix() for path in ws.handoff_dir().rglob("*") if path.is_file()
    })
    before = {name: hashlib.sha256(baseline[name]).hexdigest() if name in baseline else None for name in paths}
    receipt = record_adoption(root, adoption_id="a" * 32, plan={
        "installation": {"version": previous, "wheel_sha256": previous_sha}, "version": adopted, "branch": "adoption",
        "head": base_head, "files_before": before, "changed_paths": paths, "artifacts": [],
    }, approval_signature="approved-fixture")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Adopt candidate Kit")
    if bind_adoption:
        bind_adoption_pr(root, branch="adoption", number=101, head=_git(root, "rev-parse", "HEAD"))
    _git(root, "switch", "main")
    _git(root, "merge", "--squash", "adoption")
    _git(root, "commit", "-m", "Squash adoption")
    merge = _git(root, "rev-parse", "HEAD")
    (root / "product.txt").write_text("Later product work\n")
    _git(root, "add", "product.txt")
    _git(root, "commit", "-m", "Later product work")
    _git(root, "switch", "-c", "return")

    def observe(number):
        assert number == 101
        return {"number": number, "state": "MERGED", "baseRefName": "main", "mergeCommit": {"oid": merge}}

    def run(argv, **kwargs):
        return subprocess.run(argv, cwd=root, capture_output=True, text=not kwargs.get("binary", False), check=False)

    return receipt, baseline, observe, run, merge


def test_revert_plan_is_read_only_and_restores_exact_adoption_bytes(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert, execute_return_revert
    from agentic_project_kit.external_handoff_projection import check_projection

    receipt, baseline, observe, run, merge = _fixture(tmp_path)
    before = _git(tmp_path, "status", "--porcelain")
    plan = plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe)
    assert _git(tmp_path, "status", "--porcelain") == before == ""
    assert plan["merge_commit"] == merge
    result = execute_return_revert(tmp_path, receipt["adoption_id"], expected_signature=plan["approval_signature"], run=run, observe_pr=observe)
    assert result["result_status"] == "PASS", result
    for name, content in baseline.items():
        assert (tmp_path / name).read_bytes() == content, name
    assert (tmp_path / "product.txt").read_text() == "Later product work\n"
    assert check_projection(tmp_path)["code"] == "NEEDS_PROJECTION_MIGRATION"


def test_return_target_is_the_receipted_previous_pin_not_a_fixed_release(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert, execute_return_revert, return_closeout_context

    receipt, baseline, observe, run, _ = _fixture(tmp_path, previous="1.1.11", adopted="1.1.12")
    plan = plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe)
    execute_return_revert(tmp_path, receipt["adoption_id"], expected_signature=plan["approval_signature"], run=run, observe_pr=observe)
    context = return_closeout_context(tmp_path, run=run)
    assert context["target_version"] == "1.1.11"
    for name, content in baseline.items():
        assert (tmp_path / name).read_bytes() == content


def test_later_change_to_adoption_path_blocks_without_mutation(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert
    from agentic_project_kit.kit_update_runtime import UpdateBlocked

    receipt, _, observe, run, _ = _fixture(tmp_path)
    path = tmp_path / ".agentic/config.yaml"
    path.write_bytes(path.read_bytes() + b"# Later configuration change\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Later authority change")
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(UpdateBlocked, match="adoption_paths_changed") as error:
        plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe)
    assert ".agentic/config.yaml" in str(error.value)
    assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_revert_preserves_crlf_blob_identity(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert

    receipt, _, observe, run, _ = _fixture(tmp_path, crlf=True)
    assert plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe)["result_status"] == "AWAITING_APPROVAL"


def test_return_closeout_is_bound_to_prepared_revert_and_rejects_tampering(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert, execute_return_revert, return_closeout_context
    from agentic_project_kit.kit_update_runtime import UpdateBlocked

    receipt, _, observe, run, _ = _fixture(tmp_path)
    assert return_closeout_context(tmp_path, run=run) is None
    plan = plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe)
    execute_return_revert(tmp_path, receipt["adoption_id"], expected_signature=plan["approval_signature"], run=run, observe_pr=observe)
    context = return_closeout_context(tmp_path, run=run)
    assert context["adoption_id"] == receipt["adoption_id"]
    assert context["target_version"] == "1.1.10"
    _git(tmp_path, "commit", "-m", "Prepared Kit return")
    assert return_closeout_context(tmp_path, run=run)["adoption_id"] == receipt["adoption_id"]
    path = tmp_path / ".agentic/config.yaml"
    path.write_bytes(path.read_bytes() + b"# Unapproved extra change\n")
    with pytest.raises(UpdateBlocked, match="return_workspace_bytes_mismatch"):
        return_closeout_context(tmp_path, run=run)


def test_installation_return_requires_merged_revert_and_exact_previous_pin(tmp_path):
    from agentic_project_kit.kit_return import (
        plan_return_revert, execute_return_revert, bind_return_pr, verify_install_return,
    )
    from agentic_project_kit.kit_update_runtime import UpdateBlocked

    receipt, _, observe, run, _ = _fixture(tmp_path)
    adoption_id = receipt["adoption_id"]
    with pytest.raises(UpdateBlocked):
        verify_install_return(tmp_path, adoption_id, "1.1.10", run=run, observe_pr=observe)
    plan = plan_return_revert(tmp_path, adoption_id, run=run, observe_pr=observe)
    execute_return_revert(tmp_path, adoption_id, expected_signature=plan["approval_signature"], run=run, observe_pr=observe)
    _git(tmp_path, "commit", "-m", "Prepared Kit return")
    head = _git(tmp_path, "rev-parse", "HEAD")
    bind_return_pr(tmp_path, branch="return", number=102, head=head, run=run)
    _git(tmp_path, "switch", "main")
    _git(tmp_path, "merge", "--squash", "return")
    _git(tmp_path, "commit", "-m", "Squash Kit return")
    merge = _git(tmp_path, "rev-parse", "HEAD")

    def observe_return(number):
        assert number == 102
        return {"number": number, "state": "MERGED", "baseRefName": "main", "headRefOid": head, "mergeCommit": {"oid": merge}}

    proof = verify_install_return(tmp_path, adoption_id, "1.1.10", run=run, observe_pr=observe_return)
    assert proof["return_merge"] == merge
    with pytest.raises(UpdateBlocked, match="return_target_version_mismatch"):
        verify_install_return(tmp_path, adoption_id, "1.1.9", run=run, observe_pr=observe_return)


def test_return_revert_signature_binds_staged_wheel_hash(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert, execute_return_revert
    from agentic_project_kit.kit_update_artifacts import PreparedTarget
    from agentic_project_kit.kit_update_runtime import UpdateBlocked

    receipt, _, observe, run, _ = _fixture(tmp_path)
    wheel = tmp_path / ".agentic/tmp/old.whl"
    wheel.parent.mkdir(parents=True, exist_ok=True)
    wheel.write_bytes(b"approved old wheel fixture")
    artifact = {"name": "agentic-project-kit", "version": "1.1.10", "filename": wheel.name,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}
    target = PreparedTarget(tmp_path / ".agentic/tmp/old/bin/python", (wheel,), (artifact,))
    plan = plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe, target=target)
    assert plan["target_artifacts"][0]["sha256"] == artifact["sha256"]
    wheel.write_bytes(b"tampered wheel")
    before = _git(tmp_path, "rev-parse", "HEAD")
    with pytest.raises(UpdateBlocked, match="return_target_artifact_hash_mismatch"):
        execute_return_revert(tmp_path, receipt["adoption_id"], expected_signature=plan["approval_signature"], run=run, observe_pr=observe, target=target)
    assert _git(tmp_path, "rev-parse", "HEAD") == before


def test_return_rejects_replaced_original_package_artifact(tmp_path):
    from agentic_project_kit.kit_return import plan_return_revert
    from agentic_project_kit.kit_update_artifacts import PreparedTarget
    from agentic_project_kit.kit_update_runtime import UpdateBlocked

    receipt, _, observe, run, _ = _fixture(tmp_path, previous_sha="1" * 64)
    wheel = tmp_path / ".agentic/tmp/replaced.whl"
    wheel.write_bytes(b"different artifact with the same version")
    artifact = {"name": "agentic-project-kit", "version": "1.1.10", "filename": wheel.name,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}
    target = PreparedTarget(tmp_path / ".agentic/tmp/preview/bin/python", (wheel,), (artifact,))
    with pytest.raises(UpdateBlocked, match="return_previous_artifact_identity_mismatch"):
        plan_return_revert(tmp_path, receipt["adoption_id"], run=run, observe_pr=observe, target=target)


def test_existing_pr_creation_records_adoption_number_without_extra_commit(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from agentic_project_kit import transfer_repo_actions as actions
    from agentic_project_kit.kit_return import plan_return_revert

    receipt, _, observe, _, _ = _fixture(tmp_path, bind_adoption=False)
    _git(tmp_path, "switch", "adoption")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(actions, "guard_pr_create", lambda **kwargs: SimpleNamespace(decision=actions.MonitorDecision.CONTINUE))
    monkeypatch.setattr(actions, "_remote_mutation_preflight", lambda **kwargs: None)
    monkeypatch.setattr(actions, "ensure_remote_head", lambda *args, **kwargs: actions.RepoActionResult("remote", "PASS", 0, [], "", "", ""))

    def run(argv, **kwargs):
        if argv[:3] == ["gh", "pr", "create"]:
            return subprocess.CompletedProcess(argv, 0, "https://github.com/example/project/pull/101\n", "")
        return subprocess.run(argv, cwd=tmp_path, text=True, capture_output=True)

    monkeypatch.setattr(actions, "_run", run)
    before = _git(tmp_path, "rev-parse", "HEAD")
    result = actions._pr_create_unlocked(base="main", head="adoption", title="Adopt candidate", body="Fixture")
    assert result.result_status == "PASS", result
    assert _git(tmp_path, "rev-parse", "HEAD") == before
    _git(tmp_path, "switch", "return")

    def git_run(argv, **kwargs):
        return subprocess.run(argv, cwd=tmp_path, text=not kwargs.get("binary", False), capture_output=True)

    assert plan_return_revert(tmp_path, receipt["adoption_id"], run=git_run, observe_pr=observe)["pr_number"] == 101


@pytest.mark.parametrize("active", [False, True])
def test_pending_installation_return_is_read_only_and_never_plans_migration(tmp_path, monkeypatch, active):
    from agentic_project_kit.kit_return import (
        plan_return_revert, execute_return_revert, bind_return_pr, record_merged_return,
    )
    from agentic_project_kit.transfer_repo_actions import post_merge_check
    from agentic_project_kit import transfer_post_merge_lifecycle as lifecycle

    receipt, _, observe, run, _ = _fixture(tmp_path)
    adoption_id = receipt["adoption_id"]
    plan = plan_return_revert(tmp_path, adoption_id, run=run, observe_pr=observe)
    execute_return_revert(tmp_path, adoption_id, expected_signature=plan["approval_signature"], run=run, observe_pr=observe)
    _git(tmp_path, "commit", "-m", "Verified return")
    head = _git(tmp_path, "rev-parse", "HEAD")
    bind_return_pr(tmp_path, branch="return", number=102, head=head, run=run)
    _git(tmp_path, "switch", "main")
    _git(tmp_path, "merge", "--squash", "return")
    _git(tmp_path, "commit", "-m", "Squash verified return")
    merge = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    def observed(number):
        return {"number": number, "state": "MERGED", "baseRefName": "main", "headRefOid": head, "mergeCommit": {"oid": merge}}
    record_merged_return(tmp_path, 102, run=run, observe_pr=observed)
    if not active:
        monkeypatch.setattr("agentic_project_kit.transfer_repo_actions.uses_external_projection_v2", lambda _root: False)
        monkeypatch.setattr("agentic_project_kit.external_projection_policy.external_projection_contract_version", lambda: 1)
    monkeypatch.chdir(tmp_path)
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = post_merge_check()
    assert result.result_status == "PENDING", result
    assert "RETURN_INSTALLATION_APPROVAL_REQUIRED" in result.stdout
    assert "return-install" in result.next_action
    if not active:
        assert "NEEDS_PROJECTION_MIGRATION" not in result.stdout
    assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("a verified return must never auto-migrate")

    monkeypatch.setattr(lifecycle, "successor_package_refresh_pr", forbidden)
    assert lifecycle.post_merge_complete(102).result_status == "PENDING"
    _git(tmp_path, "switch", "-c", "unexpected-post-merge-branch")
    assert post_merge_check().result_status != "PENDING"
