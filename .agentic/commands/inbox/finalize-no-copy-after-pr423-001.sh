printf '\n\n\n'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '%s\n' '-------------------------------------------------------------------------'
printf '\n\n\n'
printf 'FINALIZE NO-COPY WORKFLOW STATE AFTER PR 423\n\n'

TS=$(date +%Y%m%d-%H%M%S)
TMPLOG="/tmp/${TS}_finalize-no-copy-after-pr423.log"
BRANCH="docs/finalize-no-copy-after-pr423"
OK=1

{
  printf 'FINALIZE NO-COPY WORKFLOW STATE AFTER PR 423\n\n'

  printf '### SYNC MAIN ###\n'
  git fetch origin main || OK=0
  git switch main || OK=0
  git pull --ff-only origin main || OK=0
  ./ns terminal-remote-preflight || OK=0
  ./ns artifact-gc --execute || OK=0

  printf '\n### VERIFY CURRENT NO-COPY STATE ###\n'
  git log --oneline -10 || OK=0
  ./ns command-inbox-check || OK=0
  ./ns state-freshness-check || OK=0
  ./ns handoff-check || OK=0
  ./ns governance-check || OK=0
  cat docs/reports/command_runs/LATEST_COMMAND_RUN.txt || true
  cat docs/reports/terminal/LATEST_TERMINAL_LOG.txt || true

  printf '\n### CREATE DOC BRANCH ###\n'
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then git branch -D "$BRANCH" || OK=0; fi
  git switch -c "$BRANCH" || OK=0

  printf '\n### WRITE STATUS/HANDOFF REFRESH SCRIPT ###\n'
  mkdir -p tmp
  : > tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'from pathlib import Path' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'status = Path("docs/STATUS.md")' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'handoff = Path("docs/handoff/CURRENT_HANDOFF.md")' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'status_text = status.read_text(encoding="utf-8")' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'handoff_text = handoff.read_text(encoding="utf-8")' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'status_marker = "## No-Copy Workflow Status"' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'status_block = """## No-Copy Workflow Status\n\nAs of PR #423, the repo-backed no-copy workflow is the active bridge toward the local GUI. Remote tasks are queued under `.agentic/commands/inbox/`, local execution runs through `./ns agent-next`, and durable evidence is written under `docs/reports/command_runs/` and `docs/reports/terminal/`. The current hardening includes command-run pointers, terminal-log pointers, result-footers for `p`/`f`/paste-output decisions, missing-current-script report robustness, inner fail-marker detection, communication artifact garbage collection, and `./ns command-inbox-check` rejecting completed command ids that remain pending.\n\nThe next planned release is `v0.3.27`, intended to preserve this no-copy/runner-hardening baseline before the first local GUI slice. After that release, the next feature direction is a thin local Tkinter cockpit over `git pull && ./ns agent-next`, status display, latest command-run report, latest terminal log, and gate buttons. Pattern work is intentionally deferred until after the GUI foundation.\n"""' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'handoff_marker = "## Current No-Copy / GUI Handoff"' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'handoff_block = """## Current No-Copy / GUI Handoff\n\nCurrent state after PR #423: `main` contains the hardened repo-backed no-copy workflow. Completed inbox commands are rejected by `./ns command-inbox-check` if their `command_id` already has durable command-run evidence, preventing stale completed commands from causing later `FAIL_AMBIGUOUS_COMMANDS`. The normal local operator path remains `git pull --ff-only origin main` followed by `./ns agent-next`; normal PASS/FAIL should be handled with `p` or `f` by reading remote evidence first. `HARD-FAIL -> paste output` remains reserved for auth/network/push failures, terminal crashes, missing remote evidence, or workflow-level ambiguity.\n\nImmediate sequence: first finalize this status/handoff refresh and final no-copy verification, then cut `v0.3.27`, then start the GUI foundation. The first GUI should be deliberately thin: a local Tkinter cockpit wrapping pull-and-run-next, latest command report/log display, clean-state checks, and gate buttons. Pattern Advisor work is deferred until the GUI foundation is merged and released.\n"""' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'def replace_or_append(text: str, marker: str, block: str) -> str:' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '    if marker not in text:' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '        return text.rstrip() + "\n\n" + block' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '    start = text.index(marker)' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '    next_heading = text.find("\n## ", start + 1)' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '    if next_heading == -1:' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '        return text[:start].rstrip() + "\n\n" + block + "\n"' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' '    return text[:start].rstrip() + "\n\n" + block + "\n" + text[next_heading:].lstrip("\n")' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'status.write_text(replace_or_append(status_text, status_marker, status_block), encoding="utf-8")' >> tmp/finalize_no_copy_after_pr423.py
  printf '%s\n' 'handoff.write_text(replace_or_append(handoff_text, handoff_marker, handoff_block), encoding="utf-8")' >> tmp/finalize_no_copy_after_pr423.py

  printf '\n### RUN STATUS/HANDOFF REFRESH SCRIPT ###\n'
  if [ -x .venv/bin/python ]; then .venv/bin/python tmp/finalize_no_copy_after_pr423.py || OK=0; else PYTHONPATH=src python3 tmp/finalize_no_copy_after_pr423.py || OK=0; fi
  rm -f tmp/finalize_no_copy_after_pr423.py

  printf '\n### LOCAL GATES ###\n'
  ./ns command-inbox-check || OK=0
  ./ns state-freshness-check || OK=0
  ./ns artifact-gc || OK=0
  ./ns handoff-check || OK=0
  ./ns governance-check || OK=0
  ./ns dev || OK=0

  printf '\n### COMMIT DOC REFRESH ###\n'
  git status --short || OK=0
  git add docs/STATUS.md docs/handoff/CURRENT_HANDOFF.md || OK=0
  git commit -m "Finalize no-copy workflow handoff after PR 423" || OK=0

  printf '\n### PUSH AND CREATE PR ###\n'
  git push -u origin "$BRANCH" || OK=0
  gh pr create --title "Finalize no-copy workflow handoff after PR 423" --body "Refreshes STATUS and CURRENT_HANDOFF after the PR #423 completed-command inbox guard. Records the v0.3.27-before-GUI sequence: finalize no-copy state, release v0.3.27, then start the thin local GUI cockpit; Pattern work remains deferred." --base main --head "$BRANCH" || OK=0

  if [ "$OK" -eq 1 ]; then printf '\n### RESULT: PASS ###\n'; else printf '\n### RESULT: FAIL ###\n'; fi
} 2>&1 | tee "$TMPLOG"

printf '\n### FINALIZE TERMINAL LOG ###\n'
FINALIZE_OK=1
./ns terminal-finalize "$TMPLOG" finalize-no-copy-after-pr423 || FINALIZE_OK=0
git add docs/reports/terminal/LATEST_TERMINAL_LOG.txt docs/reports/terminal/*.log || FINALIZE_OK=0
git commit -m "Preserve no-copy finalization terminal log" || FINALIZE_OK=0
git push || FINALIZE_OK=0

printf '\n### FINAL LOCAL STATE ###\n'
git branch --show-current
git status --short

if [ "$OK" -eq 1 ] && [ "$FINALIZE_OK" -eq 1 ]; then
  printf '\n### RESULT: PASS ###\n'
  printf '### NEXT CHAT REPLY: PASS -> p ###\n'
else
  printf '\n### RESULT: FAIL ###\n'
  printf '### NEXT CHAT REPLY: FAIL -> f ###\n'
fi
