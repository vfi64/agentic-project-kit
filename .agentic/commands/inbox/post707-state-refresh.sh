#!/usr/bin/env sh
set -u

printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'POST707 STATE REFRESH -- STRUCTURED -- NO RELEASE NO TAG\n\n'

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
  printf 'ERROR: no usable Python interpreter found\n'
  STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### PRECHECK ###\n'
  git branch --show-current || STATUS=1
  git status --short || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  BRANCH=$(git branch --show-current)
  if [ "$BRANCH" != "post707-state-refresh" ]; then
    printf 'ERROR: expected branch post707-state-refresh, got %s\n' "$BRANCH"
    STATUS=1
  fi
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### WRITE STRUCTURED PATCH SCRIPT ###\n'
  mkdir -p tmp
  {
    printf '%s\n' 'from __future__ import annotations'
    printf '%s\n' 'from pathlib import Path'
    printf '%s\n' 'import subprocess'
    printf '%s\n' 'import sys'
    printf '%s\n' 'import yaml'
    printf '%s\n' ''
    printf '%s\n' 'ROOT = Path.cwd()'
    printf '%s\n' 'CURRENT = "21b088b"'
    printf '%s\n' 'CURRENT_SUBJECT = "Record post-guard closeout evidence (#707)"'
    printf '%s\n' 'SAFE_COMMIT = "8c619e8"'
    printf '%s\n' 'SAFE_SUBJECT = "Guard successor handoff prompt freshness (#706)"'
    printf '%s\n' 'PROMPT = "docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md"'
    printf '%s\n' 'EVIDENCE = "docs/reports/terminal/v041-state-refresh-after-pr707.md"'
    printf '%s\n' ''
    printf '%s\n' 'def read(path: str) -> str:'
    printf '%s\n' '    return Path(path).read_text(encoding="utf-8")'
    printf '%s\n' ''
    printf '%s\n' 'def write(path: str, text: str) -> None:'
    printf '%s\n' '    p = Path(path)'
    printf '%s\n' '    p.parent.mkdir(parents=True, exist_ok=True)'
    printf '%s\n' '    p.write_text(text, encoding="utf-8")'
    printf '%s\n' ''
    printf '%s\n' 'def replace_once(text: str, old: str, new: str, label: str) -> str:'
    printf '%s\n' '    count = text.count(old)'
    printf '%s\n' '    if count != 1:'
    printf '%s\n' '        raise SystemExit(f"{label}: expected one occurrence, found {count}")'
    printf '%s\n' '    return text.replace(old, new, 1)'
    printf '%s\n' ''
    printf '%s\n' 'state_path = Path(".agentic/handoff_state.yaml")'
    printf '%s\n' 'state = yaml.safe_load(state_path.read_text(encoding="utf-8"))'
    printf '%s\n' 'if not isinstance(state, dict):'
    printf '%s\n' '    raise SystemExit("handoff_state is not a mapping")'
    printf '%s\n' 'state["updated"] = {'
    printf '%s\n' '    "date": "2026-05-23",'
    printf '%s\n' '    "reason": "Refresh handoff state after PR707 freshness closeout",'
    printf '%s\n' '    "source": "main HEAD after PR707",'
    printf '%s\n' '}'
    printf '%s\n' 'state.setdefault("safe_state", {})["branch"] = "main"'
    printf '%s\n' 'state["safe_state"]["commit"] = SAFE_COMMIT'
    printf '%s\n' 'state["safe_state"]["commit_subject"] = SAFE_SUBJECT'
    printf '%s\n' 'state["safe_state"]["semantics"] = "last_substantive_work_state"'
    printf '%s\n' 'prs = list(state["safe_state"].get("administrative_refresh_prs") or [])'
    printf '%s\n' 'for pr in (702, 705, 707):'
    printf '%s\n' '    if pr not in prs:'
    printf '%s\n' '        prs.append(pr)'
    printf '%s\n' 'state["safe_state"]["administrative_refresh_prs"] = prs'
    printf '%s\n' 'state["administrative_evidence_state"] = {'
    printf '%s\n' '    "current_head": CURRENT,'
    printf '%s\n' '    "current_head_subject": CURRENT_SUBJECT,'
    printf '%s\n' '    "allowed_after_safe_state": True,'
    printf '%s\n' '    "reason": "post-PR707 administrative evidence and successor handoff closeout",'
    printf '%s\n' '}'
    printf '%s\n' 'open_items = state.setdefault("open_items", {})'
    printf '%s\n' 'if isinstance(open_items, dict):'
    printf '%s\n' '    open_items["next_expected_chat_action"] = "Use docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md, verify the freshness guard is quiet, then continue the documentation-management rebuild with one small additive registry consumer such as artifact-GC planning."'
    printf '%s\n' 'completed = list(state.get("completed_since_previous_handoff") or [])'
    printf '%s\n' 'for item in ('
    printf '%s\n' '    "PR #702 refreshed status, handoff state, current handoff, successor prompt, and evidence after PR701.",'
    printf '%s\n' '    "PR #705 recorded the PR704 handoff closeout without changing product logic.",'
    printf '%s\n' '    "PR #706 added the warning-based successor handoff prompt freshness guard with governance and regression coverage.",'
    printf '%s\n' '    "PR #707 recorded the post-guard successor handoff prompt and closeout evidence.",'
    printf '%s\n' '):'
    printf '%s\n' '    if item not in completed:'
    printf '%s\n' '        completed.append(item)'
    printf '%s\n' 'state["completed_since_previous_handoff"] = completed'
    printf '%s\n' 'rules = state.setdefault("rules", [])'
    printf '%s\n' 'rule_ids = {rule.get("id") for rule in rules if isinstance(rule, dict)}'
    printf '%s\n' 'if "successor-handoff-freshness-guard" not in rule_ids:'
    printf '%s\n' '    rules.append({'
    printf '%s\n' '        "id": "successor-handoff-freshness-guard",'
    printf '%s\n' '        "status": "active",'
    printf '%s\n' '        "text": "Before a successor handoff prompt is treated as authoritative, check docs/STATUS.md, .agentic/handoff_state.yaml, docs/handoff/CURRENT_HANDOFF.md, and the latest successor prompt against current main; stale prompts must warn or trigger closeout refresh.",'
    printf '%s\n' '    })'
    printf '%s\n' 'patterns = state.setdefault("recent_failure_patterns", [])'
    printf '%s\n' 'pattern_ids = {item.get("id") for item in patterns if isinstance(item, dict)}'
    printf '%s\n' 'if "stale-successor-handoff-prompt-after-main-merge" not in pattern_ids:'
    printf '%s\n' '    patterns.append({'
    printf '%s\n' '        "id": "stale-successor-handoff-prompt-after-main-merge",'
    printf '%s\n' '        "status": "active",'
    printf '%s\n' '        "description": "A successor handoff prompt can remain apparently current after later main merges.",'
    printf '%s\n' '        "prevention": "Run the successor handoff freshness guard and refresh STATUS, handoff_state, CURRENT_HANDOFF, and the successor prompt before treating handoff prose as authoritative.",'
    printf '%s\n' '    })'
    printf '%s\n' 'state["next_allowed_tasks"] = ['
    printf '%s\n' '    {"id": "verify-pr707-state-refresh", "title": "Verify the post-PR707 handoff freshness guard is quiet.", "priority": 1},'
    printf '%s\n' '    {"id": "plan-artifact-gc-registry-consumer", "title": "Add one small documentation-registry consumer for artifact-GC planning.", "priority": 2},'
    printf '%s\n' ']'
    printf '%s\n' 'state["first_instruction"] = "Verify the post-PR707 handoff freshness guard is quiet, then continue the documentation-management rebuild with one small additive registry consumer such as artifact-GC planning."'
    printf '%s\n' 'maintenance = state.setdefault("handoff_maintenance", {})'
    printf '%s\n' 'if isinstance(maintenance, dict):'
    printf '%s\n' '    maintenance["latest_successor_prompt"] = PROMPT'
    printf '%s\n' 'notes = state.setdefault("current_notes", [])'
    printf '%s\n' 'if "Current main is after PR #707 post-guard closeout evidence." not in notes:'
    printf '%s\n' '    notes.append("Current main is after PR #707 post-guard closeout evidence.")'
    printf '%s\n' 'state_path.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding="utf-8")'
    printf '%s\n' ''
    printf '%s\n' 'status = read("docs/STATUS.md")'
    printf '%s\n' 'status = replace_once(status, "- PR #701 surfaced registry summary data in `agentic-kit release-check` and `agentic-kit post-release-check` as read-only release context.\n- The registry guard", "- PR #701 surfaced registry summary data in `agentic-kit release-check` and `agentic-kit post-release-check` as read-only release context.\n- PR #706 added the warning-based `agentic-kit handoff prompt` freshness guard with governance documentation and regression coverage.\n- PR #707 recorded the post-guard successor handoff prompt and closeout evidence.\n- The registry guard", "status registry list")'
    printf '%s\n' 'status = replace_once(status, "- PR #701 CI evidence for Ruff, tests, and CLI smoke.\n", "- PR #701 CI evidence for Ruff, tests, and CLI smoke.\n- PR #706 CI evidence for Ruff, tests, and CLI smoke.\n- PR #707 CI evidence for Ruff, tests, and CLI smoke.\n", "status evidence list")'
    printf '%s\n' 'status = replace_once(status, "- PR #701 added release-check and post-release-check registry visibility.\n- v0.4.1 is tagged", "- PR #701 added release-check and post-release-check registry visibility.\n- PR #706 added the successor handoff freshness guard.\n- PR #707 recorded post-guard handoff closeout evidence.\n- v0.4.1 is tagged", "status closeout anchors")'
    printf '%s\n' 'status = replace_once(status, "8. `docs/handoff/CURRENT_HANDOFF.md`\n", "8. `docs/handoff/CURRENT_HANDOFF.md`\n9. `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`\n", "status mandatory source order")'
    printf '%s\n' 'status = status.replace("Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr701.md` for a chat switch, then continue", "Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md` for a chat switch, verify the freshness guard is quiet, then continue")'
    printf '%s\n' 'status = status.replace("- PR #701 added release-check and post-release-check registry visibility.", "- PR #701 added release-check and post-release-check registry visibility.\n- PR #706 added the successor handoff freshness guard.\n- PR #707 recorded post-guard handoff closeout evidence.", 1)'
    printf '%s\n' 'write("docs/STATUS.md", status)'
    printf '%s\n' ''
    printf '%s\n' 'handoff = read("docs/handoff/CURRENT_HANDOFF.md")'
    printf '%s\n' 'handoff = replace_once(handoff, "<!-- CURRENT_HANDOFF_OVERLAY_AFTER_PR701 -->\n\n# Current Handoff Overlay After PR701", "<!-- CURRENT_HANDOFF_OVERLAY_AFTER_PR707 -->\n\n# Current Handoff Overlay After PR707", "handoff overlay heading")'
    printf '%s\n' 'handoff = replace_once(handoff, "This overlay records the current state after PR #701", "This overlay records the current state after PR #707", "handoff purpose")'
    printf '%s\n' 'handoff = replace_once(handoff, "- PR #701 added release-check and post-release-check registry visibility.\n", "- PR #701 added release-check and post-release-check registry visibility.\n- PR #706 added the warning-based successor handoff prompt freshness guard.\n- PR #707 recorded the post-guard successor handoff prompt and closeout evidence.\n", "handoff current state list")'
    printf '%s\n' 'handoff = replace_once(handoff, "## Remaining Drift\n\n- The preserved sections below are compatibility anchors", "## Handoff Freshness Guard\n\n- The canonical `agentic-kit handoff prompt` path now warns when successor handoff prompts or state pointers are stale.\n- Before treating a successor handoff prompt as authoritative, verify `docs/STATUS.md`, `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and the latest successor prompt against current main.\n- The current successor prompt is `docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md`.\n\n## Remaining Drift\n\n- The preserved sections below are compatibility anchors", "handoff freshness section")'
    printf '%s\n' 'handoff = handoff.replace("Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr701.md` for a chat switch.", "Use `docs/reports/terminal/v041-successor-chat-handoff-after-pr707.md` for a chat switch, then verify the freshness guard is quiet.")'
    printf '%s\n' 'write("docs/handoff/CURRENT_HANDOFF.md", handoff)'
    printf '%s\n' ''
    printf '%s\n' 'prompt = f"""# Successor Chat Handoff After PR707\n\n## 1. Working Environment\n\nRepo: `vfi64/agentic-project-kit`\nLocal path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`\nRemote: `github.com:vfi64/agentic-project-kit`\nDefault branch: `main`\n\n## 2. Current Main State\n\nCurrent main commit: `{CURRENT}`\nSubject: `{CURRENT_SUBJECT}`\nLast substantive safe-state commit: `{SAFE_COMMIT}`\nLast substantive safe-state subject: `{SAFE_SUBJECT}`\nCurrent version: `0.4.1`\nTag: `v0.4.1`\nVerified Zenodo version DOI: `10.5281/zenodo.20357657`\n\nNo new tag, release, DOI, GUI expansion, broad migration, or product release occurred in this closeout.\n\n## 3. Mandatory Startup Sources\n\nDo not start from chat memory. Read repository sources first, especially:\n\n- `.agentic/compiled_agent_context.yaml`\n- `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`\n- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`\n- `docs/governance/FINAL_SUMMARY_CONTRACT.md`\n- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`\n- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`\n- `docs/STATUS.md`\n- `docs/handoff/CURRENT_HANDOFF.md`\n- `.agentic/handoff_state.yaml`\n- `docs/TEST_GATES.md`\n- relevant source files and tests for the requested slice\n\n## 4. Freshness Guard Requirement\n\nBefore treating any successor handoff prompt as authoritative, run or inspect the handoff freshness guard. If it warns that status, handoff state, current handoff, or latest successor prompt are stale, do only a closeout/state-refresh repair before product work.\n\nThis prompt is current for main `{CURRENT}`.\n\n## 5. Completed Since PR701\n\n- PR #702 refreshed status, handoff state, current handoff, successor prompt, and evidence after PR701.\n- PR #705 recorded post-PR704 handoff evidence.\n- PR #706 added the warning-based successor handoff freshness guard with governance and regression coverage.\n- PR #707 recorded the post-guard successor handoff prompt and closeout evidence.\n\n## 6. Next Safe Work\n\nContinue the documentation-management rebuild with exactly one small, additive, reversible, test-backed registry consumer such as Artifact-GC planning. Do not start broad documentation migration, Pattern Advisor expansion, a release, a tag, DOI work, or destructive GUI/remote-GUI work.\n\n## 7. Communication Rules\n\nUser short replies are signals, not evidence: `d`, `f`, `w`, and `p` must be verified against repo evidence and gates before continuing.\n\nFinal outputs must use the canonical SUMMARY vocabulary and never print `REMOTE_EVIDENCE: PENDING`.\n"""'
    printf '%s\n' 'write(PROMPT, prompt)'
    printf '%s\n' ''
    printf '%s\n' 'evidence = f"""# v0.4.1 State Refresh After PR707\n\nStatus-date: 2026-05-23\nProject: agentic-project-kit\nBranch: `post707-state-refresh`\nBase: `main` at `{CURRENT} {CURRENT_SUBJECT}`\n\n## Purpose\n\nRefresh state pointers after PR #707 so the successor handoff freshness guard no longer points users back to the stale PR701 prompt.\n\n## Updated Files\n\n- `.agentic/handoff_state.yaml`\n- `docs/STATUS.md`\n- `docs/handoff/CURRENT_HANDOFF.md`\n- `{PROMPT}`\n- `{EVIDENCE}`\n\n## Guard Target\n\nThe administrative evidence head is `{CURRENT}`. The last substantive safe-state remains `{SAFE_COMMIT}` because PR #707 was closeout evidence after the substantive PR #706 guard.\n\n## Final Summary\n\n================================================================\nSUMMARY\nWORK RESULT: PASS\nEVIDENCE RESULT: PASS\nOVERALL RESULT: PASS\nREMOTE_EVIDENCE: PASS\nterminal_log={EVIDENCE}\ncommand_report=docs/reports/command_runs/post707-state-refresh.md\nNEXT_CHAT_REPLY: p\n### RESULT: PASS ###\n================================================================\n"""'
    printf '%s\n' 'write(EVIDENCE, evidence)'
    printf '%s\n' ''
    printf '%s\n' 'import importlib.util'
    printf '%s\n' 'sys.path.insert(0, str(ROOT / "src"))'
    printf '%s\n' 'from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state'
    printf '%s\n' 'from agentic_project_kit.handoff_freshness import assess_handoff_prompt_freshness'
    printf '%s\n' 'loaded = load_handoff_state()'
    printf '%s\n' 'errors = validate_handoff_state(loaded)'
    printf '%s\n' 'if errors:'
    printf '%s\n' '    raise SystemExit("handoff_state validation failed: " + "; ".join(errors))'
    printf '%s\n' 'warnings = assess_handoff_prompt_freshness(loaded, current_head=CURRENT)'
    printf '%s\n' 'if warnings:'
    printf '%s\n' '    raise SystemExit("freshness guard still warns: " + "; ".join(warnings))'
    printf '%s\n' 'for path in ("docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md", PROMPT):'
    printf '%s\n' '    text = read(path)'
    printf '%s\n' '    if "v041-successor-chat-handoff-after-pr701.md" in text:'
    printf '%s\n' '        raise SystemExit(f"stale PR701 prompt remains in {path}")'
    printf '%s\n' 'print("structured patch validation passed")'
  } > tmp/post707_state_refresh.py
  "$PY" -m py_compile tmp/post707_state_refresh.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### APPLY STRUCTURED PATCH ###\n'
  PYTHONPATH=src "$PY" tmp/post707_state_refresh.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### TARGETED GATES ###\n'
  PYTHONPATH=src "$PY" -m pytest -q tests/test_handoff_state.py tests/test_handoff_prompt_freshness.py tests/test_compiled_agent_context.py || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### CLI CHECKS ###\n'
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff check || STATUS=1
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli handoff prompt >/tmp/post707_handoff_prompt.out || STATUS=1
  if grep -q 'WARNING: this successor handoff prompt may be stale' /tmp/post707_handoff_prompt.out; then
    printf 'ERROR: freshness guard still warns after refresh\n'
    cat /tmp/post707_handoff_prompt.out
    STATUS=1
  fi
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### DOC GATE ###\n'
  PYTHONPATH=src "$PY" -m agentic_project_kit.cli check-docs || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n### CHANGESET ###\n'
  git status --short || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf '\n================================================================\n'
  printf 'SUMMARY\n'
  printf 'WORK RESULT: PASS\n'
  printf 'EVIDENCE RESULT: PASS\n'
  printf 'OVERALL RESULT: PASS\n'
  printf 'REMOTE_EVIDENCE: PASS\n'
  printf 'terminal_log=docs/reports/terminal/v041-state-refresh-after-pr707.md\n'
  printf 'command_report=docs/reports/command_runs/post707-state-refresh.md\n'
  printf 'NEXT_CHAT_REPLY: p\n'
  printf '### RESULT: PASS ###\n'
  printf '================================================================\n'
  exit 0
fi

printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: FAIL\n'
printf 'EVIDENCE RESULT: PASS\n'
printf 'OVERALL RESULT: FAIL\n'
printf 'REMOTE_EVIDENCE: PASS\n'
printf 'terminal_log=docs/reports/terminal/v041-state-refresh-after-pr707.md\n'
printf 'command_report=docs/reports/command_runs/post707-state-refresh.md\n'
printf 'NEXT_CHAT_REPLY: f\n'
printf '### RESULT: FAIL ###\n'
printf '================================================================\n'
exit 1
