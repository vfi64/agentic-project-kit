"""KIT-GF-074 and KIT-GF-075: command orders from order-create; remote-next publishes order results.

Live 2026-10-19 with Kit 1.1.1 in a consumer workspace: `transfer order-create` could only write
file actions, and after a PASS `transfer remote-next` left the written file, the order's
command-run report and LATEST_COMMAND_RUN.txt untracked on the transfer branch, so the transferred
file never reached the branch and the next Kit route met a dirty checkout. The fixtures run the
installed wheel in an external workspace with a bare origin.
"""
import json
import os
import subprocess
import sys

import pytest
from test_external_rule_registry import installed_kit as installed_kit, external as external

BRANCH = "transfer/probe-20261019"
PAYLOAD = "docs/probe.payload.txt"
TARGET = "docs/probe.txt"


def _git(root, *args, ok=True):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if ok:
        assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _cli(root, installed_kit, *args):
    env = {**os.environ, "PYTHONPATH": str(installed_kit)}
    result = subprocess.run([sys.executable, "-m", "agentic_project_kit.cli", *args], cwd=root, env=env,
                            capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout)


def _repository(root, tmp_path):
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "baseline")
    remote = tmp_path / "origin.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(remote))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-u", "origin", "main")
    return remote


def _publish_order(root, installed_kit, *args):
    _git(root, "switch", "-c", BRANCH)
    (root / PAYLOAD).write_text("transferred content\n")
    _git(root, "add", PAYLOAD)
    _git(root, "commit", "-m", "payload")
    rc, created = _cli(root, installed_kit, "transfer", "order-create", "--branch", BRANCH, *args, "--execute", "--json")
    assert rc == 0, created
    _git(root, "add", ".agentic/transfer/inbox/current.yaml")
    _git(root, "commit", "-m", "order")
    _git(root, "push", "-u", "origin", BRANCH)
    _git(root, "switch", "main")
    return created


def test_remote_next_publishes_the_written_file_and_ends_clean(external, installed_kit, tmp_path):
    root, _ = external
    remote = _repository(root, tmp_path)
    _publish_order(root, installed_kit, "--write-action", f"{TARGET}={PAYLOAD}")

    rc, report = _cli(root, installed_kit, "transfer", "remote-next", BRANCH, "--json")

    assert rc == 0 and report["result_status"] == "PASS", report.get("reasons")
    assert _git(root, "status", "--porcelain=v1", "-uall") == ""
    assert _git(root, "branch", "--show-current") == BRANCH
    published = _git(remote, "ls-tree", "-r", "--name-only", BRANCH).splitlines()
    products = report["post_report_actions"]["order_products"]
    assert products["targets"] == [TARGET]
    assert TARGET in published
    assert all(path in published for path in products["owned"]) and len(products["owned"]) == 2
    assert _git(remote, "show", f"{BRANCH}:{TARGET}") == "transferred content"
    assert "and order results" in _git(remote, "log", "--format=%s", BRANCH)


def test_order_create_writes_command_orders_and_flags_the_needed_authority(external, installed_kit, tmp_path):
    root, _ = external
    _repository(root, tmp_path)
    _git(root, "switch", "-c", BRANCH)
    rc, created = _cli(root, installed_kit, "transfer", "order-create", "--branch", BRANCH,
                       "--run-command", "agentic-kit check --json",
                       "--run-command", "agentic-kit transfer repo-status", "--json")

    assert rc == 0, created
    actions = created["order"]["actions"]
    assert [a["command"] for a in actions] == [["agentic-kit", "check", "--json"], ["agentic-kit", "transfer", "repo-status"]]
    assert [a["requires_allow_unlisted"] for a in created["command_authority"]] == [False, True]
    assert created["warnings"] == ["requires_allow_unlisted:agentic-kit transfer repo-status"]


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "python -c 'print(1)'",
        "env git push",
        "agentic-kit transfer branch-delete --branch x",
        "agentic-kit no-such-command",
        "bash -c 'agentic-kit check'",
    ],
)
def test_order_create_refuses_commands_no_local_flag_could_allow(external, installed_kit, tmp_path, command):
    root, _ = external
    _repository(root, tmp_path)
    _git(root, "switch", "-c", BRANCH)
    rc, created = _cli(root, installed_kit, "transfer", "order-create", "--branch", BRANCH,
                       "--run-command", command, "--execute", "--json")
    assert rc != 0 and created["result_status"] == "BLOCKED"
    assert not (root / ".agentic/transfer/inbox/current.yaml").exists()


def test_a_read_only_command_order_runs_and_ends_clean(external, installed_kit, tmp_path):
    root, _ = external
    _repository(root, tmp_path)
    _publish_order(root, installed_kit, "--run-command", "agentic-kit check --json")

    rc, report = _cli(root, installed_kit, "transfer", "remote-next", BRANCH, "--json")

    assert rc == 0 and report["result_status"] == "PASS", report.get("reasons")
    assert _git(root, "status", "--porcelain=v1", "-uall") == ""


def test_undeclared_changes_block_and_are_never_published(external, installed_kit, tmp_path, monkeypatch):
    root, _ = external
    remote = _repository(root, tmp_path)
    _publish_order(root, installed_kit, "--write-action", f"{TARGET}={PAYLOAD}")
    from agentic_project_kit import transfer_remote_next

    original = transfer_remote_next.run_local_transfer

    def run_and_leave_a_stray_file(*args, **kwargs):
        result = original(*args, **kwargs)
        (root / "stray.txt").write_text("not declared by the order\n")
        return result

    monkeypatch.setattr(transfer_remote_next, "run_local_transfer", run_and_leave_a_stray_file)
    monkeypatch.chdir(root)

    result = transfer_remote_next.run_remote_next_transfer(root, BRANCH)

    assert result.result_status == "BLOCKED"
    assert result.reasons == ("unexpected_worktree_changes_after_transfer",)
    assert result.preflight["unexpected_worktree_changes"] == ["stray.txt"]
    published = _git(remote, "ls-tree", "-r", "--name-only", BRANCH).splitlines()
    assert "stray.txt" not in published and TARGET in published
    assert _git(root, "status", "--porcelain=v1", "-uall") == "?? stray.txt"


def test_inbox_and_outbox_gitkeep_carriers_are_not_obsolete_transfer_files(external, installed_kit):
    """KIT-GF-076: `workspace init` writes .agentic/transfer/inbox/.gitkeep, which blocked every
    remote-next of a fresh workspace as duplicate_or_obsolete_active_transfer_files."""
    root, _ = external
    assert (root / ".agentic/transfer/inbox/.gitkeep").is_file()
    (root / ".agentic/transfer/outbox").mkdir(parents=True, exist_ok=True)
    (root / ".agentic/transfer/outbox/.gitkeep").write_text("")
    from agentic_project_kit.transfer_state import _build_transfer_file_state

    state = _build_transfer_file_state(root, branch="main", head="0" * 7, origin_main="")
    assert "duplicate_or_obsolete_active_transfer_files" not in state.get("reasons", [])
    (root / ".agentic/transfer/inbox/obsolete.yaml").write_text("old")
    state = _build_transfer_file_state(root, branch="main", head="0" * 7, origin_main="")
    assert state["state"] == "CONFLICT"


def test_an_unstartable_order_command_reports_127_instead_of_a_missing_order(tmp_path):
    from agentic_project_kit.transfer_runner import TransferAction, _run_command_action

    result = _run_command_action(tmp_path, TransferAction("run_command", command=("no-such-program-gf074",)))
    assert result["returncode"] == 127 and "could not be started" in result["stderr"]
