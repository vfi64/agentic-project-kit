#!/usr/bin/env sh
set -eu
STATUS=0
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: missing version argument. Example: ./ns release-prep 0.3.21"
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
printf "NS RELEASE PREP CYCLE %s\n\n" "$TAG"
printf "\n### SAFETY ###\n"
printf "%s\n" "Safety: prepares a release branch only; no tag, release, merge, or publish action."
printf "\n### UPDATE MAIN ###\n"
git switch main || STATUS=1
git pull --ff-only origin main || STATUS=1
printf "\n### VERIFY MAIN BEFORE RELEASE BRANCH ###\n"
./ns dev || STATUS=1
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli pr-hygiene || STATUS=1
printf "\n### CREATE RELEASE PREP BRANCH ###\n"
BRANCH="release/prepare-$TAG"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git switch "$BRANCH" || STATUS=1
else
  git switch -c "$BRANCH" || STATUS=1
fi
printf "\n### PATCH RELEASE METADATA ###\n"
.venv/bin/python tools/ns_release_metadata_prep.py "$PLAIN_VERSION" || STATUS=1

printf "\n### RELEASE CHECK AFTER METADATA PATCH ###\n"
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli release-check --version "$PLAIN_VERSION" || STATUS=1

printf "\n### CURRENT VERSION REFERENCES ###\n"
grep -R "$PLAIN_VERSION" -n pyproject.toml src/agentic_project_kit/__init__.py CITATION.cff CHANGELOG.md README.md docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md || true
printf "\n### FINAL STATE ###\n"
git branch --show-current || STATUS=1
git status --short || STATUS=1
git log --oneline -8 || STATUS=1
if [ "$STATUS" -eq 0 ]; then printf "\n### RESULT: PASS ###\n"; else printf "\n### RESULT: FAIL ###\n"; fi
exit "$STATUS"
