"""Accessible workflow figures projected from current contracts, not inferred call graphs."""
from __future__ import annotations

import ast
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import textwrap

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
    result = {'schema_version': 1, 'kind': 'workflow_figure_projection',
              'boundary': 'Editorial contract views; arrows show a reading/work sequence, not observed nested calls.',
              'sources': {p: sha256((root / p).read_bytes()).hexdigest() for p in (MANIFEST, HUMAN, HANDOFF)},
              'figures': [
                  {'id': 'G2', 'title': 'A bounded work cycle', 'nodes': nodes,
                   'boundary': 'Make the selected change between start and check. Review the finish plan before execution; blocked or failed results stop the cycle.'},
                  {'id': 'G3', 'title': 'Context survives the chat', 'nodes': [
                      {'label': 'Repository sources', 'detail': 'source_manifest.json records the inputs.'},
                      {'label': 'Successor package', 'detail': ', '.join(files)},
                      {'label': 'Validate, then continue', 'detail': 'Read validation_report.json and execution_contract.json. A failed handoff blocks continuation.'},
                      {'label': 'Successor chat', 'detail': 'Use successor_context.yaml and successor_prompt.md; inspect current repository state.'}],
                   'boundary': 'A generated package preserves inspectable context. It does not prove requirements or software correctness.'}]}
    if (root / OBSERVATION).exists():
        observation = json.loads((root / OBSERVATION).read_text())
        result['observation'] = public_observation(observation)
        result['figures'].append(observed_figure(result['observation']))
        result['sources'][OBSERVATION] = sha256((root / OBSERVATION).read_bytes()).hexdigest()
    return result


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
            'boundary': 'CLI callback entries observed in a network-denied local sandbox. Fake GitHub and always-green test CI are model assumptions. Entry does not imply successful completion; no live release or complete command coverage is claimed.'}


def observed_figure(observed: dict) -> dict:
    nodes = []
    selected = ('agentic-kit work start', 'agentic-kit work finish',
                'agentic-kit transfer chat-switch-complete', 'agentic-kit release run')
    for caller in selected:
        children = sorted({e['callee'].removeprefix('agentic-kit ') for e in observed['direct_edges']
                           if e['caller'] == caller})
        if children:
            nodes.append({'label': caller.removeprefix('agentic-kit '),
                          'detail': '; '.join(children)})
    return {'id': 'G0', 'title': 'Observed work and release entry', 'nodes': nodes,
            'direct_calls': True,
            'boundary': observed['boundary'] + ' Source: ' + observed['source_commit'] +
                        '. Run status: ' + observed['status'] + '. Release may stop before publication.'}


def svg(figure: dict) -> str:
    """Vertical deterministic cards remain readable with a plain-text alternative beside them."""
    rows = []
    y = 70
    for index, node in enumerate(figure['nodes']):
        detail = ('Direct callees: ' if figure.get('direct_calls') else '') + node['detail']
        lines = textwrap.wrap(detail, 65)
        height = 62 + 22 * len(lines)
        rows.append(f'<rect x="20" y="{y}" width="600" height="{height}" rx="14" fill="white" stroke="#0f766e"/>')
        label = ('Caller: ' if figure.get('direct_calls') else f'{index + 1}. ') + node['label']
        rows.append(f'<text x="40" y="{y + 30}" font-weight="700">{escape(label)}</text>')
        for line_no, line in enumerate(lines):
            rows.append(f'<text x="40" y="{y + 58 + line_no * 22}" font-size="15">{escape(line)}</text>')
        y += height + 32
        if not figure.get('direct_calls') and index + 1 < len(figure['nodes']):
            rows.append(f'<path d="M320 {y - 30} v24 m-5 -6 l5 6 5 -6" stroke="#0f766e" fill="none" stroke-width="2"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{y}" viewBox="0 0 640 {y}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(figure["title"])}</title><desc id="desc">{escape(figure["boundary"])}</desc>'
            f'<rect width="640" height="{y}" fill="#ecf5ef" rx="18"/>'
            f'<g font-family="system-ui,sans-serif" font-size="18" fill="#16302b"><text x="24" y="40" font-size="23" font-weight="700">{escape(figure["title"])}</text>'
            + ''.join(rows) + '</g></svg>\n')


def render_figures(projection: dict) -> str:
    parts = ['<section id="workflow-figures"><p class="eyebrow">Generated from current sources</p><h2>Work and handoff</h2>',
             '<p>' + escape(projection['boundary']) + '</p>']
    for figure in projection['figures']:
        parts.append(f'<article class="panel"><h3>{escape(figure["id"] + ": " + figure["title"])}</h3>'
                     f'<figure class="architecture-map"><img src="{figure["id"]}.svg" alt="{escape(figure["title"], quote=True)} — text sequence follows."></figure><ol>')
        parts.extend(f'<li><strong>{escape(n["label"])}</strong>: {escape(n["detail"])}</li>' for n in figure['nodes'])
        parts.append('</ol><p>' + escape(figure['boundary']) + '</p></article>')
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
