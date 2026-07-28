# DPA-ADR-014 — Define the consumer trust-state model

Status: ACCEPTED
Status-date: 2026-07-15
Review origin: Claude DPA-200 R-M03/R-M04; ChatGPT DPA-200 technical verification

## Context

The initial DPA-200 draft, matrix and trust diagram used inconsistent state sets and drift semantics. The token `planned` also collided with the document-status namespace established by DPA-ADR-009.

## Decision

DPA-200 owns a closed **consumer trust-state** dimension with these tokens:

- `computed`: renderer output exists in memory and has not passed lifecycle validation;
- `plan-captured`: a mutation plan exists and no accepted repository state is claimed;
- `written-unverified`: bytes were written by the governed lifecycle but required post-write checks are incomplete;
- `accepted`: required lifecycle validation, reproducibility checks and governing gates completed for the stated acceptance scope;
- `abandoned`: a non-accepted refresh attempt ended through failure, cancellation or supersession and its bytes MUST NOT be presented as accepted.

Trust state classifies target bytes for one governed refresh attempt. Refresh execution state and accepted-byte state MUST NOT be conflated.

Detected drift:

1. produces findings under DPA-500;
2. blocks new integration where required;
3. starts a new refresh attempt at `computed`;
4. does not silently or retroactively mutate the recorded trust state of previously accepted bytes;
5. may explicitly invalidate an acceptance scope only through a later accepted DPA-500 gate contract.

Manual and historical bytes do not acquire DPA consumer trust states merely by sharing a document. DPA-500 must define document-level acceptance for mixed documents from the projected-region trust state plus the declared authority and validation obligations of non-projected regions.

## Alternatives considered

- Keep `planned` as a trust token.
- Treat `rejected` as an undocumented pseudo-state.
- Transition accepted bytes directly back to computed on drift.
- Move the full trust model into DPA-300.

## Rationale

The decision closes the vocabulary, removes token collision and separates existing accepted bytes from a new refresh attempt. The model remains architectural while lifecycle transitions and gate consequences stay delegated.

## Consequences

DPA-200, matrix, diagram and traceability must use the five tokens exactly. DPA-300 owns permitted transitions and bypass prevention. DPA-500 owns acceptance criteria, explicit invalidation and drift findings. DPA-600 owns stale-plan effects on active attempts.

## Validation status

NORMATIVE architecture decision. No main-repository evidence is required for the model decision.

## Affected specifications

DPA-200, DPA-300, DPA-500, DPA-600.

## Affected DP slices

DP1–DP5.