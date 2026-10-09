"""KIT-GF-023: stdout is one JSON document, including pre-action failures."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import transfer, transfer_shared
from agentic_project_kit.cli_error_payload import command_error_payload


@pytest.fixture
def external(tmp_path, monkeypatch):
    (tmp_path / '.agentic').mkdir()
    (tmp_path / '.agentic/config.yaml').write_text(
        'kit_schema_version: 2\nprofile: generic\npublication: none\nhygiene:\n  doc_lifecycle: warn\n')
    reference = tmp_path / 'docs/reference/agentic-kit-commands.json'
    reference.parent.mkdir(parents=True)
    reference.write_text('{"commands": []}')
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize('argv', [
    ['branch-create', 'work'], ['branch-delete', 'work'], ['branch-switch', 'work'],
    ['push-current'], ['admin-refresh-pr', '--after-pr', '1'],
    ['pr-create', '--head', 'work', '--title', 'Fix work', '--skip-llm-context-gate'],
    ['pr-create-complete', '--title', 'Fix work', '--skip-llm-context-gate'],
    ['pr-merge-safe', '1', '--skip-llm-context-gate'],
    ['evidence-pr-complete', '--slice', 'test', '--evidence-branch', 'work', '--title', 'Fix work'],
    ['apply'],
])
def test_capability_blockers_are_one_json_document(external, monkeypatch, argv):
    snapshot = SimpleNamespace(capabilities={}, next_action='Acknowledge rules.',
                               rule_snapshot={'fail_closed': False}, primary_state='BLOCKED',
                               reasons=['missing acknowledgement'], rule_acknowledgement={})
    monkeypatch.setattr(transfer_shared, 'build_transfer_state', lambda root: snapshot)
    monkeypatch.setattr(transfer, '_ensure_external_branch_switch_preflight_or_exit', lambda **kw: False,
                        raising=False)
    monkeypatch.setattr(transfer, '_ensure_external_merge_preflight_or_exit', lambda **kw: False)
    monkeypatch.setattr(transfer, '_require_current_communication_context_or_exit', lambda **kw: None)
    monkeypatch.setattr('agentic_project_kit.instruction_lint.lint_transfer_instruction',
                        lambda path: SimpleNamespace(result_status='PASS'))
    result = CliRunner().invoke(app, ['transfer', *argv, '--json'])
    payload = json.loads(result.stdout)
    assert result.exit_code == 2, result.exception
    assert payload['result_status'] == 'BLOCKED'
    assert payload['required_capability'] in {'rules_confirmed', 'run_next_command'}
    assert 'FINAL_SIGNAL=' not in result.stdout


@pytest.mark.parametrize('argv', [
    ['run-and-log'], ['run-sequence-and-log', '--step', ''],
    ['inspect', '--path', 'missing.json'], ['status', '--path', 'missing.json'],
    ['run-local', '--path', 'missing.json'], ['show-last-report'], ['publish-last-report'],
])
def test_early_errors_are_one_json_document(external, argv):
    result = CliRunner().invoke(app, ['transfer', *argv, '--json'])
    payload = json.loads(result.stdout)
    assert result.exit_code in {1, 2}
    assert payload['result_status'] == 'BLOCKED' and payload['error']
    assert payload['returncode'] == result.exit_code and payload['next_action']


@pytest.mark.parametrize('module, function, argv', [
    ('transfer_runtime_initial', 'closeout_transfer', ['closeout']),
    ('transfer_runtime_initial', 'run_remote_next_transfer', ['remote-next']),
])
def test_runtime_failures_are_one_json_document(external, monkeypatch, module, function, argv):
    import importlib

    def fail(*args, **kwargs):
        raise RuntimeError('preserved failure evidence')

    monkeypatch.setattr(importlib.import_module(f'agentic_project_kit.cli_commands.{module}'), function, fail)
    result = CliRunner().invoke(app, ['transfer', *argv, '--json'])
    assert result.exit_code == 1
    assert json.loads(result.stdout)['error'] == 'preserved failure evidence'


def test_error_payload_preserves_quotes_and_newlines():
    payload = command_error_payload('test', ValueError('line 1\n"line 2"'), returncode=2)
    assert json.loads(json.dumps(payload))['error'] == 'line 1\n"line 2"'


def test_every_json_capability_caller_forwards_output_mode():
    root = Path(transfer_shared.__file__).parent
    checked = 0
    for path in root.glob('transfer_*.py'):
        for function in ast.walk(ast.parse(path.read_text())):
            if not isinstance(function, ast.FunctionDef):
                continue
            if 'json_output' not in {a.arg for a in [*function.args.args, *function.args.kwonlyargs]}:
                continue
            for call in ast.walk(function):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'require_capability':
                    assert any(k.arg == 'json_output' and isinstance(k.value, ast.Name)
                               and k.value.id == 'json_output' for k in call.keywords), (path, function.name)
                    checked += 1
    assert checked >= 10
