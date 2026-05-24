<!-- post-pr714-closeout -->
# Current Handoff

Status-date: 2026-05-24
Project: agentic-project-kit
Branch: main
Base branch: main
Current version: 0.4.1

## Purpose

This file is the concise current handoff pointer. It is not the long-term project history and must not duplicate full rule books. Long-term history belongs in `CHANGELOG.md`, release records, architecture/governance contracts, or committed terminal evidence.

## Current State

- Current released version: 0.4.1.
- Current release tag: v0.4.1.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
- Main is refreshed after PR #714 at `7d092cb` (`Add workflow guard diagnostics (#714)`).
- PR #714 completed workflow-guard diagnostics, patch-preflight integration, protected-control-file preservation coverage, and removal of hard word limits from protected control files.
- Evidence: `docs/reports/terminal/pr714-verify-after-test-alignment.log`.

## Current Baselines

Documentation registry:
- Machine-readable registry: `docs/DOCUMENTATION_REGISTRY.yaml`.
- Human contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
- Read-only summary: `agentic-kit docs-registry`.
- JSON report: `agentic-kit docs-registry --report PATH`.
- Registry data is visible in `check-docs`, `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.
- Broad documentation migration is forbidden. The registry guard is structural only and does not prove semantic documentation quality.

Workflow hardening:
- GitHub connector direct-path-first is mandatory for known repository paths, refs, PRs, and commits.
- Governance YAML mutation must use parse-modify-dump or an equivalent structured mutation path, then parse again.
- `.agentic/control_file_preservation.yaml` protects active rules from lossy shortening.
- Information preservation outranks compactness for protected control files.

GUI MVP:
- `cockpit-readiness`, `doctor`, and `check-docs` visually pass as bounded read-only GUI actions.
- `agent-run` and non-read-only actions remain disabled in the GUI MVP.
- Headless GUI action execution tests cover the bounded read-only action executor.

## Mandatory Successor-Chat Sources

Read these before mutation, in this order:
1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`

## Active Rules For The Next Chat Or Slice

- Start from repo state, not memory.
- Verify branch, status, log, open PRs, latest terminal log, handoff state, interpreter/tooling state, and gates before patching.
- Keep state documents curated. Do not append new current-state fragments below obsolete ones.
- Do not assume global `python`, `python3`, `agentic-kit`, `ruff`, `pytest`, or `.venv`.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- `d`, `f`, `w`, and `p` are communication signals, not evidence.
- Do not use heredocs, top-level `exit`, top-level `exec`, risky multiline `python -c`, or quote-prone shell constructs in chat-pasted terminal blocks.
- Larger terminal blocks must begin with three long separator lines and end with a structured SUMMARY block.
- Relevant workflow blocks must render the mandatory final SUMMARY through the canonical renderer route. Legacy handmade `WORK RESULT:` / `NEXT_CHAT_REPLY:` summaries are drift.
- Use `NEXT` / `CHAT_REPLY: d` only when the work and evidence are actually successful. Use `CHAT_REPLY: f` for log-backed failure and `CHAT_REPLY: paste-output` only when remote/local evidence is unavailable or unusable.
- Remote log lookup must direct-fetch the named `docs/reports/terminal/*.log` path before asking the user to paste output.
- New recurring workflow problems must become rules, failure patterns, tests, or tooling.

## Required Local Gate

Before merge or handoff, run:

```bash
./ns state-freshness-check
./ns handoff-check
./ns governance-check
./ns docs-audit
./ns dev
```

Before any remote mutation, merge verification, release publication, tag creation, or clean-tree sync workflow, additionally run `./ns terminal-remote-preflight`.

## Next Safe Step

Repair PR715 first and verify that the post-PR714 closeout state, handoff state, current handoff, and successor prompt are consistent with PR714 rather than PR712.

After PR715 is green and merged, the next immediate hardening slice is structured final-summary enforcement. Do not resume documentation-management registry/projection work until this drift is closed.

## Source of Truth

The repository is the source of truth, not the chat transcript. Current state is maintained through `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, `docs/TEST_GATES.md`, `docs/DOCUMENTATION_COVERAGE.yaml`, `.agentic/project.yaml`, `sentinel.yaml`, governance contracts, and committed terminal evidence under `docs/reports/terminal/`.

## Compatibility Coverage Anchors

These compact anchors are intentionally retained for deterministic coverage: documentation coverage, policy-pack checks, policy packs, Pattern Advisor, `patterns list`, `patterns show`, no-copy/evidence, Communication artifact GC hardening is now part of the pre-GUI baseline, long chat-generated shell or Python patch blocks, v0.3.31 is the current pre-GUI execution hardening line., Mandatory Final Summary Contract, policy-pack doctor checks, `agentic-kit post-release-check`, `.agentic/compiled_agent_context.yaml`, `CHAT_COMMUNICATION_CONTRACT.md`, `PORTABLE_CHAT_EXECUTION_CONTRACT.md`, `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`, `FINAL_SUMMARY_CONTRACT.md`, `docs/TEST_GATES.md`, planning-state freshness, post-release Zenodo, docs/DOCUMENTATION_COVERAGE.yaml, docs/DOCUMENTATION_REGISTRY.yaml, Current released version: 0.3.29, Current released version: 0.3.32, PR #650 merged, PR #651 merged, PR #652 merged.
