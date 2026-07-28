# Document Projection Architecture

Status: probe-package-staged

Status-date: 2026-07-28

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
records a DP1 Assessment readiness record that consolidates the staged evidence
and keeps DP2 implementation blocked. Later slices may add refreshed Probe
execution evidence, Assessment records or implementation plans only through
separately reviewed slices.

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
  `PASS_WITH_LIMITATIONS`.
- `../evidence/dpa/assessment/DP1_ASSESSMENT_READINESS_20260728.md`
  consolidates the imported and current DP1 evidence into an Assessment
  readiness decision surface. It records `DP2_BLOCKED`, preserves the full
  Probe PASS claim boundary and names the exact Probe, writer, rollback and
  Maintainer authorization gaps that must close before DP2 can start.

These materials are historical and preparatory. They preserve Lab validation ref
`c788a8c530eb0984d088a86e8e7951145581abbe` and older command manifest
acknowledgement `COMMAND_MANIFEST_ACK 8610cfd2990a` as evidence inputs. Any
future Probe execution in this Kit must freeze a fresh current validation ref
and command manifest acknowledgement before running.

The Kit-side DP1 read-only baseline refresh evidence under
`../evidence/dpa/probes/dp1-readonly-46deae7-20260728/` satisfies current
baseline command-health refresh only. The Assessment readiness record under
`../evidence/dpa/assessment/` turns that evidence into a precise DP2 blocker
map. Mutation-scoped fixtures remain unrun, Maintainer Assessment remains
unrecorded and the full Probe PASS claim boundary remains closed.

The read-only wrapper `agentic-kit dpa readiness` validates that staged
Assessment readiness record and reports the current DP2 blocker set without
mutating repository files.

## Generated-output and command-updated boundary

The generated or command-updated Kit outputs boundary keeps those files owned by
their source, generator or command contract. DPA import work must not manually
patch generated or command-updated Kit outputs to make target bytes match the
Lab.

This boundary includes successor-handoff package outputs and any future DPA
touchpoint that is classified as command-updated by the Kit.

## Next governed step

After this index, registry staging and Assessment-readiness slice, the next DPA
work remains governed by the closeout restrictions:

1. Preserve the DPA Lab source ref and Kit import baseline in every import slice.
2. Keep WRT-CH-003 and the full WRT-CH-001 administrative refresh PR flow
   deferred from the first DP2 target.
3. Keep DP2 implementation blocked until selected Probe and Assessment
   prerequisites are refreshed against current Kit refs and recorded.
4. Run a disposable, mutation-scoped DP1 Probe execution package before any
   production runtime mutation.
5. Run the Kit documentation, registry and release-relevant gates selected by
   each import slice.
