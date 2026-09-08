# Post-v1.0.10 Greenfield Remaining Findings Closeout

Status: implemented local retest pass  
Date: 2026-09-08  
Kit baseline: `origin/main` at `c18c74cd` before this slice  
Current branch: `codex/greenfield-remaining-fixes-1-0-10`  
Machine-readable companion:
`docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json`

## Scope

This slice adjudicates the current AGP Cockpit Greenfield finding ledger against
the Kit mainline after the post-v1.0.9 workflow fixes and closes the smallest
still-confirmed deterministic defect: `KIT-GF-018`.

The imported ledger at
`/Users/hof/Dropbox/Privat/GitHub/agp-Cockpit/docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`
is treated as external evidence, not as implementation authority. Existing Kit
B1 items remain authoritative when they already cover a finding.

## Finding Status

| Finding | Current Kit status | Action in this slice |
|---|---|---|
| `KIT-GF-001` | External workspace init has been retested successfully in a neutral external repository; remaining provenance concerns are tracked under `KIT-GF-007`. | No duplicate patch. |
| `KIT-GF-002` | Fixed by external-aware planning-doc slice gates. | No action. |
| `KIT-GF-003` | Partially addressed; first-cycle start without a previous successor package has improved, but complete post-merge successor evidence remains a retest item. | No action. |
| `KIT-GF-004` | Fixed by external-aware governance checks. | No action. |
| `KIT-GF-005` | External first-cycle work start has been retested as PASS; broader first-cycle closeout remains tied to `KIT-GF-009` and `KIT-GF-011`. | No action. |
| `KIT-GF-006` | Fixed; empty default transfer inbox is reported as `NO_COMMAND`. | No action. |
| `KIT-GF-007` | Open; requires a generated-vs-manual provenance model across DPA/adopt surfaces. | Deferred. |
| `KIT-GF-008` | Fixed by external workspace CI template and standard gate routing. | No action. |
| `KIT-GF-009` | Partially mitigated; first-cycle finish/closeout execution still needs released/external end-to-end evidence. | Deferred. |
| `KIT-GF-010` | Fixed in code and released-package retested for rule acknowledgement routing; keep future package retests explicit. | No action. |
| `KIT-GF-011` | Improved but not closed; refresh-loop reduction is broader than this cleanup repair. | Deferred. |
| `KIT-GF-012` | Fixed; dry-run now surfaces the remote preflight required by execute. | No action. |
| `KIT-GF-013` | Fixed by the patch-failure recurrence guard in v1.0.9. | No action. |
| `KIT-GF-014` | Open; requires stale or ambiguous continuation-authority detection for external workspaces. | Deferred. |
| `KIT-GF-015` | Open; requires canonical document fact propagation across registered documents. | Deferred. |
| `KIT-GF-016` | Open planning/UX item; contract-first guided execution is a product seam, not a safety hotfix. | Deferred. |
| `KIT-GF-017` | Likely addressed by the recent external PR closeout and context-carrier fixes, but still needs a fresh external retest before closure is claimed. | Verification deferred. |
| `KIT-GF-018` | Confirmed small deterministic defect. | Fixed in this slice. |

## Repair

`transfer delete-merged-work-branch` already verified that the branch belongs to
a merged PR before attempting cleanup. The remaining defect was postcondition
classification: a remote or local deletion command could fail because the branch
reference was already absent, even though the intended cleanup state had already
been achieved.

The repair keeps the existing command and safety checks:

- if local branch deletion fails, the command verifies whether the local ref is
  already absent before reporting a blocker;
- if remote branch deletion fails, the command verifies whether the remote head
  is already absent before reporting a blocker;
- successful idempotent no-ops are recorded in `idempotent_noops`;
- non-absence failures still remain blockers.

This closes only the cleanup idempotence defect. It does not claim to close the
broader successor-refresh loop or the remaining first-cycle external closeout
matrix.

## Release Assessment

A v1.0.10 safety/workflow release is justified after this slice if the standard
gates pass. The release would include:

- post-v1.0.9 external transfer target-branch and closeout hardening;
- remote-base admin refresh repair;
- idempotent merged work-branch cleanup for already-absent local or remote refs.

It should not be described as closing all Greenfield findings. The remaining
open families are larger follow-up work.

## Validation

Focused validation before the report was written:

- `tests/test_transfer_repo_actions.py` targeted delete-merged-work-branch tests:
  6 passed
- Ruff on touched source and tests: PASS
- Diff whitespace check: PASS

Full gate evidence is recorded by the release/slice closeout commands after this
report is committed.

## Remaining Work

Pause Comm-SCI Brownfield execution after the current closeout because the
maintainer identified it as compute- and token-intensive. The next lower-risk
Kit planning direction is the token/context-budget reduction investigation.

Keep these Greenfield families open:

- `KIT-GF-007`: generated-vs-manual DPA/adopt provenance;
- `KIT-GF-009`: first-cycle finish and closeout external execution evidence;
- `KIT-GF-011`: mixed handoff/status/report refresh-loop reduction;
- `KIT-GF-014`: stale or ambiguous continuation authority;
- `KIT-GF-015`: canonical document fact propagation;
- `KIT-GF-016`: contract-first guided execution UX;
- `KIT-GF-017`: released/external verification of recent context-carrier fixes.
