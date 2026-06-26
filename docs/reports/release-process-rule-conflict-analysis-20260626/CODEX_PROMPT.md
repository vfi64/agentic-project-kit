# Codex Prompt

Repo: `vfi64/agentic-project-kit`

Start from current remote `main`. Current handoff point is PR #1548, merged at commit `4d3903797990cbf1443cf9e1ba8cbc462c7a964f`.

Read first:

- `docs/planning/RELEASE_PROCESS_RULE_CONFLICT_ANALYSIS_PLAN.md`
- `docs/handoff/CODEX_RELEASE_PROCESS_RULE_CONFLICT_HANDOFF.md`
- `docs/reports/release-process-rule-conflict-analysis-20260626/README.md`
- `docs/reports/handoff-packages/latest/execution_contract.json`
- `docs/reports/handoff-packages/latest/validation_report.json`
- `.agentic/transfer/one_command_transfer_protocol.yaml`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`

Task:

Analyze the release workflow as one lifecycle. Produce a stage map and a rule-conflict table before implementation. The analysis must cover readiness, metadata preparation, release notes, state reporting, publication gating, post-merge closeout, evidence closeout, generated handoff freshness, protected-file handling, and legacy command references.

Boundaries:

No publication side effects in this analysis slice. Generated latest handoff projections are not durable rule sources. Protected files require minimal guarded changes.

First repo-backed output:

- release lifecycle stage map,
- rule conflict table,
- minimal fix list,
- tests required,
- explicit `next_mutation_allowed` decision.
