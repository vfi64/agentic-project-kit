#!/usr/bin/env sh
set -eu
STATUS=0
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: missing version argument. Example: ./ns release-gate 0.3.21"
  exit 2
fi
case "$VERSION" in
  v*) TAG="$VERSION"; PLAIN_VERSION="${VERSION#v}" ;;
  *) TAG="v$VERSION"; PLAIN_VERSION="$VERSION" ;;
esac
printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS RELEASE GATE CYCLE %s\n\n" "$TAG"
printf "\n### SAFETY ###\n"
printf "%s\n" "Safety: verifies release readiness only; no tag, release, merge, or publish action."
printf "\n### BRANCH / STATUS ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1
printf "\n### LOCAL GATE ###\n"
./ns dev || STATUS=1
printf "\n### RELEASE CHECK ###\n"
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli release-check --version "$PLAIN_VERSION" || STATUS=1
printf "\n### BUILD CHECK ###\n"
.venv/bin/python -m build || STATUS=1
.venv/bin/python -m twine check dist/* || STATUS=1
printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1
if [ "$STATUS" -eq 0 ]; then printf "\n### RESULT: PASS ###\n"; else printf "\n### RESULT: FAIL ###\n"; fi
exit "$STATUS"
