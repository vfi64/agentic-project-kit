# DPA-ADR-020 — Promotion Commits and Normative Equivalence Verification

Status: ACCEPTED
Date: 2026-07-16

## Context

The DPA-400 primary review found that the DPA-300 promotion commit changed and restructured the normative specification body after the complete review, adjudication and independent-verification chain had certified an earlier text. Sampling found no semantic regression, but the promoted text itself was not covered by the recorded verification scope.

This repeats the documented authorship-context blind spot: the session applying a change can verify its intended transformation while missing that the certified artifact changed outside the verification set.

## Decision

### 1. Promotion commits are status-only

A commit whose purpose is to promote a normative specification from `draft` to `review-ready`, `stable` or `adopted` MUST change only status and directly associated planning/index surfaces.

A promotion commit MUST NOT:

- restructure or rewrite the normative body;
- alter requirement meaning;
- add, remove or relax normative keywords;
- change traceability ownership or semantic diagrams;
- introduce new decisions.

Any such change requires a new governed amendment commit before promotion and must be included in the applicable review or verification scope.

### 2. Post-verification normative changes require equivalence verification

If a normative body changes after the last qualifying review or verification, promotion is blocked until one of the following occurs:

1. the changed text receives a new qualifying review and adjudication; or
2. an independent exact-ref, diff-scoped equivalence verification demonstrates that every load-bearing rule survives unchanged and identifies every genuine semantic difference for explicit Maintainer disposition.

The verifier MUST NOT be the context that authored the restructuring or rewrite.

### 3. DPA-300 lineage debt

The DPA-300 restructuring in promotion commit `e3f8b85c5eb76b8c6cae76dde317fd33f236ce88` requires a bounded independent equivalence verification against the last independently certified DPA-300 text.

Until that verification passes:

- DPA-300 remains usable as a review-ready dependency for continued draft work because the DPA-400 primary review found no sampled semantic regression;
- DPA-500 MUST NOT be frozen for primary review against the uncertified restructure;
- DPA-300 MUST NOT be promoted to `stable`.

## Alternatives considered

1. Treat all promotion-time rewrites as editorial by author declaration — rejected because authorship intent is not artifact evidence.
2. Revert DPA-300 immediately — rejected as disproportionate before an equivalence check.
3. Require a complete new full review for every mechanical restructure — rejected when a bounded independent diff-scoped equivalence verification is sufficient.
4. Ignore the lineage defect because another review sampled the text — rejected because incidental sampling is not a governed certification of the changed artifact.

## Rationale

Document status must describe the reviewed artifact, not merely the intended meaning. Status-only promotion commits preserve that relation. Independent equivalence verification is the cheapest safe recovery when a post-verification restructure has already occurred.

## Consequences

- The DPA-300 restructure receives an independent exact-ref equivalence review before DPA-500 review-baseline freeze.
- Review and promotion prompts MUST identify the exact normative ref being certified.
- STATUS and ROADMAP MUST track unresolved lineage-verification debt.
- DPA-800 and future kit governance MAY operationalize the same rule for high-risk mutation slices without requiring a second full review for low-risk mechanical changes.

## Validation status

NORMATIVE lab review and promotion governance decision. This decision does not itself certify DPA-300 equivalence.

## Affected artifacts and phases

- DPA-300 review lineage;
- DPA-400 adjudication;
- DPA-500 review preparation;
- later specification promotion;
- DPA-800 implementation and gate governance.