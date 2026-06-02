from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRANSFER_REMOTE_NEXT = ROOT / "src/agentic_project_kit/transfer_remote_next.py"
TRANSFER_CLI = ROOT / "src/agentic_project_kit/cli_commands/transfer.py"
TRANSFER_TESTS = ROOT / "tests/test_transfer_remote_next.py"

TRANSFER_REMOTE_NEXT.write_text(
    '''from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.transfer_local_runner import TransferLocalRun, run_local_transfer
from agentic_project_kit.transfer_runner import DEFAULT_INBOX


@dataclass(frozen=True)
class TransferRemoteNextRun:
    branch: str
    local_run: TransferLocalRun
    head: str

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "branch": self.branch,
            "head": self.head,
            "local_run": self.local_run.as_json_data(),
            "result_status": self.local_run.result_status,
            "returncode": self.local_run.returncode,
            "next_action": self.local_run.next_action,
        }


def _run(argv: list[str], cwd: Path) -> str:
    process = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(argv)}\\nstdout={process.stdout}\\nstderr={process.stderr}"
        )
    return process.stdout.strip()


def _ensure_clean(project_root: Path) -> None:
    status = _run(["git", "status", "--short"], project_root)
    if status:
        raise RuntimeError(f"worktree must be clean before transfer remote-next:\\n{status}")


def _validate_branch_name(branch: str) -> str:
    value = branch.strip()
    if not value:
        raise ValueError("branch must not be empty")
    if value.startswith("-") or ".." in value or value.endswith(".lock"):
        raise ValueError(f"unsafe branch name: {branch}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._/-")
    if any(char not in allowed for char in value):
        raise ValueError(f"unsafe branch name: {branch}")
    return value


def _read_transfer_order_data(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"transfer order not found: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"transfer order must be a mapping: {path}")
    return data


def resolve_remote_next_branch(project_root: Path, branch: str | None = None, path: Path = DEFAULT_INBOX) -> str:
    if branch is not None and branch.strip():
        return _validate_branch_name(branch)
    root = project_root.resolve()
    order_path = path if path.is_absolute() else root / path
    data = _read_transfer_order_data(order_path)
    order_branch = data.get("branch")
    if not isinstance(order_branch, str) or not order_branch.strip():
        raise ValueError(f"transfer order must define a non-empty branch: {path}")
    return _validate_branch_name(order_branch)


def run_remote_next_transfer(project_root: Path, branch: str | None = None) -> TransferRemoteNextRun:
    root = project_root.resolve()
    safe_branch = resolve_remote_next_branch(root, branch)

    _ensure_clean(root)
    _run(["git", "fetch", "origin", safe_branch], root)
    _run(["git", "switch", safe_branch], root)
    _run(["git", "pull", "--ff-only", "origin", safe_branch], root)

    local_run = run_local_transfer(root)
    head = _run(["git", "rev-parse", "--short", "HEAD"], root)
    return TransferRemoteNextRun(branch=safe_branch, local_run=local_run, head=head)
''',
    encoding="utf-8",
)

cli_text = TRANSFER_CLI.read_text(encoding="utf-8")
old = '''@transfer_app.command("remote-next")
def remote_next(
    branch: str = typer.Argument(
        ..., help="Remote transfer branch to fetch, switch to, pull, and run."
    ),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_remote_next_transfer(Path("."), branch)
'''
new = '''@transfer_app.command("remote-next")
def remote_next(
    branch: str | None = typer.Argument(
        None,
        help="Optional remote transfer branch. If omitted, read branch from the transfer order.",
    ),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_remote_next_transfer(Path("."), branch)
'''
if old not in cli_text:
    raise SystemExit("target block not found in transfer CLI")
TRANSFER_CLI.write_text(cli_text.replace(old, new), encoding="utf-8")

TRANSFER_TESTS.write_text(
    '''from __future__ import annotations

import subprocess
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_remote_next import _validate_branch_name, resolve_remote_next_branch


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True, stdout=subprocess.PIPE)


def test_validate_branch_name_accepts_transfer_branch():
    assert _validate_branch_name("transfer/example-1") == "transfer/example-1"


def test_validate_branch_name_rejects_unsafe_branch():
    for value in ["", "-bad", "bad..name", "bad name", "bad.lock"]:
        try:
            _validate_branch_name(value)
        except ValueError:
            continue
        raise AssertionError(f"unsafe branch accepted: {value!r}")


def test_resolve_remote_next_branch_accepts_explicit_branch(tmp_path):
    assert resolve_remote_next_branch(tmp_path, "transfer/example") == "transfer/example"


def test_resolve_remote_next_branch_reads_transfer_order_branch(tmp_path):
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump({"branch": "feature/example"}), encoding="utf-8")

    assert resolve_remote_next_branch(tmp_path) == "feature/example"


def test_resolve_remote_next_branch_requires_order_branch(tmp_path):
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump({"id": "missing-branch"}), encoding="utf-8")

    try:
        resolve_remote_next_branch(tmp_path)
    except ValueError as exc:
        assert "must define a non-empty branch" in str(exc)
    else:
        raise AssertionError("missing branch accepted")


def test_remote_next_blocks_dirty_worktree_before_fetch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["transfer", "remote-next", "transfer/example"])

    assert result.exit_code == 1
    assert "worktree must be clean before transfer remote-next" in result.stdout


def test_remote_next_without_branch_requires_order_branch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump({"id": "missing-branch"}), encoding="utf-8")

    result = CliRunner().invoke(app, ["transfer", "remote-next"])

    assert result.exit_code == 1
    assert "must define a non-empty branch" in result.stdout


def test_transfer_help_lists_remote_next():
    result = CliRunner().invoke(app, ["transfer", "--help"])

    assert result.exit_code == 0
    assert "remote-next" in result.stdout
''',
    encoding="utf-8",
)

print("BOOTSTRAP_REMOTE_NEXT_BRANCHLESS_PATCH=written")
print("UPDATED=src/agentic_project_kit/transfer_remote_next.py")
print("UPDATED=src/agentic_project_kit/cli_commands/transfer.py")
print("UPDATED=tests/test_transfer_remote_next.py")
