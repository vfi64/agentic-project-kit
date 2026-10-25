---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-086 — CI pin downgrade guard

## Observed
On 2026-10-22 a consumer workspace had CI pinned to Kit 1.1.5 while its local installed Kit remained at 1.1.4. Release preparation synchronized the older manifest and entrypoints, causing a downgrade in release artifacts.

## Defect and intended fix
A read-only numeric guard must compare the installed Kit version against exact workspace CI pins. Write-mode synchronization and release preparation must stop before modifications on downgrade. Preview synchronization stays nonblocking; kit update keeps its upgrade order.

## Evidence and verification
On 2026-10-25 the local feature gate reported 4068 passed and 26 failed. This does not constitute successful verification. Focused regressions, a greenfield machine retest and green PR CI are still required.

## Release target
Planned 1.1.6, category Fixed. No consumer-identifying material is included.

## KIT-GF-086 local gate follow-up (2026-10-25)

- `agentic-kit greenfield retest --id KIT-GF-086 --json`: PASS (step 125).
- `agentic-kit dev local-feature-gate`: FAIL (step 142): 26 failed, 4078 passed, 545 warnings; Ruff PASS. No named KIT-GF-086 tests failed.
- Gate remains blocking; no commit, push, PR, or release accepted as verified.
- Test-file comparison against HEAD: 13 unchanged, 0 altered among 13 failing test files. This does not establish the same tests fail on clean main.

### Local gate status (2026-10-25, step 146)
- `agentic-kit dev local-feature-gate`: **FAIL**; 4079 passed, 26 failed, 545 warnings.
- Ruff, project check and doctor: PASS. No named KIT-GF-086 regression failed.
- The 26 failed tests span existing test files unchanged from HEAD; this does **not** establish a passing baseline or waive the failures.
- Commit, push, PR, and DONE remain pending while the Kit gate is red.
