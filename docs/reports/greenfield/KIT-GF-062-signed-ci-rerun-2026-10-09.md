---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-062: signed-ci-rerun

Date: 2026-10-09
Kit state: CLOSED in this patch; released-package Cockpit retest pending.
Source: vfi64/agp-Cockpit main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, family KIT-GF-062.
The external ledger remains read-only; VERIFIED_FIXED belongs to its owner.

## Finding and repair

No Kit route could rerun a failed CI run that never started. The new thin
`pr rerun-checks` adapter composes an importable Actions evidence collector,
pure failed-job classifier and signed executor. The signature covers repo, PR
head, latest run IDs, attempts and job evidence. Failed executable steps override
the 3-second startup rule. Unknown evidence blocks. Pagination is checked in full.
Fresh head/attempt checks precede mutation. Durable pre-request intent prevents
repeating a request after a lost response. Remote effects declare workflow_rerun.

## Regression and external retest

`tests/test_pr_ci_rerun.py`: NOT_RUN versus real failed step, signatures, head and
attempt drift, pagination, no mutation on rejection, and replay-safe receipts.
External retest: plan an Actions quota/startup failure, approve the exact plan,
verify only failed jobs are retried and receipt run IDs match. A genuine failed
test must be refused. An installed-wheel fixture must provide generated command
references and contain neither Kit tests nor the Kit documentation registry.

## Risks and approach

A rerun does not fix exhausted quota. No-log API failures are not proof of NOT_RUN.
Other providers remain outside this mutation route. The API cannot atomically
compare a PR head while accepting a rerun; fresh preflight plus immutable run
identity bounds that race. A lost POST response intentionally stops for diagnosis.
Small typed result dictionaries and pure classifiers suffice; a separate DCO
framework would add no useful validation beyond these explicit states.

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
