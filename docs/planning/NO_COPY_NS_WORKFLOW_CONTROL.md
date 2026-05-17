# No Copy NS Workflow Control

Status: active
Decision status: proposed
Scope: unify ./ns no-copy workflow control with future GUI cockpit action model
Review policy: review before implementation, after ns workflow milestone, and before GUI action integration

## Purpose

Reduce Chat-to-Terminal copy-and-paste by making `./ns` the primary local workflow controller while preserving a path toward the GUI cockpit.

## Context

The repository already has `./ns`, `./ns go`, `./ns up`, `agentic-kit workflow ...`, and a shared Cockpit Action Registry. In practice, long ad-hoc terminal blocks still caused quoting and heredoc failures. The latest failure showed that `./ns go` currently delegates to `agentic-kit workflow go`, which uses `.agentic/current_work.yaml` and may execute `git_pull_ff_only`. That is unsafe or unsuitable for active feature branches with local slice work.

## Problem

- `./ns go` is too blunt for feature-branch development because the default workflow includes `git_pull_ff_only`.
- Long Chat-provided shell blocks are error-prone and contradict the no-copy goal.
- `.agentic/current_work.yaml` is governed by tests and documentation coverage and must not be repurposed as free-form slice scratch state.
- The terminal workflow must not diverge from the future GUI cockpit action model.

## Target model

- `./ns` remains the human entry point.
- `./ns dev` runs local feature-branch gates without `git pull --ff-only`.
- `./ns go` remains available for the governed workflow path but should warn or guard when used in a risky feature-branch state.
- `./ns up` should remain the upload / PR-oriented path and later become more state-aware.
- All multi-step `./ns` outputs should end with `### RESULT: PASS ###` or `### RESULT: FAIL ###`.
- New actions should be documented as future GUI cockpit candidates rather than becoming shell-only hidden behavior.

## Initial implementation slice

1. Add `./ns dev` as a quote-safe local feature gate.
2. Make `./ns` menu advertise `dev`, `go`, `up`, and cockpit inspection commands clearly.
3. Add a guard message around risky `./ns go` usage on feature branches with local changes.
4. Ensure relevant `./ns` flows print explicit PASS/FAIL markers.
5. Add tests for the `./ns` menu and command references.
6. Update STATUS/HANDOFF after implementation.

## Out of scope for this slice

- No write-capable GUI actions.
- No automatic merge/release button.
- No replacement of the existing workflow runner.
- No mutation of `.agentic/current_work.yaml` as slice scratch state.

## GUI compatibility

The `./ns dev`, `./ns go`, and `./ns up` concepts should remain representable as Cockpit Actions with safety classes and command metadata. The GUI should eventually display these actions using the shared action registry rather than reimplementing command logic.

## Evidence

- `python -m pytest -q`
- `ruff check .`
- `agentic-kit check-docs`
- `agentic-kit doctor`
- `agentic-kit pr-hygiene`
- local smoke test for `./ns dev`
