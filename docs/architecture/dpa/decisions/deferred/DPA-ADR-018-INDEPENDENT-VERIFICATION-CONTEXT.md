# DPA-ADR-018 — Independent Verification Context for High-Risk Changes

Status: DEFERRED PROPOSAL
Date: 2026-07-15
Deferred-to: DPA-800 / DPA-900 and later main-repository governance

## Context

Across the Phase A, DPA-200 and DPA-300 review cycles, implementation sessions reliably verified their intended invariant and decision changes but repeatedly missed cross-artifact residues and evidence-discipline defects. A fresh session from the same model family found those defects by reading the committed artifact without having authored the change.

The relevant separation is therefore not product identity. It is separation between authorship context and verification context.

The main repository already treats chat memory as non-authoritative and requires exact-ref evidence for governed work. Later DP2–DP5 implementation will introduce mutation-capable slices whose gate evidence must not merely restate the implementing session's intent.

## Deferred proposal

For a high-risk governed change, the session that authors or applies the mutation should not be the sole session that certifies its final gate evidence.

A qualifying independent verification context would:

- start from the exact immutable implementation or adjudication ref;
- read the applicable bootstrap, contracts and evidence without relying on the author's chat memory;
- disclose prior exposure and whether it authored the verified change;
- verify committed artifacts and outputs rather than the author's stated intent;
- report PASS or FAIL with exact findings and limitations;
- remain distinct in context from the authoring session, even when the same model family or product is used.

Potential default scope:

- normative contract or governance changes;
- changes to registries, lifecycle writers, locks, gates, evidence contracts or protected workflow behavior;
- mutation-capable DP2–DP5 slices;
- post-adjudication or post-remediation verification that authorizes promotion, merge or strict enforcement.

Low-risk editorial changes, spelling fixes and mechanically generated changes fully covered by deterministic tests require a bounded fast path rather than a full second bootstrap.

## Alternatives considered

1. Require a different named AI product — rejected because product identity does not guarantee contextual independence.
2. Allow the authoring session to self-certify every change — weakened by repeated lab evidence of an authorship blind spot for cross-artifact residues.
3. Require independent verification for every commit — rejected as disproportionate and likely to create process inflation.
4. Replace Maintainer adjudication or real-repository Probes with model independence — rejected because context separation does not protect against shared model blind spots or incorrect architecture assumptions.

## Rationale

Authors tend to verify the intended transformation. A fresh context must reconstruct the actual state and is more likely to detect residue, stale references and classification drift.

Context independence is complementary to, not a replacement for:

1. deterministic tests and gates;
2. independent artifact verification;
3. Maintainer adjudication;
4. exact-ref Probes against the real repository.

## Deferral consequence

This proposal is intentionally not adjudicated or expanded during DPA-400 work.

The observed learning is preserved in `specs/dpa/DPA-900-FUTURE.md` and `ROADMAP.md`. DPA-800 or DPA-900 may later define risk classes, evidence fields and workflow handoff after DPA-400/500 and Probe evidence are available.

No current normative DPA or kit-governance rule is created by this file.