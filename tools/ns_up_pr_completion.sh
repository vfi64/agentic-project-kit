#!/usr/bin/env sh
set -eu
STATUS=0
MERGED=0

printf "\n\n\n"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------------"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS UP PR COMPLETION CYCLE\n\n"

printf "\n### SAFETY ###\n"
printf "Safety: bounded PR completion cycle; waits for checks, squash-merges the current PR only, updates main only after a successful merge, and runs local gates.\n"

printf "\n### BRANCH / STATUS ###\n"
BRANCH="$(git branch --show-current)" || STATUS=1
printf "branch=%s\n" "$BRANCH"
git status --short || STATUS=1

if [ "$BRANCH" = "main" ]; then
  printf "ERROR: ./ns up must run from a PR branch, not main.\n"
  STATUS=1
fi

if [ -n "$(git status --porcelain)" ]; then
  printf "ERROR: working tree is dirty. Commit or restore changes before ./ns up.\n"
  printf "Hint: run ./ns clean-evidence if the dirtiness is only workflow evidence under tmp/agent-evidence or docs/reports/CURRENT_WORKFLOW_OUTPUT.md.\n"
  printf "Then rerun ./ns up after reviewing git status --short.\n"
  STATUS=1
fi

printf "\n### NO-OP BRANCH CHECK ###\n"
if [ "$BRANCH" != "main" ]; then
  BASE_DIFF="$(git rev-list --count main.."$BRANCH" 2>/dev/null || printf "unknown")"
  printf "commits_ahead_of_main=%s\n" "$BASE_DIFF"
  if [ "$BASE_DIFF" = "0" ]; then
    printf "Branch has no commits ahead of main; treating as idempotent no-op completion.\n"
    git switch main || STATUS=1
    git pull --ff-only origin main || STATUS=1
    printf "\n### VERIFY MAIN ###\n"
    ./ns dev || STATUS=1
    PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli pr-hygiene || STATUS=1
    printf "\n### FINAL STATE ###\n"
    git branch --show-current || STATUS=1
    git log --oneline -8 || STATUS=1
    git status --short || STATUS=1
    if [ "$STATUS" -eq 0 ]; then
      printf "\n### RESULT: PASS ###\n"
    else
      printf "\n### RESULT: FAIL ###\n"
    fi
    exit "$STATUS"
  fi
fi

printf "\n### IDENTIFY CURRENT PR ###\n"
PR_NUMBER=""
if [ "$STATUS" -eq 0 ]; then
  if PR_NUMBER="$(gh pr view --json number --jq .number)"; then
    printf "PR_NUMBER=%s\n" "$PR_NUMBER"
  else
    printf "ERROR: no current PR found for this branch.\n"
    STATUS=1
  fi
fi

PR_STATE=""
MERGEABLE=""
if [ "$STATUS" -eq 0 ]; then
  printf "\n### PR VIEW ###\n"
  gh pr view "$PR_NUMBER" --json number,title,state,mergeable,headRefName,baseRefName,statusCheckRollup || STATUS=1
  PR_STATE="$(gh pr view "$PR_NUMBER" --json state --jq .state)" || STATUS=1
  MERGEABLE="$(gh pr view "$PR_NUMBER" --json mergeable --jq .mergeable)" || STATUS=1
  printf "state=%s\n" "$PR_STATE"
  printf "mergeable=%s\n" "$MERGEABLE"
  if [ "$PR_STATE" = "MERGED" ]; then
    printf "PR is already merged; treating this as an idempotent completion state.\n"
    MERGED=1
  elif [ "$MERGEABLE" != "MERGEABLE" ]; then
    printf "ERROR: PR is not mergeable. Resolve conflicts or wait for GitHub to compute mergeability before ./ns up.\n"
    STATUS=1
  fi
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### PR CHECKS SNAPSHOT ###\n"
  gh pr checks "$PR_NUMBER" || true
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### WAIT FOR GREEN CHECKS AND MERGE ###\n"
  if gh pr checks "$PR_NUMBER" --watch; then
    if gh pr merge "$PR_NUMBER" --squash --delete-branch; then
      MERGED=1
    else
      STATUS=1
    fi
  else
    STATUS=1
  fi
fi

if [ "$MERGED" -eq 1 ]; then
  printf "\n### UPDATE MAIN ###\n"
  git switch main || STATUS=1
  git pull --ff-only origin main || STATUS=1

  printf "\n### VERIFY MAIN ###\n"
  ./ns dev || STATUS=1
  PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli pr-hygiene || STATUS=1
else
  printf "\n### UPDATE MAIN SKIPPED ###\n"
  printf "Main update skipped because PR merge did not complete successfully.\n"
fi

printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git log --oneline -8 || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
