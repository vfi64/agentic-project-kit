"""KIT-GF-065: external publication policy limits both steps and signed consent."""
import json

import pytest
import yaml

from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions, run_release
from test_release_run import FakeRunner, _workspace


BASE = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2']
POLICIES = [('none', BASE), ('github', [*BASE, 'C4']),
            ('github+pypi', [*BASE, 'C3', 'C4']),
            ('github+pypi+zenodo', [*BASE, 'C3', 'C4', 'D1', 'D2', 'D3', 'D4', 'D5'])]


def configure(root, policy, **release):
    _workspace(root, publication=policy)
    path = root / '.agentic/config.yaml'
    config = yaml.safe_load(path.read_text())
    config['release'].update(release)
    path.write_text(yaml.safe_dump(config))
    reference = root / 'docs/reference/agentic-kit-commands.json'
    reference.parent.mkdir(parents=True)
    reference.write_text('{"commands": []}')


@pytest.mark.parametrize('policy,steps', POLICIES)
@pytest.mark.parametrize('mode', ['per_gate', 'upfront'])
def test_exact_steps_and_gates_in_external_workspace(tmp_path, policy, steps, mode):
    configure(tmp_path, policy, approval=mode, branch_prefix='release/')
    if 'C3' not in steps:
        (tmp_path / '.github/workflows/release.yml').unlink()
    runner = FakeRunner()
    result = run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=runner)
    assert result['result_status'] == 'AWAITING_APPROVAL' and result['current_step'] == 'B4'
    assert result['gate']['branch'] == 'release/1.2.3'
    assert not any('--execute' in c for c in runner.calls)
    if mode == 'upfront':
        plan = result['gate']['release_plan']
        assert plan['steps'] == steps
        assert ('workflow' in plan) == ('C3' in steps)
        assert ('doi_branch' in plan) == ('D4' in steps)
    gates = []
    for _ in range(4):
        if result['result_status'] != 'AWAITING_APPROVAL':
            break
        gates.append(result['current_step'])
        result = run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path, execute=True,
                             expected_signature=result['gate']['approval_signature'], approved_by='owner',
                             consent_source='external-test'), runner=runner)
    assert result['result_status'] == 'PASS', result
    assert result['finished_steps'] == steps
    expected_gates = [s for s in steps if s in {'B4', 'C2', 'C3', 'D4'}]
    assert [a['step_id'] for a in result['approvals']] == expected_gates
    assert gates == (['B4'] if mode == 'upfront' else expected_gates)
    assert any(c[:3] == ['gh', 'workflow', 'run'] for c in runner.calls) == ('C3' in steps)
    assert any('post-release-doi-closeout' in c for c in runner.calls) == ('D4' in steps)


@pytest.mark.parametrize('mode', ['per_gate', 'upfront'])
def test_missing_package_workflow_blocks_before_offer_or_dispatch(tmp_path, mode):
    configure(tmp_path, 'github+pypi', approval=mode)
    (tmp_path / '.github/workflows/release.yml').unlink()
    runner = FakeRunner()
    result = run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=runner)
    for _ in range(2):
        if result['result_status'] != 'AWAITING_APPROVAL':
            break
        result = run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path, execute=True,
                             expected_signature=result['gate']['approval_signature'], approved_by='owner',
                             consent_source='external-test'), runner=runner)
    assert result['result_status'] == 'BLOCKED' and result['current_step'] == 'C3'
    assert 'package-index-workflow-missing:release.yml' in result['blockers']
    assert not any(c[:3] == ['gh', 'workflow', 'run'] for c in runner.calls)
    assert not any(a['step_id'] == 'C3' for a in result['approvals'])


def test_github_without_workflow_never_offers_package_gate(tmp_path):
    configure(tmp_path, 'github', approval='upfront')
    (tmp_path / '.github/workflows/release.yml').unlink()
    run = ReleaseRun(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=FakeRunner())
    result = run._run_or_gate('C3')
    assert result['blockers'] == ['step-not-declared-by-publication-policy']
    assert run.runner.calls == [] and not run.state.get('gates')


@pytest.mark.parametrize('prefix', ['../release/', '/release/', 'release//', '', 'release ', 42])
def test_invalid_branch_prefix_blocks_without_subprocess(tmp_path, prefix):
    configure(tmp_path, 'github', branch_prefix=prefix)
    runner = FakeRunner()
    result = run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=runner)
    assert result['blockers'] == ['invalid-release-branch-prefix']
    assert not runner.calls


def test_default_branch_stays_compatible(tmp_path):
    configure(tmp_path, 'none')
    run = ReleaseRun(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=FakeRunner())
    assert run.branch == 'codex/release-1.2.3' and run.doi_branch == 'codex/release-1.2.3-doi'


@pytest.mark.parametrize('change,blocker', [('publication', 'release-state-publication-policy-drift'),
                                          ('branch', 'release-state-branch-drift')])
def test_resumed_policy_or_branch_drift_blocks_before_actions(tmp_path, change, blocker):
    configure(tmp_path, 'github')
    runner = FakeRunner()
    run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=runner)
    path = tmp_path / '.agentic/config.yaml'
    config = yaml.safe_load(path.read_text())
    if change == 'publication':
        config['publication'] = 'github+pypi'
    else:
        config['release']['branch_prefix'] = 'release/'
    path.write_text(yaml.safe_dump(config))
    runner.calls.clear()
    result = run_release(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=runner)
    assert result['blockers'] == [blocker] and not runner.calls


def test_github_post_check_does_not_wait_for_zenodo(tmp_path, monkeypatch):
    configure(tmp_path, 'github')
    runner = FakeRunner()
    runner.block_step = 'post-release-check'
    monkeypatch.setattr('agentic_project_kit.release_run.time.sleep', lambda _: pytest.fail('unexpected DOI wait'))
    run = ReleaseRun(ReleaseRunOptions(version='1.2.3', root=tmp_path), runner=runner)
    assert run._step_c4()['result_status'] == 'BLOCKED'
    assert sum('post-release-check' in c for c in runner.calls) == 1
    assert json.loads((run.step_dir / 'C4.json').read_text())['returncode'] == 0
