# Successor Chat Handoff After PR706

## 1. Working Environment

Repo: `vfi64/agentic-project-kit`
Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Current Main State

Current main commit: `8c619e8`
Subject: `Guard successor handoff prompt freshness (#706)`
Current version: `0.4.1`
Tag: `v0.4.1`
Verified Zenodo version DOI: `10.5281/zenodo.20357657`

PR #706 is merged and added the canonical successor handoff freshness guard.

## 3. Mandatory Startup Rule

Do not start from chat memory. Read the repository sources first, especially:

- `.agentic/compiled_agent_context.yaml`
- `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `.agentic/handoff_state.yaml`
- `docs/TEST_GATES.md`
- relevant source files and tests for the requested slice

## 4. Important Freshness Note

The freshness guard now exists in the canonical path `agentic-kit handoff prompt` and must be respected. If it warns that status, handoff state, current handoff, or latest successor prompt are stale, treat that as drift and do not continue product work except to repair the drift.

This prompt itself is current for `8c619e8`.

## 5. What PR706 Changed

PR #706 added:

- `src/agentic_project_kit/handoff_freshness.py`
- warning output in `agentic-kit handoff prompt`
- `docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md`
- compiled context anchors for `successor-handoff-freshness-guard`
- regression tests for the old stale successor prompt failure pattern

The guard is warning-based, not fail-closed, so a drifted repository can still produce a repairable prompt.

## 6. Current Planning Direction

Continue the documentation-management rebuild only after the handoff freshness state is current.

Recommended next substantive slice:

1. Artifact-GC registry planning or a narrow read-only Artifact-GC/registry consumer.
2. Keep the slice additive, reversible, and test-backed.
3. Do not start broad documentation migration.
4. Do not create a tag or release.
5. Do not expand Pattern Advisor yet.

## 7. Known Risk From This Closeout

This prompt was written remotely. If `.agentic/handoff_state.yaml`, `docs/STATUS.md`, or `docs/handoff/CURRENT_HANDOFF.md` still point to an older main commit, the new guard should warn. That warning is correct and must be repaired before new product work.

## 8. Communication Rules

User short replies are signals, not evidence:

- `d`/`D`: verify evidence before continuing.
- `f`/`F`: inspect or upload evidence before asking for pasted output.
- `w`/`W`: continue within the current rules.
- `p`: log-backed PASS accepted.

Final outputs must use the canonical SUMMARY vocabulary and never print `REMOTE_EVIDENCE: PENDING`.
