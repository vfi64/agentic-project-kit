# Remaining portability classification

Status: active

Decision status: proposed

Review policy: required before implementation

Project: agentic-project-kit portability closeout

## Purpose

Classify remaining `ns`-named Python modules, shell scripts, and shell-dependent helper routes after the completed migration of `ns dev`, `ns go`, `ns up`, and `ns upload`.

This document is classification-only. It must not be treated as implementation evidence.

## Current clean baseline

The previous ns command migration closeout completed with PR #1408.

Known baseline after PR #1408:

- `main == origin/main`
- HEAD: `d60a5ab1a23d6ce9a7a9d69dae1f77c248a066ea`
- worktree clean
- `post-merge-check`: PASS / NOOP
- `repo-status`: PASS
- `docs-audit`: PASS

## Classification summary

| Item | Current role | Decision | Target slice |
|---|---|---:|---|
| `tools/capture_workflow_output.sh` | Shell helper for workflow output capture | port/remove after exact caller check | Slice 2 |
| `tools/local_workflow_cycle.sh` | Shell workflow cycle helper, referenced by `tools/next-step.py` | port to Python/agentic-kit route | Slice 2 |
| `tools/next-step.py` | Python helper still calling shell workflow cycle | adjust to Python route | Slice 2 |
| `tools/screen_control_gate.sh` | Shell gate with terminal/output assumptions | handle separately; port or explicitly mark local-only | Slice 3 |
| `src/agentic_project_kit/ns_slice_runner.py` | Remaining `ns`-named Python runtime path | rename/port to neutral agentic-kit command/module or isolate as legacy | Slice 4 |
| `tests/test_ns_slice_runner.py` | Test for `ns_slice_runner` behavior | update with Slice 4 | Slice 4 |
| `tools/ns_release_metadata_prep.py` | Release metadata prep script referenced from release prep path | move into `src/agentic_project_kit` or integrate into release prep core | Slice 5 |
| `tests/test_ns_interpreter_and_no_exec_guard.py` | Guard against unsafe ns interpretation/exec behavior | likely keep as safety regression or rename after runtime ns removal | Slice 4/6 |
| `tests/test_ns_evidence_guard_shortcut.py` | Guard against unsafe ns evidence shortcuts | likely keep as safety regression or rename after runtime ns removal | Slice 4/6 |
| `tools/workflow_runner.py` | Python workflow runner with subprocess/tool interactions | audit as dependency of Slice 2 | Slice 2 |
| `tools/NEXT_TRANSFER_TASK.py` | Transfer task helper with potential shell/process assumptions | audit as dependency of Slice 2 | Slice 2 |

## Slice plan

### Slice 2: Workflow shell helpers

Scope:

- `tools/capture_workflow_output.sh`
- `tools/local_workflow_cycle.sh`
- `tools/next-step.py`
- related uses in `tools/workflow_runner.py`
- related uses in `tools/NEXT_TRANSFER_TASK.py`

Goal:

- remove shell dependency from the active workflow cycle path;
- provide Python-backed or `agentic-kit`-backed route;
- keep behavior tested;
- do not introduce a compatibility shell layer unless explicitly documented as local-only.

### Slice 3: Screen control gate

Scope:

- `tools/screen_control_gate.sh`

Goal:

- handle separately because terminal/screen/TTY assumptions are higher-risk;
- port to Python/agentic-kit if it is part of supported workflow;
- otherwise mark explicitly as local-only developer helper or remove.

### Slice 4: `ns_slice_runner`

Scope:

- `src/agentic_project_kit/ns_slice_runner.py`
- `tests/test_ns_slice_runner.py`
- affected `ns` entrypoint behavior

Goal:

- remove or neutralize remaining runtime `ns`-named path;
- if behavior remains useful, migrate to neutral module and first-class `agentic-kit` command;
- keep no-exec and evidence safety guards.

### Slice 5: release metadata prep

Scope:

- `tools/ns_release_metadata_prep.py`
- release prep callers and tests

Goal:

- remove `tools/ns_*` script from release path;
- move logic into package module or integrate directly into release prep core;
- keep release gates green.

### Slice 6: portability closeout

Goal:

- no active `.sh` runtime dependency;
- no active `./ns` runtime route;
- no required `ns_*` runtime module names except deliberate historical tests/docs;
- full gates green;
- docs/status/handoff updated.

## Non-goals

Do not:

- restore old `./ns` command families;
- start GUI or release work;
- delete safety tests without replacement coverage;
- replace protected docs broadly;
- combine screen/TTY work with unrelated shell cleanup.



## Slice 2 status

Status: in progress in `feature/port-workflow-shell-helpers`.

Intent:

- move active workflow progression away from `tools/local_workflow_cycle.sh`;
- provide Python-backed output capture through `tools/capture_workflow_output.py`;
- keep shell files only as legacy/local helpers until a later removal decision, unless active references are fully eliminated in this slice.
