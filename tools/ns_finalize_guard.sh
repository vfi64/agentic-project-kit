#!/usr/bin/env sh
set -eu
STATUS=0

BRANCH="${1:-}"
MARKER="${2:-}"
if [ -z "$BRANCH" ]; then
  printf "%s\n" "ERROR: missing finalization branch. Usage: ./ns finalize-guard <branch> [marker-text]"
  exit 1
fi

printf "\n\n\n"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------------"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS FINALIZATION GUARD\n\n"
printf "Safety: idempotent finalization branch guard; no commit, push, PR, merge, tag, release, or branch deletion.\n"

printf "\n### UPDATE MAIN REFERENCES ###\n"
git fetch origin main >/dev/null 2>&1 || STATUS=1

printf "\n### CURRENT STATE ###\n"
CURRENT_BRANCH="$(git branch --show-current)" || STATUS=1
printf "current_branch=%s\n" "$CURRENT_BRANCH"
printf "target_branch=%s\n" "$BRANCH"
git status --short || STATUS=1

printf "\n### MARKER CHECK ON MAIN ###\n"
if [ -n "$MARKER" ]; then
  if git grep -F "$MARKER" origin/main -- docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md >/dev/null 2>&1; then
    printf "marker_already_on_main=true\n"
    printf "Idempotent completion: requested finalization marker is already present on main.\n"
    printf "\n### RESULT: PASS ###\n"
    exit 0
  fi
  printf "marker_already_on_main=false\n"
else
  printf "marker_check=skipped\n"
fi

printf "\n### BRANCH EXISTENCE CHECK ###\n"
LOCAL_EXISTS=0
REMOTE_EXISTS=0
git show-ref --verify --quiet "refs/heads/$BRANCH" && LOCAL_EXISTS=1 || true
git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1 && REMOTE_EXISTS=1 || true
printf "local_branch_exists=%s\n" "$LOCAL_EXISTS"
printf "remote_branch_exists=%s\n" "$REMOTE_EXISTS"

if [ "$LOCAL_EXISTS" -eq 0 ] && [ "$REMOTE_EXISTS" -eq 0 ]; then
  printf "Finalization branch does not exist yet; safe to create it.\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

if [ "$REMOTE_EXISTS" -eq 1 ]; then
  git fetch origin "$BRANCH" >/dev/null 2>&1 || STATUS=1
fi

printf "\n### AHEAD / BEHIND CHECK ###\n"
COMPARE_REF="$BRANCH"
if [ "$LOCAL_EXISTS" -eq 0 ] && [ "$REMOTE_EXISTS" -eq 1 ]; then
  COMPARE_REF="origin/$BRANCH"
fi
COUNTS="$(git rev-list --left-right --count origin/main..."$COMPARE_REF")" || STATUS=1
BEHIND="$(printf "%s" "$COUNTS" | awk "{print \$1}")"
AHEAD="$(printf "%s" "$COUNTS" | awk "{print \$2}")"
printf "commits_behind_main=%s\n" "$BEHIND"
printf "commits_ahead_of_main=%s\n" "$AHEAD"

if [ "$AHEAD" = "0" ]; then
  printf "Idempotent completion: finalization branch has no commits ahead of main.\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

printf "Finalization branch has commits ahead of main; continue normal PR path.\n"
if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi
exit "$STATUS"
