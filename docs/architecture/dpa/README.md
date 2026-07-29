# Document Projection Architecture

Status: probe-package-staged

Status-date: 2026-07-29

Document class: architecture

## Scope

This directory is the controlled Kit-side staging point for the Document
Projection Architecture (DPA).

This directory is staged through DPA-IMPORT-3. DPA-IMPORT-1 introduced the
architecture index and registry staging. DPA-IMPORT-2 imports the
selected detailed architecture package: specifications, accepted and deferred
DPA decisions, traceability matrices and diagrams. DPA-IMPORT-3 imports Probe
package staging material and selected DP1 evidence snapshots.

This subtree introduces no runtime behavior change, no DP2 implementation, no
full Probe PASS claim, no DPA stable claim and no main-repository conformance
claim. The full Probe PASS claim boundary remains closed.

## Source and closeout evidence

The current source package is the DPA Lab PR carrying final pre-import closeout:

- repository: `vfi64/agentic-project-kit-dpa-lab`;
- PR: `https://github.com/vfi64/agentic-project-kit-dpa-lab/pull/15`;
- Lab head: `0cf944cc153e65a272c773286791f8891efdd1bc`;
- Lab merge commit: `6f927efd625b4239f9ab0e710b48e7d9534fdfec`;
- Kit freeze ref for closeout: `c788a8c530eb0984d088a86e8e7951145581abbe`;
- Kit import baseline for DPA-IMPORT-2:
  `07656f4a94475a8394989467afc6937e04709478`;
- Kit import baseline for DPA-IMPORT-3:
  `e89b0fac21c5599f8e531a937c550134469716cf`;
- closeout token: `DPA_PRE_IMPORT_CLOSEOUT_COMPLETE`.

The Lab records DPA-000 and DPA-100 as `stable`, and DPA-200 through DPA-900 as
`review-ready`. Those statuses are Lab architecture statuses only; they do not
make this Kit checkout DPA-conformant.

## Current import boundary

The selected destination family is:

- `docs/architecture/dpa/` for architecture entry points and later selected
  specification material;
- `docs/architecture/evidence/dpa/` for later exact-ref evidence summaries;
- `docs/reports/dpa/` for later historical closeout or import-slice reports.

DPA-IMPORT-1 used only the architecture entry point and documentation registry
staging. DPA-IMPORT-2 adds selected specifications, decisions, traceability and
diagrams. DPA-IMPORT-3 adds Probe manuals, fixture manifests, selected-writer
planning and historical DP1 evidence snapshots. The current Kit line also
records a DP1 Assessment readiness record that consolidates staged and current
fixture evidence and records DP2 authorization for the selected self-hosting
target scope. Later slices may add refreshed Probe execution evidence,
Assessment records or implementation plans only through separately reviewed
slices.

## Imported architecture package

### Specifications

- `specs/README.md` — DPA specification file map.
- `specs/DPA-000-VISION.md` — stable vision and invariants.
- `specs/DPA-100-FOUNDATIONS.md` — stable terminology and authority model.
- `specs/DPA-200-DOCUMENT-MODEL.md` — review-ready document model.
- `specs/DPA-200-DOCUMENT-FORM-MATRIX.md` — review-ready document-form matrix.
- `specs/DPA-300-REGISTRY-LIFECYCLE-INTEGRATION.md` — review-ready registry and lifecycle contract.
- `specs/DPA-400-RENDERER-CONTRACT.md` — review-ready renderer contract.
- `specs/DPA-500-FRESHNESS-AND-GATES.md` — review-ready freshness and gates contract.
- `specs/DPA-600-CONCURRENCY.md` — review-ready concurrency and workflow serialization contract.
- `specs/DPA-700-MIGRATION.md` — review-ready migration and rollback contract.
- `specs/DPA-800-DP1-DP5.md` — review-ready DP1 through DP5 implementation-sequence contract.
- `specs/DPA-900-FUTURE.md` — review-ready future evolution and review-economics contract.

### Decisions

- `decisions/DPA-ADR-013-DOCUMENT-FORM-PARTITION-AND-BOUNDARIES.md`
- `decisions/DPA-ADR-014-CONSUMER-TRUST-STATE-MODEL.md`
- `decisions/DPA-ADR-015-EARLY-DP1-DISCOVERY.md`
- `decisions/DPA-ADR-016-ACCEPTANCE-STATE-AND-INTERRUPTED-RECOVERY.md`
- `decisions/DPA-ADR-017-PARENT-ENTRY-PARTITION-CONTRACT.md`
- `decisions/DPA-ADR-019-RENDERER-INPUT-RESOURCE-AND-VERSION-MODEL.md`
- `decisions/DPA-ADR-020-PROMOTION-COMMIT-AND-EQUIVALENCE-VERIFICATION.md`
- `decisions/DPA-ADR-021-FRESHNESS-REACCEPTANCE-AND-LAYERED-ACCEPTANCE.md`
- `decisions/deferred/DPA-ADR-018-INDEPENDENT-VERIFICATION-CONTEXT.md`

ADR-018 is imported only as a deferred, non-normative proposal because DPA-900
preserves it as historical review-economy input. It is not accepted Kit
governance.

### Traceability and diagrams

- `traceability/` contains the DPA-200 through DPA-900 traceability matrices.
- `diagrams/` contains the imported Mermaid architecture diagrams.

Traceability and diagrams support review and implementation planning. They do
not supersede the specification files and do not prove Kit conformance.

### Probe Package Staging

- `probes/` contains the DPA-IMPORT-3 Probe package staging index, Probe
  backlog, DP1 Probe manuals, execution-package draft, selected-writer fixture
  plan, validation checklist and fixture/cleanup package.
- `../evidence/dpa/probes/` contains selected historical Lab evidence
  snapshots: read-only baseline evidence with result `PASS_WITH_LIMITATIONS`
  and mutation-sandbox evidence with result `PARTIAL`. It also contains the
  current Kit read-only DP1 baseline refresh at
  `46deae72c2d37ae18331203bc3a6be19c9a67f64` with result
  `PASS_WITH_LIMITATIONS`, current PROBE-001 registry compatibility evidence,
  PROBE-002 lifecycle readiness preflight, the WRT-CH-001 admin-refresh
  observations, PROBE-003 workflow serialization readiness preflight and Renderer
  Probe readiness preflight, plus current read-only Probe execution for
  `READ_ONLY`/`NOT_REQUIRED` fixture cases and current authorized
  non-production fixture evidence for the remaining Probe families.
- `../evidence/dpa/assessment/DP1_ASSESSMENT_READINESS_20260728.md`
  consolidates the imported and current DP1 evidence into an Assessment
  readiness decision surface. It records `DP2_AUTHORIZED`, preserves the full
  Probe PASS claim boundary and authorizes DP2 only for the selected
  self-hosting target scope.

These materials are historical and preparatory. They preserve Lab validation ref
`c788a8c530eb0984d088a86e8e7951145581abbe` and older command manifest
acknowledgement `COMMAND_MANIFEST_ACK 8610cfd2990a` as evidence inputs. Any
future Probe execution in this Kit must freeze a fresh current validation ref
and command manifest acknowledgement before running.

The Kit-side DP1 read-only baseline refresh evidence under
`../evidence/dpa/probes/dp1-readonly-46deae7-20260728/` satisfies current
baseline command-health refresh only. The full fixture evidence under
`../evidence/dpa/probes/fixture-evidence-b1b708cb-20260728/` records 36
authorized non-production fixture passes and rollback cleanup proof for the
current Kit ref. The Assessment readiness record under
`../evidence/dpa/assessment/` turns that evidence into a precise DP2
authorization map. The Maintainer Assessment is now recorded as `DP2_AUTHORIZED`, with
`docs/handoff/CURRENT_HANDOFF.md` and writer `WRT-CH-001` selected as the first
DP2 target scope. Probe-family and rollback-cleanup evidence are satisfied for
the current Kit ref, DP2 authorization is recorded and the full Probe PASS claim
boundary remains closed.

The read-only wrapper `agentic-kit dpa readiness` validates that staged
Assessment readiness record, reports the deterministic implementation
percentage and shows the current DP2 authorization state without mutating
repository files.

The read-only wrapper `agentic-kit dpa readonly-probe-execution` executes only
DP1 Probe fixture-manifest cases whose mutation scope is `READ_ONLY` and whose
authorization is `NOT_REQUIRED`. It records mutable or context-dependent cases
as blocked, writes bounded Probe evidence when requested and preserves the full
Probe PASS and DP2 authorization boundaries.

The controlled wrapper `agentic-kit dpa fixture-evidence` executes DP1 fixture
manifest cases in read-only source state, temporary fixture roots and
disposable branch simulations after an explicit non-production fixture
authorization token. It can write bounded Probe evidence, prove rollback
cleanup for fixture state and still preserves the DP2 authorization, production
mutation, Kit conformance and generated-output boundaries.

The read-only wrapper `agentic-kit dpa probe-003-readiness` validates current
PROBE-003 workflow serialization source, test and control surfaces, optionally
writes bounded DPA probe evidence and preserves the full Probe PASS boundary
until authorized disposable workflow fixtures execute.

The read-only wrapper `agentic-kit dpa renderer-readiness` validates current
Renderer Probe candidate source, test and control surfaces, optionally writes
bounded DPA probe evidence and preserves the full Renderer Probe PASS boundary
until an approved DPA renderer map, identity/version fixtures and side-effect
fixtures exist.

The read-only wrapper `agentic-kit dpa probe-004-readiness` validates current
PROBE-004 migration and rollback source, test and control surfaces, optionally
writes bounded DPA probe evidence and preserves the full PROBE-004 PASS
boundary until Maintainer-scoped migration-form, rollback-package, renderer
rollback and generated-output rollback fixtures execute.

The read-only wrapper `agentic-kit dpa dp2-decision-readiness` packages the
current blocker set, candidate first DP2 target scope and required Maintainer
actions for review. It may write bounded Assessment evidence, but it does not
record Maintainer Assessment, select DP2 scope, prove rollback cleanup or
authorize DP2.

The read-only wrapper `agentic-kit dpa maintainer-record-check` validates the
current blocked DP2 Maintainer Assessment record or an explicitly supplied
template/authorization record. It allows Assessment recording without DP2
authorization, and still fails closed for premature authorization claims,
missing Probe dispositions, unselected target scope and missing rollback proof.

The controlled wrapper `agentic-kit dpa current-handoff-refresh` is the first
DP2 lifecycle implementation guard for the selected `docs/handoff/CURRENT_HANDOFF.md`
target. It renders the current operational handoff block from
`.agentic/operational_handoff_state.yaml`, checks the DP2 authorization record,
uses the existing Workspace mutation lock, rejects stale validation refs,
rejects target drift against persisted DPA acceptance state, revalidates source,
target and HEAD under lock, verifies written bytes and records lifecycle-owned
acceptance state under `.agentic/dpa/acceptance/`. Initial acceptance requires
the explicit `--initialize-acceptance` flag. The wrapper does not mutate
successor-handoff packages, does not claim Kit-wide DPA conformance and does not
replace the existing post-merge Handoff PR workflow.

The release-preparation writer `agentic-kit release-prep` now routes its
`docs/handoff/CURRENT_HANDOFF.md` version-line mutation through the same DPA
target-drift, Workspace-lock, under-lock revalidation, post-Write verification
and acceptance-state path whenever the current workspace carries DPA readiness
or DPA acceptance state. Non-DPA workspaces retain the prior release metadata
write behavior. This records WRT-CH-002 as the acceptance-state writer for that
target mutation; it does not execute a release, publish a tag, publish a DOI or
claim Kit-wide DPA conformance.

The post-release DOI closeout writer `agentic-kit post-release-doi-closeout
--write` now routes its `docs/handoff/CURRENT_HANDOFF.md` verified-release and
DOI metadata mutation through the same DPA target-drift, Workspace-lock,
under-lock revalidation, post-Write verification and acceptance-state path
whenever the current workspace carries DPA readiness or DPA acceptance state.
Non-DPA workspaces retain the prior DOI metadata write behavior. This records
WRT-CH-003 as the acceptance-state writer for that target mutation; it does not
publish a release, create DOI records or claim Kit-wide DPA conformance.

The read-only wrapper `agentic-kit dpa readiness` now reports DPA
implementation readiness at 100% for the current authorization record: all DP2
entry evidence fields are satisfied for the current Kit ref and no DP2 entry
blockers remain. The current selected self-hosting writer scope is
`WRT-CH-001` plus `WRT-CH-002` plus `WRT-CH-003` plus `WRT-CH-004`; no current
self-hosting `CURRENT_HANDOFF.md` writer remains deferred. `WRT-CH-005` and
`WRT-CH-006` remain outside that selected target scope.

The current WRT-CH-001 observation package under
`../evidence/dpa/probes/wrt-ch001-admin-refresh-observation-57a892e4-20260729/`
records the merged post-PR1932 handoff refresh PR #1933 after the
self-stale successor-prompt fix. It is administrative refresh observation
evidence only; it does not expand the selected first DP2 target scope and does
not claim disposable fixture execution or Kit conformance.

The WRT-CH-002 scope-extension package under
`../evidence/dpa/probes/fixture-evidence-38df3ee1-wrt-ch002-20260729/`
records a fresh authorized non-production fixture run at Kit validation ref
`38df3ee1810a8731058f2f1971df317c2ab7b3ca`. The matching Maintainer-record
check under
`../evidence/dpa/assessment/maintainer-record-check-38df3ee1-wrt-ch002-20260729/`
validates the updated DP2 authorization record. This authorizes DPA reliance
for the WRT-CH-002 release-preparation writer only inside the selected
`docs/handoff/CURRENT_HANDOFF.md` target scope; it does not execute a release,
mutate production metadata or claim Kit conformance.

The WRT-CH-003 scope-extension package under
`../evidence/dpa/probes/fixture-evidence-f345cf25-wrt-ch003-20260729/`
records a fresh authorized non-production fixture run at Kit validation ref
`f345cf252f16843f92c45577523ef877cdd04355`. The matching Maintainer-record
check under
`../evidence/dpa/assessment/maintainer-record-check-f345cf25-wrt-ch003-20260729/`
validates the updated DP2 authorization record. This authorizes DPA reliance
for the WRT-CH-003 post-release DOI closeout writer only inside the selected
`docs/handoff/CURRENT_HANDOFF.md` target scope; it does not publish DOI
metadata, mutate production metadata or claim Kit conformance.

The WRT-CH-004 scope-extension package under
`../evidence/dpa/probes/fixture-evidence-be37f052-wrt-ch004-20260729/`
records a fresh authorized non-production fixture run at Kit validation ref
`be37f052d67cc2646d56c103cef962823a01cee5`. The matching Maintainer-record
check under
`../evidence/dpa/assessment/maintainer-record-check-be37f052-wrt-ch004-20260729/`
validates the updated DP2 authorization record. This authorizes DPA reliance
for the WRT-CH-004 action-spec surfaced mutation-authority writer only inside
the selected `docs/handoff/CURRENT_HANDOFF.md` target scope; it does not execute
any surfaced action, mutate production state or claim Kit conformance.
The source implementation is the parameterized action-spec guard in
`src/agentic_project_kit/action_specs.py`: every built-in action surface that
mentions a `CURRENT_HANDOFF.md` mutation must declare WRT-CH-004, name the
selected lifecycle writer it dispatches through and expose the route in
`agentic-kit actions show <id>`.

Historical evidence packages still preserve earlier `DP2_BLOCKED` and
"DP2 implementation blocked" states. Those records remain part of the audit trail;
they do not override the current `DP2_AUTHORIZED` Assessment record.

## Generated-output and command-updated boundary

The generated or command-updated Kit outputs boundary keeps those files owned by
their source, generator or command contract. DPA import work must not manually
patch generated or command-updated Kit outputs to make target bytes match the
Lab.

This boundary includes successor-handoff package outputs and any future DPA
touchpoint that is classified as command-updated by the Kit.

## Next governed step

After this index, registry staging, Assessment-readiness, initial lifecycle
wrapper slice, WRT-CH-002 release-preparation routing and WRT-CH-003
post-release DOI closeout routing, the next DPA work remains governed by the
closeout restrictions:

1. Preserve the DPA Lab source ref and Kit import baseline in every import slice.
2. Keep WRT-CH-001 administrative refresh, WRT-CH-002 release preparation and
   WRT-CH-003 post-release DOI closeout on the lifecycle-owned
   `CURRENT_HANDOFF.md` acceptance-state path.
3. Keep the full WRT-CH-001 administrative refresh PR-flow evidence boundary
   separate until that observation is explicitly closed.
4. Keep DP2 implementation within the authorized
   WRT-CH-001/WRT-CH-002/WRT-CH-003/WRT-CH-004 target scope unless a later
   Maintainer Assessment selects or authorizes another target.
5. Re-run the fixture evidence package before any production runtime mutation if
   Probe manuals, fixture manifest, selected target, command manifest or DPA
   implementation code changes.
6. Run the Kit documentation, registry and release-relevant gates selected by
   each import slice.
