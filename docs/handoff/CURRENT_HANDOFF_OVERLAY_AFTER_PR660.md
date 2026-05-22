# Current Handoff Overlay After PR660

Status-date: 2026-05-22
Project: agentic-project-kit
Branch: main
Base branch: main

## Purpose

This overlay records the current state after PR #659 and PR #660 without shortening `docs/handoff/CURRENT_HANDOFF.md`. It exists because `CURRENT_HANDOFF.md` still contains old compatibility and historical anchors that must not be removed by a broad rewrite.

## Current State

- Current released version: 0.3.37.
- Current release tag: v0.3.37.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20329450`.
- PR #656 closed out the GUI MVP three read-only actions: `cockpit-readiness`, `doctor`, and `check-docs`.
- PR #657 modeled administrative evidence state in generated handoff prompts.
- PR #659 repaired `docs/STATUS.md` current-state drift after PR #657.
- PR #660 refreshed `.agentic/handoff_state.yaml` after PR #659.

## Current GUI Baseline

- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- `agent-run` and non-read-only GUI actions remain disabled in the GUI MVP.

## Remaining Drift

- `docs/handoff/CURRENT_HANDOFF.md` still opens with old v0.3.30/v0.3.34 planning text.
- Historical PRs #562, #564, and #568 still need explicit classification or closure.
- A later local or typed patch should merge this overlay into `CURRENT_HANDOFF.md` non-destructively while preserving existing test-bound anchors.

## Next Safe Step

Classify or close historical PRs #562, #564, and #568, then repair `docs/handoff/CURRENT_HANDOFF.md` through a non-destructive patch that preserves all existing compatibility anchors.

Do not start v0.4.0 release-readiness conclusions until those remaining drift items are handled and gates are green.
