#!/usr/bin/env sh
set -eu
STATUS=0

PLAN_FILE="${1:-}"
if [ -z "$PLAN_FILE" ]; then
  printf "%s\n" "ERROR: missing plan file. Usage: ./ns slice-runner <plan-file>"
  printf "%s\n" "Plan format: one shell command per line; blank lines and lines starting with # are ignored."
  exit 1
fi

if [ ! -f "$PLAN_FILE" ]; then
  printf "ERROR: plan file not found: %s\n" "$PLAN_FILE"
  exit 1
fi

printf "\n\n\n"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------------"
printf "%s\n" "--------------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS SLICE RUNNER\n\n"

printf "\n### SAFETY ###\n"
printf "%s\n" "Safety: deterministic sequential runner; advances only after PASS and stops immediately on FAIL."
printf "plan=%s\n" "$PLAN_FILE"

STEP=0
while IFS= read -r COMMAND || [ -n "$COMMAND" ]; do
  case "$COMMAND" in
    "") continue ;;
    \#*) continue ;;
  esac
  STEP=$((STEP + 1))
  printf "\n### STEP %s ###\n" "$STEP"
  printf "%s\n" "$COMMAND"
  if sh -c "$COMMAND"; then
    printf "STEP %s RESULT: PASS\n" "$STEP"
  else
    STATUS=1
    printf "STEP %s RESULT: FAIL\n" "$STEP"
    printf "%s\n" "Stopping slice runner at first failing step."
    break
  fi
done < "$PLAN_FILE"

printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
