#!/usr/bin/env bash
set -u
set -o pipefail

OUT="Screen-Control_Output.txt"

{
  echo "=== Screen-Control Gate Output ==="
  echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "PWD: $(pwd)"
  echo

  echo "=== git branch ==="
  git branch --show-current
  echo

  echo "=== git status --short ==="
  git status --short
  echo

  echo "=== git log --oneline -8 ==="
  git log --oneline -8
  echo

  echo "=== python -m pytest -q ==="
  python -m pytest -q
  PYTEST_RC=$?
  echo "pytest exit code: $PYTEST_RC"
  echo

  echo "=== ruff check . ==="
  ruff check .
  RUFF_RC=$?
  echo "ruff exit code: $RUFF_RC"
  echo

  echo "=== agentic-kit check-docs ==="
  agentic-kit check-docs
  CHECK_DOCS_RC=$?
  echo "check-docs exit code: $CHECK_DOCS_RC"
  echo

  echo "=== agentic-kit doctor ==="
  agentic-kit doctor
  DOCTOR_RC=$?
  echo "doctor exit code: $DOCTOR_RC"
  echo

  if [ $# -gt 0 ]; then
    echo "=== extra command(s) ==="
    echo "$*"
    "$@"
    EXTRA_RC=$?
    echo "extra command exit code: $EXTRA_RC"
  else
    EXTRA_RC=0
  fi

  echo
  echo "=== Summary ==="
  echo "pytest:      $PYTEST_RC"
  echo "ruff:        $RUFF_RC"
  echo "check-docs:  $CHECK_DOCS_RC"
  echo "doctor:      $DOCTOR_RC"
  echo "extra:       $EXTRA_RC"

  if [ "$PYTEST_RC" -eq 0 ] && [ "$RUFF_RC" -eq 0 ] && [ "$CHECK_DOCS_RC" -eq 0 ] && [ "$DOCTOR_RC" -eq 0 ] && [ "$EXTRA_RC" -eq 0 ]; then
    echo "OVERALL: PASS"
    exit 0
  else
    echo "OVERALL: FAIL"
    exit 1
  fi
} 2>&1 | tee "$OUT"

exit "${PIPESTATUS[0]}"
