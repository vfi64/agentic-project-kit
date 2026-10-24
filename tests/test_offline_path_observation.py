"""Observation integrity, fail-closed isolation, and callback ancestry boundaries."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

TOOLS = Path(__file__).resolve().parents[1] / 'scripts/offline_path'


def load(name):
    spec = importlib.util.spec_from_file_location('offline_' + name, TOOLS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_direct_edges_do_not_expand_ancestors_or_treat_entry_as_success():
    events = [{'command': 'child', 'parent': {'command': 'parent'},
               'ancestors': [{'command': 'grandparent'}, {'command': 'parent'}]},
              {'command': 'parent', 'parent': None},
              {'command': 'child', 'parent': {'command': 'parent'}}]
    assert load('evidence').edges(events) == [{'caller': 'parent', 'callee': 'child', 'entries': 2}]


@pytest.mark.parametrize('rc,data', [(1, {'result_status': 'PASS'}),
                                     (0, {'result_status': 'BLOCKED'}), (0, {}),
                                     (0, {'result_status': 'FAIL'})])
def test_zero_rc_or_missing_json_cannot_certify_a_step(rc, data):
    assert not load('evidence').acceptable(rc, data)


def test_approval_is_a_plan_not_completion():
    evidence = load('evidence')
    data = {'result_status': 'AWAITING_APPROVAL'}
    assert not evidence.acceptable(0, data)
    assert evidence.acceptable(0, data, plan=True)
    assert evidence.payload('prefix\n{"result_status":"FAIL"}\nsuffix') == {'result_status': 'FAIL'}


@pytest.mark.parametrize('path', ['/', '/Users/owner/project', '/private', '/private/tmp/../../Users'])
def test_policy_refuses_nonowned_roots(path):
    with pytest.raises(ValueError):
        load('isolation').policy(Path(path))


def test_policy_denies_network_and_write_except_owned_root():
    text = load('isolation').policy(Path('/private/tmp/owned-fixture'))
    assert '(deny network*)' in text and '(deny file-write*)' in text
    assert '(allow file-write* (subpath "/private/tmp/owned-fixture"))' in text


def test_tracer_observes_real_callback_with_helper_and_subprocess(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    child = source / 'child.py'
    child.write_text('def child():\n    return 1\nchild()\n')
    outer = source / 'outer.py'
    outer.write_text('import subprocess,sys\ndef parent():\n    def argv(*parts): return list(parts)\n    subprocess.run(argv(sys.executable, sys.argv[1]), check=True)\nparent()\n')
    targets = tmp_path / 'targets.json'
    targets.write_text(json.dumps({'outer.py:2': {'command': 'parent', 'function': 'parent'},
                                  'child.py:1': {'command': 'child', 'function': 'child'}}))
    (tmp_path / 'sitecustomize.py').write_text('import callback_trace\n')
    trace = tmp_path / 'trace.jsonl'
    import os
    env = {**os.environ, 'PYTHONPATH': str(tmp_path) + ':' + str(TOOLS), 'OFFLINE_SOURCE': str(source),
           'OFFLINE_TARGETS': str(targets), 'OFFLINE_TRACE': str(trace)}
    done = subprocess.run([sys.executable, str(outer), str(child)], env=env, capture_output=True)
    assert done.returncode == 0, done.stderr
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert [e['command'] for e in events] == ['parent', 'child']
    assert events[1]['parent'] == {'command': 'parent', 'id': events[0]['id']}
    assert load('evidence').edges(events) == [{'caller': 'parent', 'callee': 'child', 'entries': 1}]


def test_fake_github_refuses_unmodeled_endpoint(tmp_path):
    import os
    db = tmp_path / 'github.json'
    db.write_text('{"next":1,"prs":{}}')
    done = subprocess.run([sys.executable, str(TOOLS / 'fake_gh.py'), 'api', 'repos/sim/kit-sim/unknown'],
                          env={**os.environ, 'FAKE_GH_DB': str(db), 'FAKE_GH_ORIGIN': str(tmp_path)},
                          capture_output=True, text=True)
    assert done.returncode == 2
    assert 'OFFLINE_UNMODELED_API' in done.stderr


def test_explicit_pth_trace_works_with_isolated_python(tmp_path):
    """-I ignores PYTHONPATH and may select a system sitecustomize; .pth import must win."""
    import os
    env = tmp_path / 'venv'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(env)], check=True, capture_output=True)
    candidates = list(env.glob('lib/python*/site-packages')) + list(env.glob('Lib/site-packages'))
    site = candidates[0]
    (site / 'observe.pth').write_text(str(TOOLS) + '\nimport callback_trace\n')
    source = tmp_path / 'source'
    source.mkdir()
    script = source / 'demo.py'
    script.write_text('def demo():\n    pass\ndemo()\n')
    targets = tmp_path / 'targets.json'
    targets.write_text(json.dumps({'demo.py:1': {'command': 'demo', 'function': 'demo'}}))
    trace = tmp_path / 'trace.jsonl'
    python = env / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    done = subprocess.run([str(python), '-I', str(script)], capture_output=True,
                          env={**os.environ, 'OFFLINE_SOURCE': str(source),
                               'OFFLINE_TARGETS': str(targets), 'OFFLINE_TRACE': str(trace)})
    assert done.returncode == 0, done.stderr
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert len(events) == 1 and events[0]['command'] == 'demo'


def test_shared_callback_aliases_are_preserved():
    """The real workflow upload/upload-output aliases must not overwrite each other."""
    targets = load('targets')
    from typer.main import get_command
    from agentic_project_kit.cli import app
    data = targets.collect(get_command(app))
    mapped = [name for entry in data.values() for name in entry['commands']]
    assert 'agentic-kit workflow upload' in mapped
    assert 'agentic-kit workflow upload-output' in mapped
    manifest = json.loads((TOOLS.parents[1] / 'docs/reference/agentic-kit-commands.json').read_text())
    assert set(mapped) == {c['qualified_name'] for c in manifest['commands']}


def test_missing_trace_or_dangling_parent_is_not_complete():
    evidence = load('evidence')
    assert evidence.trace_findings([], [{'name': 'finish'}]) == ['untraced steps: finish']
    events = [{'id': '1', 'command': 'child', 'step': 'finish',
               'parent': {'id': 'unknown', 'command': 'parent'}}]
    assert evidence.trace_findings(events, [{'name': 'finish'}]) == ['missing or inconsistent callback parent']
    events.insert(0, {'id': 'unknown', 'command': 'parent', 'step': 'finish', 'parent': None})
    assert evidence.trace_findings(events, [{'name': 'finish'}]) == []
    assert evidence.normalize_events(events) == [
        {'id': 0, 'command': 'parent', 'step': 'finish', 'parent': None},
        {'id': 1, 'command': 'child', 'step': 'finish', 'parent': 0}]


def test_timeout_kills_the_owned_process_group_and_retains_output(monkeypatch, tmp_path):
    isolation = load('isolation')
    calls = []

    class Process:
        pid = 12345
        returncode = -9
        attempts = 0

        def communicate(self, timeout=None):
            self.attempts += 1
            if self.attempts == 1:
                raise subprocess.TimeoutExpired(['demo'], timeout)
            return 'partial stdout', 'partial stderr'

    monkeypatch.setattr(isolation.subprocess, 'Popen', lambda *a, **kw: Process())
    monkeypatch.setattr(isolation.os, 'killpg', lambda *args: calls.append(args))
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        isolation.isolated(['demo'], root=tmp_path, cwd=tmp_path, env={}, timeout=1)
    assert calls == [(12345, isolation.signal.SIGKILL)]
    assert caught.value.stdout == 'partial stdout'
    assert caught.value.stderr == 'partial stderr'
