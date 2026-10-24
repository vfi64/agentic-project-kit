"""Export reviewed callback evidence without runtime paths, process IDs or raw command output."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from evidence import edges, normalize_events, trace_findings


def export(source: Path, output: Path) -> dict:
    data = json.loads((source / 'observation.json').read_text())
    raw = (source / 'callbacks.jsonl').read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    if not events or data.get('isolation_probe') != {'network': 1, 'outside_write': 1}:
        raise ValueError('missing callback or OS isolation receipts')
    if data.get('status') == 'BOUNDED_COMPLETE' and data.get('publication_boundary') != {'gate': 'C2', 'approved': False}:
        raise ValueError('completed observation lacks its unapproved C2 boundary')
    findings = trace_findings(events, data['steps'])
    if findings or data['direct_edges'] != edges(events) or data['callback_entries'] != len(events):
        raise ValueError('trace receipts disagree with the observation summary: ' + '; '.join(findings))
    normalized = normalize_events(events)
    callbacks = json.dumps(normalized, indent=2, sort_keys=True) + '\n'
    keys = ('schema_version', 'kind', 'source_commit', 'status', 'assumptions',
            'tool_hashes', 'fixture_transformations', 'callback_targets', 'registered_commands',
            'alias_callbacks', 'synthetic_release_version', 'publication_boundary', 'stop_reason',
            'instrumentation_findings', 'callback_entries', 'direct_edges', 'ambiguous_entries',
            'duration_seconds', 'isolation_probe')
    public = {key: data[key] for key in keys if key in data}
    public['steps'] = [{k: step[k] for k in ('name', 'rc', 'result_status', 'seconds')} for step in data['steps']]
    public['raw_trace_sha256'] = sha256(raw).hexdigest()
    public['normalized_trace_sha256'] = sha256(callbacks.encode()).hexdigest()
    public['exporter_sha256'] = sha256(Path(__file__).read_bytes()).hexdigest()
    public['unique_commands_entered'] = len({e['command'] for e in events})
    public['observation_boundary'] = ('One self-hosting fixture with synthetic history. Callback entries and fake green CI '
                                      'do not prove successful live publication, universal coverage, or a common kernel.')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'callbacks.json').write_text(callbacks)
    (output / 'observation.json').write_text(json.dumps(public, indent=2, sort_keys=True) + '\n')
    rows = ['# Offline work and release-entry observation', '',
            f"Source: `{data['source_commit']}`. Outcome: **{data['status']}**.", '',
            f"{len(events)} CLI callback entries; {public['unique_commands_entered']} different commands; "
            f"{len(data['direct_edges'])} distinct **direct** edges. These are not ancestor-closure counts.", '',
            public['observation_boundary'], '',
            '## Bounded execution', '',
            'The inherited OS probes denied both network and outside-root writes with EPERM. '
            'All Git and fake-GitHub effects stayed in the owned fixture. No model, remote API, '
            'real PR, tag, release, PyPI or Zenodo publication was used.', '',
            '| Step | rc | Structured verdict | Seconds |', '|---|---:|---|---:|']
    rows += [f"| {s['name']} | {s['rc']} | {s['result_status'] or 'text acknowledgement'} | {s['seconds']} |" for s in data['steps']]
    rows += ['', 'B4 changes version files and handoff projections inside the synthetic fixture; the source pin names its initial code base.', '', 'Stop boundary: ' + data.get('stop_reason', 'not recorded') + '.', '',
             'Callback entries include plans and dry runs; command names alone do not identify remote effects. The release track stops before C2 publication approval. This is a work/prepare/closeout '
             'observation, not the complete publication path. G0 shows direct callees for selected '
             'entrypoints; G2/G3 remain separate current contract views.', '',
             '## Reproduction and preserved limits', '',
             'Run the pinned developer runner into a fresh owned temporary directory, then use '
             '`scripts/offline_path/export.py` to reproduce the bounded public projection. '
             'Process IDs, synthetic Git commit times and durations vary. Callback receipts and '
             'source/runner hashes are retained; no byte-identical runtime timing is promised.', '',
             'The historical 2026-10-15 simulation also included inferred core ownership and ancestor '
             'relationships. Its 301 pairs are not this report\'s direct-edge denominator. '
             'Static analysis remains incomplete and its `*parts` extension stays deferred to D1.', '',
             'Development preflights were preserved locally: the first dependency lookup chose an '
             'old site-packages directory; initial tracing was displaced by system sitecustomize; '
             'a missing fixture tag caused release readiness to block. These were runner/fixture '
             'defects, not evidence of Kit product defects. The final runner uses the current '
             'interpreter path, an explicit .pth import, a version tag and trace-integrity checks.', '',
             'See `docs/reference/OFFLINE_PATH_OBSERVATION.md` and the two regression modules. '
             'No historical audit was overwritten.', '']
    (output / 'README.md').write_text('\n'.join(rows))
    return public


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = export(args.source, args.output)
    print(json.dumps({'status': report['status'], 'source_commit': report['source_commit'],
                      'callback_entries': report['callback_entries'], 'direct_edges': len(report['direct_edges'])}))
