#!/usr/bin/env sh
set -eu
STATUS=0

printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS PR CLEANUP CLASSIFICATION\n\n"

printf "### SAFETY ###\n"
printf "%s\n" "Safety: read-only PR classification; no close, merge, edit, push, delete, tag, or release action."

if ! command -v gh >/dev/null 2>&1; then
  printf "%s\n" "ERROR: gh CLI is required for PR classification."
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi

printf "\n### OPEN PR CLASSIFICATION ###\n"
TMP_FILE="$(mktemp "${TMPDIR:-/tmp}/ns-pr-cleanup.XXXXXX")"
trap 'rm -f "$TMP_FILE"' EXIT HUP INT TERM

if ! gh pr list --state open --limit 100 --json number,headRefName,baseRefName,mergeable,isDraft,title,author,updatedAt --jq '.[] | [.number, .headRefName, .baseRefName, .mergeable, .isDraft, .author.login, .updatedAt, .title] | @tsv' > "$TMP_FILE"; then
  printf "%s\n" "ERROR: unable to list open PRs."
  printf "\n### RESULT: FAIL ###\n"
  exit 1
fi

COUNT="$(wc -l < "$TMP_FILE" | tr -d " ")"
printf "open_pr_count=%s\n" "$COUNT"

if [ "$COUNT" = "0" ]; then
  printf "%s\n" "No open PRs found."
  printf "\n### FINAL STATE ###\n"
  git branch --show-current || STATUS=1
  git status --short || STATUS=1
  printf "\n### RESULT: PASS ###\n"
  exit 0
fi

TAB="$(printf "\t")"
while IFS="$TAB" read -r NUMBER HEAD BASE MERGEABLE DRAFT AUTHOR UPDATED TITLE
do
  CLASS="ACTIVE_FEATURE_PR"
  ACTION="review_manually"

  case "$HEAD" in
    dependabot/*)
      CLASS="DEPENDABOT_PR"
      ACTION="review_dependency_update"
      ;;
    docs/finalize-*|docs/record-*|docs/post-*)
      CLASS="STALE_DOCS_FINALIZATION_CANDIDATE"
      ACTION="run_finalize_guard_before_closing_or_recreating"
      ;;
    release/prepare-*)
      CLASS="RELEASE_PREP_PR"
      ACTION="verify_release_state_before_merge_or_close"
      ;;
  esac

  if [ "$MERGEABLE" = "CONFLICTING" ]; then
    if [ "$CLASS" = "STALE_DOCS_FINALIZATION_CANDIDATE" ]; then
      CLASS="SUPERSEDED_OR_CONFLICTING_DOCS_FINALIZATION"
      ACTION="run_finalize_guard_then_human_decide_safe_close"
    elif [ "$CLASS" = "DEPENDABOT_PR" ]; then
      ACTION="review_dependency_conflict"
    else
      CLASS="CONFLICTING_RELEVANT_PR"
      ACTION="human_review_required"
    fi
  fi

  if [ "$DRAFT" = "true" ]; then
    ACTION="draft_review_required"
  fi

  printf "#%s class=%s action=%s mergeable=%s draft=%s head=%s base=%s author=%s updated=%s title=%s\n" "$NUMBER" "$CLASS" "$ACTION" "$MERGEABLE" "$DRAFT" "$HEAD" "$BASE" "$AUTHOR" "$UPDATED" "$TITLE"
done < "$TMP_FILE"

printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi
exit "$STATUS"
