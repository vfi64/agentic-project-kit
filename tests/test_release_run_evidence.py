import json
import os
import subprocess
import sys
import pytest
from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions, run_release
from agentic_project_kit.release_run_evidence import evidence_path, snapshot
from test_release_run import FakeRunner, _workspace
from test_external_rule_registry import installed_kit as installed_kit, external as external


def prepared(tmp_path):
    _workspace(tmp_path)
    config = tmp_path / ".agentic/config.yaml"
    config.write_text(
        config.read_text().replace("release:\n", "release:\n  evidence_archive: true\n")
    )
    run = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=FakeRunner())
    run.state = {
        "schema_version": 1,
        "version": "1.2.3",
        "finished_steps": list(run.sequence),
        "step_results": {
            s: {"result_status": "PASS", "returncode": 0, "blockers": []} for s in run.sequence
        },
        "gates": {},
        "approvals": [
            {
                "step_id": "D4",
                "approved_by": "owner",
                "consent_source": "work order",
                "gate": {
                    "version": "1.2.3",
                    "tag": "v1.2.3",
                    "approval_signature": "doi-signature",
                    "target_commit": "abc123",
                },
            }
        ],
    }
    run._save_state()
    return run


def test_archive_requires_signature_and_matches_actual_completed_steps(tmp_path):
    run = prepared(tmp_path)
    options = ReleaseRunOptions(
        version="1.2.3", root=tmp_path, approved_by="owner", consent_source="work order"
    )
    first = run_release(options, runner=run.runner)
    assert first["result_status"] == "AWAITING_APPROVAL" and first["current_step"] == "E1"
    path = tmp_path / evidence_path("1.2.3")
    assert not path.exists()
    wrong = run_release(
        ReleaseRunOptions(**{**options.__dict__, "execute": True, "expected_signature": "wrong"}),
        runner=run.runner,
    )
    assert wrong["result_status"] == "BLOCKED" and not path.exists()
    final = run_release(
        ReleaseRunOptions(
            **{
                **options.__dict__,
                "execute": True,
                "expected_signature": first["gate"]["approval_signature"],
            }
        ),
        runner=run.runner,
    )
    assert final["result_status"] == "PASS"
    data = json.loads(path.read_text())
    assert data["steps"] == run.state["step_results"]
    assert data["approvals"][0]["signature"] == "doi-signature"
    assert "stdout" not in path.read_text() and str(tmp_path) not in path.read_text()
    assert any("work" in c and "finish" in c and "--execute" in c for c in run.runner.calls)
    before = len(run.runner.calls)
    again = run_release(options, runner=run.runner)
    assert again["result_status"] == "PASS" and len(run.runner.calls) == before


def test_incomplete_evidence_never_becomes_pass(tmp_path):
    run = prepared(tmp_path)
    run.state["step_results"]["C3"]["result_status"] = "BLOCKED"
    with pytest.raises(ValueError):
        snapshot(run)
    run._save_state()
    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=run.runner)
    assert result["result_status"] == "BLOCKED"
    assert not (tmp_path / evidence_path("1.2.3")).exists()
    with pytest.raises(ValueError):
        evidence_path("../secret")


def test_existing_archive_is_preserved_when_different(tmp_path):
    run = prepared(tmp_path)
    opts = ReleaseRunOptions(version="1.2.3", root=tmp_path)
    plan = run_release(opts, runner=run.runner)
    p = tmp_path / evidence_path("1.2.3")
    p.parent.mkdir(parents=True)
    p.write_text("preserve evidence")
    result = run_release(
        ReleaseRunOptions(
            version="1.2.3",
            root=tmp_path,
            execute=True,
            expected_signature=plan["gate"]["approval_signature"],
        ),
        runner=run.runner,
    )
    assert result["result_status"] == "BLOCKED" and p.read_text() == "preserve evidence"


def test_installed_wheel_external_archive_route(external, installed_kit):
    root, cli = external
    script = """
import json, subprocess
from pathlib import Path
from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions, run_release
root = Path.cwd()
config = root / '.agentic/config.yaml'
config.write_text(config.read_text() + '\\nrelease:\\n  evidence_archive: true\\n')
calls = []
def runner(argv, cwd):
    calls.append(list(argv))
    if list(argv) == ['git', 'rev-parse', 'HEAD']:
        return subprocess.CompletedProcess(argv, 0, 'abc123\\n', '')
    return subprocess.CompletedProcess(argv, 0, json.dumps({'result_status':'PASS'}), '')
options = ReleaseRunOptions(version='1.2.3', root=root, approved_by='test-owner', consent_source='offline regression')
run = ReleaseRun(options, runner=runner)
run.state = {'version':'1.2.3', 'finished_steps':list(run.sequence), 'step_results':{s:{'result_status':'PASS','returncode':0,'blockers':[]} for s in run.sequence}}
run._save_state()
plan = run_release(options, runner=runner)
assert plan['current_step'] == 'E1' and plan['result_status'] == 'AWAITING_APPROVAL'
assert not (root/'docs/reports/release/release-run-1.2.3.json').exists()
final = run_release(ReleaseRunOptions(**{**options.__dict__, 'execute':True, 'expected_signature':plan['gate']['approval_signature']}), runner=runner)
assert final['result_status'] == 'PASS'
data = json.loads((root/'docs/reports/release/release-run-1.2.3.json').read_text())
assert data['steps'] == run.state['step_results']
assert any('finish' in c and '--execute' in c for c in calls)
assert not any('doc-registry' in c or 'release-publish' in c for c in calls)
print('PASS')
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(installed_kit)},
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr[-1500:]
    assert result.stdout.strip() == "PASS"
