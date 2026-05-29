from pathlib import Path
import subprocess
import yaml

PR_NUMBER = 894
STATE = Path('.agentic/handoff_state.yaml')
STATUS = Path('docs/STATUS.md')
HANDOFF = Path('docs/handoff/CURRENT_HANDOFF.md')
PROMPT = Path('docs/reports/terminal/v044-successor-chat-handoff-after-pr894.md')
LOG = Path('docs/reports/terminal/post-pr894-handoff-refresh.log')


def run(*args):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.strip()


def prepend(path, title, body):
    text = path.read_text(encoding='utf-8')
    if title in text[:2000]:
        return False
    path.write_text(title + '\n\n' + body.strip() + '\n\n' + text, encoding='utf-8')
    return True


run('git', 'fetch', 'origin', 'main')
head = run('git', 'rev-parse', 'origin/main')
short = head[:7]
subject = run('git', 'log', '-1', '--format=%s', 'origin/main')

state = yaml.safe_load(STATE.read_text(encoding='utf-8'))
state.setdefault('updated', {}).update({
    'date': '2026-05-29',
    'reason': 'post-PR894 handoff refresh',
    'source': 'PR894 main verification',
})
state.setdefault('safe_state', {}).update({
    'branch': 'main',
    'commit': head,
    'commit_subject': subject,
    'semantics': 'current_main_head',
    'working_tree_expected_clean': True,
})
prs = state.setdefault('safe_state', {}).setdefault('administrative_refresh_prs', [])
if PR_NUMBER not in prs:
    prs.append(PR_NUMBER)
entry = 'PR #894 merged post-merge gate bootstrap visibility documentation before this administrative handoff refresh.'
items = state.setdefault('completed_since_previous_handoff', [])
if entry not in items:
    items.insert(0, entry)
state['first_instruction'] = 'Start the next chat from the fresh post-PR894 successor handoff prompt and obey agentic-kit handoff post-merge-refresh-status before product work.'
state.setdefault('handoff_maintenance', {})['latest_successor_prompt'] = str(PROMPT)
state.setdefault('administrative_evidence_state', {}).update({
    'current_head': head,
    'current_head_subject': subject,
    'head_subject': subject,
    'allowed_after_safe_state': True,
    'reason': 'PR894 post-merge gate bootstrap visibility merged on main',
    'latest_successor_prompt': str(PROMPT),
    'current_subject': subject,
    'safe_state_semantics': 'current_main_head',
})
STATE.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding='utf-8')

title = '## Post-PR894 Handoff Refresh State'
body = f'''Current verified main HEAD is `{head}` (`{short}`).
Commit subject: `{subject}`.

PR #894 is merged. This is an administrative post-merge handoff/status refresh before chat handoff.

The post-merge handoff refresh status gate is the canonical decision point after merges: `agentic-kit handoff post-merge-refresh-status`.

Next safe step after this refresh is merged and verified: start the successor chat from the fresh prompt and continue only if the machine-readable refresh status is `result=NOOP`.'''
status_changed = prepend(STATUS, title, body)
handoff_changed = prepend(HANDOFF, title, body)

prompt = subprocess.run(['.venv/bin/python', '-m', 'agentic_project_kit.cli', 'handoff', 'prompt'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
PROMPT.write_text(prompt.stdout, encoding='utf-8')
warning = 'WARNING: this successor handoff prompt may be stale' in prompt.stdout
LOG.write_text('\n'.join([
    'POST_PR894_HANDOFF_REFRESH',
    f'target_head={head}',
    f'target_subject={subject}',
    f'status_changed={status_changed}',
    f'current_handoff_changed={handoff_changed}',
    f'prompt_path={PROMPT}',
    f'prompt_returncode={prompt.returncode}',
    f'freshness_warning_present={warning}',
    'result=PASS',
]) + '\n', encoding='utf-8')
print(LOG)
print('result=PASS')
