# NS Up PR Completion

Status: active
Decision status: proposed
Scope: reduce chat-to-terminal copy-and-paste by letting ./ns up complete the standard PR verification and merge cycle
Review policy: review before implementation, after ns workflow milestone, and before GUI action integration

## Purpose

TODO: describe the purpose of this governed planning document.

## Context

TODO: summarize the relevant repository state and constraints.

## Plan

TODO: define the planned work in small, reviewable slices.

## Evidence

TODO: list required gates, tests, review points, or audit evidence.

## Current migration status

This PR-completion note is retained as legacy context. Active PR lifecycle work should now prefer `agentic-kit transfer pr-create-complete`, `pr-complete`, `post-merge-complete`, `post-merge-check`, and related bounded wrappers.

Before GUI implementation, any active `./ns` PR workflow must be mapped to a tested `agentic-kit` replacement or explicitly deprecated.
