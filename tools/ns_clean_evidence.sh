#!/usr/bin/env sh
set -eu
STATUS=0

printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS CLEAN EVIDENCE\n\n"

printf "\n### SAFETY ###\n"
printf "%s\n" "Safety: removes ignored tmp evidence and restores known tracked workflow evidence only; does not delete arbitrary docs/reports files."

printf "\n### BEFORE STATUS ###\n"
git status --short || STATUS=1

printf "\n### RESTORE KNOWN TRACKED WORKFLOW EVIDENCE ###\n"
for path in .agentic/workflow_state docs/reports/CURRENT_WORKFLOW_OUTPUT.md
do
  if git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    if ! git diff --quiet -- "$path" 2>/dev/null || ! git diff --cached --quiet -- "$path" 2>/dev/null; then
      printf "restore_tracked=%s\n" "$path"
      git restore --staged --worktree "$path" || STATUS=1
    else
      printf "clean_tracked=%s\n" "$path"
    fi
  else
    printf "skip_untracked_path=%s\n" "$path"
  fi
done

printf "\n### REMOVE IGNORED TMP EVIDENCE ###\n"
if [ -d tmp/agent-evidence ]; then
  printf "%s\n" "remove_ignored_dir=tmp/agent-evidence"
  rm -rf tmp/agent-evidence || STATUS=1
else
  printf "%s\n" "no_ignored_tmp_evidence=tmp/agent-evidence"
fi

printf "\n### UNTRACKED DOC REPORTS REVIEW ###\n"
UNTRACKED_REPORTS="$(git status --short docs/reports 2>/dev/null | grep "^?? " || true)"
if [ -n "$UNTRACKED_REPORTS" ]; then
  printf "%s\n" "$UNTRACKED_REPORTS"
  printf "%s\n" "NEEDS_HUMAN_REVIEW: untracked docs/reports files were not deleted automatically."
  STATUS=1
else
  printf "%s\n" "No untracked docs/reports files found."
fi

printf "\n### AFTER STATUS ###\n"
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
