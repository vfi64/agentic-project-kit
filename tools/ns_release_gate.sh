#!/usr/bin/env sh
set -eu
STATUS=0

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: usage: ./ns release-gate <version>"
  printf "%s\n" "### RESULT: FAIL ###"
  exit 2
fi

TAG="v$VERSION"

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
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli release-check --version "$VERSION" || STATUS=1

printf "\n### CLEAN DIST ###\n"
rm -rf dist build *.egg-info || STATUS=1
mkdir -p dist || STATUS=1

printf "\n### BUILD CHECK ###\n"
.venv/bin/python -m build || STATUS=1
.venv/bin/python -m twine check dist/* || STATUS=1

printf "\n### VERIFY DIST ONLY CONTAINS TARGET VERSION ###\n"
ls -la dist || STATUS=1
if ls dist | grep -v "$VERSION" >/dev/null 2>&1; then
  printf "%s\n" "ERROR: dist contains artifacts that do not match $VERSION."
  ls dist || true
  STATUS=1
fi

printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
