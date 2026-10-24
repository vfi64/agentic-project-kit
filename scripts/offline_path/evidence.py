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
