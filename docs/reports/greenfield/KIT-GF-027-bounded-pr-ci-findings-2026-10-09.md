---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-027: bounded-pr-ci-findings

Date: 2026-10-09
Kit state: CLOSED in this patch; released-package Cockpit retest pending.
Source: vfi64/agp-Cockpit main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, family KIT-GF-027.
The external ledger remains read-only; VERIFIED_FIXED belongs to its owner.

## Finding and repair

PR orchestration returned large nested stdout and used an execution-error exit
for a valid red-CI finding. The shared output module adds opt-in --summary to
create/complete/closeout routes, preserving detailed JSON compatibility and all
raw evidence in a local file. Structured FAILED/NOT_RUN/PENDING findings return
rc 0 while result_status stays BLOCKED. All unrelated failures stay nonzero.
Existing guarded consumers require result_status PASS, so rc 0 cannot green a PR.
The readiness adapter adds read-only current-head NOT_RUN diagnosis.

## Regression and external retest

`tests/test_pr_orchestration_output.py`: <4 KB success projection, lossless full
step evidence, nested CI propagation, nonzero execution errors and mixed failures.
Existing lifecycle/guardrail suites exercise unchanged guarded merge behavior.
External retest: installed-wheel manifest workspace, compact create/closeout
projection and a red CI result; no recovery-only execution error should be needed.
NOT_RUN must name pr rerun-checks. Repair the real CI, then resume the same PR.

## Risks and approach

Consumers must inspect result_status, not rc alone. --summary is opt-in so existing
callers needing detailed step JSON retain their contract. Evidence storage failure
blocks the summary instead of losing logs. Core projection is modular; existing
large lifecycle adapters only call it. Further lifecycle modularization is a
separate slice. Explicit dictionaries suffice; an extra DCO layer adds no value.

## Validation evidence

Manifest ACK: `COMMAND_MANIFEST_ACK dc9b0fdad017`.
Full suite: 3378 tests passed. 103 targeted tests passed. Eight installed-wheel checks passed in a newly
initialized external manifest workspace with generated command references,
no Kit tests and no documentation registry. Package provenance resolved through
site-packages. The fixture exercised signed CLI execution, refusal, replay,
full raw evidence and bounded output; it did not rerun production CI.
Ruff, check-docs and doctor passed (76 existing report-only lifecycle warnings).
The bound DPA readiness ACK was synchronized; its authorization scope is unchanged.
The architecture contract remains valid. No release, tag or publication changed.

CI found ANSI-colored help output in three new option assertions. The assertions
now remove ANSI formatting while checking the same public options. The focused
color-enabled CLI checks passed. During that actual test failure, the new CI
classifier correctly refused a rerun because the executable Tests step failed;
the closeout returned a structured FAILED finding and preserved its merge block.
