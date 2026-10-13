---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-066: machine-readable adjudications and release evidence

Date: 2026-10-13
Kit state: CLOSED in the candidate implementation; planned fix release 1.0.25.
Consumer VERIFIED_FIXED remains a separate decision after retained external retests.

CLI contract: status exits 0 for a valid catalog and 2 for unknown IDs or invalid
schema. Export defaults to PLANNED (exit 0), returns PASS for unchanged bytes,
and writes only with --execute and a matching --expected-signature. Invalid
inputs/signatures exit 2 without overwriting projections. Its only write scope
is the two status projections and the retest report; remote_effects is none.

## Finding and repair

The curated source `.agentic/greenfield_findings.json` records every requested
family (001–018, 021–066 and bootstrap). The signed `greenfield export` route
renders `docs/reports/greenfield/external-findings-status.json`, its installed
wheel projection and `EXTERNAL_FINDINGS_RETESTS.md` byte-deterministically.
Each record names state, fixed_in, known Kit PRs, report, preconditions, exact
argv templates, bindings and expected result fields. Unknown PRs stay unknown.
Candidate release numbers are planned, not published.

`agentic-kit greenfield status --json` reads installed-package adjudications
without Kit sources, tests, network or a documentation registry. `--id` selects
a family. Validation rejects missing families, unsupported states, unsafe
report paths and incomplete retests. Tests validate every template against CLI
declarations. This is an adjudication export, not a successful retest result.
GF-016 stays PARTIAL pending guided-contract proof in C; GF-063 stays PARTIAL
pending custom-CI support in D. The private consumer ledger is untouched.

## Completed-run evidence contract

`release.evidence_archive: true` opts into final release-run gate E1, enabled
in the Kit repository. E1 requires a separate signature even with upfront
consent and runs only after every applicable publishing/DOI step is PASS.
It writes `docs/reports/release/release-run-<version>.json` with bounded step
results, publishing gate signatures, approvers, consent sources and publication
target, then uses work-start/work-finish/green-CI/post-merge-handoff to commit it.
Registration/reconciliation occurs only when the workspace adopts a registry.
Raw logs, commands, absolute local paths and credentials are excluded.

The snapshot proves completed publishing steps; its own future archive merge
must be verified from Git/PR evidence. Publication and archive targets differ.
E1's own approval stays in local state, avoiding a signature/content cycle.
Existing workspaces are unchanged without opt-in. Different existing evidence
blocks; failures and partial progress persist; successful repetition is a no-op.
No release is executed by this implementation slice.

055/056/058/059 explicitly link the pending 1.0.25 evidence. Absence is never
PASS. Ordinary D4 success does not prove D2R recovery; live proof remains
pending the separately authorized release after the requested implementation.

## Regression and expected external retest

`tests/test_greenfield_status.py` checks deterministic bytes, report coverage,
schema negatives, signatures, idempotency, CLI template validity and installed
wheel reads without Kit tests or registry. `tests/test_release_run_evidence.py`
checks E1 signatures, exact completed-state projection, incomplete-run rejection,
preservation, governed lifecycle calls and an installed-wheel external fixture.
The fixture uses a deterministic fake lifecycle runner and never publishes.

Consumer retest: `agentic-kit greenfield status --json` must return
schema_version=1 and every requested family. Repeat with `--id KIT-GF-055`;
inspect kit_release_evidence availability before treating it as proof. Exact
per-family commands are in the generated retest report and export records.
After a real complete release, approve E1 with its exact signature, verify its
archive PR and administrative handoff merge, and compare committed steps with
the retained local run. No fake publishing evidence is committed here.

Manifest ACK: COMMAND_MANIFEST_ACK 64e1fd0929d3, regenerated through Kit
entrypoint, successor-package and docs/site projection routes. The existing
DPA readiness ACK helper changes only the manifest reference, preserving
Maintainer decisions.
