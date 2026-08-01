# Document Projection Architecture

The files in this directory form the normative DPA specification series.

Normative keywords `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT` and `MAY` are used in their ordinary RFC sense.

No repository-specific statement is `VERIFIED` until validated against an exact main-repository validation ref.

## Canonical file map

| Number | Canonical file | Current status |
|---|---|---|
| DPA-000 | `DPA-000-VISION.md` | stable |
| DPA-100 | `DPA-100-FOUNDATIONS.md` | stable |
| DPA-200 | `DPA-200-DOCUMENT-MODEL.md` | stable |
| DPA-300 | `DPA-300-REGISTRY-LIFECYCLE-INTEGRATION.md` | stable |
| DPA-400 | `DPA-400-RENDERER-CONTRACT.md` | stable |
| DPA-500 | `DPA-500-FRESHNESS-AND-GATES.md` | stable |
| DPA-600 | `DPA-600-CONCURRENCY.md` | stable |
| DPA-700 | `DPA-700-MIGRATION.md` | stable |
| DPA-800 | `DPA-800-DP1-DP5.md` | stable |
| DPA-900 | `DPA-900-FUTURE.md` | stable |

A DPA number MUST have exactly one canonical normative file. Amendments and historical pointers MUST identify their owner and MUST NOT remain competing normative homes.

Current Stable Promotion overlay: DPA-200 through DPA-900 are stable for the
accepted Kit-side DP1-DP5 implementation and evidence scope recorded in
`docs/architecture/evidence/dpa/assessment/DPA_STABLE_PROMOTION_RECORD_20260801.json`.
The canonical status values in the table remain aligned to the document
headers. Future target expansion still requires fresh exact-ref evidence before
it can inherit this stable scope.
