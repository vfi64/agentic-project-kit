"""Accessible workflow figures projected from current contracts, not inferred call graphs."""
from __future__ import annotations

import ast
from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path

from agentic_project_kit.site_figure_cells import HUMAN_SOURCE, PACKAGE_LABELS, PROTECTION_REPORT, finish_contract, protection_binding, selected_finish
from agentic_project_kit.site_figure_templates import render_template

MANIFEST = 'docs/reference/agentic-kit-commands.json'
HUMAN = 'docs/reference/HUMAN_WORKFLOW_COMMANDS.md'
HANDOFF = 'src/agentic_project_kit/successor_handoff_package.py'
OBSERVATION = 'docs/reports/offline_path_20261024/observation.json'
# Editorial reading order. Membership and help remain manifest-owned; these are not execution edges.
WORK = ('work start', 'work check', 'work finish', 'transfer chat-switch-complete')


def collect_figures(root: Path) -> dict:
    manifest = json.loads((root / MANIFEST).read_text())
    commands = {c['qualified_name']: c for c in manifest['commands']}
    nodes = []
    guide = (root / HUMAN).read_text()
    for name in WORK:
        full = 'agentic-kit ' + name
        if full not in commands or full not in guide:
            raise ValueError(f'workflow figure command missing from manifest or guide: {full}')
        command = commands[full]
        nodes.append({'label': name, 'detail': command['when_to_use'],
                      'surface': command['surface'], 'safety': command['safety']})
    tree = ast.parse((root / HANDOFF).read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == '_generated_handoff_projection_paths')
    files = sorted({call.args[0].value for call in ast.walk(function) if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute) and call.func.attr == 'package_file'
                    and call.args and isinstance(call.args[0], ast.Constant)})
    required = {'execution_contract.json', 'source_manifest.json', 'successor_context.yaml',
                'successor_prompt.md', 'validation_report.json'}
    if set(files) != required:
        raise ValueError('handoff package shape changed; review the public figure')
    states = finish_contract(root)
    result = {'schema_version': 1, 'kind': 'workflow_figure_projection',
              'boundary': 'G2/G3 are contract views, not observed nested calls. G0 shows one observed work-finish execution.',
              'sources': {p: sha256((root / p).read_bytes()).hexdigest() for p in (MANIFEST, HUMAN, HANDOFF, HUMAN_SOURCE)},
              'figures': [
                  {'id': 'G2', 'title': 'A bounded work cycle', 'nodes': [
                       {'label': 'Plan', 'detail': nodes[2]['detail'] + ' Dry run by default; successful prechecks yield PLANNED.'},
                       {'label': 'Approve', 'detail': 'Review the plan, then rerun with --execute.'},
                       {'label': 'Execute', 'detail': 'Default merge path: commit, handoff refresh, push and PR closeout. Failed prerequisites block subsequent closeout stages; diagnostics may still run.'},
                       {'label': 'Record and continue', 'detail': 'All steps successful: PASS. Otherwise BLOCKED, rc 2; inspect and fix the cause before planning again. Continue from the repository successor package.'}],
                   'boundary': 'Make the selected change between start and check. Review the finish plan before execution; blocked or failed results stop the cycle.'},
                  {'id': 'G3', 'title': 'Context survives the chat', 'nodes': [
                      {'label': 'Repository sources', 'detail': 'source_manifest.json records the inputs.'},
                      {'label': 'Successor package', 'detail': ', '.join(files)},
                      {'label': 'Validate, then continue', 'detail': 'Read validation_report.json and execution_contract.json. A failed handoff blocks continuation.'},
                      {'label': 'Successor chat', 'detail': 'Use successor_context.yaml and successor_prompt.md; inspect current repository state.'}],
                   'boundary': 'A generated package preserves inspectable context. It does not prove requirements or software correctness.'}]}
    if (root / OBSERVATION).exists():
        result['observation'] = checked_observation(root)
        result['protection'] = protection_binding(root)
        result['sources'][PROTECTION_REPORT] = sha256((root / PROTECTION_REPORT).read_bytes()).hexdigest()
        events = json.loads((root / Path(OBSERVATION).parent / 'callbacks.json').read_text())
        selected = selected_finish(events)
        figure = observed_figure(result['observation'])
        figure.update(title='What work finish actually ran', nodes=[
            {'label': str(i + 1) + '. ' + label, 'detail': 'Observed direct callback entry.'}
            for i, label in enumerate(selected['calls'])])
        figure['cells'] = {f'call-{i+1}': label for i, label in enumerate(selected['calls'])}
        figure['cells'].update({f'number-{i+1}': str(i+1) for i in range(len(selected['calls']))})
        figure['cells'].update(
            provenance='Offline sandbox · ' + result['observation']['source_commit'][:12] + ' · local Git + fake GitHub · no release publication',
            nested=f"↳ {selected['nested_entries']} nested entries:",
            protection=f"Rules acknowledged {selected['acknowledgements']} times. K0c: commit and push may reach the rule validator; not observed inside CLI callbacks.")
        figure['boundary'] += (' K0c historical static may-reachability (source ' + result['protection']['source_commit'] + ') supplies the validator note, not the callback trace.')
        result['figures'].append(figure)
        for name in ('observation.json', 'callbacks.json'):
            path = str(Path(OBSERVATION).parent / name)
            result['sources'][path] = sha256((root / path).read_bytes()).hexdigest()
    result['figures'][0]['cells'] = states | {'blocked_name': states['blocked'].split('=')[1].split(' ·')[0], 'blocked_rc': states['blocked'].split(' · ')[1]}
    result['figures'][0]['boundary'] = (
        'Contract view of the default merge path of work finish. A successful dry run is PLANNED; '
        'any phase can block (BLOCKED, rc 2). Failed prerequisites block subsequent closeout stages; '
        'diagnostics may still run. PASS records successful completion, not semantic correctness.')
    result['figures'][1]['cells'] = {'file-' + key: value for key, value in PACKAGE_LABELS.items()}
    result['figures'][1]['boundary'] += (
        ' Handoff does not rely on chat memory. On validation failure, inspect the failure, '
        'fix its cause, and revalidate before continuing.')
    for figure in result['figures']:
        for suffix in ('', '-mobile'):
            path = 'site/templates/figures/' + figure['id'] + suffix + '.svg'
            result['sources'][path] = sha256((root / path).read_bytes()).hexdigest()
        common = {'description'} | set(figure['cells'])
        if figure['id'] == 'G2':
            figure['template_slots'] = {'desktop': sorted(common - {'blocked_name', 'blocked_rc'}), 'mobile': sorted(common - {'blocked'})}
        elif figure['id'] == 'G0':
            figure['template_slots'] = {'desktop': sorted(common), 'mobile': sorted(common - {'protection'})}
        else:
            figure['template_slots'] = {'desktop': sorted(common), 'mobile': sorted(common)}
    return result


def checked_observation(root: Path) -> dict:
    data = json.loads((root / OBSERVATION).read_text())
    raw = (root / Path(OBSERVATION).parent / 'callbacks.json').read_bytes()
    if sha256(raw).hexdigest() != data.get('normalized_trace_sha256'):
        raise ValueError('offline callback receipt digest mismatch')
    events = json.loads(raw)
    counts = Counter()
    for i, event in enumerate(events):
        parent = event['parent']
        if event['id'] != i or (parent is not None and (not isinstance(parent, int) or not 0 <= parent < i)):
            raise ValueError('offline callback receipt parent mismatch')
        if parent is not None:
            counts[(events[parent]['command'], event['command'])] += 1
    expected = [{'caller': a, 'callee': b, 'entries': n} for (a, b), n in sorted(counts.items())]
    if expected != data.get('direct_edges') or len(events) != data.get('callback_entries'):
        raise ValueError('offline direct edges disagree with callback receipts')
    if data.get('status') == 'BOUNDED_COMPLETE' and data.get('publication_boundary') != {'gate': 'C2', 'approved': False}:
        raise ValueError('offline completion lacks its unapproved publication boundary')
    return public_observation(data)


def public_observation(data: dict) -> dict:
    """Whitelist public facts; never publish local paths, raw argv, tokens or fake PR URLs."""
    import re
    if not re.fullmatch(r'[0-9a-f]{40}', str(data.get('source_commit', ''))):
        raise ValueError('offline observation requires an exact source commit')
    edges = data.get('direct_edges', [])
    if not all(isinstance(e.get('entries'), int) and e['entries'] > 0
               and all(re.fullmatch(r'agentic-kit [a-z0-9 -]+', str(e.get(k, '')))
                       for k in ('caller', 'callee')) for e in edges):
        raise ValueError('invalid observed direct edge')
    failures = [{'name': str(s['name']), 'rc': s['rc'], 'result_status': str(s.get('result_status'))}
                for s in data.get('steps', []) if s['rc'] != 0 or s.get('result_status') in ('BLOCKED', 'FAIL')]
    return {'failed_steps': failures, 'source_commit': data['source_commit'], 'status': str(data['status']),
            'direct_edges': edges,
            'boundary': 'CLI callback entries observed in a network-denied local sandbox. Fake GitHub and always-green test CI are model assumptions. Entries include plans and dry runs. Entry does not imply successful completion; no live release or complete command coverage is claimed.'}


def observed_figure(observed: dict) -> dict:
    return {'id': 'G0', 'title': 'What work finish actually ran', 'nodes': [],
            'boundary': observed['boundary'] + ' Source: ' + observed['source_commit'] +
                        '. Run status: ' + observed['status'] + '. No release publication.'}


def svg(figure: dict, *, compact: bool = False, root: Path | None = None) -> str:
    """Render both reviewed layouts from the same validated data cells."""
    return render_template(figure, compact=compact, root=root or Path(__file__).resolve().parents[2])


def render_figures(projection: dict) -> str:
    parts = ['<section id="workflow-figures"><p class="eyebrow">Generated from current sources</p><h2>Work and handoff</h2>',
             '<p>' + escape(projection['boundary']) + '</p>']
    for figure in projection['figures']:
        parts.append(f'<article class="panel" id="figure-{figure["id"]}"><h3>{escape(figure["id"] + ": " + figure["title"])}</h3>'
                     f'<figure class="architecture-map workflow-map"><picture><source media="(max-width: 1050px)" srcset="{figure["id"]}-mobile.svg"><img src="{figure["id"]}.svg" alt="{escape(figure["title"], quote=True)} — text sequence follows."></picture></figure><details><summary>Text description and source boundaries</summary><ol>')
        parts.extend(f'<li><strong>{escape(n["label"])}</strong>: {escape(n["detail"])}</li>' for n in figure['nodes'])
        parts.append('</ol><p>' + escape(figure['boundary']) + '</p></details></article>')
    observed = projection.get('observation')
    if observed:
        parts.append('<article class="panel"><h3>Observation boundary</h3><p>' + escape(observed['boundary']) + '</p>')
        parts.append(f'<p>Source commit: <code>{observed["source_commit"]}</code> · {escape(observed["status"])}</p>')
        if observed.get('failed_steps'):
            parts.append('<p>Stopped steps: ' + escape('; '.join(f"{s['name']} (rc={s['rc']}, {s['result_status']})" for s in observed['failed_steps'])) + '</p>')
        parts.append('<p>The bounded observation and its stop point remain separate from the contract views above.</p>'
                     '<p><a href="workflow-figures.json">Read the source bindings and observed direct edges</a></p></article>')
    parts.append('<p><a href="workflow-figures.json">Figure sources and hashes</a></p></section>')
    return '\n'.join(parts)
