# Hermes Executor H0 Inventory

Status: completed read-only inventory  
Date: 2026-08-23  
Repository: vfi64/agentic-project-kit  
Branch: codex/hermes-executor-h0-inventory  
Base main: be575977d59e29dec2e8d2abdf7a9b86461a1fda

## Purpose

This report records the H0 inventory for
`planner-kit-executor-hermes-integration` in
`docs/planning/PROJECT_DIRECTION.yaml`.

H0 is intentionally read-only. It does not introduce a Hermes runtime adapter,
does not create a new command taxonomy, does not change transfer/workflow state,
and does not publish or mutate release artifacts.

## Task Identity

- Carrier ref: `gui-transfer-tasks`
- Carrier path: `.agentic/transfer/inbox/current.yaml`
- Task id: `14c20cbbb6de3006`
- Verified task body SHA-256:
  `73469189b052e196728d766bc175968e1588c7c43c51c19efd30953905c51981`
- Current command manifest ACK: `COMMAND_MANIFEST_ACK a6c875ef652f`
- Command manifest command count observed: 251

## Source Boundaries

Authoritative repository sources inspected for this slice:

- `docs/reference/agentic-kit-commands.json`
- `docs/reports/handoff-packages/latest/`
- `AGENTS.md`
- `docs/architecture/ARCHITECTURE_CONTRACT.md`
- `docs/DOCUMENTATION_COVERAGE.yaml`
- `docs/STATUS.md`
- `docs/TEST_GATES.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/planning/PROJECT_DIRECTION.yaml`
- `src/agentic_project_kit/action_specs.py`
- `src/agentic_project_kit/action_registry.py`
- `src/agentic_project_kit/cockpit.py`
- `src/agentic_project_kit/gui_action_execution.py`
- `src/agentic_project_kit/work_orders.py`
- `src/agentic_project_kit/typed_work_order_runner.py`

User-provided planning input was inspected as source material, not as executable
or governance authority:

- Hermes automation masterplan, SHA-256
  `d9a10715dc0ec8e0f916e7244b7f2ee8faec4748d833295459bec2e749044c01`
- LLM onboarding/tutor planning document, SHA-256
  `91be3912870e56cbb42daeaa4e6f29772011cec892d10eeb0d3a3982b4c97e7f`

## Current Kit Authority Surface

The Kit already has the authority surfaces that a Planner-Kit-Executor design
must reuse instead of duplicating:

- Command selection authority: `agentic-kit command-for` over the generated
  command manifest.
- Command manifest: `docs/reference/agentic-kit-commands.json`, manifest SHA
  `a6c875ef652f`, 251 commands.
- Action specifications: `agentic-kit actions list` exposes five
  parameterized action contracts focused on PR, release, DOI, and finalization
  lifecycle work.
- Cockpit actions: `agentic-kit cockpit actions --json` exposes 18 registered
  GUI-facing actions; 11 are `read_only` and 7 are `bounded`.
- Cockpit execution guard: `src/agentic_project_kit/gui_action_execution.py`
  allows only read-only GUI MVP execution by default.
- Workflow surface: `agentic-kit workflow ...` already models bounded local
  workflow state and evidence pointers.
- Work-order surface: `agentic-kit work-order ...` already has read-only
  list/show/check commands and bounded run/upload/typed-run commands.
- Typed work orders: `src/agentic_project_kit/typed_work_order_runner.py`
  supports structured `command_argv` and `cockpit_action` steps, blocks dirty
  worktrees by default, and writes bounded terminal logs under
  `docs/reports/terminal/`.
- Handoff authority: `docs/reports/handoff-packages/latest/`,
  `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`,
  `.agentic/handoff_state.yaml`, and
  `.agentic/operational_handoff_state.yaml`.
- Release boundary: `agentic-kit release-status --json` reports version 1.0.3
  as prepared but not published; no local tag exists. Live publishing remains
  behind the explicit release capability boundary and was not altered in H0.

## Hermes Boundary

Hermes is present on this workstation as a local process surface, including
`hermes_cli.main gateway run` and a user-local Hermes agent process. No
repo-native Hermes module, command family, or checked-in executor adapter exists
in the current `src/`, `tests/`, or governed planning paths.

Therefore Hermes must be treated as an external executor candidate, not as a Kit
authority source. Any durable integration must pass through Kit-owned command
resolution, capability checks, evidence, and handoff lifecycle.

## H0 Findings

1. A parallel planner, workflow taxonomy, state machine, handoff mechanism, or
   documentation authority would conflict with the architecture contract.
2. The first durable integration point should be a Kit-owned adapter contract,
   not a Hermes-specific command family.
3. The most promising H1 proof-of-concept surface is typed work orders plus
   cockpit/action-registry resolution, because they already model structured
   steps, safety classes, dirty-state blocking, and terminal evidence.
4. `agentic-kit actions list` and `agentic-kit cockpit actions --json` expose
   different registries. H1 must decide whether executor-facing actions should
   resolve through parameterized `ActionSpec`, CockpitAction, the command
   manifest, or a small facade that composes them without creating a second
   authority.
5. Not every inspection command has JSON output yet. For example,
   `agentic-kit actions list` and `agentic-kit cockpit status` rejected
   `--json` during H0. H1 should avoid requiring uniform JSON where the current
   command contract does not provide it, or explicitly scope a separate
   command-contract improvement slice.
6. The live release publisher is a useful capability-boundary precedent: even
   with `--execute`, publication fails closed unless the explicit local
   capability file exists. Executor/browser capabilities should follow the same
   deny-by-default shape.
7. The current typed work-order inbox has no pending command. H0 did not enqueue,
   execute, or clean any work orders.

## H1 Contract Requirements

H1 should be a gap analysis and proof-of-concept contract only. Before any
runtime mutation path is added, H1 should define:

- planner intent input schema;
- Kit command/action resolution rule;
- executor transport output schema;
- allowed safety classes and default deny behavior;
- capability boundary for local browser/session/credential access;
- dirty-worktree and stale-head preconditions;
- idempotency rule for repeated executor runs;
- terminal/evidence paths and false-PASS rejection expectations;
- failure states and human escalation messages;
- post-merge and successor-handoff requirements;
- tests that prove Hermes remains an adapter and the Kit remains the authority.

## DCO Decision

Deterministic Cell Orchestration is not used for H0 because this is a simple
inventory report with no selective repair need. H1 should reconsider a small
typed contract if the proof-of-concept needs independently validated planner
intent, command resolution, executor result, and evidence cells.

## Next Safe Slice

Proceed to H1 on a fresh branch after this H0 evidence PR is complete and
post-merge handoff refresh passes. H1 should produce a proof-of-concept contract
and targeted tests or fixtures, still without local runtime mutation unless the
contract explicitly proves a bounded read-only path.
