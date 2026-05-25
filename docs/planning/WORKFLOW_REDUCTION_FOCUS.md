# Workflow Reduction Focus

Status-date: 2026-05-25
Status: active
Decision status: accepted
Review policy: Review after the documentation-management foundation and before expanding GUI scope or Pattern Advisor scope.
Project: agentic-project-kit

## Purpose

This document records the near-term product focus for `agentic-project-kit` after the v0.4.1 documentation-registry baseline.

The next maturity step is not to add more advisory intelligence. The next maturity step is to reduce manual orchestration while preserving safety, evidence, and deterministic governance.

## Strategic Focus

The kit should increasingly answer these questions from repository state instead of chat memory:

- What is the current state?
- What is the next safe action?
- What is forbidden?
- What is stale?
- What evidence exists?
- Which documents are live state, governance, release history, generated artifacts, temporary artifacts, or evidence?

The goal is to move from a powerful expert tool toward a robust working instrument.

## Machine-Readable Source Direction

Operational truth should move into machine-readable sources. Human-readable Markdown should explain, summarize, or project that state instead of becoming the unverified source of state.

The governing rule is: every operational statement must be traceable to a machine-readable source of truth or to a machine-checkable anchor. This includes state, governance, next actions, evidence, release state, handoff state, registry entries, work orders, artifact retention, and automation behavior.

This does not mean that every document should be forced into YAML or JSON. README files, websites, handbooks, tutorials, architecture rationale, and explanatory notes may remain primarily human-readable. The stricter requirement applies to operative content that affects project state or executable behavior.

Target shape:

- machine-readable sources: `.agentic/handoff_state.yaml`, `docs/DOCUMENTATION_REGISTRY.yaml`, `.agentic/work_orders/*.yaml`, `.agentic/communication_artifacts.yaml`, release metadata, evidence manifests, gate reports, and generated state summaries;
- human-facing projections: `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, successor handoff prompts, README excerpts, handbook text, website text, GUI dashboards, and LLM-generated explanations.

LLM assistance should use the structured sources to translate project state into clear human prose on request. The LLM may explain and review; it should not be the only place where operational truth exists.

## Rule Registry Improvement Direction

The governed rule registry is the current proof point for this direction: rules have moved from chat-only memory into machine-readable inventory, migration, coverage, direct-test-plan, validation, and report artifacts.

Remaining rule-registry weaknesses must be reduced as incremental planning work, not as a second broad rebuild. The accepted backlog is `docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md`.

The improvement direction is:

1. keep the current rule-registry baseline usable while documentation-management work resumes;
2. harden the schema through typed or schema-backed validation;
3. generate human projections instead of duplicating registry state manually;
4. replace high-value `required_terms` checks with stronger behavioral or structural assertions;
5. add query and impact-analysis commands when documentation management or GUI readiness needs them;
6. evaluate external policy tooling only after the internal domain model is stable.

This keeps the rule registry professional without letting perfectionism block the next documentation-registry and projection slices.

## Priority Order

1. Finish the documentation-management foundation through small, additive, reversible, test-backed registry slices.
2. Use the registry to make status, handoff, evidence, artifacts, and retention/GC behavior visible and machine-checkable.
3. Build the GUI as a control surface over already-hardened read-only or bounded actions.
4. Defer Pattern Advisor expansion until the document and evidence substrate is stable.

## Work Model Direction

Future work should prefer small machine-readable work orders over long chat-orchestrated execution. A work order should state:

- slice name,
- goal,
- allowed files,
- required tests or checks,
- forbidden actions,
- closeout requirements.

Chat should describe intent. Repo-owned tools should execute typed operations. Markdown should increasingly be a curated projection of machine-readable state, not the primary state source.

## Handoff and Status Direction

Handoff prompts should be generated from state files, Git state, PR state, registry data, and gate evidence wherever possible. Manual free prose should be a curated supplement, not the source of truth.

`docs/STATUS.md` should remain a compact dashboard. Long history belongs in `CHANGELOG.md`, release records, evidence logs, or dedicated planning documents such as this file.

## Sequencing Decision

This focus must be recorded before completing the documentation-management phase so that the remaining registry slices and the later GUI are shaped by it.

Implementation should not interrupt the current documentation-management line. The practical sequence is:

1. record the focus now;
2. continue the handoff/status freshness guard and documentation-registry work;
3. complete the documentation-management foundation enough for artifact and evidence visibility;
4. then make the GUI expose this reduced-orchestration model;
5. only after that, resume Pattern Advisor expansion.

## Non-Goals For The Current Line

- no broad documentation migration,
- no release or tag work,
- no destructive GUI or remote-GUI actions,
- no expansion of Pattern Advisor before the registry and GUI foundations are ready,
- no new chat-only rules without a repository home and, where appropriate, deterministic checks.

## Review Rule

When a future slice adds complexity, reviewers should ask whether it reduces manual orchestration or only adds another surface area. Prefer the smallest change that makes state, evidence, next action, or drift more explicit.
