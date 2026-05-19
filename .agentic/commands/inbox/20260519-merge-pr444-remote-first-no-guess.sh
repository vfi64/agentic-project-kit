printf '\n\n\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '-------------------------------------------------------------------------\n'
printf '\n\n\n'
printf 'MERGE PR 444 REMOTE-FIRST NO-GUESS GOVERNANCE\n\n'

if [ "$(git branch --show-current)" != "main" ]; then
  git switch main || { printf 'switch main FAIL\n'; exit 1; }
fi

git pull --ff-only origin main || { printf 'pull main FAIL\n'; exit 1; }

gh pr checks 444 --watch || { printf 'pr checks FAIL\n'; exit 1; }
gh pr merge 444 --squash --delete-branch || { printf 'merge PR 444 FAIL\n'; exit 1; }

git switch main || { printf 'switch main after merge FAIL\n'; exit 1; }
git pull --ff-only origin main || { printf 'pull main after merge FAIL\n'; exit 1; }

./ns dev || { printf 'dev gate FAIL\n'; exit 1; }

git status --short
git log --oneline --decorate -8

printf '\n================================================================\n'
printf 'SUMMARY\n'
printf 'WORK RESULT: PASS\n'
printf 'EVIDENCE RESULT: PASS\n'
printf 'OVERALL RESULT: PASS\n'
printf 'REMOTE_EVIDENCE: PASS\n'
printf 'terminal_log=SEE_COMMAND_REPORT\n'
printf 'command_report=SEE_LATEST_COMMAND_RUN\n'
printf 'NEXT_CHAT_REPLY: p\n'
printf '### RESULT: PASS ###\n'
printf '================================================================\n'
