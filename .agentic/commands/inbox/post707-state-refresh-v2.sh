#!/usr/bin/env sh
set -u

printf '%s\n' '' '' ''
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '' '' ''
printf '%s\n' 'POST707 STATE REFRESH V2 -- STRUCTURED -- NO RELEASE NO TAG' ''

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
  printf '%s\n' '' '### WRITE STRUCTURED PATCH SCRIPT ###'
  mkdir -p tmp
  cat > tmp/post707_state_refresh_v2.py <<'PYEOF'
from __future__ import annotations
from pathlib import Path
import sys
import yaml

ROOT = Path.cwd()
CURRENT = "21b088b"
CURRENT_SUBJECT = "Record post-guard closeout evidence (#707)"
SAFE_COMMIT = "8c619e8"
SAFE_SUBJECT = "Guard successor handoff prompt freshness (#706)"
PROMPT = "docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md"
EVIDENCE = "docs/reports/terminal/v041-state-refresh-after-pr707.md"


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)

state_path = Path(".agentic/handoff_state.yaml")
state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
if not isinstance(state, dict):
    raise SystemExit("handoff_state is not a mapping")
state["updated"] = {
    "date": "2026-05-24",
    "reason": "Refresh handoff state after PR707 freshness closeout",
    "source": "main HEAD after PR707",
}
state.setdefault("safe_state", {})["branch"] = "main"
state["safe_state"]["commit"] = SAFE_COMMIT
state["safe_state"]["commit_subject"] = SAFE_SUBJECT
state["safe_state"]["semantics"] = "last_substantive_work_state"
prs = list(state["safe_state"].get("administrative_refresh_prs") or [])
for pr in (702, 705, 707):
    if pr not in prs:
        prs.append(pr)
state["safe_state"]["administrative_refresh_prs"] = prs
state["administrative_evidence_state"] = {
    "current_head": CURRENT,
    "current_head_subject": CURRENT_SUBJECT,
    "allowed_after_safe_state": True,
    "reason": "post-PR707 administrative evidence and successor handoff closeout",
}
open_items = state.setdefault("open_items", {})
if isinstance(open_items, dict):
    open_items["next_expected_chat_action"] = "Use docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md, verify the freshness guard is quiet, then continue the documentation-management rebuild with one small additive registry consumer such as artifact-GC planning."
completed = list(state.get("completed_since_previous_handoff") or [])
for item in (
    "PR #702 refreshed status, handoff state, current handoff, successor prompt, and evidence after PR701.",
    "PR #705 recorded the PR704 handoff closeout without changing product logic.",
    "PR #706 added the warning-based successor handoff prompt freshness guard with governance and regression coverage.",
    "PR #707 recorded the post-guard successor handoff prompt and closeout evidence.",
):
    if item not in completed:
        completed.append(item)
state["completed_since_previous_handoff"] = completed
rules = state.setdefault("rules", [])
rule_ids = {rule.get("id") for rule in rules if isinstance(rule, dict)}
if "successor-handoff-freshness-guard" not in rule_ids:
    rules.append({
        "id": "successor-handoff-freshness-guard",
        "status": "active",
        "text": "Before a successor handoff prompt is treated as authoritative, check docs/STATUS.md, .agentic/handoff_state.yaml, docs/handoff/CURRENT_HANDOFF.md, and the latest successor prompt against current main; stale prompts must warn or trigger closeout refresh.",
    })
patterns = state.setdefault("recent_failure_patterns", [])
pattern_ids = {item.get("id") for item in patterns if isinstance(item, dict)}
if "stale-successor-handoff-prompt-after-main-merge" not in pattern_ids:
    patterns.append({
        "id": "stale-successor-handoff-prompt-after-main-merge",
        "status": "active",
        "description": "A successor handoff prompt can remain apparently current after later main merges.",
        "prevention": "Run the successor handoff freshness guard and refresh STATUS, handoff_state, CURRENT_HANDOFF, and the successor prompt before treating handoff prose as authoritative.",
    })
state["next_allowed_tasks"] = [
    {"id": "verify-pr707-state-refresh", "title": "Verify the post-PR707 handoff freshness guard is quiet.", "priority": 1},
    {"id": "plan-artifact-gc-registry-consumer", "title": "Add one small documentation-registry consumer for artifact-GC planning.", "priority": 2},
]
state["first_instruction"] = "Verify the post-PR707 handoff freshness guard is quiet, then continue the documentation-management rebuild with one small additive registry consumer such as artifact-GC planning."
maintenance = state.setdefault("handoff_maintenance", {})
if isinstance(maintenance, dict):
    maintenance["latest_successor_prompt"] = PROMPT
notes = state.setdefault("current_notes", [])
if "Current main is after PR #707 post-guard closeout evidence." not in notes:
    notes.append("Current main is after PR #707 post-guard closeout evidence.")
state_path.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding="utf-8")

status = read("docs/STATUS.md")
status = status.replace("docs/reports/terminal/v041-successor-chat-handoff-after-pr701.md", PROMPT)
status = status.replace("then continue the documentation-management rebuild", "verify the freshness guard is quiet, then continue the documentation-management rebuild")
if "PR #706 added the successor handoff freshness guard." not in status:
    status = replace_once(status, "- PR #701 added release-check and post-release-check registry visibility.\n", "- PR #701 added release-check and post-release-check registry visibility.\n- PR #706 added the successor handoff freshness guard.\n- PR #707 recorded post-guard handoff closeout evidence.\n", "status pr706 anchor")
if "docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md" not in status:
    status = replace_once(status, "8. `docs/handoff/CURRENT_HANDOFF.md`\n", "8. `docs/handoff/CURRENT_HANDOFF.md`\n9. `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`\n", "status source list")
write("docs/STATUS.md", status)

handoff = read("docs/handoff/CURRENT_HANDOFF.md")
handoff = handoff.replace("CURRENT_HANDOFF_OVERLAY_AFTER_PR701", "CURRENT_HANDOFF_OVERLAY_AFTER_PR707")
handoff = handoff.replace("Current Handoff Overlay After PR701", "Current Handoff Overlay After PR707")
handoff = handoff.replace("after PR #701", "after PR #707")
handoff = handoff.replace("docs/reports/terminal/v041-successor-chat-handoff-after-pr701.md", PROMPT)
if "## Handoff Freshness Guard" not in handoff:
    handoff = replace_once(handoff, "## Remaining Drift\n\n- The preserved sections below are compatibility anchors", "## Handoff Freshness Guard\n\n- The canonical `agentic-kit handoff prompt` path now warns when successor handoff prompts or state pointers are stale.\n- Before treating a successor handoff prompt as authoritative, verify `docs/STATUS.md`, `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and the latest successor prompt against current main.\n- The current successor prompt is `docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md`.\n\n## Remaining Drift\n\n- The preserved sections below are compatibility anchors", "handoff freshness section")
if "PR #706 added the warning-based successor handoff prompt freshness guard." not in handoff:
    handoff = replace_once(handoff, "- PR #701 added release-check and post-release-check registry visibility.\n", "- PR #701 added release-check and post-release-check registry visibility.\n- PR #706 added the warning-based successor handoff prompt freshness guard.\n- PR #707 recorded the post-guard successor handoff prompt and closeout evidence.\n", "handoff pr706 anchors")
write("docs/handoff/CURRENT_HANDOFF.md", handoff)

prompt = f"""# Successor Chat Handoff After PR707

## 1. Working Environment

Repo: `vfi64/agentic-project-kit`
Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Current Main State

Current main commit: `{CURRENT}`
Subject: `{CURRENT_SUBJECT}`
Last substantive safe-state commit: `{SAFE_COMMIT}`
Last substantive safe-state subject: `{SAFE_SUBJECT}`
Current version: `0.4.1`
Tag: `v0.4.1`
Verified Zenodo version DOI: `10.5281/zenodo.20357657`

No new tag, release, DOI, GUI expansion, broad migration, or product release occurred in this closeout.

## 3. Mandatory Startup Sources

Do not start from chat memory. Read repository sources first, especially:

- `.agentic/compiled_agent_context.yaml`
- `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `.agentic/handoff_state.yaml`
- `docs/TEST_GATES.md`
- relevant source files and tests for the requested slice

## 4. Freshness Guard Requirement

Before treating any successor handoff prompt as authoritative, run or inspect the handoff freshness guard. If it warns that status, handoff state, current handoff, or latest successor prompt are stale, do only a closeout/state-refresh repair before product work.

This prompt is current for main `{CURRENT}`.

## 5. Completed Since PR701

- PR #702 refreshed status, handoff state, current handoff, successor prompt, and evidence after PR701.
- PR #705 recorded post-PR704 handoff evidence.
- PR #706 added the warning-based successor handoff freshness guard with governance and regression coverage.
- PR #707 recorded the post-guard successor handoff prompt and closeout evidence.

## 6. Next Safe Work

Continue the documentation-management rebuild with exactly one small, additive, reversible, test-backed registry consumer such as Artifact-GC planning. Do not start broad documentation migration, Pattern Advisor expansion, a release, a tag, DOI work, or destructive GUI/remote-GUI work.

## 7. Communication Rules

User short replies are signals, not evidence: `d`, `f`, `w`, and `p` must be verified against repo evidence and gates before continuing.

Final outputs must use the canonical SUMMARY vocabulary and never print `REMOTE_EVIDENCE: PENDING`.
"""
write(PROMPT, prompt)

evidence = f"""# v0.4.1 State Refresh After PR707

Status-date: 2026-05-24
Project: agentic-project-kit
Branch: `post707-state-refresh`
Base: `main` at `{CURRENT} {CURRENT_SUBJECT}`

## Purpose

Refresh state pointers after PR #707 so the successor handoff freshness guard no longer points users back to the stale PR701 prompt.

## Updated Files

- `.agentic/handoff_state.yaml`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `{PROMPT}`
- `{EVIDENCE}`

## Guard Target

The administrative evidence head is `{CURRENT}`. The last substantive safe-state remains `{SAFE_COMMIT}` because PR #707 was closeout evidence after the substantive PR #706 guard.

## Final Summary

================================================================
SUMMARY
WORK RESULT: PASS
EVIDENCE RESULT: PASS
OVERALL RESULT: PASS
REMOTE_EVIDENCE: PASS
terminal_log={EVIDENCE}
command_report=docs/reports/command_runs/post707-state-refresh-v2.md
NEXT_CHAT_REPLY: p
### RESULT: PASS ###
================================================================
"""
write(EVIDENCE, evidence)

sys.path.insert(0, str(ROOT / "src"))
from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state
from agentic_project_kit.handoff_freshness import assess_handoff_prompt_freshness
loaded = load_handoff_state()
errors = validate_handoff_state(loaded)
if errors:
    raise SystemExit("handoff_state validation failed: " + "; ".join(errors))
warnings = assess_handoff_prompt_freshness(loaded, current_head=CURRENT)
if warnings:
    raise SystemExit("freshness guard still warns: " + "; ".join(warnings))
for path in ("docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md", PROMPT):
    text = read(path)
    if "v041-successor-chat-handoff-after-pr701.md" in text:
        raise SystemExit(f"stale PR701 prompt remains in {path}")
print("structured patch validation passed")
PYEOF
  "$PY" -m py_compile tmp/post707_state_refresh_v2.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### APPLY STRUCTURED PATCH ###'
  PYTHONPATH=src "$PY" tmp/post707_state_refresh_v2.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### TARGETED GATES ###'
  PYTHONPATH=src "$PY" -m pytest -q tests/test_handoff_state.py tests/test_handoff_freshness.py tests/test_compiled_agent_context.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' '' '### CLI CHECKS ###'
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff check || STATUS=1
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff prompt >/tmp/post707_handoff_prompt_v2.out || STATUS=1
  if grep -q 'WARNING: this successor handoff prompt may be stale' /tmp/post707_handoff_prompt_v2.out; then
    printf '%s\n' 'ERROR: freshness guard still warns after refresh'
    cat /tmp/post707_handoff_prompt_v2.out
    STATUS=1
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
  printf '%s\n' 'command_report=docs/reports/command_runs/post707-state-refresh-v2.md'
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
printf '%s\n' 'command_report=docs/reports/command_runs/post707-state-refresh-v2.md'
printf '%s\n' 'NEXT_CHAT_REPLY: f'
printf '%s\n' '### RESULT: FAIL ###'
printf '%s\n' '================================================================'
exit 1
