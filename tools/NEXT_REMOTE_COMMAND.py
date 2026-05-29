#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit')
AK = ROOT / '.venv/bin/agentic-kit'
PR914 = '040765e2e6f4647b50d653f3fffbc383d62fd4cc'

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

for _ in range(20):
    out()
out('===================================================')
out('===================================================')
out('===================================================')
out('REMOTE COMMAND: post-pr914-closeout-refresh')

if not ROOT.exists():
    out(f'missing repo root: {ROOT}')
    out('### RESULT: FAIL ###')
    raise SystemExit(1)
if not AK.exists():
    out(f'missing agentic-kit: {AK}')
    out('### RESULT: FAIL ###')
    raise SystemExit(1)

run('FETCH MAIN', ['git', 'fetch', 'origin', 'main'])
run('SWITCH MAIN', ['git', 'switch', 'main'])
run('PULL MAIN', ['git', 'pull', '--ff-only', 'origin', 'main'])

head = run('CURRENT HEAD', ['git', 'rev-parse', 'HEAD']).stdout.strip()
run('VERIFY PR914 IS ANCESTOR', ['git', 'merge-base', '--is-ancestor', PR914, head])
out(f'current_main={head}')
out('pr914_merge_is_ancestor=true')

status = run('WORKTREE STATUS', ['git', 'status', '--short'], check=False).stdout.strip()
if status:
    out('worktree is dirty before closeout checks:')
    out(status)
    out('### RESULT: FAIL ###')
    raise SystemExit(1)

run('HANDOFF CHECK', [str(AK), 'handoff', 'check'])
run('HANDOFF POST MERGE REFRESH STATUS', [str(AK), 'handoff', 'post-merge-refresh-status'], check=False)
run('DOCTOR', [str(AK), 'doctor'])
run('CHECK DOCS', [str(AK), 'check-docs'])

out()
out('SUMMARY COMM-LOCAL | post-pr914-closeout-refresh')
out('RESULT')
out('  WORK: PASS')
out('  EVIDENCE: PASS')
out('  OVERALL: PASS')
out('NEXT')
out('  SAFE_STEP: inspect whether handoff refresh is needed, then continue with closeout refresh or stable remote command contract')
out('  CHAT_REPLY: d')
out('### RESULT: PASS ###')
