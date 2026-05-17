#!/usr/bin/env sh
set -eu
STATUS=0

VERSION="${1:-}"
CONFIRM="${2:-}"
TAG="v$VERSION"
TOKEN="publish-$TAG"

printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS RELEASE PUBLISH CYCLE %s\n\n" "$TAG"

printf "\n### SAFETY ###\n"
printf "Safety: publishes only with exact confirmation token: %s\n" "$TOKEN"

if [ -z "$VERSION" ]; then
  printf "ERROR: usage: ./ns release-publish <version> publish-v<version>\n"
  STATUS=1
fi

if [ "$STATUS" -eq 0 ] && [ "$CONFIRM" != "$TOKEN" ]; then
  printf "ERROR: refusing release publish without exact confirmation token.\n"
  printf "Run: ./ns release-publish %s %s\n" "$VERSION" "$TOKEN"
  STATUS=1
fi

printf "\n### BRANCH / STATUS ###\n"
BRANCH="$(git branch --show-current)" || STATUS=1
printf "branch=%s\n" "$BRANCH"
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ] && [ "$BRANCH" != "main" ]; then
  printf "ERROR: release publish must run from main after release metadata PR merge.\n"
  STATUS=1
fi

if [ "$STATUS" -eq 0 ] && [ -n "$(git status --porcelain)" ]; then
  printf "ERROR: working tree is dirty. Commit or restore changes before publishing.\n"
  STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### UPDATE MAIN ###\n"
  git pull --ff-only origin main || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RELEASE GATE ###\n"
  ./ns release-gate "$VERSION" || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### VERIFY TAG IS UNUSED ###\n"
  if git rev-parse "$TAG" >/dev/null 2>&1; then
    printf "ERROR: local tag already exists: %s\n" "$TAG"
    STATUS=1
  fi
  if git ls-remote --exit-code --tags origin "$TAG" >/dev/null 2>&1; then
    printf "ERROR: remote tag already exists: %s\n" "$TAG"
    STATUS=1
  fi
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### CREATE AND PUSH TAG ###\n"
  git tag "$TAG" || STATUS=1
  git push origin "$TAG" || STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RELEASE WORKFLOW STATUS ###\n"
  gh run list --workflow Release --limit 5 || true
  printf "\nTag %s was pushed. If the Release workflow is asynchronous, verify completion with gh run list and gh release view.\n" "$TAG"
fi

printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git log --oneline -8 || STATUS=1
git status --short || STATUS=1

if [ "$STATUS" -eq 0 ]; then
  printf "\n### RESULT: PASS ###\n"
else
  printf "\n### RESULT: FAIL ###\n"
fi

exit "$STATUS"
