# Übergabeprompt

Wir arbeiten im Repo `vfi64/agentic-project-kit`.

Nicht aus Chat-Erinnerung starten. Lies zuerst die repo-basierten Pflichtquellen in dieser Reihenfolge:

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. `.agentic/handoff_state.yaml`
10. `AGENTS.md`
11. `CHANGELOG.md`
12. `README.md`
13. `CITATION.cff`
14. `docs/releases/VERIFIED_RELEASES.md`

## Aktueller verifizierter Stand vor Chat-Wechsel

- Current release: `0.4.1` / tag `v0.4.1`.
- Zenodo concept DOI: `10.5281/zenodo.20101359`.
- Verified Zenodo version DOI: `10.5281/zenodo.20357657`.
- Last substantive safe/admin state for this handoff: `ef43055 Add artifact policy registry consumer (#709)`.
- PR #709 exposed `.agentic/communication_artifacts.yaml` through the read-only documentation registry summary and JSON report.
- PR #709 did not change cleanup behavior, release metadata, tags, DOI metadata, GUI actions, or destructive workflows.
- The documentation-management rebuild is roughly 40-43 percent complete.

## Freshness and loop guard

Before treating this prompt as authoritative, run or inspect the successor handoff freshness guard. The relevant expected commit marker is `ef43055`.

Important: a pure administrative handoff refresh merge after this prompt must not create an endless refresh loop. The guard may accept an administrative refresh commit when the prompt names the last substantive safe/admin state. Non-administrative commits after `ef43055` still require a state/prompt refresh.

## Current documentation-registry state

- Machine-readable registry: `docs/DOCUMENTATION_REGISTRY.yaml`.
- Registry contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
- Read-only summary: `agentic-kit docs-registry`.
- Read-only JSON report: `agentic-kit docs-registry --report PATH`.
- Registry visibility exists in `check-docs`, `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.
- Artifact policy source consumed by the registry summary: `.agentic/communication_artifacts.yaml`.
- Broad migration remains forbidden. The registry guard is structural only and does not prove semantic documentation quality.

## Current GUI baseline

- `cockpit-readiness` visually passes as a bounded read-only GUI action.
- `doctor` visually passes as a bounded read-only GUI action.
- `check-docs` visually passes as a bounded read-only GUI action.
- `agent-run` and non-read-only GUI actions remain disabled in the GUI MVP.
- The future Tkinter cockpit must be a thin presentation layer over registry actions and machine-readable results.

## Active workflow rules

- Start from repo state, not memory.
- Do not mutate before reading the mandatory sources.
- Treat `d`, `f`, `w`, and `p` as communication signals, not evidence.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Recurring workflow failures must become documented, test-backed guards.
- Keep registry slices small, additive, reversible, and test-backed.
- No broad documentation migration yet.
- No release, tag, DOI change, destructive GUI action, or remote/destructive GUI action.

## Required gate set for current-state or handoff changes

Use project-local tooling first:

- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns docs-audit`
- `./ns dev`
- `agentic-kit check-docs`
- `agentic-kit doctor`
- `agentic-kit post-release-check --version 0.4.1`

Remote-only work may rely on equivalent GitHub CI evidence when local Python gates are unavailable.

## Erste Arbeitsanweisung

Verify the post-PR709 successor handoff prompt and freshness guard. Then continue the documentation-management rebuild with one small, additive, reversible, test-backed registry slice, preferably toward machine-readable source/projection planning.

Do not start a broad migration, release, tag, DOI update, or destructive GUI action.

================================================================
SUMMARY
WORK RESULT: PASS
EVIDENCE RESULT: PASS
OVERALL RESULT: PASS
REMOTE_EVIDENCE: PASS
terminal_log=NONE
command_report=NONE
NEXT_CHAT_REPLY: p
### RESULT: PASS ###
================================================================
