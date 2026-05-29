#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
BRANCH = 'feature/remote-next-typed-work-order-runner'
DIFF = Path('/tmp/remote-next-typed-work-order-runner.diff')
FILES = [
    'src/agentic_project_kit/cli.py',
    'src/agentic_project_kit/remote_next.py',
    'src/agentic_project_kit/cli_commands/remote_next.py',
    'tests/test_remote_next.py',
    'docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md',
]

def out(s: str = '') -> None:
    print(s, flush=True)

def run(label: str, argv: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    out(); out('### ' + label + ' ###'); out('$ ' + ' '.join(argv))
    p = subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.stdout:
        print(p.stdout.rstrip(), flush=True)
    out('status=' + str(p.returncode))
    if check and p.returncode != 0:
        out('### RESULT: FAIL ###')
        raise SystemExit(p.returncode)
    return p

for _ in range(20):
    out()
out('=' * 51); out('=' * 51); out('=' * 51)
out('REMOTE COMMAND: continue remote-next branch')

branch = run('CURRENT BRANCH', ['git', 'branch', '--show-current']).stdout.strip()
if branch != BRANCH:
    out('wrong branch: ' + branch + ' expected ' + BRANCH)
    out('### RESULT: FAIL ###')
    raise SystemExit(1)

run('STATUS BEFORE GATES', ['git', 'status', '--short'])
run('TARGETED TESTS', [str(ROOT / '.venv/bin/python'), '-m', 'pytest', 'tests/test_remote_next.py', '-q'])
run('RUFF CHECK', [str(ROOT / '.venv/bin/python'), '-m', 'ruff', 'check', 'src/agentic_project_kit/remote_next.py', 'src/agentic_project_kit/cli_commands/remote_next.py', 'tests/test_remote_next.py'])
run('CHECK DOCS', [str(ROOT / '.venv/bin/agentic-kit'), 'check-docs'])
run('DOCTOR', [str(ROOT / '.venv/bin/agentic-kit'), 'doctor'])

DIFF.write_text(run('CAPTURE DIFF', ['git', 'diff', '--binary']).stdout, encoding='utf-8')
run('PROTECTED CHANGE PLAN', ['./ns', 'protected-change-plan', '--diff-file', str(DIFF)])
run('GIT ADD', ['git', 'add', *FILES])
status = run('STATUS AFTER ADD', ['git', 'status', '--short']).stdout.strip()
if not status:
    out('nothing to commit')
    out('### RESULT: FAIL ###')
    raise SystemExit(1)
run('GIT COMMIT', ['git', 'commit', '-m', 'Add remote-next typed work order runner'])
run('GIT PUSH', ['git', 'push', '-u', 'origin', BRANCH])

out('SUMMARY COMM-LOCAL | remote-next-typed-work-order-runner')
out('RESULT')
out('  WORK: PASS')
out('  EVIDENCE: PASS')
out('  OVERALL: PASS')
out('NEXT')
out('  SAFE_STEP: create PR and inspect CI')
out('  CHAT_REPLY: d')
out('### RESULT: PASS ###')
