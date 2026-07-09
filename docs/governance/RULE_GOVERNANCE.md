Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Rule Governance

## Purpose

This document prevents workflow rules from existing only as chat memory.

## Contract

A durable workflow rule is complete only when all of the following are true:

- The rule has a stable rule id.
- The rule has a stable repository location.
- The rule is documented in a workflow document or a project contract file.
- The rule is protected by at least one deterministic test.
- The test fails if the rule id, documentation, or implementation guard disappears.
- The rule is not treated as complete when it only appears in chat, a handoff prompt, or temporary terminal output.

## Current rule id

- `rules-must-be-test-backed`

## Consequence

A new workflow rule is not done until the repository contains the rule, its documentation, and a regression test. This includes terminal-handoff rules such as always making PASS and FAIL output remotely available.
