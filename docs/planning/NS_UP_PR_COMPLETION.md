# NS Up PR Completion

Status: superseded
Decision status: superseded
Review policy: review before implementation, after ns workflow milestone, and before GUI action integration
Lifecycle note: Superseded by `agentic-kit transfer pr-complete`; the legacy `agentic_project_kit.ns_up_pr_completion` module was removed after the command migration classification.

## Purpose

TODO: describe the purpose of this governed planning document.

## Context

TODO: summarize the relevant repository state and constraints.

## Plan

TODO: define the planned work in small, reviewable slices.

## Evidence

TODO: list required gates, tests, review points, or audit evidence.

## Current migration status

This PR-completion note is retained as legacy context. Active PR lifecycle work must use `agentic-kit transfer pr-create-complete`, `pr-complete`, `post-merge-complete`, `post-merge-check`, and related bounded wrappers.

The old `ns up` route is no longer a supported runtime path. Do not reintroduce `agentic_project_kit.ns_up_pr_completion`; put missing PR-completion behavior into the transfer command family instead.
