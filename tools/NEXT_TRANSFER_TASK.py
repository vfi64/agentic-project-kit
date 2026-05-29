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


def replace(rel: str, old: str, new: str) -> None:
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
    print('TRANSFER TASK CONTINUE: rn/rnc aliases and g dialog signal')

    branch = run('CURRENT BRANCH', ['git', 'branch', '--show-current']).stdout.strip()
    if branch != BRANCH:
        print(f'wrong branch: {branch}; expected {BRANCH}')
        print('### RESULT: FAIL ###')
        return 1

    replace(
        'src/agentic_project_kit/evidence_commit_paths.py',
        '    deletion_lines = {line.strip()[3:] for line in status_before if line.startswith(" D ") or line.startswith("D  ")}\n',
        '    deletion_lines = {line[3:] for line in status_before if line.startswith(" D ") or line.startswith("D  ")}\n',
    )
    replace(
        'src/agentic_project_kit/remote_next_closeout.py',
        'def _path_from_status(line: str) -> str:\n    text = line.strip()\n    if " -> " in text:\n        return text.split(" -> ", 1)[1]\n    return text[3:]\n',
        'def _path_from_status(line: str) -> str:\n    if " -> " in line:\n        return line.split(" -> ", 1)[1]\n    return line[3:]\n',
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
