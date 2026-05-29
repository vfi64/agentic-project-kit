from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT / 'docs/reports/terminal/post-merge-gate-bootstrap-visibility.log'
FILES = [
    ROOT / 'docs/handoff/START_NEW_CHAT_PROMPT.md',
    ROOT / 'docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md',
]
CURRENT = ROOT / 'docs/handoff/CURRENT_HANDOFF.md'

SECTION = '''## Post-Merge Handoff Refresh Status Gate

After every PR merge and local main sync, run agentic-kit handoff post-merge-refresh-status before product work.

Interpretation is machine-derived:

- result=NOOP: continue without an administrative handoff refresh.
- result=REFRESH_REQUIRED: create an administrative handoff refresh slice before product work.

This is not a chat-judgement step. The kit decides whether a post-merge handoff refresh is required; d, f, and w remain communication signals only.
'''

CURRENT_NOTE = '''## Post-Merge Handoff Refresh Status Gate Visibility

The post-merge handoff refresh status gate is now documented for bootstrap visibility. After any PR merge and local main sync, run agentic-kit handoff post-merge-refresh-status. Continue only on result=NOOP; create an administrative handoff refresh slice on result=REFRESH_REQUIRED before product work.
'''

changed = []
for path in FILES:
    text = path.read_text(encoding='utf-8')
    if '## Post-Merge Handoff Refresh Status Gate' not in text:
        marker = '## Prompt to '
        index = text.find(marker)
        if index < 0:
            raise RuntimeError('missing prompt marker in ' + str(path))
        text = text[:index].rstrip() + '\n\n' + SECTION.rstrip() + '\n\n' + text[index:]
        path.write_text(text, encoding='utf-8')
        changed.append(str(path.relative_to(ROOT)))

text = CURRENT.read_text(encoding='utf-8')
if '## Post-Merge Handoff Refresh Status Gate Visibility' not in text:
    CURRENT.write_text(CURRENT_NOTE.rstrip() + '\n\n' + text, encoding='utf-8')
    changed.append(str(CURRENT.relative_to(ROOT)))

LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text('POST_MERGE_GATE_BOOTSTRAP_VISIBILITY\nchanged_files=' + (','.join(changed) if changed else '<none>') + '\nresult=PASS\n', encoding='utf-8')
print(str(LOG.relative_to(ROOT)))
print('result=PASS')
