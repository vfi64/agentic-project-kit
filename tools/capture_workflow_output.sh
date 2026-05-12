#!/usr/bin/env bash
set -u

mkdir -p tmp/agent-evidence docs/reports
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="tmp/agent-evidence/workflow-output-${STAMP}.md"

{
  echo "# Workflow output"
  echo
  echo "Date: $(date "+%Y-%m-%d %H:%M:%S")"
  echo "Branch: $(git branch --show-current)"
  echo
  echo "## Git status"
  git status --short
  echo
  echo "## Git log"
  git log --oneline -10
  echo
  echo "## Screen-control gate"
  ./tools/screen_control_gate.sh
} > "$OUT" 2>&1

{
  echo "# Current workflow output"
  echo
  echo "Date: $(date "+%Y-%m-%d %H:%M:%S")"
  echo "Branch: $(git branch --show-current)"
  echo
  echo "## Purpose"
  echo
  echo "Captured complete workflow output for remote handoff."
  echo
  echo "## Evidence file"
  echo
  echo "$OUT"
} > docs/reports/CURRENT_WORKFLOW_OUTPUT.md

printf "%s
" "$OUT"
