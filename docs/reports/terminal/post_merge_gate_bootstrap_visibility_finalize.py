from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BRANCH = 'docs/post-merge-gate-bootstrap-visibility'
LOG = ROOT / 'docs/reports/terminal/post-merge-gate-bootstrap-visibility-finalize.log'
EXPECTED = [
    'docs/handoff/START_NEW_CHAT_PROMPT.md',
    'docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md',
    'docs/handoff/CURRENT_HANDOFF.md',
    'docs/reports/terminal/post-merge-gate-bootstrap-visibility.log',
    'docs/reports/terminal/post_merge_gate_bootstrap_visibility_helper.py',
    'docs/reports/terminal/post_merge_gate_bootstrap_visibility_finalize.py',
]


def run(args, *, check=True):
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    return_code = proc.returncode
    if check and return_code != 0:
        raise RuntimeError(
            'command failed: ' + ' '.join(args) + '\n' + proc.stdout + proc.stderr
        )
    return proc


def main() -> int:
    lines = ['POST_MERGE_GATE_BOOTSTRAP_VISIBILITY_FINALIZE']
    try:
        branch = run(['git', 'branch', '--show-current']).stdout.strip()
        lines.append(f'branch={branch}')
        if branch != BRANCH:
            lines.append('result=FAIL')
            lines.append(f'error=expected_branch_{BRANCH}')
            return 1

        run([sys.executable, 'docs/reports/terminal/post_merge_gate_bootstrap_visibility_helper.py'])

        for path in EXPECTED:
            if (ROOT / path).exists():
                run(['git', 'add', path])

        status = run(['git', 'status', '--short']).stdout.splitlines()
        lines.append('status_after_add=' + ('<clean>' if not status else '|'.join(status)))

        staged = run(['git', 'diff', '--cached', '--name-only']).stdout.splitlines()
        lines.append('staged_files=' + (','.join(staged) if staged else '<none>'))
        if not staged:
            lines.append('result=FAIL')
            lines.append('error=no_staged_changes')
            return 1

        run(['git', 'commit', '-m', 'Document post-merge gate bootstrap visibility'])
        head = run(['git', 'rev-parse', '--short', 'HEAD']).stdout.strip()
        lines.append(f'committed_head={head}')
        run(['git', 'push', 'origin', BRANCH])
        lines.append('push=PASS')
        lines.append('result=PASS')
        return 0
    except Exception as exc:
        lines.append('result=FAIL')
        lines.append('error=' + str(exc).replace('\n', '\\n'))
        return 1
    finally:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(str(LOG.relative_to(ROOT)))
        print(lines[-1])


if __name__ == '__main__':
    raise SystemExit(main())
