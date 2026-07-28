# PROBE-004 Migration And Rollback Readiness

Status: partial-blocked-for-dp2

Status-date: 2026-07-28

Document class: evidence/log

## Scope

This package records a current Kit-side PROBE-004 migration and rollback
readiness preflight for the Document Projection Architecture.

Validation ref:
`3dd2a616aaa47995e333059e80912ae0bea55656`

Command manifest acknowledgement:
`COMMAND_MANIFEST_ACK 6238b5e0fcaa`

This is not migration execution, not rollback execution, not a full PROBE-004
PASS claim, not DP2 authorization, not production mutation and not Kit
conformance evidence.

## Result

`results.json` records `PARTIAL_BLOCKED_FOR_DP2` with zero structural findings.
The current candidate source, test and control surfaces are present.

The remaining blockers are expected at this stage:

- PROBE-004 is still recorded as `PARTIAL_BLOCKED_FOR_DP2` in the Assessment
  readiness record.
- `probe_004_full_evidence` remains `BLOCKED` for DP2 entry.
- migration-form selection and lower-risk rejection fixtures have not executed.
- rollback-package identity and recoverability fixtures have not executed.
- renderer semantic-version rollback and unavailable-renderer fail-closed
  fixtures have not executed.
- generated or command-updated output rollback fixtures still require
  source-command execution evidence.
- Maintainer-scoped target selection and rollback instructions are not recorded.

## Generated-output boundary

The preflight inspects current successor-handoff package JSON outputs as
source surfaces only. It does not patch those command-owned outputs manually and
does not treat their current bytes as durable migration target bytes.

## Files

- `results.json` - machine-readable PROBE-004 readiness preflight result.
