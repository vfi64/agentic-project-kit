# NS Release Shortcuts

Status: active
Decision status: proposed
Scope: automate release preparation, release gates, and guarded publishing through ./ns commands
Review policy: review before v0.3.21 release preparation and before any release publishing automation

## Purpose

TODO: describe the purpose of this governed planning document.

## Context

TODO: summarize the relevant repository state and constraints.

## Plan

TODO: define the planned work in small, reviewable slices.

## Evidence

TODO: list required gates, tests, review points, or audit evidence.

## Current migration status

This release-shortcut note is retained as legacy context. Release and post-release work should now use the tested `agentic-kit` release, transfer, handoff, and post-merge commands.

Before GUI implementation, any active release shortcut that still points primarily to `./ns` must be replaced by an `agentic-kit` command path or explicitly deprecated.
