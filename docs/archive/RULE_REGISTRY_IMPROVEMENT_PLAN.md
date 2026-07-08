# Rule Registry Improvement Plan

Document class: historical archive
Status-date: 2026-07-08
Archived-from: docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md
Superseded-by: docs/planning/PROJECT_DIRECTION.yaml

Status: active
Decision status: accepted
Review policy: Review after each documentation-registry foundation milestone and before introducing external policy engines.
Project: agentic-project-kit

## Purpose

This plan records the remaining improvement backlog for the governed rule-registry system after the PR764 completion-reporting closeout and PR765 handoff refresh.

The current rule registry is good enough to resume documentation-management work. This plan prevents the remaining weaknesses from being lost, while also preventing a broad second registry rebuild from blocking the next documentation-registry slices.

## Current Baseline

The rule-registry baseline is considered complete for the current scope:

- active mechanisms are represented in `.agentic/rule_mechanism_inventory.yaml`,
- legacy rule migration is represented in `.agentic/rule_migrations.yaml`,
- test coverage classification is represented in `.agentic/rule_test_coverage.yaml`,
- direct-test follow-up state is represented in `.agentic/rule_direct_test_plan.yaml`,
- validation runs through `agentic-kit rule-registry check`, workflow-guard, and patch-preflight,
- completion is visible through `agentic-kit rule-registry report` and `agentic-kit rule-registry report --json`,
- the JSON report exposes `summary.direct_coverage_complete`,
- the human report exposes explicit completion status.

This means the registry is an active governance subsystem, not a chat-only memory aid.

## Remaining Weaknesses

The following weaknesses are intentionally retained as planning items rather than treated as blockers:

1. Schema hardness: YAML plus custom validation works, but a typed schema would make malformed registry entries easier to reject and easier to document.
2. Projection drift: status, handoff, handoff-state, planning, and registry files still repeat overlapping state. This is safer than chat memory but still creates maintenance cost.
3. Required-term roughness: term presence proves that a surface contains an anchor, not that the implementation fully satisfies the rule intent.
4. Query ergonomics: the report is now explicit, but the system still lacks a richer query layer for rule domains, owners, enforcement paths, conflict domains, GUI relevance, and evidence relevance.
5. Human documentation drift: Markdown still contains curated summaries that can diverge from registry state unless generated or checked more strongly.
6. Semantic boundary: deterministic checks can validate structure and anchors; they cannot prove the full meaning or adequacy of a governance rule.
7. Ecosystem boundary: external policy engines may add value, but adopting them too early would add complexity before the domain model is stable.

## Improvement Backlog

### Phase A: Typed schema hardening

Goal: make the registry schema explicit and reusable.

Candidate changes:

- introduce Pydantic models or JSON Schema for rule mechanism entries, migration entries, coverage entries, and direct-test plan entries;
- expose schema validation through existing `agentic-kit rule-registry check` output;
- add tests that reject invalid IDs, invalid status values, missing required fields, duplicate owners, invalid conflict domains, invalid coverage states, and unknown enforcement phases;
- document the schema as generated or schema-backed reference material.

Estimated effort: small to medium, roughly 2-4 small PRs.

### Phase B: Generated projections

Goal: reduce manually duplicated current-state prose.

Candidate changes:

- generate a Markdown rule-registry overview from the machine-readable registry;
- generate a compact status snippet that reports rule-registry completion state, active mechanism count, and follow-up count;
- generate a handoff snippet that reports the registry state without duplicating the whole registry;
- make generated snippets visibly marked as generated or projection material;
- add tests that generated projections stay in sync with registry inputs.

Estimated effort: medium, roughly 4-8 small PRs.

### Phase C: Stronger assertions beyond required terms

Goal: replace selected term-presence checks with concrete behavioral or structural assertions.

Candidate changes:

- check that expected CLI commands are actually registered;
- check that validators expose expected functions or return expected finding types;
- check that tests referenced by a mechanism contain at least one expected assertion or fixture name;
- check that workflow-guard and patch-preflight actually call or import the registry validator;
- check that evidence-related mechanisms exercise failure and pass cases, not only happy paths;
- keep `required_terms` as lightweight anchors where deeper checks are not justified.

Estimated effort: medium to large, roughly 5-10 small PRs.

### Phase D: Query and impact analysis layer

Goal: make the registry useful as a planning and review instrument, not only as a gate.

Candidate changes:

- add queries for rules by category, owner, enforcement phase, priority, conflict domain, surface, and test coverage state;
- expose which mechanisms affect GUI readiness, release safety, evidence transport, documentation registry work, and remote mutation;
- emit a machine-readable dependency or impact report for proposed changes;
- add a review command that answers: which active rules could be affected by this file set?

Estimated effort: medium, roughly 3-6 small PRs.

### Phase E: Documentation integration

Goal: make human documentation a projection of registry state where possible.

Candidate changes:

- register the rule-registry improvement plan and generated overview in `docs/DOCUMENTATION_REGISTRY.yaml`;
- link the registry plan from the workflow-reduction planning document;
- add documentation-registry classes or notes for generated rule projections;
- keep `docs/STATUS.md` compact and point to generated projections instead of duplicating rule detail;
- add drift checks that flag stale rule-registry prose in active planning docs.

Estimated effort: medium, roughly 4-7 small PRs.

### Phase F: Optional external policy tooling

Goal: evaluate external tools only after the internal domain model is stable.

Candidate options:

- JSON Schema for portable schema validation;
- OPA/Rego or Conftest for declarative policy checks over structured registry data;
- Semgrep for code-pattern checks where Python source structure matters more than YAML registry data.

Decision rule:

External tools should be adopted only if they reduce custom code or catch classes of drift that the current Python validator cannot catch cleanly. They must not become an additional manual ritual with no deterministic benefit.

Estimated effort: larger, roughly 1-3 weeks if introduced broadly. This phase is explicitly optional.

## Sequencing

Do not start all phases at once.

Preferred sequence:

1. Resume documentation-management work with small additive registry or projection slices.
2. Add typed schema hardening when a registry change next touches the validator.
3. Add generated projections before duplicating more status or handoff prose.
4. Replace high-value `required_terms` checks with stronger assertions only where the rule is repeatedly affected by drift.
5. Add query and impact-analysis commands when the GUI or documentation-management workflow needs them.
6. Evaluate external policy tooling only after the internal registry has stable schemas and projections.

## Non-Goals

- no immediate second broad rule-registry rebuild,
- no release, tag, or DOI mutation,
- no GUI expansion as part of this plan,
- no replacement of the current Python validator by an external policy engine before the schema is stable,
- no claim that deterministic validation proves full semantic governance quality.

## Acceptance Direction

The near-term target is not perfection. The near-term target is to preserve the completed rule-registry baseline while reducing the remaining weaknesses in small, test-backed slices.

A future closeout may declare this plan complete when:

- the schema is typed or schema-backed,
- core rule state has generated human projections,
- high-risk rules have behavioral assertions beyond term presence,
- reports can answer rule-impact questions needed by documentation management and GUI readiness,
- status and handoff docs no longer duplicate detailed rule-registry state manually.
