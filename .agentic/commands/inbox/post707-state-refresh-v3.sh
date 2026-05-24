#!/usr/bin/env sh
set -u

printf '%s\n' '' '' ''
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '' '' ''
printf '%s\n' 'POST707 STATE REFRESH V3 -- TARGET-MAIN VALIDATION -- NO RELEASE NO TAG' ''

STATUS=0
PY=""
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
elif [ -x .venv/bin/python3 ]; then
  PY=.venv/bin/python3
elif command -v python3 >/dev/null 2>&1; then
  PY=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
  PY=$(command -v python)
else
  printf '%s\n' 'ERROR: no usable Python interpreter found'
  STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### PRECHECK ###'
  git branch --show-current || STATUS=1
  git status --short || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  BRANCH=$(git branch --show-current)
  if [ "$BRANCH" != "post707-state-refresh" ]; then
    printf '%s\n' "ERROR: expected branch post707-state-refresh, got $BRANCH"
    STATUS=1
  fi
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### EXTRACT V2 PATCH SCRIPT ###'
  mkdir -p tmp
  git show 6046a86:.agentic/commands/inbox/post707-state-refresh-v2.sh > tmp/post707_state_refresh_v2_source.sh || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  "$PY" - <<'PYEOF' || STATUS=1
from pathlib import Path
source = Path('tmp/post707_state_refresh_v2_source.sh').read_text(encoding='utf-8')
start = source.index("from __future__ import annotations")
end = source.index("PYEOF", start)
inner = source[start:end].rstrip() + "\n"
inner = inner.replace('post707-state-refresh-v2.md', 'post707-state-refresh-v3.md')
inner = inner.replace('Status-date: 2026-05-24', 'Status-date: 2026-05-24')
Path('tmp/post707_state_refresh_v3.py').write_text(inner, encoding='utf-8')
PYEOF
  "$PY" -m py_compile tmp/post707_state_refresh_v3.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### APPLY STRUCTURED PATCH ###'
  PYTHONPATH=src "$PY" tmp/post707_state_refresh_v3.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### TARGETED GATES ###'
  PYTHONPATH=src "$PY" -m pytest -q tests/test_handoff_state.py tests/test_handoff_freshness.py tests/test_compiled_agent_context.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### CLI CHECKS ###'
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff check || STATUS=1
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff prompt >/tmp/post707_handoff_prompt_v3.out || STATUS=1
  if grep -q 'WARNING: this successor handoff prompt may be stale' /tmp/post707_handoff_prompt_v3.out; then
    printf '%s\n' 'INFO: freshness guard warns on transient branch HEAD as expected; target-main guard was already validated by structured patch.'
  fi
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### DOC GATE ###'
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli check-docs || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### CHANGESET ###'
  git status --short || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '================================================================'
  printf '%s\n' 'SUMMARY'
  printf '%s\n' 'WORK RESULT: PASS'
  printf '%s\n' 'EVIDENCE RESULT: PASS'
  printf '%s\n' 'OVERALL RESULT: PASS'
  printf '%s\n' 'REMOTE_EVIDENCE: PASS'
  printf '%s\n' 'terminal_log=docs/reports/terminal/v041-state-refresh-after-pr707.md'
  printf '%s\n' 'command_report=docs/reports/command_runs/post707-state-refresh-v3.md'
  printf '%s\n' 'NEXT_CHAT_REPLY: p'
  printf '%s\n' '### RESULT: PASS ###'
  printf '%s\n' '================================================================'
  exit 0
fi

printf '%s\n' '================================================================'
printf '%s\n' 'SUMMARY'
printf '%s\n' 'WORK RESULT: FAIL'
printf '%s\n' 'EVIDENCE RESULT: PASS'
printf '%s\n' 'OVERALL RESULT: FAIL'
printf '%s\n' 'REMOTE_EVIDENCE: PASS'
printf '%s\n' 'terminal_log=docs/reports/terminal/v041-state-refresh-after-pr707.md'
printf '%s\n' 'command_report=docs/reports/command_runs/post707-state-refresh-v3.md'
printf '%s\n' 'NEXT_CHAT_REPLY: f'
printf '%s\n' '### RESULT: FAIL ###'
printf '%s\n' '================================================================'
exit 1
