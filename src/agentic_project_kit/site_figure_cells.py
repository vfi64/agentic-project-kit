"""Source-bound cells for the fixed workflow layouts; incompatible shapes fail closed."""
from __future__ import annotations

import ast
import json
from pathlib import Path

HUMAN_SOURCE = 'src/agentic_project_kit/cli_commands/human_workflows.py'
# Layout contract, not a second execution authority. Compare every entry, including duplicates.
FINISH_SEQUENCE = (
    'transfer repo-status', 'transfer protected-diff-plan', 'rules acknowledge', 'transfer commit',
    'rules acknowledge', 'transfer chat-switch-complete', 'rules acknowledge', 'transfer commit',
    'rules acknowledge', 'transfer push-current', 'transfer pr-create-complete',
    'transfer sync-main', 'transfer post-merge-check', 'transfer repo-status',
)
PACKAGE_LABELS = {
    'successor_context.yaml': 'project context', 'successor_prompt.md': 'next-chat prompt',
    'execution_contract.json': 'rules and commands', 'source_manifest.json': 'source identities',
    'validation_report.json': 'validation report',
}


def finish_contract(root: Path) -> dict:
    """Read the actual pure result function, without importing or executing workflow adapters."""
    tree = ast.parse((root / HUMAN_SOURCE).read_text())
    payload = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_payload')
    # The public diagram has exactly these branches. A changed state model needs a layout review.
    assignments = [n for n in ast.walk(payload) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'result_status' for t in n.targets)]
    states = {n.value.value for n in assignments if isinstance(n.value, ast.Constant)}
    if states != {'PLANNED', 'PASS', 'BLOCKED'} or len(assignments) != 3:
        raise ValueError('work finish result states changed; review figure')
    branch = next(n for n in payload.body if isinstance(n, ast.If))
    planned = branch.orelse[0] if branch.orelse else None
    if not (isinstance(branch.test, ast.Name) and branch.test.id == 'blockers'
            and isinstance(planned, ast.If)
            and ast.dump(planned.test) == ast.dump(ast.parse('dry_run and action == "work-finish"', mode='eval').body)
            and branch.body and planned.body and planned.orelse
            and isinstance(branch.body[0], ast.Assign) and isinstance(planned.body[0], ast.Assign)
            and isinstance(planned.orelse[0], ast.Assign)
            and ast.literal_eval(branch.body[0].value) == 'BLOCKED'
            and ast.literal_eval(planned.body[0].value) == 'PLANNED'
            and ast.literal_eval(planned.orelse[0].value) == 'PASS'):
        raise ValueError('work finish state conditions changed; review figure')
    returns = [n for n in ast.walk(payload) if isinstance(n, ast.Dict)]
    rc = next(v for d in returns for k, v in zip(d.keys, d.values)
              if isinstance(k, ast.Constant) and k.value == 'returncode')
    if ast.dump(rc) != ast.dump(ast.parse('2 if result_status == "BLOCKED" else 0', mode='eval').body):
        raise ValueError('work finish return codes changed; review figure')
    finish = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'work_finish_command')
    arguments = dict(zip([a.arg for a in finish.args.args], finish.args.defaults))
    for name, flag in [('dry_run', '--dry-run/--execute'), ('merge', '--merge/--no-merge')]:
        default = arguments.get(name)
        if not (isinstance(default, ast.Call) and default.args
                and isinstance(default.args[0], ast.Constant) and default.args[0].value is True
                and flag in [n.value for n in ast.walk(default) if isinstance(n, ast.Constant)]):
            raise ValueError('work finish defaults changed; review figure')
    return {'planned': 'STATE=PLANNED', 'passed': 'STATE=PASS', 'blocked': 'STATE=BLOCKED · rc 2'}


def selected_finish(events: list[dict]) -> dict:
    roots = [e for e in events if e['parent'] is None and e['command'] == 'agentic-kit work finish'
             and e['step'] == 'finish work']
    if len(roots) != 1:
        raise ValueError('expected exactly one observed finish work execution')
    children = [e for e in events if e['parent'] == roots[0]['id']]
    names = [e['command'].removeprefix('agentic-kit ') for e in children]
    if tuple(names) != FINISH_SEQUENCE:
        raise ValueError('observed finish sequence changed; review phase layout')
    pr = next(e for e in children if e['command'] == 'agentic-kit transfer pr-create-complete')
    descendants = {pr['id']}
    for event in events:
        if event['parent'] in descendants:
            descendants.add(event['id'])
    labels = [n.removeprefix('transfer ') for n in names]
    labels[3], labels[7] = 'commit (work)', 'commit (handoff)'
    return {'calls': labels, 'nested_entries': len(descendants) - 1,
            'acknowledgements': names.count('rules acknowledge')}


PROTECTION_REPORT = 'docs/reports/protection_mechanisms_20261023/reachability.json'


def protection_binding(root: Path) -> dict:
    """Keep a historical static witness separate from the CLI observation."""
    report = json.loads((root / PROTECTION_REPORT).read_text())
    mechanism = next(m for m in report['mechanisms']
                     if m['function'] == 'agentic_project_kit.rule_ack:validate_rule_acknowledgement')
    selected = [r for r in mechanism['reached_by'] if r['command'] in
                ('agentic-kit transfer commit', 'agentic-kit transfer push-current')]
    if len(selected) != 2 or any(not r.get('witness') or r['witness'][-1] != mechanism['function'] for r in selected):
        raise ValueError('K0c rule acknowledgement witnesses changed; review figure')
    return {'source_commit': report['source_commit'], 'kind': 'historical_static_may_reachability',
            'witnesses': selected}
