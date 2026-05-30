#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
BRANCH = 'feature/rnc-no-closeout-status'
TMP_DIFF = Path('/tmp/rnc-no-closeout-status.diff')


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
    print('TRANSFER TASK: rnc no-closeout status')

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
        'src/agentic_project_kit/remote_next_closeout.py',
        '@dataclass(frozen=True)\nclass RemoteNextCloseoutResult:\n    success: bool\n    branch: str\n    closeout_branch: str\n    commit_sha: str\n    paths: tuple[str, ...]\n    findings: tuple[str, ...]\n',
        '@dataclass(frozen=True)\nclass RemoteNextCloseoutResult:\n    success: bool\n    status: str\n    branch: str\n    closeout_branch: str\n    commit_sha: str\n    paths: tuple[str, ...]\n    findings: tuple[str, ...]\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '        return RemoteNextCloseoutResult(False, branch, "", "", (), (f"expected main branch, got {branch}",))\n',
        '        return RemoteNextCloseoutResult(False, "fail", branch, "", "", (), (f"expected main branch, got {branch}",))\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '        return RemoteNextCloseoutResult(False, branch, "", "", (), ("no closeout paths are dirty",))\n',
        '        return RemoteNextCloseoutResult(False, "no_closeout", branch, "", "", (), ("no closeout paths are dirty",))\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '        return RemoteNextCloseoutResult(False, branch, "", "", paths, tuple(f"unexpected dirty path: {path}" for path in unexpected))\n',
        '        return RemoteNextCloseoutResult(False, "fail", branch, "", "", paths, tuple(f"unexpected dirty path: {path}" for path in unexpected))\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '        return RemoteNextCloseoutResult(False, branch, closeout_branch, "", paths, ((switch.stderr or switch.stdout or "git switch failed").strip(),))\n',
        '        return RemoteNextCloseoutResult(False, "fail", branch, closeout_branch, "", paths, ((switch.stderr or switch.stdout or "git switch failed").strip(),))\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '        return RemoteNextCloseoutResult(False, branch, closeout_branch, result.commit_sha, paths, result.findings)\n    return RemoteNextCloseoutResult(True, branch, closeout_branch, result.commit_sha, paths, ())\n',
        '        return RemoteNextCloseoutResult(False, "fail", branch, closeout_branch, result.commit_sha, paths, result.findings)\n    return RemoteNextCloseoutResult(True, "pass", branch, closeout_branch, result.commit_sha, paths, ())\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '        f"success={\'yes\' if result.success else \'no\'}",\n        f"source_branch={result.branch}",\n',
        '        f"success={\'yes\' if result.success else \'no\'}",\n        f"result_status={result.status}",\n        f"source_branch={result.branch}",\n'
    )
    patch_file(
        'src/agentic_project_kit/remote_next_closeout.py',
        '    lines.append(f"### RESULT: {\'PASS\' if result.success else \'FAIL\'} ###")\n',
        '    result_label = "PASS" if result.success else "NO-CLOSEOUT" if result.status == "no_closeout" else "FAIL"\n    lines.append(f"### RESULT: {result_label} ###")\n'
    )

    patch_file(
        'src/agentic_project_kit/cli_commands/remote_next.py',
        '        if not result.success:\n            raise typer.Exit(code=1)\n',
        '        if result.status == "no_closeout":\n            raise typer.Exit(code=2)\n        if not result.success:\n            raise typer.Exit(code=1)\n'
    )

    patch_file(
        'tests/test_remote_next_closeout.py',
        'def test_rnc_blocks_unexpected_dirty_path(tmp_path: Path) -> None:\n',
        'def test_rnc_reports_no_closeout_on_clean_worktree(tmp_path: Path) -> None:\n    init_repo(tmp_path)\n\n    result = run_remote_next_closeout(tmp_path, push=False)\n\n    assert not result.success\n    assert result.status == "no_closeout"\n    assert result.findings == ("no closeout paths are dirty",)\n\n\ndef test_rnc_blocks_unexpected_dirty_path(tmp_path: Path) -> None:\n'
    )
    patch_file(
        'tests/test_remote_next_closeout.py',
        'def test_rn_and_rnc_cli_are_registered(monkeypatch, tmp_path: Path) -> None:\n',
        'def test_rnc_cli_uses_exit_2_for_no_closeout(tmp_path: Path) -> None:\n    init_repo(tmp_path)\n\n    result = CliRunner().invoke(app, ["rnc", "--root", str(tmp_path), "--no-push"])\n\n    assert result.exit_code == 2, result.output\n    assert "result_status=no_closeout" in result.output\n    assert "### RESULT: NO-CLOSEOUT ###" in result.output\n\n\ndef test_rn_and_rnc_cli_are_registered(monkeypatch, tmp_path: Path) -> None:\n'
    )

    patch_file(
        'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md',
        'Use `agentic-kit rn` as the short alias for `agentic-kit remote-next`. Use `agentic-kit rnc` to close out the dirty path set produced by the last successful remote-next run. The GUI must expose these as Run Next Work Order and Close Out Last Run.\n',
        'Use `agentic-kit rn` as the short alias for `agentic-kit remote-next`. Use `agentic-kit rnc` to close out the dirty path set produced by the last successful remote-next run. If no closeout paths are dirty, `rnc` must report `result_status=no_closeout`, render `### RESULT: NO-CLOSEOUT ###`, and exit with code 2 rather than presenting the state as a hard failure. The GUI must expose these as Run Next Work Order and Close Out Last Run.\n'
    )

    run('TARGETED TESTS', [ROOT / '.venv/bin/python', '-m', 'pytest', 'tests/test_remote_next_closeout.py', 'tests/test_cockpit.py', '-q'])
    run('RUFF', [ROOT / '.venv/bin/python', '-m', 'ruff', 'check', 'src/agentic_project_kit/remote_next_closeout.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'tests/test_remote_next_closeout.py'])
    run('CHECK DOCS', [ROOT / '.venv/bin/agentic-kit', 'check-docs'])
    run('DOCTOR', [ROOT / '.venv/bin/agentic-kit', 'doctor'])
    TMP_DIFF.write_text(run('CAPTURE DIFF', ['git', 'diff', '--binary']).stdout, encoding='utf-8')
    run('PROTECTED CHANGE PLAN', ['./ns', 'protected-change-plan', '--diff-file', str(TMP_DIFF)])
    run('GIT ADD', ['git', 'add', 'src/agentic_project_kit/remote_next_closeout.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'tests/test_remote_next_closeout.py', 'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md'])
    run('GIT COMMIT', ['git', 'commit', '-m', 'Report rnc no-closeout without hard failure'])
    run('GIT PUSH', ['git', 'push', '-u', 'origin', BRANCH])
    print()
    print('SUMMARY COMM-LOCAL | rnc-no-closeout-status')
    print('RESULT')
    print('  WORK: PASS')
    print('  EVIDENCE: PASS')
    print('  OVERALL: PASS')
    print('NEXT')
    print('  SAFE_STEP: create PR for rnc no-closeout status')
    print('  CHAT_REPLY: d')
    print('### RESULT: PASS ###')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
