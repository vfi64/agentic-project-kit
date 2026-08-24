# Post-v1.0.4 B1-KIT-006 External Post-Merge Base Branch Check

Status: implemented_retest_pass  
Status date: 2026-08-24  
Finding source:

- `docs/reports/POST_V1_0_4_B1_COMM_SCI_CYCLE_002_RESULTS_20260824.md`
- external repository: `vfi64/Comm-SCI-Control-private`
- external integration branch retested: `feature/ui-access-levels-v2`

## Scope

This slice fixes and retests `B1-KIT-006`: external post-merge checking was
hard-wired to `main`, so a governed external integration branch could not be
evaluated after a PR merge.

During the retest, two adjacent external-boundary assumptions also surfaced and
were fixed in the same slice:

- the old self-hosting handoff state file is not a required external workspace
  artifact when the deterministic successor handoff package is present;
- successor-package freshness must not require the self-hosting
  `RESULT=NEW_CHAT_BOOTSTRAP_DONE` marker in external manifest workspaces,
  because their bootstrap acceptance contract uses different generated signals.

The slice does not perform a new Comm-SCI product cycle and does not publish a
Kit release.

## Implementation

Implemented changes:

- `agentic-kit transfer post-merge-check` now accepts `--base-branch` as an
  alias for `--main-branch`;
- branch mismatch diagnostics now use
  `NEXT=switch_to_expected_branch_and_sync` instead of a main-only next action;
- `handoff post-merge-refresh-status` resolves the handoff-state path through
  the workspace manifest;
- missing self-hosting handoff state now reports structured
  `result=STATE_UNAVAILABLE` instead of raising a traceback;
- missing external manifest-workspace handoff state now reports structured
  `result=NOOP` with `warning=external_handoff_state_not_required`;
- successor-package freshness keeps the self-hosting bootstrap marker
  requirement, but accepts the external bootstrap contract generated for
  external manifest workspaces.

The external boundary remains explicit: Kit-internal or self-hosting-only files
are not required from the target repository user, but target-owned handoff
package freshness still has to be generated and committed by the target repo's
normal branch/PR flow.

## Kit Validation

Targeted regression suite:

```text
13 passed, 3 warnings
```

Covered cases:

- configured non-main base branch is accepted by `post-merge-check`;
- `post-merge-check --help` exposes `--base-branch`;
- external missing handoff state is a structured NOOP with an explicit warning;
- self-hosting missing handoff state is a structured blocked state without a
  traceback;
- external successor-package freshness accepts the external bootstrap contract;
- stale successor-package generated head still blocks.

Targeted Ruff:

```text
All checks passed.
```

Command reference check after regeneration:

```text
result_status=PASS
2 passed
```

## Comm-SCI Installed-Wheel Retest

Retest workspace:

```text
/var/folders/kg/xbnzk_bn4xbbnr3psb0lpwhm0000gn/T/b1-kit-006-retest2-XXXXXX.Mhj3MCCkNS/repo
```

Retest baseline:

- branch: `feature/ui-access-levels-v2`;
- head: `181397ce1aeb252f7bcc7872b71da56032186693`;
- initial successor package `generated_head`:
  `bdef7b63723b23bb52e5c82de7c723a4a932d61c`;
- installed wheel version: `agentic-project-kit==1.0.4`, built from this fix
  branch;
- initial target worktree: clean.

Direct external handoff-state status:

```text
POST_MERGE_HANDOFF_REFRESH
current_head=181397c
freshness_warning_present=False
refresh_required=False
result=NOOP
state_path=.agentic/state/handoff/handoff_state.yaml
warning=external_handoff_state_not_required
```

Default main-oriented check remains fail-closed on the integration branch:

```text
result_status=FAIL
returncode=2
next_action=STATE=BLOCKED; NEXT=switch_to_expected_branch_and_sync
stderr=Expected branch main before post-merge lifecycle check. Current branch: feature/ui-access-levels-v2
```

Base-branch-aware check before package refresh reaches the correct next gate:

```text
agentic-kit transfer post-merge-check --base-branch feature/ui-access-levels-v2 --json
result_status=FAIL
next_action=STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH
NEXT=refresh_successor_package
stdout finding=validation_report.json generated_head does not match HEAD or refresh-only ancestry
```

After regenerating the external successor handoff package with:

```text
agentic-kit transfer chat-switch-complete --render-prompt --json
```

the command reported:

```text
result_status=PASS
generated_head=181397ce1aeb252f7bcc7872b71da56032186693
validation_report_path=.agentic/state/handoff/packages/latest/validation_report.json
```

The repeated base-branch post-merge check then passed:

```text
result_status=PASS
next_action=STATE=READY
NEXT=none
stdout note=successor_package_head_status=exact
```

The temp clone was intentionally left dirty after `chat-switch-complete` because
the refreshed external handoff package is a target-repository change. It was not
committed or pushed from this retest slice.

## Decision

`B1-KIT-006` is implemented and retested against a real Comm-SCI external
manifest workspace using an installed wheel.

B1 remains `realbetrieb_running`, not evaluable. The result improves external
post-merge diagnostics and enables a green external post-merge check after the
successor handoff package is refreshed on the target integration branch, but it
does not add a new real Comm-SCI product cycle.

Remaining external automation boundary:

- a future wrapper may be needed to create or complete the target-repository
  successor-package refresh commit/PR after an external merge;
- `B1-KIT-008` remains open for post-merge settle/admin-refresh completion
  behavior.
