#!/usr/bin/env sh
set -eu
STATUS=0

PLAN_FILE="${1:-}"
if [ -z "$PLAN_FILE" ]; then
  printf "%s
" "ERROR: missing plan file. Usage: ./ns slice-runner <plan-file>"
  printf "%s
" "Plan format: one shell command per line; blank lines and lines starting with # are ignored."
  exit 1
fi

if [ ! -f "$PLAN_FILE" ]; then
  printf "ERROR: plan file not found: %s
" "$PLAN_FILE"
  exit 1
fi

printf "


"
printf "%s
" "--------------------------------------------------------------------------------"
printf "%s
" "--------------------------------------------------------------------------------"
printf "%s
" "--------------------------------------------------------------------------------"
printf "


"
printf "NS SLICE RUNNER

"

printf "
### SAFETY ###
"
printf "%s
" "Safety: deterministic sequential runner; advances only after target-state PASS and stops immediately on retryable or failing states."
printf "plan=%s
" "$PLAN_FILE"

classify_step_output() {
  FILE="$1"
  EXIT_STATUS="$2"

  if grep -Eq "### RESULT: (FAIL|NEEDS_HUMAN_REVIEW) ###|STATUS: (FAIL|NEEDS_HUMAN_REVIEW)|RESULT: (FAIL|NEEDS_HUMAN_REVIEW)" "$FILE"; then
    printf "%s
" "FAIL"
    return 0
  fi

  if grep -Eq "### RESULT: (PENDING|WAIT) ###|STATUS: (PENDING|WAIT)|RESULT: (PENDING|WAIT)" "$FILE"; then
    printf "%s
" "PENDING"
    return 0
  fi

  if grep -Eq "### RESULT: (PASS|DONE|NOOP|ALREADY_ON_MAIN|ALREADY_MERGED|ALREADY_RELEASED|DOI_VERIFIED|SUPERSEDED) ###|STATUS: (PASS|DONE|NOOP|ALREADY_ON_MAIN|ALREADY_MERGED|ALREADY_RELEASED|DOI_VERIFIED|SUPERSEDED)|RESULT: (PASS|DONE|NOOP|ALREADY_ON_MAIN|ALREADY_MERGED|ALREADY_RELEASED|DOI_VERIFIED|SUPERSEDED)" "$FILE"; then
    printf "%s
" "PASS"
    return 0
  fi

  if [ "$EXIT_STATUS" -eq 0 ]; then
    printf "%s
" "PASS"
  else
    printf "%s
" "FAIL"
  fi
}

STEP=0
while IFS= read -r COMMAND || [ -n "$COMMAND" ]; do
  case "$COMMAND" in
    "") continue ;;
    \#*) continue ;;
  esac
  STEP=$((STEP + 1))
  STEP_OUT="$(mktemp "${TMPDIR:-/tmp}/ns-slice-step.XXXXXX")"
  printf "
### STEP %s ###
" "$STEP"
  printf "%s
" "$COMMAND"
  set +e
  sh -c "$COMMAND" > "$STEP_OUT" 2>&1
  COMMAND_STATUS="$?"
  set -e
  cat "$STEP_OUT"
  CLASSIFICATION="$(classify_step_output "$STEP_OUT" "$COMMAND_STATUS")"
  rm -f "$STEP_OUT"

  if [ "$CLASSIFICATION" = "PASS" ]; then
    printf "STEP %s RESULT: PASS
" "$STEP"
    continue
  fi

  if [ "$CLASSIFICATION" = "PENDING" ]; then
    STATUS=2
    printf "STEP %s RESULT: PENDING
" "$STEP"
    printf "%s
" "Stopping slice runner at retryable state; no dependent follow-up actions were run."
    break
  fi

  STATUS=1
  printf "STEP %s RESULT: FAIL
" "$STEP"
  printf "%s
" "Stopping slice runner at first failing step."
  break
done < "$PLAN_FILE"

printf "
### FINAL STATE ###
"
git branch --show-current || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "
### RESULT: PASS ###
"
elif [ "$STATUS" -eq 2 ]; then
  printf "
### RESULT: PENDING ###
"
else
  printf "
### RESULT: FAIL ###
"
fi

exit "$STATUS"
