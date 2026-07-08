# Next-Turn A0 Standard Error Additions

Status-date: 2026-05-25
Status: active
Decision status: accepted
Review policy: Review together with `docs/governance/WORK_ORDER_WORKFLOW_CONTRACT.md` before Slice A1.

## Purpose

This addendum records standard-error variants observed during the Slice A0 implementation and merge cycle. They refine the standard-error list in `docs/governance/WORK_ORDER_WORKFLOW_CONTRACT.md` and should be folded into the main list when the next planning-file maintenance slice runs locally.

## Additions

- `patch-generator-shell-python-quoting`: assistant-authored patch generators must not use large shell blocks with embedded Python and shell parameter expansion such as `${...}` as the normal path. The durable fix is fixed-slot work orders and small local modules, not larger copy-and-paste blocks.
- `checkout-blocked-by-untracked-generated-files`: branch switching must preflight untracked target files before checkout. If a checkout would overwrite generated files, the runner must stop with a recovery instruction instead of setting a stale failure state after later gates pass.
- `nothing-to-commit-treated-as-failure`: already-reached target states such as an existing commit, existing PR, existing branch, or clean no-op must be classified as `PASS_ALREADY_DONE` or `NOOP`, not as a failed slice.
- `local-green-but-status-stale-fail`: a prior phase failure must not permanently poison the final result when later phases prove the desired state is valid. The runner needs phase-scoped status and a final decision model that distinguishes product failure, evidence failure, and recoverable control-flow failure.
- `fail-log-upload-not-guaranteed`: `f` is only robust when the run guarantees remote evidence publication or explicitly reports `REMOTE_EVIDENCE: FAIL`. Local-only `/tmp` logs are insufficient for the intended `d`/`f` protocol.

## A1 Acceptance Implication

Slice A1 must implement a result/evidence finalizer that writes structured results and terminal logs from the beginning of execution, publishes them when the declared remote-evidence policy allows it, and records a precise recovery instruction when publication is unsafe or impossible.

A1 should also introduce idempotent final-result classification so `nothing to commit`, already-existing PRs, already-merged PRs, and already-uploaded evidence are not treated as ordinary failures.

## Review Policy

Review this addendum together with `docs/governance/WORK_ORDER_WORKFLOW_CONTRACT.md` before Slice A1 starts. When Slice A1 updates the main plan, fold these additions into the primary standard-error list or explicitly keep this file as the active addendum.
