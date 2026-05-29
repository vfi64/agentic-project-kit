#!/usr/bin/env sh
printf '\n%.0s' $(seq 1 20)
printf '%s\n' '==================================================='
printf '%s\n' '==================================================='
printf '%s\n' '==================================================='
set -u
EXPECTED='040765e2e6f4647b50d653f3fffbc383d62fd4cc'
AK='/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/.venv/bin/agentic-kit'
git fetch origin main || exit 1
git pull --ff-only origin main || exit 1
HEAD=$(git rev-parse HEAD)
if [ "$HEAD" != "$EXPECTED" ]; then
  echo "main HEAD mismatch: $HEAD expected $EXPECTED"
  echo '### RESULT: FAIL ###'
  exit 1
fi
git status --short
$AK handoff check || exit 1
$AK handoff post-merge-refresh-status || exit 1
$AK doctor || exit 1
$AK check-docs || exit 1
echo 'SUMMARY COMM-LOCAL | post-pr914-closeout-precheck'
echo 'RESULT'
echo '  WORK: PASS'
echo '  EVIDENCE: PASS'
echo '  OVERALL: PASS'
echo 'NEXT'
echo '  SAFE_STEP: inspect repo-backed command run evidence and continue closeout refresh if required'
echo '  CHAT_REPLY: d'
echo '### RESULT: PASS ###'
