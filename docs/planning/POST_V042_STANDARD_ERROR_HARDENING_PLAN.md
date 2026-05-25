# Post-v0.4.2 Standard-Error Hardening Plan

Status-date: 2026-05-25
Status: active
Decision status: accepted
Project: agentic-project-kit

## Purpose

This plan records the near-term sequence after v0.4.2 release verification.

## Sequence

1. Complete the v0.4.2 DOI metadata closeout.
2. Fix protected control-file preservation before further registry hardening.
3. Start Rule Registry Phase A with a minimal typed schema slice.
4. Treat projection drift and handoff staleness as one closeout synchronization problem.
5. Add one high-value assertion beyond required-term checks.
6. Defer GUI safety-class cleanup until the governance hardening sequence is green.

## Acceptance

The first implementation PR after the v0.4.2 DOI closeout must target protected control-file preservation unless the DOI closeout discovers a higher-severity release-state inconsistency.
