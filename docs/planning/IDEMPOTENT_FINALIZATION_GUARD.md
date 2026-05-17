# Idempotent finalization branch guard

Status: proposed
Decision status: Proposed

## Goal

Remove recurring non-semantic FAIL states from finalization and documentation slices.

## Recurring failure classes

- finalization branch already exists
- target documentation marker already exists
- no staged changes after an idempotent patch
- pull request creation attempted although there are no commits between base and head
- direct commit to main during documentation-only state updates
- fragile quote-heavy patch scripts failing before the intended patch is applied
- newly created documents missing required lifecycle headers

## Required behavior

- If the target marker already exists on main, report PASS and do not create a branch.
- If the branch already exists and contains the target commit, switch to it or main deterministically.
- If there is no diff after patching, treat this as PASS only when the target marker exists.
- Never create a PR when head and base have no commit difference.
- Never commit directly to main for a feature or finalization slice.
- New markdown documents must include Status and Decision status headers immediately.
- Patch generation must use shell-simple file writing or stable line-based scripts, not quote-fragile inline Python.

## Implementation note

The guard should become part of the deterministic ns slice runner so bounded workflows can advance on PASS, stop on real FAIL, and treat already-achieved target states as idempotent PASS.
