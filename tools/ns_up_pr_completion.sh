#!/usr/bin/env sh
set -eu
STATUS=0

printf "\n\n\n"
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf "\n\n\n"
printf "NS UP PR COMPLETION CYCLE\n\n"

printf "\n### SAFETY ###\n"
printf "Safety: bounded PR completion cycle; waits for checks, squash-merges the current PR only, updates main, and runs local gates.\n"

printf "\n### BRANCH / STATUS ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1

printf "\n### IDENTIFY CURRENT PR ###\n"
PR_NUMBER=""
if PR_NUMBER="$(gh pr view --json number --jq .number)"; then
  printf "PR_NUMBER=%s\n" "$PR_NUMBER"
else
  printf "ERROR: no current PR found for this branch.\n"
  STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### PR VIEW ###\n"
  gh pr view "$PR_NUMBER" --json number,title,state,mergeable,headRefName,baseRefName,statusCheckRollup || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### PR CHECKS ###\n"
  gh pr checks "$PR_NUMBER" || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### WAIT FOR GREEN CHECKS AND MERGE ###\n"
  if gh pr checks "$PR_NUMBER" --watch; then
    gh pr merge "$PR_NUMBER" --squash --delete-branch || STATUS=1
  else
    STATUS=1
  fi
fi

printf "\n### UPDATE MAIN ###\n"
git switch main || STATUS=1
git pull --ff-only origin main || STATUS=1

printf "\n### VERIFY MAIN ###\n"
./ns dev || STATUS=1
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli pr-hygiene || STATUS=1

printf "\n### FINAL MAIN STATE ###\n"
git branch --show-current || STATUS=1
git log --oneline -8 || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
