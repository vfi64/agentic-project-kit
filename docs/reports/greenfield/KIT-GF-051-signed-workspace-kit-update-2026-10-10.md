---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-051: signed workspace Kit update

Date: 2026-10-10
Kit state: CLOSED in this patch; released-package Cockpit retest pending.
Source: vfi64/agp-Cockpit origin/main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, family KIT-GF-051.
The source ledger is unchanged; only Cockpit sets VERIFIED_FIXED.

## Finding and repair

External Kit adoption required manual environment installation, two CI pin edits,
entrypoint synchronization and checks. The new `kit update` route composes these
steps through a thin CLI and focused discovery, configuration, artifact, pin,
runtime and orchestration modules. A dry run resolves exact binary release
artifacts from one explicit index, verifies hashes and previews the target CLI
in a temporary environment. It does not alter the target installation or tracked
files. Signed execution binds branch/head, environment identity and inventory,
artifact hashes, index, file hashes, target manifest and ordered operations.

Execution installs through the workspace-owned interpreter, verifies the new
version, raises only the two pins in a matching managed CI pair, runs the new
runtime's entrypoint synchronizer, then requires check and doctor PASS. Customized
CI is preserved byte-for-byte apart from the pin; full template replacement still
obeys GF-042. Wrong/stale signatures, ambiguous CI, unavailable/yanked targets,
downgrades and unknown provenance stop. Network effects are index/artifact reads;
there is no remote repository write or publication. Main/master require a work
branch first, and normal work finish handles the resulting patch.

## Regression and external retest

`tests/test_kit_update.py` covers signatures, immutable artifacts, CI provenance,
partial failures, concurrent edits, target-runtime gates, idempotent fresh plans,
CLI JSON and manifest contracts. Discovery is independently covered by
`tests/test_kit_installation.py`. Together 85 focused tests passed.

Eight real installed-wheel checks passed in a separate initialized manifest
workspace containing generated command references, no Kit tests and no Kit doc
registry. Its own environment started with actual PyPI Kit 1.0.18, outside global
PATH. A loopback fixture index supplied the freshly built candidate wheel and
dependencies. Signed adoption produced installed version = both CI pins = 1.0.22
and ACK `a3c2547eb39e`, preserving a read-only copy of Cockpit's customized CI.
Check and doctor passed through the adopted interpreter. Wrong-signature refusal,
same-version replay and unavailable 99.0.0 refusal passed. PYTHONPATH pointed at
the source checkout while isolated Python ensured installed-wheel provenance.
The candidate uses the checkout's existing version for fixture packaging only;
no public wheel, tag, release or production workspace was changed.

Cockpit must repeat the ledger regression with a released Kit containing this
route, then finish the generated changes through its own work lifecycle. Raw
local fixture/build/state evidence is retained under ignored tmp paths; no broad
logs or runtime state are versioned.

## Risks and design

Pip installation and file edits cannot share an atomic transaction. A failure
preserves completed-step receipts and actual partial state, remains BLOCKED and
requires a fresh observed plan. Concurrent branch/file edits detected after
installation are preserved. Same-version installation is skipped only with the
matching recorded Kit wheel hash and resolved dependency versions. All package
installation trusts the explicitly selected release index and its code; this
route verifies artifact identity, not publisher semantics. Dry runs create
temporary wheel/preview artifacts. Source-only and editable installations remain
outside this conservative update path. The state/plan model is sufficient;
an additional DCO renderer framework would add complexity without useful checks.

The architecture contract remains valid; command metadata, documentation coverage
and test gates document and enforce the new public maintenance surface.

## Final local gates

3464 full-suite tests passed; Ruff, check-docs and doctor passed. Doctor retains
76 existing report-only lifecycle findings. The initial full run encountered old
ACK projections before regeneration; all 19 related authority/readiness tests
and the final complete run passed after synchronization. The bound DPA ACK was
refreshed without changing its authorization scope. Manifest and generated
entrypoints/site use `COMMAND_MANIFEST_ACK a3c2547eb39e`. Pip configuration files
are disabled during resolution and installation, so unsigned system/venv settings
cannot add an extra index or alter installation scope.

The final pin-parser review added regressions refusing pins that appear only in
inline comments, shell expressions or another argument. The correction stayed
on the same PR before merge; the full suite and all eight external checks passed
again with the corrected package.
