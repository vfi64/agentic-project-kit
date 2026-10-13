import os
import subprocess
import sys
import pytest
from agentic_project_kit.release_publish_orchestration import ReleasePublishCheck, ReleasePublishPlan
from agentic_project_kit.release_run import _release_publish_ok
from test_external_rule_registry import installed_kit as installed_kit, external as external


@pytest.mark.parametrize("check_status", ["PASS", "SKIP", "FAIL", "WARN", "UNKNOWN"])
def test_runner_consumes_orchestration_verdict(check_status):
    plan = ReleasePublishPlan("1.2.3", "v1.2.3", ".", "dry-run",
                              (ReleasePublishCheck("control", check_status, "fixture"),), (), False)
    assert _release_publish_ok(plan.as_dict()) == plan.ok == (check_status in {"PASS", "SKIP"})


@pytest.mark.parametrize("payload", [None, {}, {"status":"FAIL", "blocker_count":0},
    {"status":"PASS", "blocker_count":1}, {"status":"PASS", "blocker_count":"bad"},
    {"status":"PASS", "blocker_count":False}, {"status":"PASS"}])
def test_malformed_or_blocking_publish_summary_never_passes(payload):
    assert not _release_publish_ok(payload)


def test_installed_external_resume_c1_to_c2_keeps_b4_consent(external, installed_kit):
    root, cli = external
    script = r'''
import json, subprocess, yaml
from pathlib import Path
import agentic_project_kit.release_run as rr
from agentic_project_kit.release_publish_orchestration import evaluate_release_publish_plan
root=Path.cwd()
config=root/'.agentic/config.yaml'
configuration=yaml.safe_load(config.read_text());configuration['publication']='github';configuration['release']={'approval':'upfront'}
config.write_text(yaml.safe_dump(configuration))
calls=[]
def publish_observations(args, cwd):
    if 'release-prep' in args: return 0, json.dumps({'changed_paths':[]})
    if list(args)==['git','rev-parse','HEAD']: return 0, 'abc123\n'
    return 0, 'PASS\n'
def runner(argv,cwd):
    argv=list(argv);calls.append(argv)
    if argv==['git','rev-parse','HEAD']: output='abc123\n'
    elif argv==['git','status','--porcelain']: output=' M pyproject.toml\n'
    elif 'release-publish' in argv:
        # Real external applicability and summary, dry only even for C2.
        plan=evaluate_release_publish_plan(root,version='1.2.3',runner=publish_observations)
        assert {c.name for c in plan.checks if c.status=='SKIP'}=={'docs audit','command reference check'}
        assert plan.ok and not plan.execute_enabled
        output=json.dumps(plan.as_dict())
    elif 'finish' in argv and '--dry-run' in argv: output=json.dumps({'result_status':'PLANNED'})
    elif 'release-status' in argv: output=json.dumps({'result_status':'PASS','current_state':'current_verified'})
    else: output=json.dumps({'result_status':'PASS'})
    return subprocess.CompletedProcess(argv,0,output,'')
options=rr.ReleaseRunOptions(version='1.2.3',root=root,approved_by='fixture-owner',consent_source='offline regression')
preview=rr.run_release(options,runner=runner)
assert preview['current_step']=='B4'
# Reproduce the old C1 validator without fabricating persisted state/approval.
current_verdict=rr._release_publish_ok
rr._release_publish_ok=lambda p: p.get('status')=='PASS' and all(c['status']=='PASS' for c in p['checks'])
blocked=rr.run_release(rr.ReleaseRunOptions(**{**options.__dict__,'execute':True,'expected_signature':preview['gate']['approval_signature']}),runner=runner)
assert blocked['result_status']=='BLOCKED' and blocked['current_step']=='C1'
state_path=rr.ReleaseRun(options,runner=runner).state_path
before=json.loads(state_path.read_text())
assert before['approvals'][0]['step_id']=='B4' and 'B4' in before['finished_steps']
rr._release_publish_ok=current_verdict
calls.clear()
resumed=rr.run_release(options,runner=runner)
assert resumed['result_status']=='PASS',resumed
publish_calls=[c for c in calls if 'release-publish' in c]
assert len(publish_calls)==2 and '--dry-run' in publish_calls[0] and '--execute' in publish_calls[1]
assert not any('finish' in c for c in calls)
after=json.loads(state_path.read_text())
assert after['approvals'][0]==before['approvals'][0]
assert after['release_consent']==before['release_consent']
assert {a['step_id'] for a in after['approvals']}=={'B4','C2'}
assert after['step_results']['C1']['result_status']==after['step_results']['C2']['result_status']=='PASS'
assert not (root/'tests').exists() and not (root/'docs/DOCUMENTATION_REGISTRY.yaml').exists()
print('PASS')
'''
    result=subprocess.run([sys.executable,"-c",script],cwd=root,
        env={**os.environ,"PYTHONPATH":str(installed_kit)},capture_output=True,text=True)
    assert result.returncode==0,result.stdout[-1500:]+result.stderr[-1500:]
    assert result.stdout.strip()=="PASS"
