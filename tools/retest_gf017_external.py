"""Run an installed Kit CLI with strict local GitHub transport doubles."""

from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile

import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--kit-python", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
options = parser.parse_args()
py = options.kit_python.absolute()
base = Path(tempfile.mkdtemp(prefix="kit-gf017-external-")).resolve()
log = base / "commands.jsonl"


def run(args, cwd=None, env=None, expect=0):
    p = subprocess.run(
        list(map(str, args)), cwd=cwd or base, env=env, text=True, capture_output=True, timeout=180
    )
    with log.open("a") as f:
        f.write(
            json.dumps(
                {
                    "argv": list(map(str, args)),
                    "rc": p.returncode,
                    "stdout": p.stdout,
                    "stderr": p.stderr,
                }
            )
            + "\n"
        )
    if expect is not None:
        assert p.returncode == expect, (p.returncode, p.stdout[-1500:], p.stderr[-1000:])
    return p


version = run(
    [
        py,
        "-I",
        "-c",
        'from importlib.metadata import version; print(version("agentic-project-kit"))',
    ]
).stdout.strip()
venv = py.parent.parent
ws = base / "consumer"
ws.mkdir()
cli = [py, "-I", "-m", "agentic_project_kit.cli"]
run([*cli, "workspace", "init", "--root", ws, "--execute"])
run([*cli, "commands", "sync-entrypoints", "--root", ws, "--execute", "--json"])
(ws / ".gitignore").write_text(".agentic/tmp/\n.agentic/rule_ack/\n")
realgit = shutil.which("git")
run([realgit, "init", "-b", "feature/gf017"], cwd=ws)
run([realgit, "add", "."], cwd=ws)
run(
    [
        realgit,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "External fixture",
    ],
    cwd=ws,
)
run(
    [realgit, "remote", "add", "origin", "https://github.com/fixture-owner/gf017-consumer.git"],
    cwd=ws,
)
head = run([realgit, "rev-parse", "HEAD"], cwd=ws).stdout.strip()
fake = base / "transport"
fake.mkdir()
data = base / "remote.json"
calls = base / "remote-calls.jsonl"
merged = base / "merged"
data.write_text(json.dumps({"head": head, "conclusion": "SUCCESS"}))
gh = fake / "gh"
gh.write_text(
    """#!__PY__
import json,os,sys
from pathlib import Path
a=sys.argv[1:]; d=json.loads(Path(os.environ['GF017_REMOTE']).read_text())
with Path(os.environ['GF017_CALLS']).open('a') as f:f.write(json.dumps(a)+'\\n')
marker=Path(os.environ['GF017_MERGED'])
if a[:2]==['pr','view']:
    payload={'number':42,'baseRefName':'main','baseRefOid':'a'*40,'headRefName':'feature/gf017','headRefOid':d['head'],
             'state':'MERGED' if marker.exists() else 'OPEN','url':'https://github.com/fixture-owner/gf017-consumer/pull/42',
             'mergeStateStatus':'CLEAN','mergedAt':'2026-10-10T00:00:00Z' if marker.exists() else None,
             'mergeCommit':{'oid':'b'*40} if marker.exists() else None,
             'statusCheckRollup':[{'name':'test','status':'COMPLETED','conclusion':d['conclusion']}]}
    print(json.dumps(payload));sys.exit(0)
if a[:2]==['pr','merge']:
    assert '--match-head-commit' in a and a[a.index('--match-head-commit')+1]==d['head']
    marker.write_text('fixture merge receipt');print('merged fixture PR');sys.exit(0)
if a[:2]==['run','list']:
    print(json.dumps([{'databaseId':71,'name':'CI','status':'completed','conclusion':'success','url':'https://github.com/fixture-owner/gf017-consumer/actions/runs/71'}]));sys.exit(0)
if a and a[0]=='api' and a[-1].endswith('/jobs'):
    print(json.dumps({'total_count':1,'jobs':[]}));sys.exit(0)
print('Unexpected remote call: '+repr(a),file=sys.stderr);sys.exit(99)
""".replace("__PY__", str(py))
)
gh.chmod(0o755)
git = fake / "git"
git.write_text(
    """#!__PY__
import os,sys
if sys.argv[1:2]==['ls-remote']:
    print(os.environ['GF017_HEAD']+'\\tHEAD');sys.exit(0)
if any(x in sys.argv[1:] for x in ['fetch','push','pull','clone','submodule']):
    print('Unexpected network Git command',file=sys.stderr);sys.exit(99)
os.execv('__GIT__',['__GIT__',*sys.argv[1:]])
""".replace("__PY__", str(py)).replace("__GIT__", realgit)
)
git.chmod(0o755)
env = {
    **os.environ,
    "PATH": str(fake) + os.pathsep + str(venv / "bin") + os.pathsep + os.environ["PATH"],
    "GF017_REMOTE": str(data),
    "GF017_CALLS": str(calls),
    "GF017_MERGED": str(merged),
    "GF017_HEAD": head,
    "PYTHONPATH": "/nonexistent-kit-source",
}
outbox = ws / ".agentic/transfer/outbox/last_result.txt"
latest = ws / ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json"
for p in (outbox, latest):
    if p.exists():
        p.unlink()
assert not (ws / "tests").exists() and not (ws / "docs/DOCUMENTATION_REGISTRY.yaml").exists()
assert (ws / "docs/reference/agentic-kit-commands.json").exists()
missing = run([*cli, "transfer", "require-fresh-llm-context", "--json"], cwd=ws, env=env, expect=2)
missing_payload = json.loads(missing.stdout)
assert {"outbox_missing", "latest_handoff_report_missing"} <= set(missing_payload["blockers"])
args = [*cli, "transfer", "pr-merge-safe", "42", "--expected-head-sha", head, "--json"]
positive = run(args, cwd=ws, env=env, expect=None)
result = {
    "version": version,
    "workspace": str(ws),
    "log": str(log),
    "head": head,
    "positive_rc": positive.returncode,
    "positive_stdout": positive.stdout,
    "positive_stderr": positive.stderr,
    "merged": merged.exists(),
}
if merged.exists():
    merged.unlink()
    data.write_text(json.dumps({"head": head, "conclusion": "FAILURE"}))
    negative = run(args, cwd=ws, env=env, expect=None)
    result["red_rc"] = negative.returncode
    result["red_merged"] = merged.exists()
    result["red_stdout"] = negative.stdout
    data.write_text(json.dumps({"head": "c" * 40, "conclusion": "SUCCESS"}))
    stale = run(args, cwd=ws, env=env, expect=None)
    result["stale_rc"] = stale.returncode
    result["stale_merged"] = merged.exists()
    result["stale_stdout"] = stale.stdout
    data.write_text(json.dumps({"head": head, "conclusion": "SUCCESS"}))
    (ws / "product.py").write_text("print('substantive change')\n")
    dirty = run(args, cwd=ws, env=env, expect=2)
    result["dirty_rc"] = dirty.returncode
    result["dirty_merged"] = merged.exists()
    assert "external_dirty_worktree" in dirty.stdout
result["missing_blockers"] = missing_payload["blockers"]
result["remote_calls"] = calls.read_text() if calls.exists() else ""
options.output.parent.mkdir(parents=True, exist_ok=True)
options.output.write_text(json.dumps(result, indent=2) + "\n")
print(
    json.dumps(
        {
            k: result.get(k)
            for k in [
                "version",
                "workspace",
                "positive_rc",
                "merged",
                "red_rc",
                "red_merged",
                "stale_rc",
                "stale_merged",
                "dirty_rc",
                "dirty_merged",
            ]
        }
    )
)

assert result["positive_rc"] == 0 and result["merged"]
assert result.get("red_rc") != 0 and not result.get("red_merged")
assert result.get("stale_rc") == 2 and not result.get("stale_merged")
assert result.get("dirty_rc") == 2 and not result.get("dirty_merged")
