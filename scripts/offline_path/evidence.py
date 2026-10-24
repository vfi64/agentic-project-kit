"""Reduce callback entries without conflating direct calls, ancestry or successful completion."""
from __future__ import annotations

from collections import Counter


def edges(events: list[dict]) -> list[dict]:
    counts = Counter((e['parent']['command'], e['command']) for e in events if e.get('parent') and e['command'] != '<ambiguous>'
                     and e['parent']['command'] != '<ambiguous>')
    return [{'caller': a, 'callee': b, 'entries': count} for (a, b), count in sorted(counts.items())]


def payload(stdout: str) -> dict:
    start = stdout.find('{')
    if start < 0:
        return {}
    try:
        result, _ = __import__('json').JSONDecoder().raw_decode(stdout[start:])
    except ValueError:
        return {}
    return result if isinstance(result, dict) else {}


def acceptable(rc: int, data: dict, *, plan: bool = False) -> bool:
    allowed = {'PASS', 'NOOP', 'READY', 'COMPLETE', 'COMPLETED'}
    if plan:
        allowed |= {'AWAITING_APPROVAL', 'PLANNED'}
    return rc == 0 and data.get('result_status', data.get('status')) in allowed


def trace_findings(events: list[dict], steps: list[dict]) -> list[str]:
    """No completed experiment without trace receipts for every top-level step."""
    findings = []
    missing = sorted({s['name'] for s in steps} - {e['step'] for e in events})
    if missing:
        findings.append('untraced steps: ' + ', '.join(missing))
    known = {}
    for event in events:
        if event['id'] in known:
            findings.append('duplicate callback identity')
        parent = event.get('parent')
        if parent and known.get(parent['id']) != parent['command']:
            findings.append('missing or inconsistent callback parent')
        if event['command'] == '<ambiguous>':
            findings.append('ambiguous callback command')
        known[event['id']] = event['command']
    return sorted(set(findings))


def normalize_events(events: list[dict]) -> list[dict]:
    """Keep reconstructible direct parents without publishing process IDs or local argv."""
    ids = {event['id']: i for i, event in enumerate(events)}
    return [{'id': i, 'command': event['command'], 'step': event['step'],
             'parent': ids[event['parent']['id']] if event.get('parent') else None}
            for i, event in enumerate(events)]
