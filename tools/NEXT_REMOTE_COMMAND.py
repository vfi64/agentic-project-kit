#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
BRANCH = 'feature/remote-next-typed-work-order-runner'

def out(text: str = '') -> None:
    print(text, flush=True)

def run(label: str, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    out()
    out(f'### {label} ###')
    out('$ ' + ' '.join(cmd))
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.stdout:
        print(p.stdout.rstrip(), flush=True)
    out(f'status={p.returncode}')
    if check and p.returncode != 0:
        out('### RESULT: FAIL ###')
        raise SystemExit(p.returncode)
    return p

def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    out(f'wrote={path}')

for _ in range(20):
    out()
out('===================================================')
out('===================================================')
out('===================================================')
out('REMOTE COMMAND: implement agentic-kit remote-next')

PY = ROOT / '.venv/bin/python'
AK = ROOT / '.venv/bin/agentic-kit'
if not PY.exists() or not AK.exists():
    out('missing repo .venv python or agentic-kit')
    out('### RESULT: FAIL ###')
    raise SystemExit(1)

run('FETCH MAIN', ['git', 'fetch', 'origin', 'main'])
branch = run('CURRENT BRANCH', ['git', 'branch', '--show-current']).stdout.strip()
if branch == BRANCH:
    run('RESET BROKEN FEATURE BRANCH', ['git', 'reset', '--hard'])
run('SWITCH MAIN', ['git', 'switch', 'main'])
run('PULL MAIN', ['git', 'pull', '--ff-only', 'origin', 'main'])
status = run('PRE-BRANCH STATUS', ['git', 'status', '--porcelain'], check=False).stdout.strip()
if status:
    out('dirty worktree before feature branch:')
    out(status)
    out('### RESULT: FAIL ###')
    raise SystemExit(1)

existing = subprocess.run(['git', 'rev-parse', '--verify', BRANCH], cwd=ROOT, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if existing.returncode == 0:
    run('SWITCH EXISTING BRANCH', ['git', 'switch', BRANCH])
    run('RESET FEATURE BRANCH TO MAIN', ['git', 'reset', '--hard', 'main'])
else:
    run('CREATE FEATURE BRANCH', ['git', 'switch', '-c', BRANCH])

remote_next_py = r'''from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path

from agentic_project_kit.typed_work_order_queue import (
    TypedNextResult,
    run_typed_next,
    typed_next_result_as_json_data,
)

STATUS_SYNC_FAIL = "sync_fail"


@dataclasses.dataclass(frozen=True)
class RemoteNextResult:
    sync_status: str
    returncode: int
    message: str
    typed_next: TypedNextResult | None = None


def _run_git(project_root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _sync_main(project_root: Path) -> tuple[bool, str]:
    fetch = _run_git(project_root, ["git", "fetch", "origin", "main"])
    if fetch.returncode != 0:
        return False, (fetch.stderr or fetch.stdout or "git fetch origin main failed").strip()
    branch = _run_git(project_root, ["git", "branch", "--show-current"])
    if branch.returncode != 0:
        return False, (branch.stderr or branch.stdout or "git branch --show-current failed").strip()
    if branch.stdout.strip() != "main":
        switch = _run_git(project_root, ["git", "switch", "main"])
        if switch.returncode != 0:
            return False, (switch.stderr or switch.stdout or "git switch main failed").strip()
    pull = _run_git(project_root, ["git", "pull", "--ff-only", "origin", "main"])
    if pull.returncode != 0:
        return False, (pull.stderr or pull.stdout or "git pull --ff-only origin main failed").strip()
    return True, "main synced"


def run_remote_next(project_root: Path = Path(".")) -> RemoteNextResult:
    root = project_root.resolve()
    ok, message = _sync_main(root)
    if not ok:
        return RemoteNextResult(STATUS_SYNC_FAIL, 2, message)
    typed_result = run_typed_next(root)
    return RemoteNextResult("synced", typed_result.returncode, typed_result.message, typed_result)


def remote_next_result_as_json_data(result: RemoteNextResult) -> dict[str, object]:
    return {
        "schema_version": 1,
        "sync_status": result.sync_status,
        "returncode": result.returncode,
        "message": result.message,
        "typed_next": typed_next_result_as_json_data(result.typed_next) if result.typed_next else None,
    }


def render_remote_next_result(result: RemoteNextResult) -> str:
    lines = [
        "REMOTE_NEXT_RESULT",
        f"sync_status={result.sync_status}",
        f"returncode={result.returncode}",
        f"message={result.message}",
    ]
    if result.typed_next is not None:
        lines.extend(
            [
                f"typed_queue_status={result.typed_next.queue_status}",
                f"typed_result_status={result.typed_next.result_status}",
            ]
        )
        if result.typed_next.terminal_log:
            lines.append(f"terminal_log={result.typed_next.terminal_log}")
    return "\n".join(lines)
'''

remote_next_cli = r'''from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.remote_next import (
    remote_next_result_as_json_data,
    render_remote_next_result,
    run_remote_next,
)


def register_remote_next_command(app: typer.Typer) -> None:
    @app.command("remote-next")
    def remote_next_command(
        project_root: Annotated[Path, typer.Option("--root")] = Path("."),
        json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON result.")] = False,
    ) -> None:
        result = run_remote_next(project_root)
        if json_output:
            typer.echo(json.dumps(remote_next_result_as_json_data(result), indent=2, sort_keys=True))
        else:
            typer.echo(render_remote_next_result(result))
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
'''

cli_path = ROOT / 'src/agentic_project_kit/cli.py'
cli_text = cli_path.read_text(encoding='utf-8')
if 'from agentic_project_kit.cli_commands.remote_next import register_remote_next_command' not in cli_text:
    cli_text = cli_text.replace(
        'from agentic_project_kit.cli_commands.release import register_release_commands\n',
        'from agentic_project_kit.cli_commands.release import register_release_commands\nfrom agentic_project_kit.cli_commands.remote_next import register_remote_next_command\n',
    )
if 'register_remote_next_command(app)' not in cli_text:
    cli_text = cli_text.replace('register_release_commands(app)\n', 'register_release_commands(app)\nregister_remote_next_command(app)\n')
cli_path.write_text(cli_text, encoding='utf-8')
out('patched=src/agentic_project_kit/cli.py')

write('src/agentic_project_kit/remote_next.py', remote_next_py)
write('src/agentic_project_kit/cli_commands/remote_next.py', remote_next_cli)

test_remote_next = r'''from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.remote_next import (
    STATUS_SYNC_FAIL,
    remote_next_result_as_json_data,
    render_remote_next_result,
    run_remote_next,
)
from agentic_project_kit.typed_work_order_runner import RESULT_PENDING


def test_remote_next_syncs_main_then_runs_typed_next(tmp_path, monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_git(project_root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(tuple(argv))
        if argv == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(argv, 0, stdout="feature/x\n", stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout="ok\n", stderr="")

    typed = SimpleNamespace(
        returncode=2,
        message="No typed work order queued.",
        queue_status="no_command",
        result_status=RESULT_PENDING,
        source_path=None,
        executed_path=None,
        terminal_log=None,
    )

    monkeypatch.setattr("agentic_project_kit.remote_next._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.remote_next.run_typed_next", lambda root: typed)

    result = run_remote_next(tmp_path)

    assert result.sync_status == "synced"
    assert result.returncode == 2
    assert result.typed_next is typed
    assert ("git", "fetch", "origin", "main") in calls
    assert ("git", "switch", "main") in calls
    assert ("git", "pull", "--ff-only", "origin", "main") in calls


def test_remote_next_reports_sync_failure(tmp_path, monkeypatch):
    def fake_git(project_root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="fetch failed")

    monkeypatch.setattr("agentic_project_kit.remote_next._run_git", fake_git)

    result = run_remote_next(tmp_path)

    assert result.sync_status == STATUS_SYNC_FAIL
    assert result.returncode == 2
    assert "fetch failed" in result.message
    assert result.typed_next is None


def test_remote_next_render_and_json_shape():
    result = SimpleNamespace(
        sync_status="sync_fail",
        returncode=2,
        message="failed",
        typed_next=None,
    )

    rendered = render_remote_next_result(result)
    data = remote_next_result_as_json_data(result)

    assert "REMOTE_NEXT_RESULT" in rendered
    assert data["schema_version"] == 1
    assert data["typed_next"] is None


def test_remote_next_cli_is_registered(monkeypatch):
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_next.run_remote_next",
        lambda root: SimpleNamespace(sync_status="synced", returncode=0, message="ok", typed_next=None),
    )

    result = CliRunner().invoke(app, ["remote-next"])

    assert result.exit_code == 0, result.output
    assert "REMOTE_NEXT_RESULT" in result.output
'''
write('tests/test_remote_next.py', test_remote_next)

no_copy = ROOT / 'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md'
no_copy_text = no_copy.read_text(encoding='utf-8')
addition = '''

## Fixed remote-next dialog path

For dialog-oriented local work, the preferred target path is `agentic-kit remote-next`. The command synchronizes `main` and executes the next typed work order through the repo-backed typed work-order runner. Chat assistants should prefer queuing a typed work order for this path over pasting long local terminal blocks. The GUI must use the same command path instead of introducing a separate execution model.
'''
if '## Fixed remote-next dialog path' not in no_copy_text:
    no_copy.write_text(no_copy_text + addition, encoding='utf-8')
    out('patched=docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md')

run('TARGETED TESTS', [str(PY), '-m', 'pytest', 'tests/test_remote_next.py', '-q'])
run('RUFF CHECK', [str(PY), '-m', 'ruff', 'check', 'src/agentic_project_kit/remote_next.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'tests/test_remote_next.py'])
run('CHECK DOCS', [str(AK), 'check-docs'])
run('DOCTOR', [str(AK), 'doctor'])

planner = run('PROTECTED CHANGE PLAN', ['./ns', 'protected-change-plan'], check=False)
if planner.returncode != 0:
    out('protected-change-plan failed')
    out('### RESULT: FAIL ###')
    raise SystemExit(planner.returncode)

run('GIT STATUS BEFORE COMMIT', ['git', 'status', '--short'])
run('GIT ADD', ['git', 'add', 'src/agentic_project_kit/cli.py', 'src/agentic_project_kit/remote_next.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'tests/test_remote_next.py', 'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md'])
run('GIT COMMIT', ['git', 'commit', '-m', 'Add remote-next typed work order runner'])
run('GIT PUSH', ['git', 'push', '-u', 'origin', BRANCH])

out()
out('SUMMARY COMM-LOCAL | remote-next-typed-work-order-runner')
out('RESULT')
out('  WORK: PASS')
out('  EVIDENCE: PASS')
out('  OVERALL: PASS')
out('NEXT')
out('  SAFE_STEP: create PR for feature/remote-next-typed-work-order-runner and inspect CI')
out('  CHAT_REPLY: d')
out('### RESULT: PASS ###')
