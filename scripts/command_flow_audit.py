"""Render bounded source-flow evidence; this is a developer audit, not a public command."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

from command_flow_analysis import SourceFlow, load_sources


LIMITS = [
    'Possible source flow is not a runtime trace, an executed action or an authorization grant.',
    'Only literal argv prefixes, simple local aliases and resolved helper returns/parameters are followed.',
    'Only subprocess argv terminals establish execution; command strings and Python module launches remain unknown.',
    'Unknown calls and container mutation invalidate argv prefixes rather than being guessed.',
    'Dynamic dispatch, methods on instances, global values, relative imports and code inside subprocesses are not expanded.',
    'Branches over-approximate possible flow; arbitrary path feasibility and exceptions are not proven.',
    'Only analyzed function bodies contribute references; globals and unreferenced computed commands are not an inventory.',
    'No universal call graph, lock coverage, kernel claim or G0 graphic is established by these results.',
]


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def callback_functions(root):
    from typer.main import get_command
    from agentic_project_kit.cli import app

    result = {}
    def walk(command, path):
        children = getattr(command, 'commands', None)
        if children:
            for name, child in sorted(children.items()):
                walk(child, [*path, name])
        else:
            fn = inspect.unwrap(command.callback)
            if not Path(inspect.getsourcefile(fn)).resolve().is_relative_to(root / 'src'):
                raise ValueError('CLI callback is not loaded from the pinned repository')
            result['agentic-kit ' + ' '.join(path)] = fn.__module__ + ':' + fn.__qualname__.replace('.<locals>.', '.')
    walk(get_command(app), [])
    return result


def generate(root, source_commit):
    source_commit = git(root, 'rev-parse', source_commit)
    paths = ['src', 'scripts/command_flow_analysis.py', 'scripts/command_flow_audit.py', 'docs/reference/agentic-kit-commands.json']
    for path in paths[1:3]:
        git(root, 'cat-file', '-e', source_commit + ':' + path)
    if git(root, 'ls-files', '--others', '--exclude-standard', '--', *paths):
        raise ValueError('untracked analyzed inputs cannot be pinned')
    if git(root, 'diff', '--name-only', source_commit, '--', *paths):
        raise ValueError('analyzed inputs differ from pinned source commit')
    manifest = json.loads((root / paths[-1]).read_text())
    commands = [r['qualified_name'] for r in manifest['commands']]
    sources = load_sources(root)
    analyzer = SourceFlow(sources, commands)
    flow = analyzer.run()
    if not flow['converged']:
        raise ValueError('bounded flow analysis did not converge')
    callbacks = callback_functions(root)
    if set(callbacks) != set(commands):
        raise ValueError('CLI and manifest command inventory differ')
    rows = []
    def targets(refs):
        return sorted({analyzer.sites[r]['command'] for r in refs if r in analyzer.sites})
    for command, fid in sorted(callbacks.items()):
        summary = analyzer.summaries.get(fid)
        rows.append({'command': command, 'function': fid, 'resolved_callback': summary is not None,
                     'possible_execution_targets': targets(summary.execution) if summary else [],
                     'recommendation_targets': targets(summary.recommendation) if summary else []})
    by_command = {r['command']: r for r in rows}
    sync, adopt = by_command['agentic-kit transfer sync-main'], by_command['agentic-kit workspace adopt']
    controls = {
        'sync_main_acknowledges_rules': 'agentic-kit rules acknowledge' in sync['possible_execution_targets'],
        'adopt_bootstrap_is_guidance': 'agentic-kit rule-registry bootstrap' in adopt['recommendation_targets'],
        'adopt_does_not_execute_bootstrap': 'agentic-kit rule-registry bootstrap' not in adopt['possible_execution_targets'],
    }
    if not all(controls.values()):
        raise ValueError(f'known source-flow controls failed: {controls}')
    return {'schema_version': 1, 'analysis_status': 'BOUNDED_STATIC_INCOMPLETE',
            'source_commit': source_commit, 'manifest_sha': manifest['meta']['manifest_sha'],
            'source_digest': hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
            'counts': dict(sorted(Counter(r['classification'] for r in flow['sites']).items())),
            'controls': controls, 'limitations': LIMITS, 'commands': rows, **flow}


def render(data):
    lines = ['# Command references: execution or recommendation', '',
             f"Pinned source: `{data['source_commit']}`; manifest `{data['manifest_sha']}`.", '',
             f"Analysis: **{data['analysis_status']}**, converged in {data['rounds']} rounds.", '',
             'Counts describe source reference sites, not executed calls or runtime coverage.', '',
             '| Site classification | Count |', '|---|---:|']
    lines += [f'| {kind} | {count} |' for kind, count in sorted(data['counts'].items())]
    lines += ['', '## Known-case controls', '', '| Control | Result |', '|---|---|']
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in sorted(data['controls'].items())]
    lines += ['', '## Command-level source flows', '',
              'These are statically resolved helper flows; empty columns do not prove absence.', '',
              '| Command | Possible execution | Recommendation |', '|---|---|---|']
    lines += [f"| `{r['command']}` | {', '.join(r['possible_execution_targets']) or 'no witness'} | {', '.join(r['recommendation_targets']) or 'no witness'} |"
              for r in data['commands'] if r['possible_execution_targets'] or r['recommendation_targets']]
    lines += ['', '## Boundaries', ''] + ['- ' + limit for limit in data['limitations']]
    lines += ['', 'Historical K0/K0c reports are unchanged. Review this evidence before deciding G0; no drawing is authorized here.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    data = generate(args.root.resolve(), args.source_commit)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'flow.json').write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    (args.out / 'README.md').write_text(render(data))
    print(json.dumps({'analysis_status': data['analysis_status'], 'counts': data['counts'], 'controls': data['controls']}, sort_keys=True))


if __name__ == '__main__':
    main()
