#!/usr/bin/env sh
set -eu
STATUS=0

TITLE="${1:-}"
BODY="${2:-}"
BASE="${3:-main}"

printf "\n\n\n"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------------"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS PR CREATE OR SKIP\n\n"

if [ -z "$TITLE" ]; then
  printf "ERROR: missing title argument.\n"
  printf "Usage: tools/ns_pr_create_or_skip.sh TITLE BODY [BASE]\n"
  exit 1
fi

BRANCH="$(git branch --show-current)" || STATUS=1
printf "\n### BRANCH / STATUS ###\n"
printf "branch=%s\n" "$BRANCH"
git status --short || STATUS=1

if [ "$BRANCH" = "$BASE" ]; then
  printf "No PR needed: current branch is base branch %s.\n" "$BASE"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

printf "\n### CHECK BRANCH DELTA ###\n"
git fetch origin "$BASE" || STATUS=1
DELTA="$(git rev-list --count "origin/$BASE..HEAD")" || STATUS=1
printf "commits_ahead_of_%s=%s\n" "$BASE" "$DELTA"

if [ "$STATUS" -eq 0 ] && [ "$DELTA" -eq 0 ]; then
  printf "No PR needed: branch has no commits ahead of origin/%s.\n" "$BASE"
  printf "This is an idempotent already-completed state, not a failure.\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

printf "\n### EXISTING PR CHECK ###\n"
if gh pr view --json number,title,state,url; then
  printf "Existing PR found for current branch.\n"
else
  printf "\n### CREATE PR ###\n"
  gh pr create --base "$BASE" --title "$TITLE" --body "$BODY" || STATUS=1
fi

printf "\n### PR STATUS ###\n"
gh pr status || STATUS=1

printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git log --oneline -6 || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
