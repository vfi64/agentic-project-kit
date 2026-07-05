<!--
Status: superseded
Authority: docs/planning/PROJECT_DIRECTION.yaml
Reason: Strategy, roadmap, and idea direction now live in the machine-readable project direction source.
Retention: Keep as historical context until a later protected reference check archives or removes it explicitly.
-->

# Document and Artifact Governance OS Plan

Status-date: 2026-05-23
Status: active planning document
Scope: planning only; no implementation, release, tag, or GUI behavior change

## Purpose

This plan defines a modular Document and Artifact Governance OS for `agentic-project-kit`: a GitHub-native documentation, evidence, temporary-artifact, and policy-control subsystem optimized for long-running collaboration between maintainers, large language models, Codex-like coding agents, Claude Code-like agents, and future GUI/cockpit surfaces.

The goal is not to add more Markdown. The goal is to turn repository knowledge into typed, machine-checkable, lifecycle-aware project infrastructure.

## Problem Statement

The project already has strong documentation guards, release checks, handoff contracts, terminal-safety rules, and CHANGELOG quality checks. The remaining risk is that these controls are distributed across individual documents, tests, CLI commands, and chat conventions.

Without a central registry and lifecycle model, recurring failures remain likely:

- active documentation can drift away from current state,
- historical terminal evidence can be confused with active rules,
- generated handoff files can be edited manually and drift from their generator,
- temporary logs can become the only evidence for a completed slice,
- local machine paths, account names, credentials, tokens, or other sensitive material can leak into active documentation,
- duplicate release, DOI, GUI-baseline, and next-step facts can become inconsistent,
- new documents can appear without ownership, class, update trigger, language policy, or validation profile,
- expensive full scans can slow the standard development loop,
- LLM-generated changes can satisfy structure while missing lifecycle, evidence, or source-of-truth obligations.

## Current-System Preservation Requirement

The existing documentation governance is intentionally imperfect but battle-tested. It currently works because many special-purpose guards were added after real project failures. The Document and Artifact Governance OS must preserve that quality before it attempts to consolidate it.

The migration rule is:

```text
Preserve current guards. Add registry. Prove parity. Then consolidate.
```

The new system must initially be additive. It may classify, explain, report, and add new findings, but it must not remove, weaken, or replace existing `check-docs`, `docs-audit`, CHANGELOG, STATUS, handoff, terminal-safety, final-summary, Ruff-scope, evidence, or release guards until parity is proven by tests.

Any migration of an existing special-purpose guard into the registry system requires:

- a list of the old guard's positive and negative regression cases,
- tests showing that the new registry-backed validator catches the same failures,
- explicit documentation of any behavior change,
- no loss of standard-gate speed,
- maintainer approval before the old guard is removed or softened.

## Release Before Rebuild Gate

Before the first implementation PR that changes the architecture of documentation governance, the project should publish a release of the current functioning baseline.

This pre-rebuild release is required because the current system is already useful and empirically hardened. Freezing it gives the project a stable rollback and comparison point before registry, artifact lifecycle, GC, language policy, and security-filter implementation work begins.

The release-before-rebuild rule is:

- complete a normal release from the current stable main before the first architectural documentation-governance implementation slice,
- verify the release through the existing release and post-release checks,
- record the release and DOI metadata using the existing release-closeout workflow,
- refresh `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `CHANGELOG.md`, `CITATION.cff`, `README.md`, and `docs/releases/VERIFIED_RELEASES.md` as required by the current process,
- only then start implementation of `.agentic/knowledge_registry.yaml` or the new registry validators.

Planning-only PRs may still update this plan before the release. Implementation PRs for the new governance OS must wait until the pre-rebuild release closeout is complete.

## Design Principles

1. Repository state is the source of truth; chat memory is not.
2. Every durable document or artifact has a declared class, lifecycle, owner, source-of-truth relationship, validation profile, and garbage-collection policy.
3. Active documentation and historical evidence are different resource classes and must not be checked with the same rules.
4. Deterministic guards enforce structure, references, lifecycle, known leak patterns, freshness, and consistency; semantic judgement remains an advisory layer unless it can be made deterministic.
5. Generated files must declare their generator and manual-edit policy.
6. Temporary artifacts must either be promoted to remote evidence, discarded, or garbage-collected by policy.
7. The system must be modular: registry, validators, security filters, source-of-truth graph, update triggers, artifact GC, and advisory review are separate but composable modules.
8. Fast checks must remain fast. Full audits may be deeper and more expensive, but they should not be required for every small edit.
9. LLM/Codex/Claude-Code integration must be explicit: prompts, handoffs, work orders, summaries, and remote evidence are first-class controlled artifacts.
10. Safety is fail-closed for leaks, missing evidence, contradictory current-state facts, unknown active documents, and unsafe GC decisions.
11. Existing guards remain authoritative during migration unless a new registry-backed guard has proven parity.
12. The first implementation stage is read-only or advisory where possible; hard enforcement expands only after stable tests and documented behavior.

## Resource Classes

The first registry version should support at least these document classes:

- `live_state`: concise current-state pointers such as `docs/STATUS.md`.
- `handoff`: successor-agent or successor-chat handoff documents.
- `governance_contract`: binding project rules and communication contracts.
- `architecture_contract`: architecture boundaries and source-of-truth design.
- `release_record`: release, DOI, and version history such as `CHANGELOG.md` and `docs/releases/VERIFIED_RELEASES.md`.
- `workflow_contract`: command, runner, evidence, CI, and work-order behavior.
- `planning`: active, completed, superseded, or archived plans.
- `agent_instruction`: active instructions for LLMs, Codex-like systems, Claude Code-like systems, and humans.
- `reference`: explanatory documentation that is not the canonical current-state source.
- `machine_config`: machine-readable project configuration and policy files.
- `generated_artifact`: files generated from tools, prompts, templates, or structured state.
- `evidence_log`: historical logs and committed evidence.
- `temporary_artifact`: local or short-lived files such as raw terminal captures.
- `archive`: preserved but inactive material.

The first registry version should also support artifact classes:

- `terminal_log`
- `command_report`
- `generated_handoff`
- `latest_pointer`
- `typed_work_order`
- `executed_work_order_record`
- `local_terminal_capture`
- `build_artifact`
- `cache`
- `manual_test_artifact`
- `quarantine_record`

## Lifecycle States

Each resource should declare one lifecycle state:

- `active`
- `generated`
- `historical_evidence`
- `temporary`
- `archived`
- `superseded`
- `quarantined`
- `approved_exception`

Lifecycle state determines which validators apply and whether the garbage collector may act.

## Core Registries

Start with one compact registry file to avoid over-engineering:

```yaml
schema_version: 1
resources: []
policies: {}
validators: {}
update_triggers: {}
gc: {}
security_filters: {}
```

Recommended initial path:

```text
.agentic/knowledge_registry.yaml
```

A rendered human overview can later be generated as:

```text
docs/registry/KNOWLEDGE_REGISTRY.md
```

Split the registry only when the single file becomes too large or when tests show that modular loading improves maintainability:

```text
.agentic/document_registry.yaml
.agentic/artifact_registry.yaml
.agentic/document_policies.yaml
.agentic/security_filters.yaml
.agentic/update_triggers.yaml
.agentic/gc_policies.yaml
```

## Registry Entry Shape

A typical active document entry should look like this:

```yaml
- id: status
  path: docs/STATUS.md
  kind: document
  class: live_state
  lifecycle: active
  owner: governance
  review_level: strict_gate
  language_policy: english_required
  secret_policy: forbidden
  local_path_policy: forbidden
  gc_policy: never_delete
  source_of_truth: false
  derived_from:
    - .agentic/handoff_state.yaml
    - CHANGELOG.md
    - docs/releases/VERIFIED_RELEASES.md
  update_triggers:
    - release_closeout
    - gui_baseline_change
    - governance_rule_change
    - handoff_state_refresh
  validators:
    - required_sections
    - max_words
    - no_unresolved_placeholders
    - freshness_against_handoff_state
    - no_historical_accumulation
  redundancy_policy: concise_pointer_only
```

A historical evidence entry should look different:

```yaml
- id: terminal_logs
  path_glob: docs/reports/terminal/*.log
  kind: artifact
  class: terminal_log
  lifecycle: historical_evidence
  owner: evidence
  review_level: historical_preserve
  language_policy: preserve_original
  secret_policy: forbidden
  local_path_policy: allowed_as_historical_evidence
  gc_policy: preserve_if_referenced
  validators:
    - final_result_marker_when_workflow_log
    - no_known_secret_patterns
```

A temporary artifact entry should be explicit:

```yaml
- id: local_terminal_captures
  path_glob: /tmp/agentic-project-kit-*.log
  kind: artifact
  class: local_terminal_capture
  lifecycle: temporary
  owner: evidence
  review_level: temporary_gc_managed
  language_policy: not_applicable
  secret_policy: forbidden
  local_path_policy: allowed_local_only
  gc_policy: ttl_delete_after_promotion_or_expiry
  promote_to: docs/reports/terminal/
```

## Security and Local-Leak Filters

Security filters are not optional. They are a core module of the system.

The first implementation should detect at least:

- maintainer-specific absolute paths such as `/Users/...`, `/home/...`, Windows user-profile paths, Dropbox/iCloud/OneDrive machine paths, mounted-volume paths, and absolute repository roots,
- local account names and machine-specific usernames in active documentation,
- private keys and certificate blocks,
- API tokens and access tokens for common providers,
- `.env`-style assignments containing sensitive names,
- plaintext credential patterns,
- basic-auth URLs,
- JWT-like strings when they appear outside explicit test fixtures,
- private IPs or hostnames when not explicitly allowed,
- personal email addresses when not covered by citation, author, or release metadata policy.

Policies must be class-dependent:

```yaml
security_filters:
  local_absolute_paths:
    active_documentation: block
    governance_contract: block
    agent_instruction: block
    evidence_log: warn
    temporary_artifact: warn
  known_secret_patterns:
    all: block
  private_key_blocks:
    all: block
  generated_prompt_leaks:
    generated_artifact: block
```

Secrets should normally be blocked everywhere, including evidence logs. If a security incident requires preservation, it should be moved into a quarantined, explicitly classified incident workflow rather than ordinary documentation.

## Exception and Quarantine Model

The system needs controlled exceptions. Without exceptions it will become unusable; with uncontrolled exceptions it will become meaningless.

Every exception must include:

- rule id,
- affected path or glob,
- resource class,
- reason,
- owner,
- expiry or permanent-historical-evidence marker,
- approval record,
- validator that confirms the exception scope is not broader than declared.

Example:

```yaml
exceptions:
  - id: historical-terminal-local-paths
    rule: local_absolute_paths
    path_glob: docs/reports/terminal/*.log
    class: terminal_log
    reason: historical terminal evidence may preserve original local working-directory output
    owner: governance
    expires: null
    status: approved_exception
```

Quarantine states:

- `clean`
- `warning`
- `blocked`
- `quarantined`
- `approved_exception`

Merge gates must fail for `blocked` and `quarantined` resources unless the workflow is explicitly a quarantine-remediation slice.

## Source-of-Truth Graph

The registry must distinguish canonical sources from projections.

Examples:

```yaml
facts:
  current_version:
    sources:
      - pyproject.toml
      - CITATION.cff
    projections:
      - README.md
      - docs/STATUS.md
      - docs/handoff/CURRENT_HANDOFF.md
    validators:
      - version_drift
  zenodo_version_doi:
    sources:
      - docs/releases/VERIFIED_RELEASES.md
      - CITATION.cff
    projections:
      - README.md
      - docs/STATUS.md
      - docs/handoff/CURRENT_HANDOFF.md
    evidence:
      - docs/reports/terminal/*.log
```

This prevents uncontrolled duplication. A duplicated fact is allowed only when the registry states whether it is a source, a projection, or historical evidence.

## Update Trigger Matrix

Each important event must define required follow-up resources.

Initial triggers:

- `release_preparation`
- `release_publication`
- `post_release_doi_closeout`
- `gui_baseline_change`
- `governance_rule_change`
- `workflow_command_change`
- `handoff_state_refresh`
- `terminal_safety_change`
- `documentation_language_policy_change`
- `artifact_gc_policy_change`
- `secret_filter_policy_change`

Example:

```yaml
update_triggers:
  post_release_doi_closeout:
    required_resources:
      - CHANGELOG.md
      - CITATION.cff
      - README.md
      - docs/releases/VERIFIED_RELEASES.md
      - docs/STATUS.md
      - docs/handoff/CURRENT_HANDOFF.md
      - .agentic/handoff_state.yaml
    required_evidence:
      - post_release_check_log
```

## Garbage Collector Integration

The garbage collector must be a registry-driven lifecycle executor, not an independent cleanup script.

GC policies:

- `never_delete`
- `preserve_forever`
- `preserve_if_referenced`
- `delete_after_ttl`
- `delete_after_promotion`
- `ttl_delete_after_promotion_or_expiry`
- `quarantine_instead_of_delete`

The GC must check references before deletion. Reference sources include at least:

- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `.agentic/handoff_state.yaml`
- `CHANGELOG.md`
- `docs/releases/VERIFIED_RELEASES.md`
- terminal latest pointers
- command reports
- pull request bodies when available through GitHub APIs
- the knowledge registry itself

The GC must support:

- dry-run mode,
- apply mode,
- protected-resource reporting,
- unclassified-resource reporting,
- stale-temporary-resource reporting,
- promoted-evidence detection,
- final-summary evidence validation.

A final summary that cites only `/tmp/...` evidence after a completed slice must fail a gate unless the slice explicitly remains local-only and incomplete.

## Validator Modules

The implementation should be modular. Suggested Python modules:

```text
src/agentic_project_kit/knowledge_registry.py
src/agentic_project_kit/knowledge_registry_schema.py
src/agentic_project_kit/knowledge_registry_check.py
src/agentic_project_kit/document_security_filters.py
src/agentic_project_kit/document_language_policy.py
src/agentic_project_kit/source_truth_graph.py
src/agentic_project_kit/update_trigger_matrix.py
src/agentic_project_kit/artifact_lifecycle.py
src/agentic_project_kit/artifact_gc_core.py
src/agentic_project_kit/llm_artifact_contracts.py
```

Suggested CLI surface:

```text
agentic-kit knowledge-registry check
agentic-kit knowledge-registry list
agentic-kit knowledge-registry explain PATH
agentic-kit docs-fast
agentic-kit docs-audit
agentic-kit security-docs-check
agentic-kit artifact-audit
agentic-kit artifact-gc --dry-run
agentic-kit artifact-gc --apply
agentic-kit release-docs-check
```

Existing `check-docs` should stay the standard gate and call only fast deterministic checks. `docs-audit` should call the full registry, language, redundancy, freshness, artifact, and security checks.

## Performance Profiles

Define validation profiles instead of one monolithic check:

- `docs-fast`: changed active documents plus registry syntax.
- `check-docs`: standard CI gate for active docs, release records, and current-state contracts.
- `docs-audit`: full documentation governance audit.
- `artifact-audit`: evidence logs, command reports, generated handoffs, temporary artifacts, GC dry-run classification.
- `security-docs-check`: known leak patterns and exception validation.
- `release-docs-check`: release, DOI, version, citation, and changelog consistency.
- `nightly-full`: expensive full repository scan, including historical evidence classification and stale-reference checks.

This avoids making every small PR pay the cost of a full historical log scan.

## LLM, Codex, and Claude-Code Integration

The registry must treat LLM-facing artifacts as first-class resources:

- agent instructions,
- successor-chat handoff prompts,
- generated command prompts,
- typed work orders,
- final summaries,
- terminal evidence logs,
- PR bodies,
- review comments when used as operational state,
- GUI action-result reports.

LLM-facing validation rules:

- no chat-only operational rule unless it is also reflected in a repository source,
- no unsafe terminal instructions,
- no local machine path in active prompts,
- no token-like material in generated prompts,
- handoff prompts must list mandatory sources,
- final summaries must be machine-readable,
- `d`, `f`, `w`, and similar compact replies must be interpreted only as communication signals, not evidence,
- generated handoffs must declare source documents and generator command,
- Codex/Claude-Code style agent instructions must be portable across machines.

## Advisory Semantic Review Boundary

The system should support optional advisory review without pretending that advisory review is a deterministic proof.

Hard gates should cover:

- schema validity,
- required registration,
- resource existence,
- lifecycle validity,
- known leak patterns,
- source-of-truth consistency,
- update-trigger obligations,
- generated-file drift,
- final-summary evidence validity,
- GC safety.

Advisory review may cover:

- clarity,
- conceptual completeness,
- semantic redundancy,
- over-complexity,
- quality of human explanation,
- whether a plan is still strategically useful.

Advisory findings must not silently block a release unless converted into deterministic checks or explicit maintainer decisions.

## Implementation Roadmap

### Phase 0: Release Current Documentation-Governance Baseline

Before changing the architecture of the documentation-governance system, publish a release from the current stable main and complete the existing release closeout.

This phase freezes the current working behavior as a known-good baseline. It also prevents the new registry work from being mixed with release metadata, DOI updates, GUI-readiness state, or unrelated documentation cleanup.

Required evidence:

- normal release-check pass,
- release publication evidence,
- post-release-check pass,
- DOI metadata closeout where applicable,
- refreshed current-state and handoff files,
- remote terminal evidence.

No registry implementation PR may be merged before this phase is complete.

### Phase 1: Planning and Registry Skeleton

- Add `.agentic/knowledge_registry.yaml` with schema version, resource classes, lifecycle states, policies, and a small initial resource set.
- Register core active resources: `README.md`, `AGENTS.md`, `CHANGELOG.md`, `CITATION.cff`, `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `docs/releases/VERIFIED_RELEASES.md`, core governance docs, terminal reports, and temporary local log patterns.
- Add documentation explaining resource classes and lifecycle states.
- No hard enforcement beyond YAML parse and basic schema validation.
- Do not remove or weaken existing documentation checks.

### Phase 2: Registry Check

- Add `agentic-kit knowledge-registry check`.
- Validate known classes, lifecycle values, policy values, path existence for active resources, and glob syntax for artifact classes.
- Fail if a core active document is missing from the registry.
- Add tests for valid registry, invalid class, missing active file, and unknown policy.
- Run as an additive check first, preferably through `docs-audit` rather than mandatory `check-docs`.

### Phase 3: Security and Local-Leak Guard

- Add class-dependent checks for local absolute paths, user-specific repository roots, credentials, private key blocks, token-like strings, `.env`-style sensitive assignments, and generated prompt leaks.
- Make active documentation and governance fail closed.
- Allow historical terminal logs to warn on local paths but block known secret patterns.
- Add controlled exception records with scope, owner, reason, and expiry.
- Prove that the guard does not break historical evidence preservation.

### Phase 4: Artifact Lifecycle and GC Contract

- Bind artifact GC to the registry.
- Implement `artifact-gc --dry-run` before any destructive cleanup.
- Protect referenced evidence.
- Report unclassified resources.
- Fail final-summary validation when `/tmp/...` is the only evidence for a completed remote-relevant slice.
- Do not enable destructive GC until dry-run behavior and reference protection are tested.

### Phase 5: Source-of-Truth Graph and Update Triggers

- Encode version, DOI, release, GUI-baseline, handoff, and governance-rule facts as source/projection/evidence relationships.
- Add update-trigger checks for release closeout, GUI baseline changes, governance rule changes, and handoff refreshes.
- Integrate with `check-docs` where fast and deterministic.
- Keep existing release and state checks until parity is proven.

### Phase 6: Performance Profiles and CI Integration

- Keep `check-docs` fast.
- Add deeper `docs-audit`, `artifact-audit`, `security-docs-check`, and `release-docs-check` profiles.
- Consider scheduled CI or maintainer-invoked full scans for expensive checks.
- Do not move expensive full-history scans into the normal fast path.

### Phase 7: LLM/Codex/Claude-Code Operating Layer

- Register generated handoff prompts, typed work orders, agent instructions, final summaries, and GUI action reports.
- Validate portable prompts, mandatory sources, no unsafe command patterns, no local machine data, and correct evidence references.
- Surface registry state through GUI/cockpit read-only actions before any remote/destructive GUI expansion.

### Phase 8: Advisory Review Layer

- Add optional advisory semantic review reports.
- Keep advisory findings separate from deterministic gates unless promoted to explicit rules.
- Store advisory reports as classified generated artifacts, not as source-of-truth documents.

## First Concrete Slice After The Pre-Rebuild Release

The next implementation PR after the pre-rebuild release should be small:

1. Add `.agentic/knowledge_registry.yaml` with the first resource classes and core resource entries.
2. Add a parser and schema-level validator.
3. Add `agentic-kit knowledge-registry check`.
4. Add tests for valid and invalid registry cases.
5. Wire the check into `docs-audit` only, not yet into mandatory `check-docs`.
6. Preserve all current guards unchanged.

Only after the first registry check is stable should the project add security filters, GC integration, and update-trigger enforcement.

## Guard Parity And Consolidation Policy

Existing special-purpose guards may be consolidated into registry-backed validators only after parity is proven.

A parity PR must include:

- a short inventory of the old guard,
- examples of known failures it catches,
- tests proving the new validator catches the same failures,
- a performance note for standard gates,
- explicit confirmation that no required current-state, release, handoff, evidence, terminal-safety, or CHANGELOG behavior was lost.

Until then, duplicated checks are acceptable. Temporary duplication is safer than losing a battle-tested guard.

## Non-Goals For The First Implementation

- Do not rewrite all documentation.
- Do not scan every historical log in every standard gate.
- Do not turn advisory semantic judgement into a hard gate.
- Do not make the GUI responsible for governance logic.
- Do not delete temporary files until dry-run reporting and reference protection are tested.
- Do not add remote or destructive GUI actions as part of this plan.
- Do not replace the existing functioning documentation-governance system in one large migration.
- Do not start implementation before the pre-rebuild release closeout is complete.

## Success Criteria

The system is successful when:

- the pre-rebuild release freezes the current functioning documentation-governance baseline,
- every active document has a class, lifecycle, owner, policy set, and validator profile,
- evidence logs and active rules are treated differently,
- generated files declare their generator and manual-edit policy,
- temporary files are either promoted, discarded, expired, or protected by clear GC policy,
- local machine data and sensitive material are blocked or quarantined according to class-dependent policy,
- release, DOI, GUI-baseline, and handoff facts are checked through a source-of-truth graph,
- update-trigger obligations are explicit and test-backed,
- standard gates remain fast,
- deeper audits remain available for release, handoff, and maintenance slices,
- LLM/Codex/Claude-Code collaboration artifacts are portable, inspectable, and evidence-backed,
- old guards are consolidated only after parity is proven.
