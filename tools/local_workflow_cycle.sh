#!/usr/bin/env bash
set -euo pipefail

STATE_FILE=".agentic/workflow_state"
STATE="$(tr -d "[:space:]" < "$STATE_FILE")"

if [ "$STATE" = "TEST" ]; then
  OUT="$(./tools/capture_workflow_output.sh)"
  printf "%s\n" "UPLOAD" > "$STATE_FILE"
  printf "Captured workflow output: %s\n" "$OUT"
  printf "%s\n" "Next state: UPLOAD"
  exit 0
fi

if [ "$STATE" = "UPLOAD" ]; then
  git add .agentic/workflow_state docs/reports/CURRENT_WORKFLOW_OUTPUT.md tests/test_workflow_state.py tools/capture_workflow_output.sh tools/local_workflow_cycle.sh
  git add -f tmp/agent-evidence/workflow-output-*.md
  git commit -m "Add temporary workflow evidence"
  git push -u origin "$(git branch --show-current)"
  printf "%s\n" "TEST" > "$STATE_FILE"
  printf "%s\n" "Uploaded workflow evidence. Local state reset to TEST; commit the reset separately if desired."
  exit 0
fi

printf "Invalid workflow state: %s\n" "$STATE" >&2
exit 1
