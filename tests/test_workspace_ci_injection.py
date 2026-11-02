"""An initialized workspace can explicitly opt into its missing managed CI."""
import json

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.workspace_ci_update import (
    WorkspaceCiUpdateError, build_workspace_ci_update_plan, execute_workspace_ci_update,
    managed_ci_template_text, managed_injected_ci_text,
)


@pytest.fixture
def workspace(tmp_path):
    manifest = tmp_path / '.agentic/config.yaml'
    manifest.parent.mkdir()
    manifest.write_text('kit_schema_version: 2\nproject: {name: fixture, type: generic}\n')
    source = tmp_path / '.agentic/ci/agentic-gate.yaml'
    source.parent.mkdir()
    source.write_text(managed_ci_template_text())
    return tmp_path


def test_cli_injects_only_after_explicit_execute_and_is_idempotent(workspace):
    command = ['workspace', 'ci-update', '--root', str(workspace), '--inject-ci', '--json']
    target = workspace / '.github/workflows/agentic-gate.yaml'
    preview = CliRunner().invoke(app, command)
    assert preview.exit_code == 0, preview.output
    assert json.loads(preview.output)['changed_paths'] == ['.github/workflows/agentic-gate.yaml']
    assert not target.exists()
    result = CliRunner().invoke(app, command + ['--execute'])
    assert result.exit_code == 0, result.output
    assert target.read_text() == managed_injected_ci_text()
    repeat = CliRunner().invoke(app, command + ['--execute'])
    assert repeat.exit_code == 0, repeat.output
    assert json.loads(repeat.output)['changed_paths'] == []


def test_default_never_creates_missing_workflow(workspace):
    plan = build_workspace_ci_update_plan(workspace)
    execute_workspace_ci_update(plan)
    assert not (workspace / '.github').exists()


@pytest.mark.parametrize('custom', ['source', 'workflow', 'managed_workflow'])
def test_opt_in_preserves_custom_files(workspace, custom):
    source = workspace / '.agentic/ci/agentic-gate.yaml'
    target = workspace / '.github/workflows/agentic-gate.yaml'
    if custom == 'source':
        source.write_text('name: custom source\n')
    else:
        target.parent.mkdir(parents=True)
        target.write_text(('' if custom == 'workflow' else managed_injected_ci_text()) + 'name: custom\n')
    before = {p.relative_to(workspace): p.read_bytes() for p in workspace.rglob('*') if p.is_file()}
    result = CliRunner().invoke(app, ['workspace', 'ci-update', '--root', str(workspace),
                                     '--inject-ci', '--execute', '--json'])
    assert result.exit_code == 2, result.output
    assert json.loads(result.output)['result_status'] == 'BLOCKED'
    assert before == {p.relative_to(workspace): p.read_bytes() for p in workspace.rglob('*') if p.is_file()}


def test_core_rechecks_new_workflow_before_writing(workspace):
    plan = build_workspace_ci_update_plan(workspace, inject_ci=True)
    target = workspace / '.github/workflows/agentic-gate.yaml'
    target.parent.mkdir(parents=True)
    target.write_text('name: appeared after planning\n')
    with pytest.raises(WorkspaceCiUpdateError):
        execute_workspace_ci_update(plan)
    assert target.read_text() == 'name: appeared after planning\n'


def test_core_creates_both_missing_managed_files(workspace):
    source = workspace / '.agentic/ci/agentic-gate.yaml'
    source.unlink()
    plan = build_workspace_ci_update_plan(workspace, inject_ci=True)
    assert plan.changed_paths == ('.agentic/ci/agentic-gate.yaml', '.github/workflows/agentic-gate.yaml')
    execute_workspace_ci_update(plan)
    assert source.read_text() == managed_ci_template_text()
    assert (workspace / '.github/workflows/agentic-gate.yaml').read_text() == managed_injected_ci_text()


def test_opt_in_refuses_a_symlinked_workflow_parent(workspace, tmp_path_factory):
    outside = tmp_path_factory.mktemp('outside-ci')
    (workspace / '.github').symlink_to(outside, target_is_directory=True)
    plan = build_workspace_ci_update_plan(workspace, inject_ci=True)
    assert plan.result_status == 'BLOCKED'
    assert plan.blockers[0].reason == 'unsafe_managed_ci_path'
    assert not list(outside.iterdir())
