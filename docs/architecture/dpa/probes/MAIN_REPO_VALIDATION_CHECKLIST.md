# Main Repository Validation Checklist

Status: active

Status-date: 2026-07-28

## Current read-only validation pass

Recorded in:

`evidence/repo-facts/CURRENT-MAIN-VALIDATION-C788A8C5-20260727.md`

- [x] Fetch current `origin/main`.
- [x] Confirm local `main`, local `HEAD` and `origin/main` match
  `c788a8c530eb0984d088a86e8e7951145581abbe`.
- [x] Confirm the Kit worktree is clean before and after read-only inspection.
- [x] Inspect command manifest entries relevant to handoff, docs, registry,
  evidence and transfer.
- [x] Inspect successor handoff generated-output and command-contract surfaces.
- [x] Run current read-only Kit documentation gates:
  `agentic-kit check-docs` and `agentic-kit doctor`.
- [x] Run current read-only/dry-run Kit diagnostic commands for divergence,
  repo status, command-reference currency, handoff check, registry summary,
  unregistered-document check and handoff lifecycle planning/reporting.
- [x] Record candidate source and test surfaces for PROBE-001, PROBE-002,
  PROBE-003, PROBE-004 and renderer Probes.
- [x] Draft a Probe execution package shape with preflight commands, candidate
  evidence layout and explicit missing fixture gates.
- [x] Record current static source-level `CURRENT_HANDOFF.md` reader/writer
  graph for Probe and controlled-import planning.
- [x] Draft selected-writer fixture and out-of-scope planning matrix for the
  current `CURRENT_HANDOFF.md` writer graph.
- [x] Materialize a prepared DP1 Probe fixture manifest covering PROBE-001,
  PROBE-002, renderer Probes, PROBE-003 and PROBE-004.
- [x] Materialize cleanup and Assessment rules for read-only, temporary-repo
  and disposable-branch fixture modes.
- [x] Add deterministic Lab validation for the prepared Probe fixture manifest.
- [x] Execute and record read-only DP1 baseline evidence with
  `PASS_WITH_LIMITATIONS`.
- [x] Add deterministic Lab validation for read-only DP1 baseline evidence.
- [x] Execute and record sandbox-only selected-writer mutation evidence with
  `PARTIAL`; no Kit production state was mutated.
- [x] Add deterministic Lab validation for sandbox-only mutation evidence.
- [x] Draft controlled-import destination and PR-slice proposals.
- [x] Record that the generated successor-package freshness blocker observed at
  `70403d...` is resolved on current Kit `main` by PR #1877.
- [x] Prepare an internal sandbox Assessment and Maintainer decision package for
  final DPA pre-import closeout preparation.
- [x] Record Maintainer adjudication, audit rerun and final DPA pre-import
  closeout.

## Still open before Probe execution or Kit mutation

- [x] Adjudicate whether the sandbox-only mutation evidence is sufficient for
  pre-import closeout preparation or whether additional disposable fixtures are
  required, using
  `integration/FINAL_DPA_PRE_IMPORT_MAINTAINER_DECISION_PACKAGE_20260728.md`.
- [ ] Freeze exact executable Probe command lines against any remaining final
  non-sandbox Probe validation ref.
- [ ] Freeze the prepared Probe fixture manifest revision against any remaining
  mutation-scoped Probe validation ref.
- [ ] Select exact evidence paths for mutation-scoped Probe families at
  execution time.
- [x] Obtain Maintainer authorization for any additional mutation-scoped
  fixtures and record Maintainer out-of-scope adjudications where selected
  writers are deferred.
- [ ] Verify handoff state authority for the selected production target.
- [ ] Verify documentation registry schema compatibility with proposed DPA
  `ProjectionContract` and `PartitionContract` fixtures.
- [ ] Verify lifecycle finding model compatibility with projection findings.
- [ ] Verify `checks.py` and required-check structure contracts for selected
  projection gates.
- [ ] Verify refresh concurrency guards under branch, PR and integration
  scenarios.
- [x] Record Maintainer-selected controlled-import destination paths and PR
  slice boundaries.
- [ ] Run DP1 Probe execution.
- [ ] Update DPA specifications only if confirmed differences require governed
  amendments.
