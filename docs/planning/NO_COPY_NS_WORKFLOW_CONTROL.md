# No Copy NS Workflow Control

Status: active
Decision status: proposed
Scope: unify ./ns no-copy workflow control with future GUI cockpit action model
Review policy: review before implementation, after ns workflow milestone, and before GUI action integration

## Purpose

Reduce Chat-to-Terminal copy-and-paste by making `./ns` the primary local workflow controller while preserving a path toward the GUI cockpit.

## Context


## Problem

- Long Chat-provided shell blocks are error-prone and contradict the no-copy goal.
- `.agentic/current_work.yaml` is governed by tests and documentation coverage and must not be repurposed as free-form slice scratch state.
- The terminal workflow must not diverge from the future GUI cockpit action model.

## Target model

- `./ns` remains the human entry point.
- All multi-step `./ns` outputs should end with `### RESULT: PASS ###` or `### RESULT: FAIL ###`.
- New actions should be documented as future GUI cockpit candidates rather than becoming shell-only hidden behavior.

## Initial implementation slice

2. Make `./ns` menu advertise `dev`, `go`, `up`, and cockpit inspection commands clearly.
4. Ensure relevant `./ns` flows print explicit PASS/FAIL markers.
5. Add tests for the `./ns` menu and command references.
6. Update STATUS/HANDOFF after implementation.

## Out of scope for this slice

- No write-capable GUI actions.
- No automatic merge/release button.
- No replacement of the existing workflow runner.
- No mutation of `.agentic/current_work.yaml` as slice scratch state.

## GUI compatibility


## Evidence

- `python -m pytest -q`
- `ruff check .`
- `agentic-kit check-docs`
- `agentic-kit doctor`
- `agentic-kit pr-hygiene`

## Current migration status

This document is retained as legacy workflow context. Active workflow instructions should now prefer bounded `agentic-kit` commands over direct `./ns` use.

Before GUI implementation:
- classify every remaining `./ns` reference as active, legacy, compatibility, or obsolete;
- replace active workflow instructions with tested `agentic-kit` commands;
- keep any remaining `./ns` mention explicitly labeled as legacy or compatibility-only.
