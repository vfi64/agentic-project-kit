# DPA-ADR-015 — Permit early read-only DP1 discovery

Status: ACCEPTED

Status-date: 2026-07-15

## Context

The original phase model placed all DP1 activity in Phase E after lab adoption and after the complete DPA-000 through DPA-900 specification sequence. DPA-200 and the existing validation checklist already require discovery of the real main-repository reader, writer, authority, registry, lifecycle, finding, lock and workflow structure before a production document form or integration contract can be selected.

Writing DPA-300 solely from unvalidated assumptions would create avoidable correction loops. At the same time, moving all of DP1 before DPA-300 would mix factual discovery with contract conformance and implementation assessment.

## Decision

DP1 remains one formal slice. It has three internal stages:

1. **Discovery** — read-only inventory of observed main-repository facts at one exact validation ref.
2. **Probe** — bounded compatibility checks against a reviewable DPA contract, including parser, validator and lifecycle-extension probes.
3. **Assessment** — proof-of-architecture conclusion based on Discovery and Probe evidence.

Only the Discovery stage MAY execute before DPA-300 and before lab adoption.

Early Discovery MUST:

- be strictly read-only;
- use one exact recorded validation ref;
- create no production code, runtime files or `.agentic/` state;
- perform no migration, mutation, registry change or adoption;
- ask factual inventory questions only;
- make no contract-sufficiency or conformance judgment;
- replace assumptions with evidence where the observed facts justify it;
- never create, modify, accept or reject architecture decisions by itself;
- store bounded static records under `evidence/repo-facts/` using the DPA-ADR-011 evidence discipline;
- preserve all repository-specific behavior claims as scoped to the inspected validation ref.

Probe and Assessment remain governed validation work after a reviewable DPA-300 contract exists. They MUST distinguish observed capability from architectural suitability.

## Alternatives considered

- Keep all DP1 work after DPA-900 and lab adoption.
- Move all DP1 work before DPA-300.
- Rename the three internal stages as separate DP slices.
- Allow discovery outputs to determine architecture automatically.

## Rationale

The decision obtains cheap, high-value factual evidence before registry and lifecycle contracts are written, while preserving the authority boundary between evidence and design. Keeping DP1 as one slice avoids changing the stable DP1–DP5 terminology. Separating Discovery from Probe prevents factual inventory from being misrepresented as conformance evidence.

## Consequences

- `LAB_EXECUTION_CONTRACT.md` and `ROADMAP.md` must permit the bounded early Discovery exception.
- A governed `integration/DP1_DISCOVERY_CONTRACT.md` must define exact factual questions, prohibited actions, evidence outputs and exit criteria.
- DPA-300 should be drafted from Discovery evidence where available.
- Compatibility Probes and the final Proof-of-Architecture Assessment remain later DP1 stages.
- Discovery may falsify or verify assumptions but cannot select a production migration form or amend normative architecture.

## Validation status

NORMATIVE governance and sequencing decision. No main-repository fact is asserted by this decision.

## Affected specifications and governance

- `LAB_EXECUTION_CONTRACT.md`
- `ROADMAP.md`
- `STATUS.md`
- future `DPA-800-DP1-DP5.md`
- `integration/DP1_DISCOVERY_CONTRACT.md`

## Affected DP slices

DP1 only; DP2–DP5 sequencing is unchanged.
