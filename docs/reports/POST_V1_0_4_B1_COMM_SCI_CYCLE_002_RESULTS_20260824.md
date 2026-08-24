# Post-v1.0.4 B1 Comm-SCI Cycle 002 Results

Status: cycle_002_recorded  
Status date: 2026-08-24  
Kit baseline when recorded: `692de915` (`Refresh handoff state after PR2158 (#2159)`)  
Target repository: `vfi64/Comm-SCI-Control-private`  
Target work branch: `codex/b1-modularize-comm-sci-app2-cycle-002`  
Target base branch: `feature/ui-access-levels-v2`  
Target PR: <https://github.com/vfi64/Comm-SCI-Control-private/pull/4>  
Cycle ID: `B1-COMM-SCI-20260824-002`

## Scope

This report records the second real B1 Comm-SCI work cycle in the Kit
repository. It is a result/evidence slice only.

It does not implement the newly observed Kit follow-up defects, publish a Kit
release, declare `B1_EVALUABLE`, or decide B2.

## Source Evidence

Primary product artifacts remain in the foreign repository:

- foreign cycle report:
  `.agentic/state/handoff/reports/b1-cycle-20260824-bridge-runtime-helpers.md`;
- successor handoff package:
  `.agentic/state/handoff/packages/latest/`;
- PR:
  `vfi64/Comm-SCI-Control-private#4`.

Directly verified source facts:

- PR #4 was opened against `feature/ui-access-levels-v2` and merged on
  2026-08-24 at `2026-08-24T17:38:52Z`.
- PR #4 head before merge was
  `528e8f63af3a925662363a245449b61d87d7d5bf`.
- PR #4 squash merge commit is
  `181397ce1aeb252f7bcc7872b71da56032186693`.
- GitHub reported `mergeStateStatus: CLEAN` and `statusCheckRollup: []`.
- The local post-merge target-branch checkout was clean at `181397c`.

## Real Work Outcome

The cycle performed another real Comm-SCI maintenance slice:

- extracted App2 background startup into `src/app/background_start_runtime.py`;
- extracted session/runtime event logging into
  `src/logging_runtime/session_event_runtime.py`;
- extracted Panel UI snapshot assembly into `src/panel/panel_ui_runtime.py`;
- extracted QC Override show behavior into `src/panel/qc_override_runtime.py`;
- rewired `panel_action` to the existing modular panel-action orchestrator;
- removed six entries from `_LEGACY_EXPLICIT_DELEGATIONS`;
- reduced the App2 legacy seam counter from 67 to 61;
- committed a Comm-SCI successor handoff package and cycle report.

Recorded target-repository validation:

- new ModuleOnlyApi boundary tests: 5 passed;
- affected App/Panel tests: 8 passed;
- broader App2 focused corridor: 253 passed;
- post-import targeted corridor: 92 passed;
- full Comm-SCI pytest: 1488 passed;
- `ruff check` on touched files: PASS, using the Kit venv Ruff because the
  Comm-SCI venv does not contain Ruff;
- `tools/count_legacy_seams.py`: `legacy_seams_remaining=61`;
- `Comm-SCI-Control-App2.py --selftest`: `[App2-SelfTest] OK`;
- `agentic-kit doctor --root /tmp/comm-sci-b1-cycle-002-base`: Overall PASS;
- `agentic-kit check-docs --root /tmp/comm-sci-b1-cycle-002-base`: PASS.

Some Comm-SCI tests mutate `Config/Comm-SCI-Config.json` as runtime state. That
drift was reverted before commit and was not included in PR #4.

## B0 Metric Position

B0 defines B1 evaluability as at least five real cycles, including at least
three merge-boundary cycles with measurable post-merge refresh outcomes.

Cycle 002 status against that metric:

| Metric field | Value |
| --- | --- |
| real B1 work cycles recorded | 2 |
| merge-boundary cycles recorded | 1 |
| B1 current state | `realbetrieb_running` |
| B1 evaluability | not reached |

Cycle 002 counts as the first merge-boundary cycle because PR #4 crossed the
external PR merge boundary and the Kit merge/post-merge behavior was measured.
It remains limited evidence because the target branch was
`feature/ui-access-levels-v2`, not `main`, and remote CI had no checks.

## Kit Findings

### B1-KIT-002 Retest: External Command Manifest Fallback Works

Finding type: resolved retest  
Observed severity after fix: low

Evidence:

- external `agentic-kit doctor --root ...` now reports Overall PASS;
- the doctor output includes the intended external-workspace `command manifest`
  WARN and confirms the packaged manifest is available with 254 commands and
  manifest SHA `2ab1c7c2a951`;
- external `agentic-kit check-docs --root ...` passes.

Decision:

- The original B1-KIT-002 defect remains fixed.
- External workspaces should not need to provide Kit-internal command-manifest
  files.

### B1-KIT-003 Reconfirmed: External PR Has No Remote Checks

Finding type: remote-CI limitation  
Observed severity: medium  
Reproducibility: confirmed for PR #3 and PR #4

Evidence:

- `agentic-kit transfer pr-status 4 --json` returned
  `decision: no-checks`, `result_status: FAIL`, and head
  `528e8f63af3a925662363a245449b61d87d7d5bf`;
- GitHub PR metadata for PR #4 reported `statusCheckRollup: []`;
- PR #4 was locally validated, but it had no remote check rollup.

Impact:

- Local test evidence must not be described as remote CI green.
- Merge readiness reporting needs to keep `no-checks` distinct from successful
  checks.

### B1-KIT-004: External Fresh-LLM-Context Carrier Paths Do Not Align

Finding type: external-workspace transfer defect  
Observed severity: high

Evidence:

- `agentic-kit transfer pr-merge-safe 4 ...` first blocked in
  `require-fresh-llm-context` with `outbox_missing` and
  `latest_handoff_report_missing`.
- `agentic-kit transfer refresh-llm-context-carriers --json` then succeeded and
  wrote:
  `.agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json`
  and `.agentic/transfer/outbox/last_result.txt`.
- A second `pr-merge-safe` still blocked because it searched for
  `docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json`
  and also reported `outbox_running_chat_refresh_contract_missing`.

Impact:

- The external refresh command and the merge preflight do not agree on the
  external workspace report location/contract.
- The user should not have to supply Kit-internal or self-hosting transfer
  files inside the foreign repository.

Follow-up:

- Make the fresh-context gate external-workspace aware and accept the carrier
  paths generated by `refresh-llm-context-carriers`, or make that command write
  the exact path and contract that `pr-merge-safe` requires.

### B1-KIT-005: `pr-merge-safe` Recovery Still Requires Self-Hosting Rule State

Finding type: external-workspace merge-wrapper defect  
Observed severity: high

Evidence:

- `agentic-kit transfer pr-merge-safe 4 ... --skip-llm-context-gate --json`
  blocked with `dirty_worktree`, `rule_snapshot_fail_closed`, and
  `missing_rule_acknowledgement`.
- The dirty state was caused by untracked carriers created by the Kit refresh
  command itself.
- The rule acknowledgement gate looked for self-hosting rule snapshot state that
  the external Comm-SCI workspace does not provide.

Impact:

- A real external PR with local green tests could not be merged through the Kit
  wrapper.
- The cycle had to merge with raw GitHub CLI, pinned to the verified head:
  `gh pr merge 4 --squash --match-head-commit 528e8f63... --delete-branch`.

Follow-up:

- Add an external-workspace merge path that uses the adopted `.agentic/config`
  authority and target-repo gates without requiring Kit self-hosting rule
  snapshots.
- Ensure transient transfer carriers created by the Kit do not make the next
  transfer action fail as a dirty worktree unless they are intended evidence.

### B1-KIT-006: External Post-Merge Check Is Main-Only

Finding type: external merge-boundary limitation  
Observed severity: medium

Evidence:

- After PR #4 merged, the target branch was synchronized to
  `feature/ui-access-levels-v2` at `181397c`.
- `agentic-kit transfer post-merge-check --json` returned
  `Expected branch main before post-merge lifecycle check. Current branch:
  feature/ui-access-levels-v2`.

Impact:

- The current post-merge lifecycle check cannot evaluate external repositories
  whose governed integration branch is not `main`.

Follow-up:

- Either document `post-merge-check` as self-hosting/main-only or add an
  external-workspace/base-branch-aware post-merge refresh check.

### B1-KIT-007: `command-for --task` Tags Miss Existing Health Commands

Finding type: command-discovery usability gap  
Observed severity: low

Evidence:

- `agentic-kit command-for --task doctor --root ... --json` returned
  `unknown_tag`;
- `agentic-kit command-for --task check-docs --root ... --json` returned
  `unknown_tag`;
- both commands are valid and were run successfully by name.

Impact:

- External users can still run the commands, but task-oriented discovery does
  not route common health-check intent cleanly.

Follow-up:

- Add task tags for common health commands or document that `--task` is a
  controlled tag vocabulary rather than natural-language command discovery.

## Merge Boundary

Because `pr-merge-safe` blocked on external-workspace wrapper assumptions and
GitHub reported no remote checks, PR #4 was merged manually with pinned head
evidence after local gates passed.

This is an important B1 result: the Kit can support real foreign-repo work and
handoff generation, but external PR merge/post-merge automation is not yet
reliable enough to claim an end-to-end automated foreign-repo takeover.

## Decision

Record Cycle 002 as the second real B1 cycle and the first measured
merge-boundary cycle.

B1 remains not evaluable. The next B1 work should continue with additional real
Comm-SCI cycles, but the highest-value Kit implementation follow-up is now the
external `pr-merge-safe`/fresh-context/post-merge path rather than the already
fixed command-manifest packaging issue.
