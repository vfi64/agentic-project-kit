---
Status: active
Decision status: proposed
Review policy: review before GUI, release automation, or larger patch-generation workflow changes
---

# Patch Artifact Preflight Slice

Purpose: stop complex shell-generated patch blocks from damaging Python, YAML, Markdown, coverage files, or terminal result contracts.

This slice must prefer deterministic preflight over fast patching.

## Status

active

## Decision status

proposed

## Required checks

- patch scripts must pass Python syntax checks before execution
- generated or changed Python files must pass py_compile before full gates
- governance YAML files must parse before and after mutation
- documentation coverage terms must remain strings
- terminal logs must satisfy the mandatory final SUMMARY contract
- gh CLI JSON fields must not be guessed; use supported fields such as state, mergedAt, mergeCommit, url
- no inner FAIL may be relabeled as OVERALL RESULT: PASS

## Non-goals

- no GUI work in this slice
- no release work in this slice
- no broad workflow rewrite in this slice

## Acceptance

- add a small CLI or ./ns-accessible preflight command
- add regression tests for YAML parse, coverage-term types, py_compile detection, final-summary validation, and unsupported shortcut patterns
- keep implementation small and deterministic
