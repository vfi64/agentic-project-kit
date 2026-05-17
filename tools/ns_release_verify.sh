#!/usr/bin/env sh
set -eu
STATUS=0

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: usage: ./ns release-verify <version>"
  exit 2
fi

TAG="v$VERSION"

printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS RELEASE VERIFY CYCLE %s\n\n" "$TAG"

printf "\n### SAFETY ###\n"
printf "%s\n" "Safety: verifies completed release state only; no tag, release, merge, push, or publish action."

printf "\n### BRANCH / STATUS ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1

printf "\n### VERIFY LOCAL TAG ###\n"
if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  git rev-parse "$TAG"
else
  printf "ERROR: local tag missing: %s\n" "$TAG"
  STATUS=1
fi

printf "\n### VERIFY REMOTE TAG ###\n"
if git ls-remote --tags origin "$TAG" | grep "$TAG" >/dev/null; then
  git ls-remote --tags origin "$TAG"
else
  printf "ERROR: remote tag missing: %s\n" "$TAG"
  STATUS=1
fi

printf "\n### WAIT FOR GITHUB RELEASE ###\n"
COUNT=0
FOUND=0
while [ "$COUNT" -lt 24 ]; do
  if gh release view "$TAG" >/tmp/ns_release_verify_release.txt 2>/tmp/ns_release_verify_release_err.txt; then
    FOUND=1
    break
  fi
  COUNT=$((COUNT + 1))
  printf "Release not visible yet for %s; retry %s/24 after 10s.\n" "$TAG" "$COUNT"
  sleep 10
done
if [ "$FOUND" -eq 1 ]; then
  cat /tmp/ns_release_verify_release.txt
else
  printf "ERROR: GitHub release still missing after wait: %s\n" "$TAG"
  if [ -f /tmp/ns_release_verify_release_err.txt ]; then cat /tmp/ns_release_verify_release_err.txt; fi
  STATUS=1
fi

printf "\n### RELEASE WORKFLOW STATUS ###\n"
gh run list --workflow Release --limit 8 || STATUS=1

printf "\n### POST RELEASE CHECK ###\n"
if [ -x ".venv/bin/agentic-kit" ]; then
  .venv/bin/agentic-kit post-release-check --version "$VERSION" || STATUS=1
else
  agentic-kit post-release-check --version "$VERSION" || STATUS=1
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
