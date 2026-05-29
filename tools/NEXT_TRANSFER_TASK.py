#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
BRANCH = 'docs/post-pr928-handoff-refresh-evidence'
PATHS = [
    '.agentic/typed_work_orders/inbox/post-pr928-handoff-refresh.yaml',
    '.agentic/typed_work_orders/executed/post-pr928-handoff-refresh.yaml',
    'docs/reports/terminal/post-pr928-handoff-refresh.log',
]


def run(label: str, argv: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print()
    print(f'### {label} ###')
    print('$ ' + ' '.join(argv))
    proc = subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.stdout:
        print(proc.stdout.rstrip())
    print(f'status={proc.returncode}')
    if check and proc.returncode != 0:
        print('### RESULT: FAIL ###')
        raise SystemExit(proc.returncode)
    return proc


def main() -> int:
    for _ in range(20):
        print()
    print('=' * 51)
    print('=' * 51)
    print('=' * 51)
    print('TRANSFER TASK: post PR928 handoff refresh evidence closeout')

    branch = run('CURRENT BRANCH', ['git', 'branch', '--show-current']).stdout.strip()
    if branch != 'main':
        print(f'wrong branch: {branch}; expected main')
        print('### RESULT: FAIL ###')
        return 1

    status = run('STATUS BEFORE CLOSEOUT', ['git', 'status', '--short'], check=False).stdout.splitlines()
    unexpected = [line for line in status if not any(line.strip().endswith(path) for path in PATHS)]
    if unexpected:
        print('unexpected dirty paths:')
        for line in unexpected:
            print(repr(line))
        print('### RESULT: FAIL ###')
        return 1

    run('CREATE CLOSEOUT BRANCH', ['git', 'switch', '-c', BRANCH])
    run('EVIDENCE COMMIT PATHS', [
        '.venv/bin/agentic-kit', 'evidence', 'commit-paths',
        '--path', PATHS[0], '--path', PATHS[1], '--path', PATHS[2],
        '--message', 'Record post-PR928 handoff refresh evidence',
        '--push',
    ])
    run('STATUS AFTER CLOSEOUT', ['git', 'status', '--short'], check=False)
    print()
    print('SUMMARY COMM-LOCAL | post-pr928-handoff-refresh-evidence')
    print('RESULT')
    print('  WORK: PASS')
    print('  EVIDENCE: PASS')
    print('  OVERALL: PASS')
    print('NEXT')
    print('  SAFE_STEP: create PR for post-PR928 handoff refresh evidence')
    print('  CHAT_REPLY: d')
    print('### RESULT: PASS ###')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
