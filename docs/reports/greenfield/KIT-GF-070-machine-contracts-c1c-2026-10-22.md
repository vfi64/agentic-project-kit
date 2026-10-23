---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-070 c1c: the six remaining local contracts

Date: 2026-10-22. Baseline: main 52f469f112a1ec4d5fceb8aec0a2657f185eacb4.
Plan: external-retest-machine-contracts. This slice is not a release.
The development catalog closes KIT-GF-070 from the completed local-contract
acceptance. fixed_in intentionally stays empty until an owner-approved release
carries this change; published 1.1.5 remains PARTIAL and consumer status stays OPEN.
The final recorded wheel includes this adjudication; its catalog hash and
implementation modules match the final source files.

## Contracts and boundaries

- KIT-GF-014: the catalog now calls transfer continue. Stale authority blocks with
  no action steps; aligned authority reaches the independent missing-order guard.
  No transfer work is executed in the control.
- KIT-GF-015: the catalog now calls docs-audit. An aligned managed canonical fact
  passes, drift blocks, and restoring it passes while review-only drift remains
  advisory. This does not claim to detect arbitrary semantic contradictions.
- KIT-GF-021: the running distribution and metadata are copied into a disposable
  interpreter outside .venv. No console script is created and Kit is absent from
  PATH; the isolated Kit installation probe still discovers the declared runtime.
- KIT-GF-032: real release ready runs against a local bare origin, release metadata,
  PR-number history and a generated committed successor package. No Kit checkout
  tests, documentation registry or site script are present. No calls are stubbed.
- KIT-GF-045: one-category derived notes block; the explicit three-category summary
  passes through the scan and preparation and makes the same local readiness pass.
- KIT-GF-067: the owned Kit outside .venv/PATH actually runs standard-error-scan and
  release ready. Independent local gates remain enforced.

The release fixtures disable publication, use only local Git remotes, and retain
missing GitHub metadata as a warning. Expected outbox/report carriers may be
untracked; tracked product state stays clean and no root tmp summary is written.
The owned-console fixture currently fails explicitly on Windows; no Windows
operational acceptance is claimed. The POSIX fixtures share dependency locations
with the caller but copy the Kit package and distribution metadata locally.

The runner's missing-contract negative test uses a synthetic catalog instead of
leaving a deliberately unproved family in the shipped catalog. Remote/release
retests remain NOT_RUN_LOCALLY, so an all-family run remains INCOMPLETE, never PASS.

## Validation

- Installed-wheel contracts and runner regression suite: 70 passed.
- Schema, export and boundary suite: 38 passed (45 deselected).
- Fresh development-wheel all-family run: PASS 44, FAIL 0, NO_MACHINE_CONTRACT 0,
  NOT_RUN_LOCALLY 40; overall INCOMPLETE, exit 3 as required. The empty consumer
  directory remains unchanged. Bounded wheel hash, catalog hash and six-family
  evidence are in KIT-GF-070-machine-contracts-c1c-2026-10-22.json.
- Ruff, check-docs and doctor: PASS. Doctor retains 76 pre-existing report-only
  lifecycle findings; they are not asserted resolved by this slice.
- Initial serial full run: 3980 passed, one safe-push audit failed on direct
  pushes in the new temporary fixture. The fixture now seeds its local bare
  origin with local fetches; no guard or exception allowlist was weakened.
  The static guard and three affected wheel contracts then passed (5 tests).
- Final serial full suite: 3981 passed, 542 warnings, 497.32 seconds.
  Final closeout continued on 2026-10-23; the recorded test run belongs to this slice.

## Cockpit reconciliation (read only)

Cockpit PR #376 already adopted released Kit 1.1.5, followed by refresh #377.
Committed evidence: docs/validation/evidence/kit-1.1.5-adoption.json in vfi64/agp-cockpit.
It records PASS 38, FAIL 0, NO_MACHINE_CONTRACT 6, NOT_RUN_LOCALLY 40, overall
INCOMPLETE (exit 3), and the ledger sync to Kit main 52f469f1. GF-081 and 082 are
FIXED in 1.1.5, not VERIFIED_FIXED; GF-070 remains OPEN. Other unrun families retain
FIXED rather than an invented verification.

At the initial 2026-10-22 inspection the Mac checkout was on release/0.3.2 with
local Kit 1.1.4; the committed adoption evidence came from Claude's cloud clone.
The read-only continuation check on 2026-10-23 now finds clean main at
`eb705614e1f64f2bf0ef1691b01fb4b38a94624b` (refresh PR381) and local Kit 1.1.5.
GF-014/015/067 remain FIXED; GF-021/032/045 retain their existing independent
VERIFIED_FIXED evidence; GF-070 remains OPEN and GF-081/082 remain FIXED in 1.1.5.
This Kit slice has changed no Cockpit file, runtime, Download or release state.

The new six contracts are development-wheel evidence until a later released Kit
is adopted and retested in the Cockpit. They must not be attributed to 1.1.5 or
used to set consumer VERIFIED_FIXED now. No new release is authorized by this slice.
