# Workflow Reduction Focus

Status-date: 2026-06-01
Status: active
Decision status: accepted
Review policy: Review after the documentation-management foundation, before adding deterministic transfer outbox implementation, and before expanding GUI scope or Pattern Advisor scope.
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

The governing rule is: every operational statement must be traceable to a machine-readable source of truth or to a machine-checkable anchor. This includes state, governance, next actions, evidence, release state, handoff state, registry entries, work orders, artifact retention, automation behavior, dialogue/transfer rules, and local-to-LLM transfer result context.

This does not mean that every document should be forced into YAML or JSON. README files, websites, handbooks, tutorials, architecture rationale, and explanatory notes may remain primarily human-readable. The stricter requirement applies to operative content that affects project state or executable behavior.

Target shape:

- machine-readable sources: `.agentic/handoff_state.yaml`, docs/DOCUMENTATION_REGISTRY.yaml`, `.agentic/work_orders/*.yaml`, `.agentic/communication_artifacts.yaml`, future `.agentic/dialogue_rules.yaml`, release metadata, evidence manifests, gate reports, generated state summaries, and generated transfer outbox context projections;
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
5. add query and impact-analysis commands when documentation management, transfer outbox context generation, or GUI readiness needs them;
6. evaluate external policy tooling only after the internal domain model is stable.

This keeps the rule registry professional without letting perfectionism block the next documentation-registry and projection slices.

## Priority Order

1. Finish the current B11 transfer-report contract semantics slice: preserve local report command semantics, make `publish-last-report` the only tracked handoff upload source, keep `show-last-report` local-only, and run the targeted transfer tests before PR creation.
2. Add the deterministic transfer outbox context projection to the rule-refresh handshake roadmap: every `.agentic/transfer/outbox/last_result.txt` write should embed a freshly extracted machine-readable header from canonical sources.
3. Introduce `.agentic/dialogue_rules.yaml` only as a tested rule-management slice, not as an unregistered parallel rule table.
4. Ensure every new documentation artifact is registered or classified through the documentation-management system, and every new durable rule is registered through the rule-management system with validation and preservation anchors where appropriate.
5. Finish the documentation-management foundation through small, additive, reversible, test-backed registry slices.
6. Use the registry to make status, handoff, evidence, artifacts, transfer outbox state, and retention/GC behavior visible and machine-checkable.
7. Build the GUI as a control surface over already-hardened read-only or bounded actions.
8. Defer Pattern Advisor expansion until the document, rule, evidence, and transfer substrates are stable.

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

Handoff prompts should be generated from state files, Git state, PR state, registry data, transfer outbox context, and gate evidence wherever possible. Manual free prose should be a curated supplement, not the source of truth.

`docs/STATUS.md` should remain a compact dashboard. Long history belongs in `CHANGELOG.md`, release records, evidence logs, or dedicated planning documents such as this file.

## B11 Transfer And Rule-Refresh Roadmap

The current transfer line has these remaining work items from the successor-handoff prompt and subsequent planning decisions:

1. Inspect and repair the existing branch `feature/b11-transfer-report-contract-semantics` without blindly overwriting dirty local work.
2. Fix `run-and-log` and `run-sequence-and-log` so their terminal short output reports local report writing only: `TRANSFER_REPORT_WRITTEN=done`, `LOCAL_REPORT=docs/reports/transfer_runs/...`, and `CHAT_REPLY=d | NEXT=Run transfer publish-last-report`.
3. Preserve the JSON report's underlying command semantics: `final_signal`, `returncode`, and the original `next_action` must not be replaced by the publish step.
4. Keep `publish-last-report` as the only source of tracked handoff upload semantics: `TRANSFER_UPLOAD=done`, `REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/...`, and `CHAT_REPLY=g`.
5. Keep `show-last-report` local-only; it must not imply a tracked handoff or remote upload.
6. Keep gitignored local reports under `docs/reports/transfer_runs/` and tracked handoff reports under `docs/reports/terminal/transfer_handoff_reports/`.
7. Move future local-to-LLM exchange toward exactly one canonical outbox file, `.agentic/transfer/outbox/last_result.txt`, generated as JSON with a deterministic context header extracted from canonical sources at each write.
8. Move future LLM-to-local exchange toward exactly one canonical inbox file, `.agentic/transfer/inbox/next_command.py.txt`, overwritten rather than accumulated.
9. Implement a local Python outbox-header builder that reads and hashes canonical sources, extracts dialogue/transfer priorities, embeds repo state, and fails closed on missing or contradictory sources.
10. Introduce `.agentic/dialogue_rules.yaml` only after schema, parser, tests, compiled-context integration, rule-mechanism inventory integration, and protected-change planning are ready.
11. Register or classify every new planning/governance/status/evidence document in the documentation-management system; do not create untracked documentation islands.
12. Register every new durable dialogue, transfer, or workflow rule in the rule-management system; do not rely on chat-only or document-only instructions when the rule affects executable behavior.
13. After green targeted tests, commit, push, create a PR only if there is a real diff against `origin/main`, wait for CI, merge only when clean, sync main, and run the post-merge handoff refresh status.
14. If post-merge status is `REFRESH_REQUIRED`, create and merge the administrative handoff-refresh PR through existing safe wrappers before continuing product work.

## Sequencing Decision

This focus must be recorded before completing the documentation-management phase so that the remaining registry slices and the later GUI are shaped by it.

Implementation should not interrupt the current transfer-report contract semantics line. The practical sequence is:

1. finish the B11 transfer-report contract semantics repair;
2. record the deterministic transfer outbox and dialogue-rule direction in planning;
3. add any new documentation artifacts to the documentation-management system and any new durable rules to the rule-management system;
4. continue the handoff/status freshness guard and documentation-registry work;
5. complete the documentation-management foundation enough for artifact and evidence visibility;
6. implement transfer outbox context generation and dialogue rules in small tested slices;
7. then make the GUI expose this reduced-orchestration model;
8. only after that, resume Pattern Advisor expansion.

## External Review Input Handling

External model reviews, advisory audits, or user-provided comparative assessments may be used as prioritization input, but they are not evidence by themselves.

When an external review identifies a repeated workflow risk, the kit should classify it into one of these outcomes:

- already covered by an executable guard or deterministic check;
- covered by a plan but still missing executable enforcement;
- useful only as advisory context;
- rejected because it conflicts with repository evidence.

The preferred response to useful external review input is not to copy ratings or qualitative praise into status documents. The preferred response is to connect the input to a concrete backlog item, guard candidate, GUI-safe action, test, or workflow-kernel capability.

For the current GUI and workflow-kernel line, the useful review signal is: prioritize enforcement and automation over additional chat-only instructions. The GUI should expose existing hardened command paths and make safe state, evidence, PR status, protected-change planning, transfer outbox state, and next-step decisions easier to execute without manual terminal orchestration.

The rule-refresh handshake is the stability core for this direction. `docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md` governs the staged work to make local-to-LLM and LLM-to-local rule freshness machine-checkable, fail-closed, and visible to the later GUI.

## Non-Goals For The Current Line

- no broad documentation migration,
- no release or tag work,
- no destructive GUI or remote-GUI actions,
- no expansion of Pattern Advisor before the registry and GUI foundations are ready,
- no new chat-only rules without a repository home and, where appropriate, deterministic checks,
- no new documentation artifacts that bypass documentation-management classification,
- no new durable rule sources that bypass rule-management registration and validation.

## Review Rule

When a future slice adds complexity, reviewers should ask whether it reduces manual orchestration or only adds another surface area. Prefer the smallest change that makes state, evidence, next action, or drift more explicit.
