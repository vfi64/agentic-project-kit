# Document Projection Architecture

Status: architecture-index-staged

Status-date: 2026-07-28

Document class: architecture

## Scope

This directory is the controlled Kit-side staging point for the Document
Projection Architecture (DPA).

This first import slice is DPA-IMPORT-1: architecture index and registry staging
only. It introduces no runtime behavior change, no DP2 implementation, no full
Probe PASS claim, no DPA stable claim and no main-repository conformance claim.
The full Probe PASS claim boundary remains closed.

## Source and closeout evidence

The current source package is the DPA Lab PR carrying final pre-import closeout:

- repository: `vfi64/agentic-project-kit-dpa-lab`;
- PR: `https://github.com/vfi64/agentic-project-kit-dpa-lab/pull/15`;
- Lab head: `0cf944cc153e65a272c773286791f8891efdd1bc`;
- Kit freeze ref for closeout: `c788a8c530eb0984d088a86e8e7951145581abbe`;
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

DPA-IMPORT-1 uses only the architecture entry point and documentation registry
staging. Later imports may add selected specifications, decisions, traceability,
diagrams, Probe manuals or evidence only through separately reviewed slices.

## Generated-output and command-updated boundary

The generated or command-updated Kit outputs boundary keeps those files owned by
their source, generator or command contract. DPA import work must not manually
patch generated or command-updated Kit outputs to make target bytes match the
Lab.

This boundary includes successor-handoff package outputs and any future DPA
touchpoint that is classified as command-updated by the Kit.

## Next governed step

After this index and registry staging slice, the next DPA work remains governed
by the closeout restrictions:

1. Preserve the DPA Lab source ref and Kit import baseline in every import slice.
2. Keep WRT-CH-003 and the full WRT-CH-001 administrative refresh PR flow
   deferred from the first DP2 target.
3. Keep DP2 implementation blocked until selected Probe and Assessment
   prerequisites are recorded.
4. Run the Kit documentation, registry and release-relevant gates selected by
   each import slice.
