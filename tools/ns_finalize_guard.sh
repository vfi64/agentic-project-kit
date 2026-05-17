#!/usr/bin/env sh
set -eu
STATUS=0

BRANCH="${1:-}"
MARKER="${2:-}"
if [ -z "$BRANCH" ]; then
  printf "%s\n" "ERROR: missing finalization branch. Usage: ./ns finalize-guard <branch> [marker-text]"
  printf "%s\n" "STATUS: FAIL_NEEDS_HUMAN_REVIEW"
  printf "%s\n" "### RESULT: FAIL ###"
  exit 1
fi

printf "\n\n\n"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------------"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS FINALIZATION GUARD\n\n"
printf "Safety: idempotent finalization branch guard; no commit, push, PR, merge, tag, release, branch deletion, or file mutation.\n"

printf "\n### UPDATE MAIN REFERENCES ###\n"
if ! git fetch origin main >/dev/null 2>&1; then
  printf "Could not fetch origin/main.\n"
  printf "STATUS: FAIL_NEEDS_HUMAN_REVIEW\n"
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi

printf "\n### CURRENT STATE ###\n"
CURRENT_BRANCH="$(git branch --show-current)" || STATUS=1
printf "current_branch=%s\n" "$CURRENT_BRANCH"
printf "target_branch=%s\n" "$BRANCH"
git status --short || STATUS=1
if [ "$STATUS" -ne 0 ]; then
  printf "STATUS: FAIL_NEEDS_HUMAN_REVIEW\n"
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi

printf "\n### MARKER CHECK ON MAIN ###\n"
MARKER_ON_MAIN=0
if [ -n "$MARKER" ]; then
  if git grep -F "$MARKER" origin/main -- docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md >/dev/null 2>&1; then
    MARKER_ON_MAIN=1
    printf "marker_already_on_main=true\n"
    printf "STATUS: PASS_ALREADY_ON_MAIN\n"
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
  printf "Finalization branch does not exist; no cleanup or PR action is needed by this guard.\n"
  printf "STATUS: PASS_NOOP_BRANCH\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

if [ "$REMOTE_EXISTS" -eq 1 ]; then
  git fetch origin "$BRANCH" >/dev/null 2>&1 || STATUS=1
fi
if [ "$STATUS" -ne 0 ]; then
  printf "STATUS: FAIL_NEEDS_HUMAN_REVIEW\n"
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi

printf "\n### AHEAD / BEHIND CHECK ###\n"
COMPARE_REF="$BRANCH"
if [ "$LOCAL_EXISTS" -eq 0 ] && [ "$REMOTE_EXISTS" -eq 1 ]; then
  COMPARE_REF="origin/$BRANCH"
fi
COUNTS="$(git rev-list --left-right --count origin/main..."$COMPARE_REF")" || STATUS=1
if [ "$STATUS" -ne 0 ]; then
  printf "STATUS: FAIL_NEEDS_HUMAN_REVIEW\n"
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi
BEHIND="$(printf "%s" "$COUNTS" | awk "{print \$1}")"
AHEAD="$(printf "%s" "$COUNTS" | awk "{print \$2}")"
printf "commits_behind_main=%s\n" "$BEHIND"
printf "commits_ahead_of_main=%s\n" "$AHEAD"

if [ "$AHEAD" = "0" ]; then
  printf "Idempotent completion: finalization branch has no commits ahead of main.\n"
  printf "STATUS: PASS_NOOP_BRANCH\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

printf "\n### CONFLICT CLASSIFICATION ###\n"
TMP_BRANCH="tmp-finalize-guard-check-$$"
git switch --quiet --detach origin/main || STATUS=1
git switch --quiet -c "$TMP_BRANCH" || STATUS=1
if [ "$STATUS" -ne 0 ]; then
  git switch --quiet "$CURRENT_BRANCH" >/dev/null 2>&1 || true
  git branch -D "$TMP_BRANCH" >/dev/null 2>&1 || true
  printf "STATUS: FAIL_NEEDS_HUMAN_REVIEW\n"
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi
set +e
git merge --no-commit --no-ff "$COMPARE_REF" >/tmp/ns_finalize_guard_merge.out 2>/tmp/ns_finalize_guard_merge.err
MERGE_STATUS="$?"
set -e
git merge --abort >/dev/null 2>&1 || true
git switch --quiet "$CURRENT_BRANCH" >/dev/null 2>&1 || true
git branch -D "$TMP_BRANCH" >/dev/null 2>&1 || true
if [ "$MERGE_STATUS" = "0" ]; then
  printf "merge_conflict=false\n"
  printf "STATUS: PASS_NEEDS_PR\n"
  printf "Finalization branch has relevant commits and appears mergeable; continue normal PR path.\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi
printf "merge_conflict=true\n"
if [ "$MARKER_ON_MAIN" -eq 1 ]; then
  printf "STATUS: PASS_SUPERSEDED\n"
  printf "Finalization branch conflicts but requested marker is already represented on main.\n"
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi
printf "STATUS: FAIL_CONFLICT_RELEVANT\n"
printf "Finalization branch has commits ahead of main and conflicts; human review is required.\n"
printf "\n### RESULT: FAIL ###\n"
exit 1
