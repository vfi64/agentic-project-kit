"""Accessible workflow figures projected from current contracts, not inferred call graphs."""
from __future__ import annotations

import ast
from collections import Counter
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
        result['observation'] = checked_observation(root)
        result['figures'].append(observed_figure(result['observation']))
        for name in ('observation.json', 'callbacks.json'):
            path = str(Path(OBSERVATION).parent / name)
            result['sources'][path] = sha256((root / path).read_bytes()).hexdigest()
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
    nodes = []
    selected = ('agentic-kit work start', 'agentic-kit work finish',
                'agentic-kit transfer chat-switch-complete', 'agentic-kit release run')
    for caller in selected:
        children = sorted({e['callee'].removeprefix('agentic-kit ') for e in observed['direct_edges']
                           if e['caller'] == caller})
        if children or caller == 'agentic-kit transfer chat-switch-complete':
            nodes.append({'label': caller.removeprefix('agentic-kit '),
                          'detail': '; '.join(children) if children else 'No nested CLI callback observed; internal Python operations are outside this view.'})
    return {'id': 'G0', 'title': 'Observed work and release entry', 'nodes': nodes,
            'direct_calls': True,
            'subtitle': ['Offline callback entries · ' + observed['source_commit'][:12],
                         'Local Git + fake GitHub · no publication'],
            'boundary': observed['boundary'] + ' Source: ' + observed['source_commit'] +
                        '. Run status: ' + observed['status'] + '. Complete publication is outside this observation.'}


def svg(figure: dict, *, compact: bool = False) -> str:
    """Render two layouts from the same cells, including a genuinely narrow SVG."""
    width = 360 if compact else 640
    wrap = 34 if compact else 65
    title_lines = textwrap.wrap(figure['title'], 24 if compact else 45)
    subtitles = figure.get('subtitle', ['Contract view · not a runtime trace'])
    y = 48 + 30 * len(title_lines) + 20 * len(subtitles)
    rows = []
    for index, node in enumerate(figure['nodes']):
        label = ('Caller: ' if figure.get('direct_calls') else f'{index + 1}. ') + node['label']
        labels = textwrap.wrap(label, 27 if compact else 48)
        detail = ('Direct callees: ' if figure.get('direct_calls') else '') + node['detail']
        lines = textwrap.wrap(detail, wrap)
        height = 36 + 24 * len(labels) + 22 * len(lines)
        rows.append(f'<rect x="16" y="{y}" width="{width - 32}" height="{height}" rx="14" fill="white" stroke="#0f766e"/>')
        for i, line in enumerate(labels):
            rows.append(f'<text x="30" y="{y + 28 + i * 24}" font-size="17" font-weight="700">{escape(line)}</text>')
        for i, line in enumerate(lines):
            rows.append(f'<text x="30" y="{y + 36 + len(labels) * 24 + i * 22}" font-size="15">{escape(line)}</text>')
        y += height + 32
        if not figure.get('direct_calls') and index + 1 < len(figure['nodes']):
            rows.append(f'<path d="M{width // 2} {y - 30} v24 m-5 -6 l5 6 5 -6" stroke="#0f766e" fill="none" stroke-width="2"/>')
    titles = ''.join(f'<text x="20" y="{32 + i * 30}" font-size="23" font-weight="700">{escape(line)}</text>' for i, line in enumerate(title_lines))
    titles += ''.join(f'<text x="20" y="{42 + len(title_lines) * 30 + i * 20}" font-size="13">{escape(line)}</text>' for i, line in enumerate(subtitles))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{y}" viewBox="0 0 {width} {y}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(figure["title"])}</title><desc id="desc">{escape(figure["boundary"])}</desc>'
            f'<rect width="{width}" height="{y}" fill="#ecf5ef" rx="18"/>'
            '<g font-family="system-ui,sans-serif" font-size="18" fill="#16302b">'
            + titles + ''.join(rows) + '</g></svg>\n')


def render_figures(projection: dict) -> str:
    parts = ['<section id="workflow-figures"><p class="eyebrow">Generated from current sources</p><h2>Work and handoff</h2>',
             '<p>' + escape(projection['boundary']) + '</p>']
    for figure in projection['figures']:
        parts.append(f'<article class="panel"><h3>{escape(figure["id"] + ": " + figure["title"])}</h3>'
                     f'<figure class="architecture-map workflow-map"><picture><source media="(max-width: 680px)" srcset="{figure["id"]}-mobile.svg"><img src="{figure["id"]}.svg" alt="{escape(figure["title"], quote=True)} — text sequence follows."></picture></figure><ol>')
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
