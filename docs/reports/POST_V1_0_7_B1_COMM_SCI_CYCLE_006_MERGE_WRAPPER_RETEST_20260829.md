# Post-v1.0.7 B1 Comm-SCI Cycle 006 Merge Wrapper Retest

Status: PASS  
Date: 2026-08-29  
Scope: sixth Comm-SCI maintenance cycle and released-package merge-wrapper
retest; not a new B1 evaluability threshold definition

## Purpose

This report records a fresh external-repository cycle against
`vfi64/Comm-SCI-Control-private` using `agentic-project-kit==1.0.7` from PyPI.

The specific retest question was whether the published `pr-merge-safe` wrapper
now returns a terminal local result after it successfully merges a real external
PR with green remote CI. Cycle 005 had shown that the wrapper could merge the
remote PR but did not return cleanly to the local caller.

Result: the old non-return limitation is closed for this retested path. The
wrapper returned `PASS` in 8.034 seconds after the successful remote merge,
through the idempotent recovery path.

## Target And Baseline

- External repository: `vfi64/Comm-SCI-Control-private`
- Target base branch: `feature/ui-access-levels-v2`
- Clean retest worktree:
  `/tmp/comm-sci-b1-cycle-006`
- Merge-settle worktree:
  `/Users/hof/Library/CloudStorage/Dropbox/Privat/GitHub/Comm-SCI-Control-private-b1-003`
- Base before work:
  `bce40ba2edd9cf46bf423e41c47381287c7fe7fb`
- Final target-branch head:
  `116263507217f640b4c89aa951a92b05651351d4`
- Package under test: `agentic-project-kit==1.0.7`
- Package identity check: `agentic-kit --version` returned
  `agentic-kit 1.0.7`

The existing main local checkout for the private target repository was not used
for mutation because it contained tracked local-log changes and was on a deleted
branch. A clean worktree was created from `origin/feature/ui-access-levels-v2`
instead.

## Backup Evidence

A mirror backup was taken before target-repository mutation.

- Successful backup timestamp: `20260829T145736Z`
- Mirror path:
  `/Users/hof/backups/comm-sci-mirror-20260829T145736Z.git`
- `git --git-dir=<mirror> fsck --no-progress`: PASS
- Mirror size: `17M`
- Branch refs: `11`
- Mirror refs SHA-256:
  `810b0ccff2e54817fc6b52ba6a8f18c10b16a0a265fb55a05398966d2606c334`
- Non-git inventory SHA-256:
  `92e12c75c7e0131c73813d82acd095324cbf34beb1406eef6ddb690e48eafd02`

The initial `gh repo clone ... -- --mirror` attempt used the configured SSH
protocol and failed because the workstation SSH key was not accepted. The
successful mirror used HTTPS through the GitHub CLI credential helper.

## Product Task

The real Comm-SCI task continued the App2 modularization line by moving three
manual-test monitor helper methods from the legacy delegation tuple into
`ModuleOnlyApiBase`:

- `_manual_test_monitor_eval`
- `_manual_test_monitor_apply_seam_state_plan`
- `_manual_test_monitor_apply_named_state_plan`

The task was functional rather than administrative. It reduced the measured
App2 legacy explicit delegation count:

```text
legacy_seams_remaining=58 -> 55
```

The product commit was:

```text
fb9c9dedacd9105f7f075f31977ac10a83bbf000
Modularize manual test monitor state helpers
```

## Local Validation

The fresh worktree did not contain the target repository's ignored `.venc313`
environment. App2 tests and selftest were therefore run with the existing target
repository Python 3.13 virtual environment:

```text
/Users/hof/Library/CloudStorage/Dropbox/Privat/GitHub/Comm-SCI-Control-private/.venc313/bin/python
Python 3.13.1
```

Validation results:

| Gate | Result |
| --- | --- |
| Focused manual-test monitor regression set | 14 passed |
| App2 runtime/manual monitor regression set | 121 passed |
| Full local target suite | 1491 passed |
| `Comm-SCI-Control-App2.py --selftest` | `[SelfTest] OK`; `[App2-SelfTest] OK` |
| `tools/count_legacy_seams.py` | `legacy_seams_remaining=55` |
| `agentic-kit transfer protected-diff-plan --label b1-cycle-006-merge-wrapper-retest --json` | PASS, 0 findings |

The App2 selftest rewrote the tracked runtime config
`Config/Comm-SCI-Config.json`; that test side effect was restored before commit
because it was unrelated to the modularization task.

## Pull Requests And CI

Product PR:

- PR: `https://github.com/vfi64/Comm-SCI-Control-private/pull/14`
- Base: `feature/ui-access-levels-v2`
- Head branch: `codex/b1-cycle-006-merge-wrapper-retest`
- Head SHA: `fb9c9dedacd9105f7f075f31977ac10a83bbf000`
- State: MERGED
- Merged at: `2026-08-29T15:04:18Z`
- Merge commit: `08b41e12f820989ade4fafed9866f1f9fb119cb6`

Product PR CI:

- Workflow: `tests`
- Run: `33259146677`
- Run number: `222`
- Event: `pull_request`
- Job: `pytest (3.11)`
- Started: `2026-08-29T15:02:15Z`
- Completed: `2026-08-29T15:03:03Z`
- Conclusion: SUCCESS

Successor package refresh PR:

- PR: `https://github.com/vfi64/Comm-SCI-Control-private/pull/15`
- Base: `feature/ui-access-levels-v2`
- Head branch: `docs/post-pr14-successor-package-refresh`
- Head SHA: `e96c625ff5eb8c9b921fbdde03a4b3d8d44d6ca2`
- State: MERGED
- Merged at: `2026-08-29T15:07:05Z`
- Merge commit: `116263507217f640b4c89aa951a92b05651351d4`

Refresh PR CI:

- Workflow: `tests`
- Run: `33259317674`
- Run number: `223`
- Event: `pull_request`
- Job: `pytest (3.11)`
- Started: `2026-08-29T15:06:01Z`
- Completed: `2026-08-29T15:06:50Z`
- Conclusion: SUCCESS

No open Comm-SCI pull requests remained after the cycle.

## Merge Wrapper Evidence

### First Attempt

The first measured `pr-merge-safe` attempt failed closed before mutation because
the target worktree contained generated local Kit state. The volatile handoff
carriers were expected; the untracked Rule-Ack file was not classified as known
volatile by the external preflight.

Measurement:

```text
start_utc=2026-08-29T15:03:31Z
end_utc=2026-08-29T15:03:32Z
duration_ms=492
exit_code=2
terminated_by_itself=true
```

Output:

```json
{
  "schema_version": 1,
  "kind": "external_pr_merge_preflight",
  "result_status": "BLOCKED",
  "returncode": 2,
  "final_signal": "f",
  "reasons": [
    "external_dirty_worktree"
  ],
  "dirty_paths": [
    ".agentic/rule_ack/current.json",
    ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json",
    ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.log",
    ".agentic/transfer/outbox/last_result.txt"
  ],
  "nonvolatile_dirty_paths": [
    ".agentic/rule_ack/current.json"
  ],
  "known_volatile_paths": [
    ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json",
    ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.log",
    ".agentic/transfer/inbox/next_command.py.txt",
    ".agentic/transfer/outbox/last_result.txt",
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log"
  ],
  "restore_result": null,
  "next_action": "Review or clean target-repository changes before running external pr-merge-safe."
}
```

This fail-closed result was safe. The remaining external hygiene gap is that
`agentic-kit rules acknowledge` can create `.agentic/rule_ack/current.json` in
an adopted external repository, while `pr-merge-safe` does not classify that
path as known volatile.

### Successful Retry

After removing only the generated untracked Rule-Ack file, the second measured
`pr-merge-safe` attempt completed by itself and returned `PASS`.

Measurement:

```text
start_utc=2026-08-29T15:04:12Z
end_utc=2026-08-29T15:04:20Z
duration_ms=8034
exit_code=0
terminated_by_itself=true
```

Output:

```json
{
  "action": "pr-merge-safe",
  "command": [
    "/private/tmp/agentic-kit-1.0.7-venv/bin/agentic-kit",
    "pr",
    "merge-if-green",
    "14",
    "--expected-head-sha",
    "fb9c9dedacd9105f7f075f31977ac10a83bbf000",
    "--main-branch",
    "feature/ui-access-levels-v2",
    "--merge-method",
    "squash",
    "--merge-state-timeout-seconds",
    "60",
    "--merge-state-poll-seconds",
    "5"
  ],
  "next_action": "STATE=ALREADY_MERGED; NEXT=run_post_merge_check_or_handoff_refresh",
  "result_status": "PASS",
  "returncode": 0,
  "stderr": "",
  "stdout": "IDEMPOTENT_PR_RECOVERY\nSTATE=ALREADY_MERGED\nPR=14\nURL=https://github.com/vfi64/Comm-SCI-Control-private/pull/14\nMERGED_AT=2026-08-29T15:04:18Z\nRESULT=PASS\n"
}
```

Adjudication: B1-KIT-012 is retested as PASS for the released
`agentic-project-kit==1.0.7` package on a real external merge-cycle path.

## Post-Merge Lifecycle

Immediately after the product PR, `agentic-kit transfer post-merge-check
--base-branch feature/ui-access-levels-v2 --json` returned
`STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH` because the current head
`08b41e12f820989ade4fafed9866f1f9fb119cb6` did not match the previously
generated successor package.

`agentic-kit transfer post-merge-settle --after-pr 14 --main-branch
feature/ui-access-levels-v2 --ci-timeout-seconds 600 --ci-poll-seconds 10
--json` completed the lifecycle:

- `lifecycle_state`: `COMPLETE`
- Refresh kind: `successor-package-refresh`
- Refresh PR: `15`
- Final post-merge check: PASS
- Final state: `STATE=READY`
- Final current head: `116263507217f640b4c89aa951a92b05651351d4`
- Successor package generated head:
  `08b41e12f820989ade4fafed9866f1f9fb119cb6`
- Successor package head status: `refresh_only_descendant`

Final post-merge check output:

```text
POST_MERGE_HANDOFF_REFRESH
current_head=11626350
freshness_warning_present=False
refresh_required=False
latest_successor_prompt=
result=NOOP
next_safe_action=continue_without_post_merge_handoff_refresh
state_path=.agentic/state/handoff/handoff_state.yaml
warning=external_handoff_state_not_required

successor_package_head_status=refresh_only_descendant
successor_package_generated_head=08b41e12f820989ade4fafed9866f1f9fb119cb6
successor_package_current_head=116263507217f640b4c89aa951a92b05651351d4
```

Cycle 006 therefore required one product PR and one administrative successor
package refresh PR. It did not require a separate external handoff PR.

## Incidental CI Observations

Comm-SCI did not run the Kit repository's deterministic CI runtime classifier.
Its target workflow remained the target-owned `tests` workflow with one
`pytest (3.11)` job. The Kit CI policy modes such as `full`,
`admin-refresh-light`, `tree-proof`, and `pytest-parallel-shadow` are
self-hosting behavior for `vfi64/agentic-project-kit`, not observed target
behavior in this Comm-SCI retest.

The B1 cycle length improved compared with cycles 003-005:

```text
Cycle 003: product PR + handoff PR + successor refresh PR
Cycle 004: product PR + handoff PR + successor refresh PR
Cycle 005: product PR + handoff PR + successor refresh PR
Cycle 006: product PR + successor refresh PR
```

This is evidence of improvement for the observed path, not proof that the
receipt-store question is solved. The source tree still needed a successor
package refresh PR after merge.

## Friction Log

| Field | Value |
| --- | --- |
| Cycle ID | `B1-COMM-SCI-20260829-006` |
| Task source | Maintainer-requested merge-wrapper retest with a real Comm-SCI modularization task |
| Start/end timestamps | `2026-08-29T14:57:36Z` to `2026-08-29T15:07:05Z` for backup through final refresh merge; final verification immediately after |
| Branch and PR | `codex/b1-cycle-006-merge-wrapper-retest`, PR #14; refresh branch `docs/post-pr14-successor-package-refresh`, PR #15 |
| Kit commands attempted | `command-for`, `rules acknowledge`, `transfer protected-diff-plan`, `transfer commit`, `transfer push-current`, `transfer refresh-llm-context-carriers`, `transfer pr-create`, `transfer pr-wait-ci`, `transfer pr-merge-safe`, `transfer post-merge-check`, `transfer post-merge-settle`, `handoff post-merge-refresh-status` |
| Gates run | Focused pytest 14 passed; App2/runtime pytest 121 passed; full local pytest 1491 passed; App2 selftest PASS; protected diff plan PASS; PR #14 CI SUCCESS; PR #15 CI SUCCESS; final post-merge-check PASS |
| Duration | Product PR CI: about 51 seconds run wall time; refresh PR CI: about 53 seconds run wall time; measured successful merge wrapper call: 8.034 seconds |
| Failures and retries | SSH mirror attempt failed then HTTPS mirror succeeded; first `push-current` blocked on stale Rule-Ack then passed after re-ack; first `pr-create` blocked on missing LLM carriers then passed after carrier refresh; first `pr-wait-ci` used an incorrect expected SHA and was rerun with the actual head; first `pr-merge-safe` blocked on nonvolatile `.agentic/rule_ack/current.json` then passed after targeted cleanup |
| Manual interventions | Created a clean target worktree instead of using a dirty deleted-branch checkout; restored App2 selftest config side effect; removed only generated untracked `.agentic/rule_ack/current.json` before retrying merge |
| Handoff/successor continuation | External handoff state itself was not required; successor package refresh was required and completed via PR #15 |
| Refresh events by the B0 definition | One pure administrative successor-package-refresh PR after the product PR |
| Final state | Product PR #14 merged; refresh PR #15 merged; target branch at `116263507217f640b4c89aa951a92b05651351d4`; `post-merge-check` PASS/READY; no open Comm-SCI PRs |
| Suspected root causes | SSH mirror issue: environment/preference; stale Ack and missing carriers: strict deterministic gate behavior; wrong expected SHA: operator error; external `.agentic/rule_ack/current.json` dirty block: Kit volatility-classification defect |

## Bypass Log

| Timestamp | Task | Planned Kit command | Why Kit command was not used | Replacement action | Friction cost | Safety impact | Suspected root cause | Reproducibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `2026-08-29T15:04Z` | Retry external `pr-merge-safe` | `agentic-kit transfer pr-merge-safe 14 ...` | Preflight treated generated untracked `.agentic/rule_ack/current.json` as nonvolatile dirty state; no observed Kit cleanup command covered that external Rule-Ack file | Removed only `.agentic/rule_ack/current.json` from the temporary target worktree, then reran `pr-merge-safe` | One blocked attempt and one cleanup step | Low; the file was generated local acknowledgement state, untracked, and not target product evidence | Defect: external Rule-Ack output is not in known volatile cleanup/preflight policy | Reproducible when external `rules acknowledge` writes `.agentic/rule_ack/current.json` before external merge preflight |
| `2026-08-29T14:58Z` | Preserve dirty existing target checkout | Product work on existing local checkout | Existing checkout contained tracked local log/history changes and was on a deleted remote branch | Used a fresh worktree from `origin/feature/ui-access-levels-v2` | One worktree setup step | Positive; avoided touching unrelated target-repository state | Preference/environment | Reproducible on this workstation until that checkout is cleaned or archived |

## Correction Record

The following older statement is now obsolete for the retested path:

```text
pr-merge-safe still does not return locally after successful remote merge until a new external merge-cycle retest proves otherwise.
```

Replacement statement:

```text
Cycle 006 retested the released `agentic-project-kit==1.0.7` merge wrapper on a real Comm-SCI external merge. `pr-merge-safe` returned terminal PASS in 8.034 seconds after the successful remote merge, through the idempotent recovery path. The remaining external follow-up is the local Rule-Ack volatility classification gap, not merge-wrapper non-return.
```

This report does not claim general Brownfield portability. It adds one stronger
released-package retest to the already adjudicated `B1_EVALUABLE` evidence base.
