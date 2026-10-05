# KIT-GF-030 / KIT-GF-031 — PR lifecycle duplicate prevention and existing-PR completion

Source findings: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (`KIT-GF-030`, `KIT-GF-031`, and related `KIT-GF-017`), read from `origin/main` commit `c042a042d6d51dc3daa41b26ac0ffb1457987de4`.

## Finding summary

- `KIT-GF-030`: after a branch was squash-merged, a repeated `transfer pr-create-complete` could open a second PR with no content difference and run CI for an empty change.
- `KIT-GF-031`: `transfer pr-complete --post-merge-complete` was rejected even though the existing-PR lifecycle already runs `post-merge-complete`; `pr-complete` could also stop on missing fresh LLM-context carriers instead of refreshing them.
- Related `KIT-GF-017`: direct safe-merge routes could stop on missing fresh LLM-context carriers in external workspaces.

## Kit repair

- Added `transfer_pr_branch_state.detect_branch_no_content_diff`, an importable helper that compares the resolved base ref with the head tree and, when there is no content diff, looks up the latest merged PR for that head/base pair.
- `transfer pr-create` and `transfer pr-create-complete` now report an already-done result instead of creating a PR when the head has no content diff against the base. `pr-create-complete` stops before PR creation, CI waiting, or merge orchestration.
- `transfer pr-complete --post-merge-complete` is now accepted as a compatibility flag. The command records `post_merge_complete_requested` and continues through its normal post-merge-complete step.
- `transfer pr-complete` and `transfer pr-merge-safe` now use the existing fresh-context auto-refresh helper before enforcing the LLM-context gate.
- Regenerated `docs/reference/AGENTIC_KIT_COMMANDS.md`, `docs/reference/agentic-kit-commands.json`, and packaged command reference data.

## Regression coverage

- `test_transfer_pr_create_complete_reports_done_when_head_has_no_base_diff` proves that a squash-merged/no-diff branch opens no PR and runs no CI/complete step.
- `test_transfer_pr_complete_accepts_post_merge_complete_flag` proves that the existing-PR orchestrator accepts `--post-merge-complete` and still runs the post-merge-complete lifecycle.
- Updated LLM-context gate tests prove `pr-complete` and `pr-merge-safe` refresh missing context carriers instead of stopping at `TRANSFER_REQUIRE_FRESH_LLM_CONTEXT`.

## Validation

Initial targeted validation:

```text
.venv/bin/python -m pytest tests/test_transfer_pr_complete_command_contract.py tests/test_transfer_llm_context_gate.py tests/test_pr_create_complete_auto_preflight.py -q
41 passed, 21 warnings
```

Final local gates:

```text
.venv/bin/python -m pytest tests/test_transfer_pr_complete_command_contract.py tests/test_transfer_llm_context_gate.py tests/test_pr_create_complete_auto_preflight.py tests/test_command_manifest.py tests/test_llm_execution_context.py tests/test_transfer_fresh_llm_context.py -q
71 passed, 33 warnings

.venv/bin/agentic-kit check-docs
PASS

.venv/bin/agentic-kit doctor
PASS (document lifecycle audit warnings are report-only)

.venv/bin/ruff check .
PASS

.venv/bin/python -m pytest -q
3118 passed, 497 warnings
```

## Boundary

The Cockpit ledger was not changed. `VERIFIED_FIXED` remains reserved for the external workspace after its own retest.
