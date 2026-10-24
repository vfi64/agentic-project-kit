"""macOS-only, inherited OS isolation for an owned offline simulation directory."""
from __future__ import annotations

import json
import os
import signal
from pathlib import Path
import subprocess


def policy(root: Path) -> str:
    root = root.resolve()
    if not root.is_relative_to(Path('/private/tmp')):
        raise ValueError('simulation root must be an owned directory under /private/tmp')
    return ('(version 1)\n(allow default)\n(deny network*)\n(deny file-write*)\n'
            f'(allow file-write* (subpath {json.dumps(str(root))}))\n'
            '(allow file-write-data (literal "/dev/null"))\n')


def isolated(argv: list[str], *, root: Path, cwd: Path, env: dict[str, str],
             timeout: int = 900) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(['/usr/bin/sandbox-exec', '-f', str(root / 'policy.sb'), *argv],
                               cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(argv, timeout, output=stdout, stderr=stderr) from exc
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


def probe(root: Path, python: str, env: dict[str, str]) -> dict:
    """Require actual EPERM for network and an outside write before executing Kit."""
    code = """import errno,json,socket
from pathlib import Path
results={}
for name,action in [('network',lambda: socket.create_connection(('127.0.0.1',9),timeout=1)),
 ('outside_write',lambda: Path('/private/tmp/kit-offline-denied-probe').open('x'))]:
 try:
  action(); results[name]='UNEXPECTED_SUCCESS'
 except OSError as exc: results[name]=exc.errno
print(json.dumps(results))
"""
    done = isolated([python, '-I', '-c', code], root=root, cwd=root, env=env, timeout=15)
    data = json.loads(done.stdout) if done.returncode == 0 else {}
    if data != {'network': 1, 'outside_write': 1}:
        raise RuntimeError(f'OS isolation not established: {done.returncode} {data} {done.stderr}')
    return data
