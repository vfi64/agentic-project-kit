Status: superseded
Status-date: 2026-07-09
Superseded-by: docs/archive/PRE_GUI_HARDENING_TASKS.md

# Pre-GUI Execution Hardening

Status: Active
Status-date: 2026-05-20
Owner: Maintainer

This contract defines the execution invariants that must be hardened before the Tkinter cockpit becomes the primary local interface.

## Scope

v0.3.31 is a pre-GUI execution hardening slice. It does not introduce the Tkinter GUI. It hardens the execution path that the GUI will later call.

## Required invariants

### No false PASS after failed gate

A workflow must not commit, push, merge, tag, or publish after a required targeted test, full gate, or postcondition check has failed. A failed gate must produce a failing final summary.

### Clean base before log creation

A work block must check for a clean base before creating a new terminal log file. If a log file is intentionally created after that precheck, the new file must be treated as an expected artifact and finalized before remote mutation.

### No nested quote patch generator

Patch generation must avoid fragile nested Python-in-shell or Python-in-Python quoting. Prefer typed work orders, direct file rewrites, small checked scripts, or repository-owned patch helpers.

### Evidence finalization contract

A terminal log that is committed as evidence must not be written to again after the evidence commit. If final verification output is needed after a merge, record it in a separate closeout log and merge it through a separate evidence PR.

### GUI boundary

The later Tkinter cockpit must remain a thin presentation layer over registry actions, cockpit JSON results, typed work orders, and machine-readable summaries. It must not invent hidden command plans.

## Preferred execution path

Chat describes intent. Repo-owned tools execute typed operations. Shell is a runner, not the patch language. Markdown is a projection and audit surface, not the strongest primary source for executable state.
