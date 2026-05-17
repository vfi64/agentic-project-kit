#!/usr/bin/env sh
set -eu
STATUS=0

VERSION="${1:-}"
CONFIRM="${2:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: usage: ./ns release-publish <version> publish-v<version>"
  printf "%s\n" "### RESULT: FAIL ###"
  exit 2
fi

TAG="v$VERSION"
EXPECTED="publish-$TAG"

printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS RELEASE PUBLISH CYCLE %s\n\n" "$TAG"

printf "\n### SAFETY ###\n"
printf "Safety: publishes only with exact confirmation token: %s\n" "$EXPECTED"
if [ "$CONFIRM" != "$EXPECTED" ]; then
  printf "%s\n" "ERROR: refusing release publish without exact confirmation token."
  printf "Run: ./ns release-publish %s %s\n" "$VERSION" "$EXPECTED"
  printf "\n### RESULT: FAIL ###\n"
  exit 2
fi

printf "\n### BRANCH / STATUS ###\n"
BRANCH="$(git branch --show-current)" || STATUS=1
printf "branch=%s\n" "$BRANCH"
git status --short || STATUS=1
if [ "$BRANCH" != "main" ]; then
  printf "%s\n" "ERROR: release publish must run from main."
  STATUS=1
fi
if [ -n "$(git status --porcelain)" ]; then
  printf "%s\n" "ERROR: working tree is dirty. Commit or restore changes before publish."
  STATUS=1
fi

printf "\n### UPDATE MAIN ###\n"
if [ "$STATUS" -eq 0 ]; then
  git pull --ff-only origin main || STATUS=1
fi

printf "\n### RELEASE GATE ###\n"
if [ "$STATUS" -eq 0 ]; then
  ./ns release-gate "$VERSION" || STATUS=1
fi

printf "\n### VERIFY TAG IS UNUSED ###\n"
if [ "$STATUS" -eq 0 ]; then
  if git rev-parse "$TAG" >/dev/null 2>&1; then
    printf "ERROR: local tag already exists: %s\n" "$TAG"
    STATUS=1
  fi
  if git ls-remote --tags origin "$TAG" | grep "$TAG" >/dev/null 2>&1; then
    printf "ERROR: remote tag already exists: %s\n" "$TAG"
    STATUS=1
  fi
  if gh release view "$TAG" >/dev/null 2>&1; then
    printf "ERROR: GitHub release already exists: %s\n" "$TAG"
    STATUS=1
  fi
fi

printf "\n### CREATE AND PUSH TAG ###\n"
if [ "$STATUS" -eq 0 ]; then
  git tag "$TAG" || STATUS=1
  git push origin "$TAG" || STATUS=1
fi

printf "\n### WAIT FOR RELEASE WORKFLOW AND GITHUB RELEASE ###\n"
if [ "$STATUS" -eq 0 ]; then
  FOUND=0
  i=0
  while [ "$i" -lt 30 ]; do
    if gh release view "$TAG" >/dev/null 2>&1; then
      FOUND=1
      break
    fi
    i=$((i + 1))
    printf "Waiting for GitHub release %s (%s/30)\n" "$TAG" "$i"
    sleep 10
  done
  if [ "$FOUND" -ne 1 ]; then
    printf "ERROR: GitHub release did not appear before timeout: %s\n" "$TAG"
    STATUS=1
  fi
fi

printf "\n### RELEASE WORKFLOW STATUS ###\n"
gh run list --workflow Release --limit 8 || STATUS=1

printf "\n### VERIFY COMPLETED RELEASE ###\n"
if [ "$STATUS" -eq 0 ]; then
  ./ns release-verify "$VERSION" || STATUS=1
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
