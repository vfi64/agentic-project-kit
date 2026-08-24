# Post-v1.0.4 B1-KIT-004/005 External Context and Merge Fix

Status: implemented_retest_pass  
Status date: 2026-08-24  
Finding sources:

- `docs/reports/POST_V1_0_4_B1_COMM_SCI_CYCLE_002_RESULTS_20260824.md`
- external repository: `vfi64/Comm-SCI-Control-private`
- external PR retested idempotently: `vfi64/Comm-SCI-Control-private#4`

## Scope

This slice fixes and retests two external-workspace defects found during Comm-SCI
Cycle 002:

- `B1-KIT-004`: `refresh-llm-context-carriers` wrote the latest report to the
  external workspace namespace, while `require-fresh-llm-context` and
  `pr-merge-safe` still looked at the self-hosting legacy docs path.
- `B1-KIT-005`: `pr-merge-safe` required Kit self-hosting rule snapshots in the
  external workspace and treated Kit-generated transient carriers as dirty
  target-repository changes.

This is a Kit repair/retest slice. It does not count as a new B1 real work
cycle because no Comm-SCI product work was performed and no new Comm-SCI PR was
created.

## Implementation

The fix keeps the external boundary explicit:

- centralized external workspace detection in `workspace_detection`;
- made the fresh LLM-context gate resolve the latest handoff report through the
  workspace namespace;
- made known volatile transfer paths workspace-aware, including
  `.agentic/state/handoff/transfer_handoff_reports/` in external workspaces;
- added installed-package fallbacks for the command manifest and transfer safety
  resources so external users do not have to provide Kit-internal files;
- added an external `pr-merge-safe` preflight that skips self-hosting rule
  acknowledgement only when the workspace is an external manifest workspace and
  the Git worktree is clean except for known Kit-generated transient carriers;
- kept substantive dirty target-repository paths fail-closed.

Target-repository decisions remain target-owned. Missing target facts or dirty
product files still block; missing Kit-internal resource files are a Kit
packaging/fallback concern.

## Kit Validation

Targeted regression suite:

```text
110 passed, 23 warnings
```

Covered cases:

- external latest transfer handoff report path is accepted from
  `.agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json`;
- external fresh-context gate passes with matching hashes while warning that
  self-hosting source hashes are not required locally;
- external `pr-merge-safe` skips self-hosting rule acknowledgement after clean
  external preflight;
- external `pr-merge-safe` blocks substantive dirty files;
- transfer safety resources are declared for wheel inclusion;
- LLM execution context can load packaged transfer policy resources in an
  external workspace.

Wheel inspection after the packaging change confirmed these installed package
resources:

```text
agentic_project_kit/reference/agentic-kit-commands.json
agentic_project_kit/reference/one_command_transfer_protocol.yaml
agentic_project_kit/reference/transfer_safety_rules.yaml
```

## Comm-SCI Installed-Wheel Retest

Retest workspace:

```text
/tmp/comm-sci-b1-kit-004-005-retest-RvUQ1k3f/repo
```

Retest baseline:

- branch: `feature/ui-access-levels-v2`;
- head: `181397c`;
- installed wheel version: `agentic-project-kit==1.0.4`, built from this fix
  branch;
- package import path:
  `.venv-kit-retest/lib/python3.14/site-packages/agentic_project_kit/__init__.py`;
- packaged resources present:
  command manifest, transfer safety rules, one-command transfer protocol.

External health checks:

- `agentic-kit command-for --task transfer --json`: PASS, packaged manifest
  discovery works in the external workspace;
- `agentic-kit doctor --root .`: Overall PASS, with the intended external
  command-manifest WARN and 254 packaged commands;
- `agentic-kit check-docs --root .`: PASS;
- initial `git status --short`: clean.

Fresh-context retest:

```text
agentic-kit transfer refresh-llm-context-carriers --json
```

Result:

- `result_status`: PASS;
- outbox path: `.agentic/transfer/outbox/last_result.txt`;
- latest report path:
  `.agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json`;
- latest log path:
  `.agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.log`.

```text
agentic-kit transfer require-fresh-llm-context --json
```

Result:

- `result_status`: PASS;
- valid contexts: `outbox`, `latest_handoff_report`;
- `refresh_required_for_running_chats`: true;
- `source_hashes_match_current_repo`: true;
- warning only:
  `external_workspace_kit_internal_source_hashes_incomplete`.

The generated LLM context recorded:

- `workspace_mode`: `external_manifest_workspace`;
- command count: 254;
- `running_chat_refresh_contract.refresh_required_for_running_chats`: true;
- volatile cleanup paths included both the legacy self-hosting report paths and
  the external namespace report paths.

Merge-wrapper retest:

```text
agentic-kit transfer pr-merge-safe 4 \
  --expected-head-sha 528e8f63af3a925662363a245449b61d87d7d5bf \
  --main-branch feature/ui-access-levels-v2 \
  --merge-method squash \
  --json
```

Result:

- `result_status`: PASS;
- `returncode`: 0;
- stdout contained `IDEMPOTENT_PR_RECOVERY`, `STATE=ALREADY_MERGED`,
  `PR=4`, and `RESULT=PASS`;
- no rule snapshot acknowledgement was required from the external workspace;
- the wrapper removed the generated transient carriers before returning.

Post-wrapper state:

- `git status --short --untracked-files=all`: clean;
- `agentic-kit transfer repo-status --json`: PASS with empty stdout;
- a strict `require-fresh-llm-context --json` run after cleanup blocked on
  missing carriers, which is expected because the merge preflight intentionally
  removed those volatile files once the merge-wrapper action had consumed them.

## Decision

`B1-KIT-004` and `B1-KIT-005` are implemented and retested against a real
Comm-SCI external manifest workspace using an installed wheel.

B1 remains `realbetrieb_running`, not evaluable: this slice fixes two Kit
defects but does not add a new real Comm-SCI work cycle or a new merge-boundary
cycle. The remaining high-value external follow-ups are:

- `B1-KIT-003`: external PRs with no remote checks must remain distinct from
  green remote CI;
- `B1-KIT-006`: post-merge checks are still main-branch oriented and need a
  documented or implemented external base-branch path;
- `B1-KIT-007`: task-oriented command discovery still does not route common
  health-check words such as `doctor` and `check-docs`;
- `B1-KIT-008`: post-merge settle/admin-refresh non-return remains open.
