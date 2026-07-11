# P5c Physical Migration Plan

Status: proposed plan
Decision status: awaiting maintainer decision
Status-date: 2026-07-11
Document class: architecture
Owner: maintainers
Execution: maintainer-gated

This document is the P5c-PLAN output for the Kit-as-OS migration line. It is a
decision-ready plan only. It does not move files, change resolver defaults,
change generated handoff locations, or make `.agentic/` the physical source for
public documents.

Execution of any physical migration remains a hard maintainer gate. The Q2
sequence continues with P6 after this plan is merged.

## Scope

P5c exists because the self-hosting manifest and resolver aliases are now in
place, while the kit repository still exposes long-standing public paths such
as `docs/STATUS.md`, `docs/handoff/`, and
`docs/reports/handoff-packages/latest/`.

The architecture goal is not to move everything for its own sake. The operating
layer allows source artifacts to live under `.agentic/`, but public surfaces may
remain as projections when external links, chat bootstraps, or reviewer
ergonomics depend on them.

## Reference Scan Baseline

Reference counts were gathered on 2026-07-11 from this P5c branch with fixed
string scans after creating this plan. Counts exclude `.git/` but include
tests, generated projections, archives, and documentation because those paths
still affect migration risk.

| Candidate | Current path or prefix | Fixed-string references | Target option |
|---|---:|---:|---|
| Documentation registry | `docs/DOCUMENTATION_REGISTRY.yaml` | 373 | `.agentic/registries/documentation_registry.yaml` |
| Documentation scope | `docs/DOC_REGISTRY_SCOPE.yaml` | 23 | `.agentic/registries/documentation_scope.yaml` |
| Public status | `docs/STATUS.md` | 1255 | `.agentic/state/status.md` plus projection |
| Human handoff prompts | `docs/handoff` | 2167 | `.agentic/state/handoff/prompts/` plus projection |
| Latest handoff package | `docs/reports/handoff-packages/latest` | 160 | `.agentic/state/handoff/latest/` plus projection |
| Persistent handoff state | `.agentic/handoff_state.yaml` | 587 | `.agentic/state/handoff/state.yaml` |
| Operational handoff state | `.agentic/operational_handoff_state.yaml` | 217 | `.agentic/state/handoff/operational_state.yaml` |
| Local rule acknowledgement | `.agentic/rule_ack` | 25 | `.agentic/state/rule_ack/` or stay local |
| Rule mechanism inventory | `.agentic/rule_mechanism_inventory.yaml` | 273 | `.agentic/rules/rule_mechanism_inventory.yaml` |
| Transfer safety rules | `.agentic/transfer_safety_rules.yaml` | 39 | `.agentic/rules/transfer_safety_rules.yaml` |
| Workspace temp | `.agentic/tmp` | 53 | stay ignored under `.agentic/tmp/` |
| Self-hosting manifest | `.agentic/config.yaml` | 45 | stay |

Hotspot files from the same scan:

| Candidate | Highest-count files |
|---|---|
| Documentation registry | `docs/reports/handoff-packages/latest/execution_contract.json` (30), `docs/reports/handoff-packages/latest/successor_prompt.md` (29), `docs/reports/handoff-packages/latest/successor_context.yaml` (28), `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (14) |
| Documentation scope | `docs/DOCUMENTATION_COVERAGE.yaml` (4), `docs/planning/PROJECT_DIRECTION.yaml` (3), `docs/DOCUMENTATION_REGISTRY.yaml` (2), this plan (2), `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md` (2) |
| Public status | `docs/reports/ns-migration/ns_to_agentic_kit_replacement_table.md` (353), `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (186), `docs/reports/branch_cleanup/obsolete_branch_cleanup_plan_20260518-193335.md` (18), `src/agentic_project_kit/status_current_state_audit.py` (13), `tests/test_transfer_repo_actions.py` (13) |
| Human handoff prompts | `docs/reports/ns-migration/ns_to_agentic_kit_replacement_table.md` (585), `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (361), `docs/reports/handoff_rules/CURRENT_HANDOFF_RULES.md` (35), `tests/test_transfer_repo_actions.py` (34) |
| Latest handoff package | `tests/test_transfer_repo_actions.py` (37), `docs/reports/handoff-packages/latest/execution_contract.json` (10), `docs/planning/PROJECT_DIRECTION.yaml` (7), `tests/test_successor_handoff_package.py` (7) |
| Persistent handoff state | `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (21), `docs/reports/branch_cleanup/obsolete_branch_cleanup_plan_20260518-193335.md` (15), `docs/reports/ns-migration/ns_to_agentic_kit_replacement_table.md` (14), `tests/test_transfer_repo_actions.py` (14) |
| Operational handoff state | `tests/test_transfer_repo_actions.py` (9), `tests/test_workspace_foundation.py` (4), this plan (2), `docs/reports/ns-migration/ns_to_agentic_kit_replacement_table.md` (2) |
| Rule acknowledgement | `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (8), `src/agentic_project_kit/transfer_state.py` (4), this plan (2), `src/agentic_project_kit/communication_rule_context.py` (2) |
| Rule inventory | `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (15), `docs/reports/ns-migration/ns_to_agentic_kit_replacement_table.md` (7), `docs/reports/handoff_rules/CURRENT_HANDOFF_RULES.md` (4), `tests/test_workspace_foundation.py` (4) |
| Transfer safety rules | `docs/reports/ns-migration/ns_to_agentic_kit_audit.md` (8), `docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json` (6), `src/agentic_project_kit/transfer_safety_context.py` (4), `tests/test_transfer_llm_context_gate.py` (4) |
| Workspace temp | `tests/test_workspace_foundation.py` (11), `tests/test_local_garbage_collector.py` (6), this plan (5), `tests/test_workspace_init.py` (5) |
| Self-hosting manifest | `tests/test_workspace_foundation.py` (9), `docs/archive/KIT_AS_OS_MASTERPLAN.md` (7), `docs/architecture/KIT_AS_OS_ARCHITECTURE.md` (4), `docs/planning/MASTER_IMPLEMENTATION_Q.md` (4) |

## Candidate Decisions

### Documentation Registries

Current paths:

- `docs/DOCUMENTATION_REGISTRY.yaml`
- `docs/DOC_REGISTRY_SCOPE.yaml`

Target paths:

- `.agentic/registries/documentation_registry.yaml`
- `.agentic/registries/documentation_scope.yaml`

Recommendation: stay for now. These files are governance surfaces that are
read by documentation gates, registry tests, docs-audit output, and reviewer
documentation. Moving them now would create a large compatibility tail with
little immediate safety gain.

Later execution option: introduce resolver-backed registry access first, then
make the `docs/` files deterministic projections with a source-hash header.
Only after check mode proves zero drift should maintainers decide whether the
`.agentic/registries/` files become canonical.

Risk: high. Broken registry paths can hide unregistered documents or produce
false documentation failures.

Rollback: keep `docs/` files as canonical until the projection gate passes.
If a later migration fails, restore the `docs/` files from git and disable the
projection source switch without changing document content.

### Rules And Rule State

Current paths include:

- `.agentic/rule_mechanism_inventory.yaml`
- `.agentic/transfer_safety_rules.yaml`
- `.agentic/rule_ack/`
- `.agentic/rule_*.yaml`
- `.agentic/no_copy_terminal_policy.yaml`
- `.agentic/communication_artifacts.yaml`

Target paths:

- `.agentic/rules/` for versioned rule capsules and inventories
- `.agentic/state/rule_ack/` for local acknowledgement state, if a move is ever
  needed

Recommendation: split conceptually, do not move yet. Versioned rule sources
belong under `.agentic/rules/` in the target layout, while acknowledgement
state is local runtime state and is already ignored by `.gitignore`.

Later execution option: add resolver methods for rule capsules, teach gates to
read through those methods, and only then move one low-risk rule file as a
pilot. Keep the old root-level `.agentic/rule_*.yaml` paths as compatibility
aliases or generated projections until all tests and command manifests stop
depending on literal paths.

Risk: medium to high. Rule files are loaded by safety gates and transfer
wrappers. A partial move can produce false PASS if a gate silently reads stale
compatibility files.

Rollback: old root-level files remain the compatibility source until the
resolver switch is complete. A failed pilot reverts by deleting the new target
file and keeping the old source.

### Status

Current path:

- `docs/STATUS.md`

Target path:

- `.agentic/state/status.md`

Recommendation: projection, not direct move. `docs/STATUS.md` has 1242 fixed
string references and is a public review and handoff anchor. It should remain
the visible public document even if its future source moves into `.agentic/`.

Projection concept:

1. Canonical source: `.agentic/state/status.md`.
2. Public projection: `docs/STATUS.md`.
3. Generator sketch:
   `agentic-kit status render-projection --source .agentic/state/status.md --output docs/STATUS.md --check`.
4. Write mode is explicit and bounded:
   `agentic-kit status render-projection --source .agentic/state/status.md --output docs/STATUS.md --write`.
5. Projection header carries the source path, source hash, generator version,
   and a warning that manual edits must be made in the source.
6. Drift gate compares the source hash and rendered output. It fails if
   `docs/STATUS.md` is edited by hand or if the projection is stale.
7. Existing docs-audit closeout synchronization checks continue to inspect the
   projected `docs/STATUS.md` until every caller is resolver-backed.

Risk: very high. Status is used by humans, handoff checks, docs-audit, release
closeout, and successor context generation.

Rollback: keep `docs/STATUS.md` as the source until the projection command has
tests and check mode is green on main. If a later source switch fails, restore
`docs/STATUS.md` as canonical and delete `.agentic/state/status.md`.

### Handoff Prompts And Packages

Current paths:

- `docs/handoff/`
- `docs/reports/handoff-packages/latest/`
- `docs/reports/terminal/post-pr*-successor-chat-handoff.md`
- `.agentic/handoff_state.yaml`
- `.agentic/operational_handoff_state.yaml`

Target paths:

- `.agentic/state/handoff/prompts/`
- `.agentic/state/handoff/latest/`
- `.agentic/state/handoff/state.yaml`
- `.agentic/state/handoff/operational_state.yaml`

Recommendation: projection or stay. Do not physically move handoff prompts or
latest packages in the next execution slice. These files are explicitly named
in `AGENTS.md`, successor prompts, chat bootstraps, and the post-merge lifecycle.
Their public paths are part of the workflow contract.

Later execution option: first add resolver-backed handoff package readers and a
projection check that proves `docs/handoff/` and
`docs/reports/handoff-packages/latest/` exactly match `.agentic/state/handoff/`.
Only after the bootstrap acceptance rule understands projections should a
maintainer decide whether the `.agentic/state/handoff/` copy is canonical.

Risk: very high. A stale or moved handoff path can strand successor chats,
trigger unnecessary admin refreshes, or make a valid refresh look stale.

Rollback: keep current public handoff paths canonical until projection drift
checks are part of the post-merge lifecycle. A failed experiment restores the
public paths and removes the projected `.agentic/state/handoff/` copies.

### Tmp And Scratch Residues

Current paths:

- `.agentic/tmp/`
- `tmp/`
- `.agentic/.DS_Store`
- `.agentic/transfer/.DS_Store`
- `docs/reports/transfer_runs/`

Target paths:

- `.agentic/tmp/` for workspace-local scratch
- no committed platform metadata files

Recommendation: stay for `.agentic/tmp/`, cleanup for committed scratch
residues in a separate small slice. `.agentic/tmp/` is already ignored. The two
`.DS_Store` files are cleanup candidates, but removing them is not part of
P5c-PLAN because this slice must not perform physical migration or cleanup.

Risk: low for `.DS_Store`, medium for temp roots because transfer and evidence
commands depend on known ignored paths.

Rollback: ignored temp directories are recreated by commands. If a later
cleanup accidentally removes a needed committed file, restore it from git and
add a deterministic test before retrying.

## Recommended Execution Phases

P5c-EXEC must not start without explicit maintainer approval. If approved, use
these separately mergeable phases:

1. Readiness slice: add resolver methods and check-only commands for status,
   registry, rules, and handoff projections. No source switch.
2. Status projection pilot: add `.agentic/state/status.md`, render
   `docs/STATUS.md`, and add a drift gate. Stop if any public status consumer
   reads the source directly instead of the projection.
3. Registry projection pilot: add `.agentic/registries/` sources and keep
   `docs/` projections until every registry command uses resolver-backed paths.
4. Rule capsule pilot: move one low-risk versioned rule file behind a resolver
   alias. Do not move acknowledgement state in the same slice.
5. Handoff projection pilot: add `.agentic/state/handoff/` mirrors and a
   post-merge projection check. Keep public handoff paths as projections.

Each execution phase needs its own branch, PR, focused tests, full tests,
docs-audit, audit-doc-currency, standard-gates-audit-suite, and a protected
diff plan.

## Stop Conditions

Stop execution immediately if any of these occur:

- a public `docs/` path loses a deterministic projection;
- a handoff bootstrap or successor package path becomes stale;
- a resolver fallback reads a stale compatibility copy silently;
- a docs or rule gate can pass while reading different source/projection
  content;
- a migration requires changing external links without a maintainer decision.

## Acceptance Mapping

- Plan created: this document.
- Reference-scan backed: see the Reference Scan Baseline table.
- Registered: `docs/DOCUMENTATION_REGISTRY.yaml` must list this document.
- No physical files moved: P5c-PLAN changes documentation and planning only.
- Maintainer gate preserved: Direction must mark `p5c-physical-migration` as
  blocked with an awaiting-maintainer-decision rationale after the PR number is
  known.
