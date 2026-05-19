Current version: 0.3.27

# Project Status

Status-date: 2026-05-18
Project: agentic-project-kit
Primary branch: main
Current work branch: main

## Purpose

agentic-project-kit generates agent-friendly project skeletons with documentation, GitHub workflow templates, task tracking, test gates, handoff files, release-state validation, citation metadata, Zenodo-backed archival, project-health diagnostics, architecture-contract governance, documentation coverage checks, generated project contracts, project profiles, policy packs, policy-pack doctor checks, deterministic document-quality heuristics, output-contract validation, bounded structural repair, workflow evidence capture, documentation-mesh drift auditing, document lifecycle auditing, local cockpit action inspection, repo-backed command execution, terminal evidence preservation, and deterministic workflow governance.

The project treats the repository, not the chat transcript, as the durable source of truth for current state, gates, handoff, evidence, rules, and release metadata. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current Goal

The immediate goal is rule-governance and evidence-governance stabilization before any GUI, release-automation, or new feature work. The current priority is to eliminate recurring workflow failures by making evidence preservation, interpreter discovery, dirty-state handling, and handoff/state refresh deterministic and test-backed.

## Current State

Current released version: 0.3.26
Current completed slice: remote mutation dirty-state preflight guard and PR #399/#400 verification

v0.3.26 is the current released and verified version recorded in project metadata. Recent work after v0.3.26 focused on rule and evidence governance rather than new user-facing features.

Recent completed governance work:

- PR #387 added an interpreter discovery failure guard.
- PR #390 added ns interpreter discovery and no-exec guard coverage.
- PR #391 added the test-backed rule governance contract.
- PR #392 preserved the rule governance verification log.
- PR #393 preserved clean main verification after local branch cleanup.
- PR #394 prepared v0.3.26 release metadata.
- PR #395 preserved the v0.3.26 publish terminal log.
- PR #396 preserved the PR #395 merge verification log.
- PR #397 preserved sync diagnosis for rule/evidence governance.
- PR #398 preserved failure evidence from a dirty-state local PR #397 merge-verification attempt.
- PR #399 added `./ns terminal-remote-preflight` and a test-backed remote mutation dirty-state guard.
- PR #400 preserved the PR #399 merge verification log.

## Active Workflow Rules

- Use project-local interpreter/tooling first. Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv` exist.
- Prefer `.venv/bin/python -m pytest -q`, `.venv/bin/ruff check .`, and `PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli ...` when running gates directly.
- Use `./ns terminal-remote-preflight` before remote mutation, merge verification, release publication, tag creation, or branch-switching/sync workflows that must start from a clean tree.
- Use `./ns terminal-finalize` to preserve relevant terminal output under `docs/reports/terminal/*.log` and update `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`.
- PASS and FAIL evidence must be remote-readable whenever technically possible. If evidence is not remote-readable, treat that as a workflow bug.
- Larger terminal workflows must begin with three separator lines and end with `### RESULT: PASS ###`, `### RESULT: FAIL ###`, or `### RESULT: PENDING ###`.
- Avoid heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, and shell constructs likely to leave `quote>`, `dquote>`, or `heredoc>` prompts.

## Gate Status

Latest verified gate evidence after PR #399 merge and before PR #400:

- `./ns terminal-remote-preflight`: PASS
- `./ns handoff-check`: PASS
- `./ns governance-check`: PASS
- `./ns dev`: PASS
- pytest: 395 passed
- ruff: PASS
- check-docs: PASS
- doctor: PASS; version drift check reports project state matches version 0.3.26

Latest terminal evidence pointer: `docs/reports/terminal/20260518-210113_pr399-merge-verification.log`.

## Next Safe Step

After this STATUS/HANDOFF refresh is merged and verified, continue rule/evidence-governance cleanup only if gates reveal remaining drift. Do not start GUI or release-automation expansion until the state files, evidence path, and rule lifecycle are clean and current.

Recommended next implementation candidate after this refresh: add a deterministic guard that detects stale accumulated STATUS/HANDOFF historical fragments so this drift cannot silently recur.

## Live Status Commands

Run these from the repository root with project-local tooling:

```bash
git status --short
git branch --show-current
./ns terminal-remote-preflight
./ns handoff-check
./ns governance-check
./ns dev
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli check-docs
PYTHONPATH=src .venv/bin/python -m agentic_project_kit.cli doctor
```

The equivalent public command names remain `agentic-kit check-docs` and `agentic-kit doctor`; the project-local module form is preferred when global executables are not guaranteed.

## Documentation Coverage Notes

`docs/DOCUMENTATION_COVERAGE.yaml` is the documentation coverage source for required terms and state-doc coverage. `agentic-kit check-docs` and `agentic-kit doctor` enforce this coverage through deterministic gates.

Pattern Advisor remains an advisory-only, read-only catalog. The current coverage terms intentionally preserve that it exposes `patterns list` and `patterns show` style inspection, but it is not an autopilot, not a gate, and not an automatic architecture decision layer.

Release verification remains covered by the post-release Zenodo path and `agentic-kit post-release-check` after publication. The current Zenodo concept DOI remains `10.5281/zenodo.20101359`.

## No-Copy Workflow Status

As of PR #423, the repo-backed no-copy workflow is the active bridge toward the local GUI. Remote tasks are queued under `.agentic/commands/inbox/`, local execution runs through `./ns agent-next`, and durable evidence is written under `docs/reports/command_runs/` and `docs/reports/terminal/`. The current hardening includes command-run pointers, terminal-log pointers, result-footers for `p`/`f`/paste-output decisions, missing-current-script report robustness, inner fail-marker detection, communication artifact garbage collection, and `./ns command-inbox-check` rejecting completed command ids that remain pending.

The next planned release is `v0.3.27`, intended to preserve this no-copy/runner-hardening baseline before the first local GUI slice. After that release, the next feature direction is a thin local Tkinter cockpit over `git pull && ./ns agent-next`, status display, latest command-run report, latest terminal log, and gate buttons. Pattern work is intentionally deferred until after the GUI foundation.
