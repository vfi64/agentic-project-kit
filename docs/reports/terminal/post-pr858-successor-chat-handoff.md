# Successor Chat Handoff after PR858

## Copy this into the next ChatGPT or Codex chat

We work in repo `vfi64/agentic-project-kit`.

Do not start from chat memory. The source of truth is the remote repository, current `main`, PRs, CI, tags, releases, issues, and committed repo artifacts.

First read `docs/handoff/NEXT_CHAT_BOOTSTRAP.md` from `main` completely and execute its boot routine.

Current verified handoff point:

- `main` HEAD after PR858: `d644744 Record Post-PR857 main closeout evidence log (#858)`
- PR857 product slice: `f5e482b Unify next-turn fixed-slot path handling (#857)`
- PR858 closeout evidence: `docs/reports/terminal/post-pr857-main-closeout.log`
- Last verified evidence inspection on main: `agentic-kit evidence inspect --require-summary docs/reports/terminal/post-pr857-main-closeout.log` returned `PASS_CONTINUE`
- `agentic-kit handoff check` passed
- `next-turn --status` returned empty fixed slot with `### RESULT: PASS ###`
- `last-result` returned `FOUND_PASS`, `evidence_verdict=PASS_CONTINUE`, `recommended_chat_reply=d`
- targeted ruff passed

Mandatory first checks before mutation:

1. Fetch and verify `origin/main`.
2. Verify current `main` HEAD is at least `d644744`.
3. Read these files before mutation:
   - `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`
   - `docs/handoff/START_NEW_CHAT_PROMPT.md`
   - `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`
   - `docs/STATUS.md`
   - `docs/handoff/CURRENT_HANDOFF.md`
   - `.agentic/handoff_state.yaml`
   - `.agentic/compiled_agent_context.yaml`
   - `.agentic/rule_mechanism_inventory.yaml`
   - `.agentic/rule_migrations.yaml`
   - `.agentic/rule_preservation.yaml`
   - `docs/governance/FINAL_SUMMARY_CONTRACT.md`
   - `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
   - `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
   - `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
   - `docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md`
   - `docs/planning/WORKFLOW_REDUCTION_FOCUS.md`
   - `docs/planning/NEXT_TURN_WORK_ORDER_WORKFLOW_PLAN.md`

Required boot report:

- current `main` HEAD
- open PRs and CI status
- whether `NEXT_CHAT_BOOTSTRAP.md` is current enough
- whether STATUS, CURRENT_HANDOFF, and handoff_state are consistent
- last clean verified evidence
- next smallest safe slice

Critical workflow rules:

- `d`, `f`, and `w` are only chat signals, not evidence.
- After `d`, `f`, `w`, or any other short control reply, inspect committed repo/remote evidence first. Do not ask for pasted terminal output before checking `next-turn last-result`, command reports, terminal logs, PR status, or committed evidence.
- Evidence-bearing local workflow finalization must use `agentic-kit evidence finalize-log` or a stricter successor. Freehand final PASS footers are not valid closeout evidence.
- Protected YAML, JSON, and Markdown control files require the repository-supported protected-change planning route.
- Do not use `agentic-kit protected-change-plan`: that command was attempted during PR857 and does not exist in this checkout.
- Before the next protected planning-doc mutation, identify the valid route, likely `./ns protected-change-plan`, a Python module route, or a currently registered equivalent. Verify it before relying on it.
- Do not develop directly on `main`.
- Use a feature branch, targeted tests, ruff, PR, machine-readable CI/merge status, guarded merge, main sync, evidence closeout, and strict evidence inspection.
- Terminal blocks must stay quote-safe, small, logged where evidence-bearing, and must not end with `exit`.

Recent completed slices:

- PR853: hardened `next-turn last-result` result-first/log-first classification.
- PR854: recorded post-PR853 main closeout evidence.
- PR855: classified `.agentic/commands/executed.jsonl` in `last-result`.
- PR856: recorded post-PR855 main closeout evidence.
- PR857: unified next-turn fixed-slot path handling so status detection, slot creation, runner execution, tests, and planning references use `.agentic/commands/inbox/next-turn.*`.
- PR858: recorded post-PR857 main closeout evidence.

Known follow-up:

The next smallest safe slice is to resolve the missing protected-change planning route. Do this before any further protected planning-doc mutation. The prior command `agentic-kit protected-change-plan` failed because that CLI route does not exist in the current checkout. Find the supported equivalent from repo sources, add or document the correct route if necessary, test it, and only then continue workflow-kernel hardening.

Suggested first local commands:

    cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
    git fetch origin main
    git checkout main
    git pull --ff-only origin main
    git status --short
    git log -8 --oneline
    PATH=".venv/bin:$PATH" agentic-kit handoff check
    PATH=".venv/bin:$PATH" agentic-kit evidence inspect --require-summary docs/reports/terminal/post-pr857-main-closeout.log
    PATH=".venv/bin:$PATH" python -m agentic_project_kit.next_turn_status next-turn --status
    PATH=".venv/bin:$PATH" python -m agentic_project_kit.next_turn_status last-result

Then continue with the smallest safe slice: resolve the missing protected-change planning route before any protected planning-doc mutation.

Expected successor behavior:

1. find the supported protected-change planning entrypoint from repo sources;
2. verify it with help/smoke output;
3. document the correct route if repo docs are wrong or incomplete;
4. add/adjust regression coverage;
5. run targeted tests and ruff;
6. create PR;
7. wait for machine-readable clean CI;
8. merge only after clean status;
9. sync main;
10. create and inspect closeout evidence with `agentic-kit evidence finalize-log` or stricter successor.
