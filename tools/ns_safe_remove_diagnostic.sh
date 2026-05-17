#!/usr/bin/env sh
set -eu
STATUS=0

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  printf "%s\n" "ERROR: missing file path. Usage: tools/ns_safe_remove_diagnostic.sh <file>"
  exit 1
fi

printf "%s\n" "Safe diagnostic cleanup target: $TARGET"
if git ls-files --error-unmatch "$TARGET" >/dev/null 2>&1; then
  printf "%s\n" "Tracked file detected; restoring from HEAD instead of deleting."
  git restore "$TARGET" || STATUS=1
elif [ -e "$TARGET" ]; then
  printf "%s\n" "Untracked file detected; removing."
  rm -f "$TARGET" || STATUS=1
else
  printf "%s\n" "File absent; no cleanup needed."
fi

exit "$STATUS"
