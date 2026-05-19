#!/bin/sh
set -u

printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'ADD REMOTE COMMAND FIRST FALLBACK RULE\n\n'

WORK_RESULT=FAIL
EVIDENCE_RESULT=FAIL
OVERALL_RESULT=FAIL
REMOTE_EVIDENCE=FAIL
TERMINAL_LOG=NONE
COMMAND_REPORT=NONE
NEXT_CHAT_REPLY=f
LOG=docs/reports/terminal/20260519-remote-command-first-rule.log
TMP=tmp/remote_command_first_rule_patch.py

mkdir -p tmp docs/reports/terminal

{
printf 'ADD REMOTE COMMAND FIRST FALLBACK RULE\n\n'
printf '### PRECHECK ###\n'
git branch --show-current
git status --short
printf '\n### WRITE PATCH SCRIPT ###\n'
cat > "$TMP" <<'PYEOF'
from pathlib import Path
import yaml

rule_text = "Before giving the user a long local terminal block for repo work, first queue a repo-backed command under .agentic/commands/inbox when remote repository access and agent-next are available. If agent-next reports NO-COMMAND, the assistant must create the missing inbox command pair remotely instead of falling back to long copy-and-paste. This rule is limited to the current no-copy command-runner workflow and must not block future GUI or structured local execution paths."

handoff = Path('.agentic/handoff_state.yaml')
data = yaml.safe_load(handoff.read_text(encoding='utf-8'))
rules = data.setdefault('rules', [])
if not any(isinstance(item, dict) and item.get('id') == 'remote-command-first-fallback' for item in rules):
    rules.append({'id': 'remote-command-first-fallback', 'status': 'active', 'text': rule_text})
patterns = data.setdefault('recent_failure_patterns', [])
if not any(isinstance(item, dict) and item.get('id') == 'long-copy-block-after-agent-next-no-command' for item in patterns):
    patterns.append({'id': 'long-copy-block-after-agent-next-no-command', 'prevention': 'When ./ns agent-next returns NO-COMMAND, queue the missing command pair remotely and ask the user to rerun git pull --ff-only origin main && ./ns agent-next. Do not replace the repo-backed workflow with a long chat-pasted terminal script unless remote queueing is impossible.'})
handoff.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')

needle = '## Remote-first no-guess rule'
addition = '''\n## Remote command first fallback\n\nWhen remote repository access and `./ns agent-next` are available, repo work should be handed off as a committed inbox command pair under `.agentic/commands/inbox/` before any long local terminal block is pasted in chat. If `./ns agent-next` returns `NO-COMMAND`, the correct repair is to queue the missing command pair remotely and ask the user to rerun `git pull --ff-only origin main` and `./ns agent-next`. This remote command first fallback is intentionally narrow: it governs the current no-copy command-runner workflow and must not block a future GUI, cockpit, or other structured local executor.\n'''
for name in ['docs/STATUS.md', 'docs/handoff/CURRENT_HANDOFF.md', 'docs/TEST_GATES.md']:
    path = Path(name)
    text = path.read_text(encoding='utf-8')
    if 'remote command first fallback' not in text:
        text = text.rstrip() + '\n' + addition + '\n'
        path.write_text(text, encoding='utf-8')

test = Path('tests/test_remote_command_first_fallback_rule.py')
test.write_text("""from pathlib import Path\n\nimport yaml\n\n\ndef test_remote_command_first_fallback_rule_is_recorded():\n    data = yaml.safe_load(Path('.agentic/handoff_state.yaml').read_text(encoding='utf-8'))\n    rules = data.get('rules', [])\n    match = [item for item in rules if isinstance(item, dict) and item.get('id') == 'remote-command-first-fallback']\n    assert match\n    assert 'agent-next' in match[0].get('text', '')\n    assert 'future GUI' in match[0].get('text', '')\n\n\ndef test_agent_next_no_command_fallback_is_recorded():\n    data = yaml.safe_load(Path('.agentic/handoff_state.yaml').read_text(encoding='utf-8'))\n    patterns = data.get('recent_failure_patterns', [])\n    assert any(isinstance(item, dict) and item.get('id') == 'long-copy-block-after-agent-next-no-command' for item in patterns)\n\n\ndef test_remote_command_first_docs_are_present():\n    for name in ['docs/STATUS.md', 'docs/handoff/CURRENT_HANDOFF.md', 'docs/TEST_GATES.md']:\n        text = Path(name).read_text(encoding='utf-8')\n        assert 'remote command first fallback' in text\n        assert '.agentic/commands/inbox/' in text\n        assert 'must not block a future GUI' in text\n""", encoding='utf-8')
PYEOF

python3 -m py_compile "$TMP"
python3 "$TMP"
printf 'patch script PASS\n'

printf '\n### YAML PARSE CHECK ###\n'
python3 - <<'PYEOF'
from pathlib import Path
import yaml
for name in ['.agentic/handoff_state.yaml', 'docs/DOCUMENTATION_COVERAGE.yaml']:
    yaml.safe_load(Path(name).read_text(encoding='utf-8'))
print('yaml parse PASS')
PYEOF

printf '\n### TARGETED PYTEST ###\n'
python3 -m pytest -q tests/test_remote_command_first_fallback_rule.py

printf '\n### PATCH PREFLIGHT ###\n'
./ns patch-preflight

printf '\n### DEV GATE ###\n'
./ns dev

printf '\n### FINAL STATUS BEFORE COMMIT ###\n'
git status --short
} 2>&1 | tee "$LOG"

if grep -q '### RESULT: FAIL ###' "$LOG"; then
  printf 'inner failure marker detected\n'
else
  if grep -q 'Agentic project check passed' "$LOG" && grep -q 'Overall: PASS' "$LOG" && grep -q 'Patch artifact preflight passed' "$LOG"; then
    git add .agentic/handoff_state.yaml docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md docs/TEST_GATES.md tests/test_remote_command_first_fallback_rule.py "$LOG"
    git commit -m 'Add remote command first fallback rule'
    git push
    WORK_RESULT=PASS
    EVIDENCE_RESULT=PASS
    OVERALL_RESULT=PASS
    REMOTE_EVIDENCE=PASS
    TERMINAL_LOG=$LOG
    NEXT_CHAT_REPLY=p
  fi
fi

printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: %s\n' "$WORK_RESULT"
printf 'EVIDENCE RESULT: %s\n' "$EVIDENCE_RESULT"
printf 'OVERALL RESULT: %s\n' "$OVERALL_RESULT"
printf 'REMOTE_EVIDENCE: %s\n' "$REMOTE_EVIDENCE"
printf 'terminal_log=%s\n' "$TERMINAL_LOG"
printf 'command_report=%s\n' "$COMMAND_REPORT"
printf 'NEXT_CHAT_REPLY: %s\n' "$NEXT_CHAT_REPLY"
printf '### RESULT: %s ###\n' "$OVERALL_RESULT"
printf '================================================================\n'

test "$OVERALL_RESULT" = PASS
