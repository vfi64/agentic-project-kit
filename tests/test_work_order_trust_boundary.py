"""Negative tests for the trust boundary where LLM-written work orders reach local execution.

Review: docs/reports/WORK_ORDER_TRUST_BOUNDARY_REVIEW_20261016.md (plan step
ai-work-order-trust-boundary-review). Each strict xfail asserts the safe behaviour for one
confirmed gap (WOTB-xx). A hardening slice that closes a gap makes its test pass, and strict
xfail then fails until the marker is removed, so a gap cannot be closed silently or reopened
unnoticed. The unmarked tests pin checks that already hold.
"""

from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from agentic_project_kit import transfer_remote_next as trn
from agentic_project_kit import transfer_runner as tr
from agentic_project_kit import typed_work_order_runner as twr
from agentic_project_kit import work_orders as wo
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import command_manifest_ack_line, lint_instruction_text
from agentic_project_kit.work_order_validator import validate_work_order_text

REPO_ROOT = Path(__file__).resolve().parents[1]


def _gap(gap_id: str, summary: str):
    return pytest.mark.xfail(strict=True, reason=f"{gap_id}: {summary}")


def _git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    return path


def _transfer_order_text(order: dict[str, object]) -> str:
    return command_manifest_ack_line(load_manifest(REPO_ROOT)) + "\n" + yaml.safe_dump(order)


def _transfer_run_command_reaches_execution(argv: list[str]) -> bool:
    """True when both the parser and the instruction lint used by `transfer apply` let argv run."""
    try:
        tr._parse_command({"command": argv})
    except ValueError:
        return False
    order = {
        "id": "probe",
        "title": "probe",
        "safety": "READ_ONLY",
        "report_path": "docs/reports/command_runs/probe.md",
        "actions": [{"type": "run_command", "command": argv}],
    }
    lint = lint_instruction_text(
        _transfer_order_text(order),
        manifest=load_manifest(REPO_ROOT),
        require_ack=True,
        strict_unknown=False,
        include_structured_commands=True,
    )
    return lint.returncode != 2


# --- typed work orders (`work-order typed-next`, `typed-run`, `remote-next`) -------------------


@_gap("WOTB-01", "typed command_argv runs any argv; the declared safety is not enforced")
def test_typed_work_order_does_not_run_arbitrary_argv_under_read_only_safety(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    order = twr.parse_typed_work_order(
        {
            "id": "probe",
            "title": "probe",
            "safety": "READ_ONLY",
            "log_path": "docs/reports/terminal/probe.log",
            "block_dirty_worktree": False,
            "steps": [{"kind": "command_argv", "argv": ["touch", "EXECUTED"]}],
        }
    )

    twr.run_typed_work_order(order, root)

    assert not (root / "EXECUTED").exists()


@_gap("WOTB-02", "a typed order authorises its own BOUNDED cockpit actions with allow_bounded")
def test_typed_work_order_cannot_self_authorize_bounded_cockpit_actions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _git_repo(tmp_path / "repo")
    granted: list[bool] = []

    def fake_run_cockpit_action(action_id: str, project_root: Path, *, allow_bounded: bool = False):
        granted.append(allow_bounded)
        return SimpleNamespace(result_status="PASS", returncode=0)

    monkeypatch.setattr(twr, "run_cockpit_action", fake_run_cockpit_action)
    monkeypatch.setattr(twr, "action_result_as_json_data", lambda result: {})
    order = twr.parse_typed_work_order(
        {
            "id": "probe",
            "title": "probe",
            "safety": "READ_ONLY",
            "log_path": "docs/reports/terminal/probe.log",
            "block_dirty_worktree": False,
            # dialog.rnc commits and pushes closeout paths.
            "steps": [{"kind": "cockpit_action", "action_id": "dialog.rnc", "allow_bounded": True}],
        }
    )

    twr.run_typed_work_order(order, root)

    assert granted == [False]


@_gap("WOTB-03", "typed log_path accepts parent segments and writes outside the repository")
def test_typed_work_order_log_path_rejects_parent_segments() -> None:
    with pytest.raises(ValueError):
        twr.parse_typed_work_order(
            {
                "id": "probe",
                "title": "probe",
                "safety": "READ_ONLY",
                "log_path": "docs/reports/terminal/../../../../outside.log",
                "steps": [{"kind": "command_argv", "argv": ["true"]}],
            }
        )


# --- shell work orders (`work-order run --execute`) ---------------------------------------------


@_gap("WOTB-03", "work-order log_path accepts parent segments and writes outside the repository")
def test_work_order_log_path_rejects_parent_segments() -> None:
    with pytest.raises(ValueError):
        wo.parse_work_order(
            {
                "id": "probe",
                "title": "probe",
                "safety": "READ_ONLY",
                "expected_branch": "feature/probe",
                "command": "pytest",
                "log_path": "docs/reports/terminal/../../../../outside.log",
            }
        )


@_gap("WOTB-04", "constitutional gates are substring checks; naming them satisfies the contract")
def test_work_order_contract_requires_gates_to_run_not_only_to_be_named() -> None:
    order = wo.parse_work_order(
        {
            "id": "probe",
            "title": "probe",
            "safety": "READ_ONLY",
            "expected_branch": "feature/probe",
            "command": "echo pytest ruff check check-docs doctor; touch EXECUTED",
            "log_path": "docs/reports/terminal/probe.log",
            "expected_outputs": ["docs/reports/terminal/probe.log"],
            "postconditions": ["pytest ruff check-docs doctor log exists no false pass"],
        }
    )

    assert wo.check_work_order(order) != []


# --- transfer orders (`transfer remote-next`, `transfer apply`, `transfer run-local`) ----------


@pytest.mark.parametrize(
    "argv",
    [
        ["env", "git", "push", "--force", "origin", "main"],
        ["/usr/bin/git", "push", "origin", "main"],
        ["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:main"],
        ["git", "-C", ".", "push", "--force", "origin", "main"],
        ["env", "gh", "pr", "merge", "1"],
        ["/usr/bin/python3", "-c", "print(1)"],
        [".venv/bin/python", "-c", "print(1)"],
    ],
)
@_gap("WOTB-05", "run_command blocks git push and python only by literal argv[0]/prefix")
def test_transfer_run_command_rejects_wrapped_raw_git_and_interpreters(argv: list[str]) -> None:
    assert not _transfer_run_command_reaches_execution(argv)


def _transfer_root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    (root / "docs" / "reference").mkdir(parents=True)
    outside.mkdir()
    for name in ("agentic-kit-commands.json",):
        (root / "docs" / "reference" / name).write_text(
            (REPO_ROOT / "docs" / "reference" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    return root, outside


def _apply(root: Path, actions: list[dict[str, object]]) -> tr.TransferResult:
    order_data = {
        "id": "probe",
        "title": "probe",
        "safety": "READ_ONLY",
        "report_path": "docs/reports/command_runs/probe.md",
        "actions": actions,
    }
    order = replace(
        tr.parse_transfer_order(order_data),
        raw_text=_transfer_order_text(order_data),
        checked_path="current.yaml",
    )
    return tr.apply_transfer_order(order, root)


@_gap("WOTB-06", "write_text_file reads its payload through a symlink that leaves the repository")
def test_transfer_write_text_file_does_not_read_payload_through_symlink(tmp_path: Path) -> None:
    root, outside = _transfer_root(tmp_path)
    (outside / "secret.txt").write_text("SECRET\n", encoding="utf-8")
    (root / "payload_link").symlink_to(outside / "secret.txt")

    _apply(root, [{"type": "write_text_file", "target_path": "docs/leak.txt", "payload_path": "payload_link"}])

    assert not (root / "docs" / "leak.txt").exists()


@_gap("WOTB-06", "write_text_file writes through a symlinked directory outside the repository")
def test_transfer_write_text_file_does_not_write_through_symlinked_directory(tmp_path: Path) -> None:
    root, outside = _transfer_root(tmp_path)
    (root / "payload.txt").write_text("planted\n", encoding="utf-8")
    (root / "docs" / "escape").symlink_to(outside, target_is_directory=True)

    _apply(root, [{"type": "write_text_file", "target_path": "docs/escape/planted.txt", "payload_path": "payload.txt"}])

    assert not (outside / "planted.txt").exists()


@_gap("WOTB-07", "the freshness anchor matches any one-character prefix of HEAD")
def test_transfer_freshness_anchor_requires_a_meaningful_prefix() -> None:
    head = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"

    assert not trn._head_matches("a", short_head=head[:7], full_head=head)


@_gap("WOTB-08", "remote-next validates one order revision and executes the one present after switch/pull")
def test_transfer_remote_next_executes_the_order_it_validated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _git_repo(tmp_path / "repo")
    inbox = root / tr.DEFAULT_INBOX
    inbox.parent.mkdir(parents=True)

    def order(order_id: str, **extra: object) -> str:
        data = {
            "id": order_id,
            "status": "active",
            "kind": trn.EXECUTABLE_TRANSFER_ORDER_KIND,
            "branch": "feature/probe",
            **extra,
        }
        return yaml.safe_dump(data)

    inbox.write_text(order("validated-order", expected_current_head="a"), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=kit@example.invalid", "-c", "user.name=Kit Test", "commit", "-q", "-m", "order"],
        cwd=root,
        check=True,
    )
    executed: list[str] = []

    def fake_run(argv: list[str], cwd: Path) -> str:
        if argv[:2] == ["git", "switch"]:
            # The switched-to and pulled branch carries a different order: no anchor, new id.
            inbox.write_text(order("unvalidated-order"), encoding="utf-8")
        return "abc1234"

    def fake_run_local_transfer(project_root: Path):
        executed.append(str(yaml.safe_load(inbox.read_text(encoding="utf-8"))["id"]))
        return SimpleNamespace(result_status="PASS", returncode=0, next_action="")

    monkeypatch.setattr(trn, "_head_matches", lambda expected, *, short_head, full_head: True)
    monkeypatch.setattr(trn, "_recover_owned_report_artifacts", lambda project_root: {})
    monkeypatch.setattr(trn, "_sync_current_branch_before_order", lambda project_root: {})
    monkeypatch.setattr(trn, "_ensure_safe_publish_target", lambda project_root, *, branch: {})
    monkeypatch.setattr(trn, "_rule_ack_snapshot", lambda project_root, *, repo_head: SimpleNamespace(confirmed=True))
    monkeypatch.setattr(trn, "_run", fake_run)
    monkeypatch.setattr(trn, "run_local_transfer", fake_run_local_transfer)
    monkeypatch.setattr(trn, "_write_remote_next_report", lambda project_root, result: result)

    result = trn.run_remote_next_transfer(root)

    assert executed in ([], ["validated-order"]), f"executed {executed}, result {result.result_status}"


@_gap("WOTB-08", "with an explicit or inferred branch (transfer continue) the freshness guard is skipped")
def test_transfer_remote_next_with_branch_still_checks_order_freshness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _git_repo(tmp_path / "repo")
    inbox = root / tr.DEFAULT_INBOX
    inbox.parent.mkdir(parents=True)
    # No freshness anchor, no status, no kind: the guard would block this order without --branch.
    inbox.write_text(yaml.safe_dump({"id": "unanchored-order", "branch": "feature/probe"}), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=kit@example.invalid", "-c", "user.name=Kit Test", "commit", "-q", "-m", "order"],
        cwd=root,
        check=True,
    )
    executed: list[str] = []

    def fake_run_local_transfer(project_root: Path):
        executed.append(str(yaml.safe_load(inbox.read_text(encoding="utf-8"))["id"]))
        return SimpleNamespace(result_status="PASS", returncode=0, next_action="")

    monkeypatch.setattr(trn, "_recover_owned_report_artifacts", lambda project_root: {})
    monkeypatch.setattr(trn, "_sync_current_branch_before_order", lambda project_root: {})
    monkeypatch.setattr(trn, "_ensure_safe_publish_target", lambda project_root, *, branch: {})
    monkeypatch.setattr(trn, "_rule_ack_snapshot", lambda project_root, *, repo_head: SimpleNamespace(confirmed=True))
    monkeypatch.setattr(trn, "_run", lambda argv, cwd: "abc1234")
    monkeypatch.setattr(trn, "run_local_transfer", fake_run_local_transfer)
    monkeypatch.setattr(trn, "_write_remote_next_report", lambda project_root, result: result)

    trn.run_remote_next_transfer(root, branch="feature/probe")

    assert executed == []


# --- fixed-slot Python work orders (next-turn.py, GUI work-order run) ---------------------------


@_gap("WOTB-09", "the next-turn.py validator is a text denylist over an arbitrary Python script")
def test_next_turn_script_validator_rejects_obfuscated_git_push() -> None:
    script = "\n".join(
        [
            "# agentic-project-kit work order",
            "# ### CANONICAL SUMMARY ###",
            "# ### RESULT:",
            "# Terminal bleibt offen. Kein exit am Blockende.",
            "# agentic-kit status",
            "import subprocess",
            'subprocess.run(["git", "push", "--force", "origin", "main"])',
        ]
    )

    assert validate_work_order_text(script).ok is False


# --- checks that hold today -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["git", "push", "origin", "main"],
        ["gh", "pr", "merge", "1"],
        ["bash", "-c", "true"],
        ["python3", "-c", "print(1)"],
        ["echo", ";"],
        ["agentic-kit", "no-such-command"],
    ],
)
def test_transfer_run_command_blocks_literal_raw_git_shells_and_unknown_kit_commands(argv: list[str]) -> None:
    assert not _transfer_run_command_reaches_execution(argv)


@pytest.mark.parametrize("target", ["../outside.txt", "/tmp/outside.txt", ".git/config", ".venv/bin/python"])
def test_transfer_write_text_file_rejects_lexical_escapes(target: str) -> None:
    with pytest.raises(ValueError):
        tr.parse_transfer_order(
            {
                "id": "probe",
                "title": "probe",
                "safety": "READ_ONLY",
                "report_path": "docs/reports/command_runs/probe.md",
                "actions": [{"type": "write_text_file", "target_path": target, "payload_path": "payload.txt"}],
            }
        )


def test_transfer_apply_requires_the_current_manifest_ack(tmp_path: Path) -> None:
    root, _ = _transfer_root(tmp_path)
    order_data = {
        "id": "probe",
        "title": "probe",
        "safety": "READ_ONLY",
        "report_path": "docs/reports/command_runs/probe.md",
        "actions": [{"type": "run_command", "command": ["touch", "EXECUTED"]}],
    }
    order = replace(
        tr.parse_transfer_order(order_data),
        raw_text="COMMAND_MANIFEST_ACK 000000000000\n" + yaml.safe_dump(order_data),
        checked_path="current.yaml",
    )

    result = tr.apply_transfer_order(order, root)

    assert result.result_status == "FAIL"
    assert not (root / "EXECUTED").exists()


def test_planner_executor_runs_only_read_only_manifest_commands(tmp_path: Path) -> None:
    from agentic_project_kit.planner_executor import (
        ADAPTER_KIT_LOCAL,
        parse_planner_executor_intent,
        run_planner_executor_intent,
    )

    def intent(argv: list[str]):
        return parse_planner_executor_intent(
            {
                "schema_version": 1,
                "id": "probe",
                "title": "probe",
                "executor_adapter": ADAPTER_KIT_LOCAL,
                "block_dirty_worktree": False,
                "steps": [{"id": "step", "kind": "command", "argv": argv}],
            }
        )

    with pytest.raises(ValueError, match="must start with agentic-kit"):
        intent(["git", "push", "origin", "main"])

    root = _git_repo(tmp_path / "repo")
    ran: list[tuple[str, ...]] = []
    result = run_planner_executor_intent(
        intent(["agentic-kit", "transfer", "push-current"]),
        root,
        execute=True,
        runner=lambda argv, project_root: ran.append(argv) or subprocess.CompletedProcess(argv, 0, "", ""),
    )

    assert ran == []
    assert result.result_status != "PASS"
