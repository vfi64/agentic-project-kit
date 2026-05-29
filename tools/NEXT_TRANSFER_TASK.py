#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
BRANCH = 'feature/rn-rnc-aliases-and-closeout'
TMP_DIFF = Path('/tmp/rn-rnc-aliases-and-closeout.diff')


def run(label: str, argv: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print()
    print(f'### {label} ###')
    print('$ ' + ' '.join(str(a) for a in argv))
    proc = subprocess.run([str(a) for a in argv], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.stdout:
        print(proc.stdout.rstrip())
    print(f'status={proc.returncode}')
    if check and proc.returncode != 0:
        print('### RESULT: FAIL ###')
        raise SystemExit(proc.returncode)
    return proc


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'wrote={rel}')


def patch_file(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print(f'pattern not found in {rel}')
        print('### RESULT: FAIL ###')
        raise SystemExit(1)
    path.write_text(text.replace(old, new), encoding='utf-8')
    print(f'patched={rel}')


def main() -> int:
    for _ in range(20):
        print()
    print('=' * 51)
    print('=' * 51)
    print('=' * 51)
    print('TRANSFER TASK: implement rn/rnc aliases and g dialog signal')

    run('SYNC MAIN', ['git', 'switch', 'main'])
    run('PULL MAIN', ['git', 'pull', '--ff-only', 'origin', 'main'])
    dirty = run('PRE-BRANCH STATUS', ['git', 'status', '--porcelain'], check=False).stdout.strip()
    if dirty:
        print('dirty worktree before feature branch:')
        print(dirty)
        print('### RESULT: FAIL ###')
        return 1

    exists = subprocess.run(['git', 'rev-parse', '--verify', BRANCH], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if exists.returncode == 0:
        run('SWITCH EXISTING BRANCH', ['git', 'switch', BRANCH])
        run('RESET BRANCH TO MAIN', ['git', 'reset', '--hard', 'main'])
    else:
        run('CREATE BRANCH', ['git', 'switch', '-c', BRANCH])

    patch_file(
        'src/agentic_project_kit/evidence_commit_paths.py',
        '    missing = [rel for rel in normalized_paths if not (root_path / rel).exists()]\n    if missing:\n        return EvidenceCommitPathsResult(\n            False,\n            branch,\n            head_before,\n            "",\n            normalized_paths,\n            log_path,\n            tuple(f"missing path: {rel}" for rel in missing),\n        )\n\n    add_result = _run_git(root_path, ["add", *normalized_paths])\n',
        '    deletion_lines = {line.strip()[3:] for line in status_before if line.startswith(" D ") or line.startswith("D  ")}\n    missing = [\n        rel for rel in normalized_paths\n        if not (root_path / rel).exists() and rel not in deletion_lines\n    ]\n    if missing:\n        return EvidenceCommitPathsResult(\n            False,\n            branch,\n            head_before,\n            "",\n            normalized_paths,\n            log_path,\n            tuple(f"missing path: {rel}" for rel in missing),\n        )\n\n    add_result = _run_git(root_path, ["add", "-A", "--", *normalized_paths])\n'
    )

    write('src/agentic_project_kit/remote_next_closeout.py', r'''
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from agentic_project_kit.evidence_commit_paths import commit_paths


@dataclass(frozen=True)
class RemoteNextCloseoutResult:
    success: bool
    branch: str
    closeout_branch: str
    commit_sha: str
    paths: tuple[str, ...]
    findings: tuple[str, ...]


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def _status_lines(root: Path) -> tuple[str, ...]:
    result = _run_git(root, ["status", "--short", "--untracked-files=all"])
    if result.returncode != 0:
        return ()
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def _path_from_status(line: str) -> str:
    text = line.strip()
    if " -> " in text:
        return text.split(" -> ", 1)[1]
    return text[3:]


def _is_allowed_closeout_path(path: str) -> bool:
    if path == ".agentic/handoff_state.yaml":
        return True
    if re.fullmatch(r"\.agentic/typed_work_orders/(inbox|executed)/[A-Za-z0-9_.-]+\.ya?ml", path):
        return True
    if re.fullmatch(r"docs/reports/terminal/[A-Za-z0-9_.-]+\.log", path):
        return True
    return False


def _derive_closeout_branch(paths: tuple[str, ...]) -> str:
    for path in paths:
        if path.startswith("docs/reports/terminal/") and path.endswith(".log"):
            stem = Path(path).stem
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-")
            if safe:
                return f"docs/{safe}-evidence"
    return "docs/remote-next-closeout-evidence"


def run_remote_next_closeout(project_root: Path = Path("."), *, push: bool = True) -> RemoteNextCloseoutResult:
    root = project_root.resolve()
    branch_result = _run_git(root, ["branch", "--show-current"])
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "UNKNOWN"
    if branch != "main":
        return RemoteNextCloseoutResult(False, branch, "", "", (), (f"expected main branch, got {branch}",))

    status = _status_lines(root)
    if not status:
        return RemoteNextCloseoutResult(False, branch, "", "", (), ("no closeout paths are dirty",))

    paths = tuple(dict.fromkeys(_path_from_status(line) for line in status))
    unexpected = tuple(path for path in paths if not _is_allowed_closeout_path(path))
    if unexpected:
        return RemoteNextCloseoutResult(False, branch, "", "", paths, tuple(f"unexpected dirty path: {path}" for path in unexpected))

    closeout_branch = _derive_closeout_branch(paths)
    switch = _run_git(root, ["switch", "-c", closeout_branch])
    if switch.returncode != 0:
        return RemoteNextCloseoutResult(False, branch, closeout_branch, "", paths, ((switch.stderr or switch.stdout or "git switch failed").strip(),))

    result = commit_paths(root=root, paths=paths, message=f"Record {closeout_branch.removeprefix('docs/')} evidence", push=push)
    if not result.success:
        return RemoteNextCloseoutResult(False, branch, closeout_branch, result.commit_sha, paths, result.findings)
    return RemoteNextCloseoutResult(True, branch, closeout_branch, result.commit_sha, paths, ())


def render_remote_next_closeout_result(result: RemoteNextCloseoutResult) -> str:
    lines = [
        "REMOTE_NEXT_CLOSEOUT_RESULT",
        f"success={'yes' if result.success else 'no'}",
        f"source_branch={result.branch}",
        f"closeout_branch={result.closeout_branch or 'NONE'}",
        f"commit_sha={result.commit_sha or 'NONE'}",
    ]
    for path in result.paths:
        lines.append(f"path={path}")
    for finding in result.findings:
        lines.append(f"finding={finding}")
    lines.append(f"### RESULT: {'PASS' if result.success else 'FAIL'} ###")
    return "\n".join(lines)
'''.lstrip())

    patch_file(
        'src/agentic_project_kit/cli_commands/remote_next.py',
        'from agentic_project_kit.remote_next import (\n    remote_next_result_as_json_data,\n    render_remote_next_result,\n    run_remote_next,\n)\n',
        'from agentic_project_kit.remote_next import (\n    remote_next_result_as_json_data,\n    render_remote_next_result,\n    run_remote_next,\n)\nfrom agentic_project_kit.remote_next_closeout import (\n    render_remote_next_closeout_result,\n    run_remote_next_closeout,\n)\n'
    )
    patch_file(
        'src/agentic_project_kit/cli_commands/remote_next.py',
        '        if result.returncode != 0:\n            raise typer.Exit(code=result.returncode)\n',
        '        if result.returncode != 0:\n            raise typer.Exit(code=result.returncode)\n\n    @app.command("rn")\n    def rn_command(\n        project_root: Annotated[Path, typer.Option("--root")] = Path("."),\n        json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON result.")] = False,\n    ) -> None:\n        result = run_remote_next(project_root)\n        if json_output:\n            typer.echo(json.dumps(remote_next_result_as_json_data(result), indent=2, sort_keys=True))\n        else:\n            typer.echo(render_remote_next_result(result))\n        if result.returncode != 0:\n            raise typer.Exit(code=result.returncode)\n\n    @app.command("rnc")\n    def rnc_command(\n        project_root: Annotated[Path, typer.Option("--root")] = Path("."),\n        no_push: Annotated[bool, typer.Option("--no-push", help="Commit locally without pushing.")] = False,\n    ) -> None:\n        result = run_remote_next_closeout(project_root, push=not no_push)\n        typer.echo(render_remote_next_closeout_result(result))\n        if not result.success:\n            raise typer.Exit(code=1)\n'
    )

    patch_file(
        'src/agentic_project_kit/cockpit.py',
        '        CockpitAction("workflow.state", "Workflow state", "workflow", ("agentic-kit", "workflow", "state"), READ_ONLY, "Show guided workflow state and recommended next step."),\n',
        '        CockpitAction("workflow.state", "Workflow state", "workflow", ("agentic-kit", "workflow", "state"), READ_ONLY, "Show guided workflow state and recommended next step."),\n        CockpitAction("dialog.rn", "Run Next Work Order", "dialog", ("agentic-kit", "rn"), BOUNDED, "Synchronize main and run the next typed work order."),\n        CockpitAction("dialog.rnc", "Close Out Last Run", "dialog", ("agentic-kit", "rnc"), BOUNDED, "Commit and push the expected closeout paths from the last remote-next run."),\n'
    )

    patch_file(
        'docs/governance/CHAT_COMMUNICATION_CONTRACT.md',
        'Manual copy-and-paste of terminal output is allowed only after a hard local failure that prevents evidence creation or transfer, including kill -9, process startup failure, terminal loss, machine crash, filesystem failure, network failure before push, or explicitly broken logging.\n',
        'Manual copy-and-paste of terminal output is allowed only after a hard local failure that prevents evidence creation or transfer, including kill -9, process startup failure, terminal loss, machine crash, filesystem failure, network failure before push, or explicitly broken logging.\n\n## Preferred dialog signals\n\nThe preferred dialog signals are `d` for done, `f` for fail, and `g` for go. `g` replaces the former German `w` signal for continuing with the next safe planned step. `w` remains accepted as a legacy alias for `g` during transition, but new tooling and generated instructions should prefer `g`.\n\nThe local command aliases are `agentic-kit rn` for run-next/remote-next and `agentic-kit rnc` for remote-next closeout. GUI controls must use these aliases rather than introducing a separate execution model.\n'
    )

    patch_file(
        'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md',
        'Closeout scripts must finalize any repo-backed log before invoking this helper and must not write to the committed repo-backed log afterwards.\n',
        'Closeout scripts must finalize any repo-backed log before invoking this helper and must not write to the committed repo-backed log afterwards. The helper must accept expected tracked deletions and stage them with `git add -A -- <paths>`.\n\n## Remote-next aliases\n\nUse `agentic-kit rn` as the short alias for `agentic-kit remote-next`. Use `agentic-kit rnc` to close out the dirty path set produced by the last successful remote-next run. The GUI must expose these as Run Next Work Order and Close Out Last Run.\n'
    )

    write('tests/test_remote_next_closeout.py', r'''
from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.remote_next_closeout import run_remote_next_closeout


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test User")
    git(root, "checkout", "-b", "main")
    (root / ".agentic/typed_work_orders/inbox").mkdir(parents=True)
    (root / ".agentic/typed_work_orders/inbox/example.yaml").write_text("id: example\n", encoding="utf-8")
    git(root, "add", ".")
    assert git(root, "commit", "-m", "init").returncode == 0


def test_rnc_commits_expected_closeout_paths_including_deletion(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / ".agentic/handoff_state.yaml").write_text("state: refreshed\n", encoding="utf-8")
    (tmp_path / ".agentic/typed_work_orders/inbox/example.yaml").unlink()
    (tmp_path / ".agentic/typed_work_orders/executed").mkdir(parents=True)
    (tmp_path / ".agentic/typed_work_orders/executed/example.yaml").write_text("id: example\n", encoding="utf-8")
    (tmp_path / "docs/reports/terminal").mkdir(parents=True)
    (tmp_path / "docs/reports/terminal/example.log").write_text("PASS\n", encoding="utf-8")

    result = run_remote_next_closeout(tmp_path, push=False)

    assert result.success, result.findings
    assert result.closeout_branch == "docs/example-evidence"
    assert git(tmp_path, "status", "--short").stdout == ""


def test_rnc_blocks_unexpected_dirty_path(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "unexpected.txt").write_text("dirty\n", encoding="utf-8")

    result = run_remote_next_closeout(tmp_path, push=False)

    assert not result.success
    assert any("unexpected dirty path" in finding for finding in result.findings)


def test_rn_and_rnc_cli_are_registered(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_next.run_remote_next",
        lambda root: type("R", (), {"sync_status": "synced", "returncode": 0, "message": "ok", "typed_next": None})(),
    )
    rn = CliRunner().invoke(app, ["rn"])
    assert rn.exit_code == 0, rn.output
    assert "REMOTE_NEXT_RESULT" in rn.output

    init_repo(tmp_path)
    (tmp_path / "docs/reports/terminal").mkdir(parents=True)
    (tmp_path / "docs/reports/terminal/example.log").write_text("PASS\n", encoding="utf-8")
    rnc = CliRunner().invoke(app, ["rnc", "--root", str(tmp_path), "--no-push"])
    assert rnc.exit_code == 0, rnc.output
    assert "REMOTE_NEXT_CLOSEOUT_RESULT" in rnc.output
'''.lstrip())

    patch_file(
        'tests/test_evidence_commit_paths.py',
        'def test_commit_paths_blocks_unexpected_dirty_paths(tmp_path: Path) -> None:\n',
        'def test_commit_paths_accepts_expected_tracked_deletion(tmp_path: Path) -> None:\n    init_repo(tmp_path)\n    rel = "docs/reports/terminal/delete-me.log"\n    path = tmp_path / rel\n    path.parent.mkdir(parents=True, exist_ok=True)\n    path.write_text("old log\\n", encoding="utf-8")\n    git(tmp_path, "add", rel)\n    assert git(tmp_path, "commit", "-m", "add log").returncode == 0\n    path.unlink()\n\n    result = commit_paths(root=tmp_path, paths=(rel,), message="Record deletion")\n\n    assert result.success, result.findings\n    assert git(tmp_path, "status", "--short").stdout == ""\n\n\ndef test_commit_paths_blocks_unexpected_dirty_paths(tmp_path: Path) -> None:\n'
    )

    patch_file(
        'tests/test_cockpit.py',
        '    assert "workflow.state" in action_ids\n',
        '    assert "workflow.state" in action_ids\n    assert "dialog.rn" in action_ids\n    assert "dialog.rnc" in action_ids\n'
    )

    run('TARGETED TESTS', [ROOT / '.venv/bin/python', '-m', 'pytest', 'tests/test_remote_next.py', 'tests/test_remote_next_closeout.py', 'tests/test_evidence_commit_paths.py', 'tests/test_cockpit.py', '-q'])
    run('RUFF', [ROOT / '.venv/bin/python', '-m', 'ruff', 'check', 'src/agentic_project_kit/remote_next_closeout.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'src/agentic_project_kit/evidence_commit_paths.py', 'tests/test_remote_next_closeout.py', 'tests/test_evidence_commit_paths.py', 'tests/test_cockpit.py'])
    run('CHECK DOCS', [ROOT / '.venv/bin/agentic-kit', 'check-docs'])
    run('DOCTOR', [ROOT / '.venv/bin/agentic-kit', 'doctor'])
    TMP_DIFF.write_text(run('CAPTURE DIFF', ['git', 'diff', '--binary']).stdout, encoding='utf-8')
    run('PROTECTED CHANGE PLAN', ['./ns', 'protected-change-plan', '--diff-file', str(TMP_DIFF)])
    run('GIT ADD', ['git', 'add', 'src/agentic_project_kit/evidence_commit_paths.py', 'src/agentic_project_kit/remote_next_closeout.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'src/agentic_project_kit/cockpit.py', 'tests/test_remote_next_closeout.py', 'tests/test_remote_next.py', 'tests/test_evidence_commit_paths.py', 'tests/test_cockpit.py', 'docs/governance/CHAT_COMMUNICATION_CONTRACT.md', 'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md'])
    run('GIT COMMIT', ['git', 'commit', '-m', 'Add rn rnc aliases and closeout flow'])
    run('GIT PUSH', ['git', 'push', '-u', 'origin', BRANCH])
    print()
    print('SUMMARY COMM-LOCAL | rn-rnc-aliases-and-closeout')
    print('RESULT')
    print('  WORK: PASS')
    print('  EVIDENCE: PASS')
    print('  OVERALL: PASS')
    print('NEXT')
    print('  SAFE_STEP: create PR for rn/rnc aliases and closeout flow')
    print('  CHAT_REPLY: d')
    print('### RESULT: PASS ###')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
