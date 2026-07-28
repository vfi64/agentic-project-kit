# DPA-900 Traceability

Status: draft

Status-date: 2026-07-27

This matrix traces DPA-900 requirements without becoming a competing normative
source. Invariant anchors are derived from the canonical register in DPA-000
§7.

| ID | Requirement | Invariants / decisions | Tests | Later work | Evidence / rollback |
|---|---|---|---|---|---|
| RE-001 | Future changes are classified before review-path selection. | DPA-INV-010, DPA-INV-017; ADR-009, ADR-012 | missing-class and mixed-class cases | review workflow | classification record; escalate uncertain change |
| RE-002 | Risk levels R0 through R5 determine minimum review depth. | DPA-INV-010, DPA-INV-012, DPA-INV-017; ADR-012 | unknown-risk and lower-path negatives | review workflow; import planning | risk record; fall back to higher risk |
| RE-003 | Fast mechanical path requires accepted generator or deterministic command evidence. | DPA-INV-010, DPA-INV-012; ADR-011 | unreproducible generated-output negative | generated-output handling | source/generator record; rerun or escalate |
| RE-004 | Editorial path cannot change normative keywords, statuses, authority or evidence scope. | DPA-INV-010, DPA-INV-017; ADR-009, ADR-020 | normative-keyword and status-change negatives | review workflow | diff record; escalate to amendment |
| RE-005 | Synchronization path updates only derived artifacts from an accepted source. | DPA-INV-010, DPA-INV-017; ADR-020 | missing-source and semantic-addition negatives | status, roadmap, traceability, handoff | source exact ref; revert unsupported sync |
| RE-006 | Bounded amendments require source findings, Maintainer adjudication and post-adjudication verification when normative review-ready bodies change. | DPA-INV-010, DPA-INV-017; ADR-012, ADR-020 | missing-adjudication and self-verification negatives | future DPA amendments | correction record; block promotion |
| RE-007 | Full governed review path remains mandatory for high-impact semantic changes. | DPA-INV-004, DPA-INV-010, DPA-INV-011, DPA-INV-012; ADR-012 | high-risk-fast-path negative | DPA reviews; DP2-DP5 | full review package; stop before mutation |
| RE-008 | Adoption or strict-enforcement path requires exact-ref Probe, Assessment, rollback and Maintainer authorization. | DPA-INV-004, DPA-INV-005, DPA-INV-010, DPA-INV-017; ADR-015 | stable-without-probe and strict-without-rollback negatives | DP5; controlled import | stage evidence; de-escalate or block |
| RE-009 | Equivalence verification compares certified source and candidate refs by load-bearing semantics. | DPA-INV-010, DPA-INV-017; ADR-020 | missing-requirement and silent-weakening cases | restructure recovery | equivalence report; full review fallback |
| RE-010 | Independent-context verification separates authorship context from verification context for high-risk work. | DPA-INV-010, DPA-INV-017; ADR-012, ADR-020; ADR-018 historical input | independence-blocked and anchored-prompt cases | review prompts; post-adjudication verification | verifier disclosure; reroute reviewer |
| RE-011 | Mechanical consistency checks reduce recurring drift without overclaiming semantic proof. | DPA-INV-010, DPA-INV-012, DPA-INV-017 | false-semantic-proof and check-failure cases | Lab and Kit gates | check output; fix drift or escalate |
| RE-012 | Generated and command-updated Kit outputs change through source, generator or command contract. | DPA-INV-010, DPA-INV-012, DPA-INV-017; ADR-011 | manual-output-patch and missing-generator cases | DP4; controlled import; Kit handoff | command/source evidence; repair via source |
| RE-013 | Review-economy records explain skipped controls and selected path. | DPA-INV-010, DPA-INV-017; ADR-009, ADR-012 | missing-record and omitted-control cases | governance reports | path record; rerun full path |
| RE-014 | Metrics measure cost and defects but cannot override required evidence. | DPA-INV-010, DPA-INV-012 | metric-as-authority negative | project governance | metric report; disregard for gate decision |
| RE-015 | Final DPA closeout requires synchronized specs, traceability, Probe manuals, import planning and no hidden blockers. | DPA-INV-010, DPA-INV-011, DPA-INV-012, DPA-INV-017; ADR-001, ADR-002 | closeout-with-missing-manuals and conformance-overclaim cases | final pre-import package | closeout audit; leave DPA open |
| RE-016 | Review economy remains governance logic and must not create a parallel Lab or Kit runtime authority. | DPA-INV-010, DPA-INV-011, DPA-INV-012; ADR-001, ADR-002 | no-parallel-review-queue and evidence-service-as-authority negatives | review workflow; controlled import | authority-boundary record; remove or reject parallel authority |

## Probe and implementation obligations

- DPA-900 does not create a new Probe family.
- DPA-900 contributes review-path, class-to-risk, blind-first, equivalence,
  generated-output, no-parallel-authority and closeout cases to future
  governance and import checks.
- Any production implementation of DPA-900 review paths remains
  `NEEDS_MAIN_REPO_VALIDATION` until exact main-repository refs, tests and
  Maintainer adjudication exist.
- Reduced-cost review records must be reversible by reverting the certified
  change or escalating to the full governed review path.

## Review boundary

This traceability file is non-normative. Any contradiction is resolved in favor
of DPA-000 through DPA-900 and accepted decisions.
