"""Contract figures must stay source-bound and observed edges retain their limited scope."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from agentic_project_kit.site_workflow_figures import collect_figures, public_observation, render_figures, svg

ROOT = Path(__file__).resolve().parents[1]


def fixture(root):
    for path in ('docs/reference/agentic-kit-commands.json', 'docs/reference/HUMAN_WORKFLOW_COMMANDS.md',
                 'src/agentic_project_kit/successor_handoff_package.py',
                 'src/agentic_project_kit/cli_commands/human_workflows.py'):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    import shutil
    shutil.copytree(ROOT / 'site/templates/figures', root / 'site/templates/figures', dirs_exist_ok=True)
    return root


def test_contract_figures_are_deterministic_and_have_text_alternatives(tmp_path):
    data = collect_figures(fixture(tmp_path))
    assert [f['id'] for f in data['figures']] == ['G2', 'G3']
    assert data == collect_figures(tmp_path)
    assert data['figures'][0]['nodes'][0]['label'] == 'Plan'
    assert 'source_manifest.json' in data['figures'][1]['nodes'][1]['detail']
    html = render_figures(data)
    for figure in data['figures']:
        parsed = ET.fromstring(svg(figure))
        mobile = ET.fromstring(svg(figure, compact=True))
        assert mobile.attrib['width'] == '380'
        assert svg(figure, compact=True) != svg(figure)
        assert parsed.attrib['role'] == 'img'
        assert parsed.find('{http://www.w3.org/2000/svg}desc') is not None
        for node in figure['nodes']:
            assert node['label'] in html
    assert 'not observed nested calls' in html


def test_manifest_help_change_reaches_figure_and_source_hash(tmp_path):
    root = fixture(tmp_path)
    before = collect_figures(root)
    path = root / 'docs/reference/agentic-kit-commands.json'
    data = json.loads(path.read_text())
    next(c for c in data['commands'] if c['path'] == ['work', 'finish'])['when_to_use'] = 'New <meaning>'
    path.write_text(json.dumps(data))
    after = collect_figures(root)
    assert before['sources'] != after['sources']
    assert after['figures'][0]['nodes'][0]['detail'].startswith('New <meaning>')
    assert 'New &lt;meaning&gt;' in svg(after['figures'][0])


def test_missing_command_or_changed_package_shape_blocks(tmp_path):
    root = fixture(tmp_path)
    path = root / 'docs/reference/HUMAN_WORKFLOW_COMMANDS.md'
    path.write_text('no commands')
    with pytest.raises(ValueError, match='command missing'):
        collect_figures(root)
    path.write_bytes((ROOT / path.relative_to(root)).read_bytes())
    path = root / 'src/agentic_project_kit/successor_handoff_package.py'
    path.write_text(path.read_text().replace('ws.package_file("successor_prompt.md")', 'ws.package_file("new_prompt.md")'))
    with pytest.raises(ValueError, match='shape changed'):
        collect_figures(root)


def test_public_observation_retains_incomplete_and_whitelists_fields():
    data = {'source_commit': 'a' * 40, 'status': 'INCOMPLETE', 'direct_edges': [],
            'secret': '/Users/private/token', 'steps': [{'name': 'example', 'rc': 0, 'result_status': 'PASS', 'argv': ['secret']}], 'stop_reason': 'local path'}
    output = public_observation(data)
    assert output['status'] == 'INCOMPLETE'
    assert 'private' not in json.dumps(output)
    assert 'Entry does not imply successful completion' in output['boundary']
    data['source_commit'] = 'main'
    with pytest.raises(ValueError, match='exact source commit'):
        public_observation(data)


def test_invalid_or_executable_edge_rejected():
    with pytest.raises(ValueError, match='edge'):
        public_observation({'source_commit': 'a' * 40, 'status': 'INCOMPLETE', 'direct_edges': [
            {'caller': '<script>', 'callee': 'agentic-kit check', 'entries': 1}]})


def test_observed_figure_is_bound_to_reconstructible_callback_receipts(tmp_path):
    from hashlib import sha256
    from agentic_project_kit.site_workflow_figures import OBSERVATION, checked_observation
    directory = tmp_path / Path(OBSERVATION).parent
    directory.mkdir(parents=True)
    events = [{'id': 0, 'parent': None, 'command': 'agentic-kit work start', 'step': 'start'},
              {'id': 1, 'parent': 0, 'command': 'agentic-kit rules acknowledge', 'step': 'start'}]
    raw = json.dumps(events).encode()
    (directory / 'callbacks.json').write_bytes(raw)
    data = {'source_commit': 'a' * 40, 'status': 'BOUNDED_COMPLETE', 'callback_entries': 2,
            'publication_boundary': {'gate': 'C2', 'approved': False},
            'normalized_trace_sha256': sha256(raw).hexdigest(), 'direct_edges': [
                {'caller': 'agentic-kit work start', 'callee': 'agentic-kit rules acknowledge', 'entries': 1}]}
    path = directory / 'observation.json'
    path.write_text(json.dumps(data))
    observation = checked_observation(tmp_path)
    assert observation['direct_edges'] == data['direct_edges']
    data['direct_edges'][0]['entries'] = 2
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='disagree'):
        checked_observation(tmp_path)
    (directory / 'callbacks.json').write_text('[]')
    with pytest.raises(ValueError, match='digest mismatch'):
        checked_observation(tmp_path)


@pytest.mark.parametrize('old,new', [('"PLANNED"', '"NEW_STATE"'),
                                    ('2 if result_status', '3 if result_status'),
                                    ('if blockers:', 'if not blockers:'),
                                    ('typer.Option(True, "--dry-run/--execute"', 'typer.Option(False, "--dry-run/--execute"')])
def test_state_or_default_changes_block_layout(tmp_path, old, new):
    root = fixture(tmp_path)
    p = root / 'src/agentic_project_kit/cli_commands/human_workflows.py'
    assert old in p.read_text()
    p.write_text(p.read_text().replace(old, new))
    with pytest.raises(ValueError, match='changed'):
        collect_figures(root)


def test_selected_execution_not_plan_or_release_and_all_bindings():
    from agentic_project_kit.site_figure_cells import selected_finish
    events = json.loads((ROOT / 'docs/reports/offline_path_20261024/callbacks.json').read_text())
    cells = selected_finish(events)
    assert len(cells['calls']) == 14
    assert cells['nested_entries'] == 31
    assert cells['acknowledgements'] == 4
    data = collect_figures(ROOT)
    figure = data['figures'][-1]
    for compact in (False, True):
        text = svg(figure, compact=compact)
        assert '31 nested entries' in text
        assert 'no release publication' in text.lower() or 'release publication was not observed' in text.lower()
        assert 'K0c' in text
        assert 'data-bind' not in text
    assert '<details><summary>' in render_figures(data)
    children = [e for e in events if e['parent'] is not None and e['step'] == 'finish work']
    # Same count, changed order must fail; plans/dry-runs elsewhere cannot hide it.
    first = next(e for e in children if e['command'] == 'agentic-kit transfer protected-diff-plan')
    first['command'] = 'agentic-kit transfer repo-status'
    with pytest.raises(ValueError, match='sequence changed'):
        selected_finish(events)


def test_template_slot_drift_blocks(tmp_path):
    import shutil
    shutil.copytree(ROOT / 'site/templates/figures', tmp_path / 'site/templates/figures')
    p = tmp_path / 'site/templates/figures/G2.svg'
    p.write_text(p.read_text().replace('data-bind="planned"', 'data-bind="unknown"'))
    with pytest.raises(ValueError, match='slots changed'):
        svg(collect_figures(ROOT)['figures'][0], root=tmp_path)


def test_nested_count_is_derived_without_fixed_callback_ids():
    from agentic_project_kit.site_figure_cells import selected_finish
    events = json.loads((ROOT / 'docs/reports/offline_path_20261024/callbacks.json').read_text())
    parent = next(e['id'] for e in events if e['command'] == 'agentic-kit transfer pr-create-complete' and e['step'] == 'finish work')
    events.append({'id': len(events), 'parent': parent, 'command': 'agentic-kit check', 'step': 'finish work'})
    assert selected_finish(events)['nested_entries'] == 32


def test_package_cells_and_accessible_description_share_source():
    data = collect_figures(ROOT)
    figure = data['figures'][1]
    assert figure['cells']['file-successor_context.yaml'] == 'project context'
    for compact in (False, True):
        text = svg(figure, compact=compact)
        assert 'successor_context.yaml' in text
        assert 'fix its cause' in text
        assert 'not rely on chat memory' in text
