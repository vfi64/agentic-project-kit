#!/usr/bin/env sh
set -eu

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" = "main" ]; then
  printf "%s\n" "ERROR: refusing commit/PR workflow on main."
  printf "%s\n" "Create a feature or docs branch first, then rerun the commit/PR workflow."
  printf "%s\n" "Expected action: create a feature or docs branch first."
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  printf "%s\n" "Commit/PR guard passed on branch: $BRANCH"
else
  printf "%s\n" "No local changes detected on branch: $BRANCH"
fi
