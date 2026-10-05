# KIT-GF-047 — End-to-end release run orchestrator

Source: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` at commit `4238af005d01a3b81251aea2cad916c26b05f46f`.

## Finding

GF-047 observed that a public Kit-style release required many owner-driven commands and hand-copied values: release readiness, release preparation, branch start, work finish, signed release publishing, package-index publication, post-release checks, DOI closeout, and final release status. The local agp-Cockpit workaround was an unversioned runner script with resumable state.

## Fix

The Kit now exposes `agentic-kit release run --version X` as a resumable release lifecycle orchestrator. It composes existing commands instead of adding new release mechanics:

- `transfer sync-main`
- `release ready`
- `release prepare`
- `work start`
- `work finish`
- `release-publish`
- configured package-index workflow dispatch/watch
- `post-release-check`
- `post-release-doi-closeout`
- final `release-status --include-remote`

The command records state, per-step JSON, and subprocess logs under the workspace temp root. It resumes at the first unfinished step.

Signed approval gates:

- B4: execute `work finish` for the release metadata branch.
- C2: execute signed `release-publish`.
- C3: dispatch and watch the configured package-index workflow.
- D4: execute `work finish` for the DOI closeout branch.

A stale or wrong release-run signature blocks before the gated effect. The command stores B3/D3 path lists and blocks if they drift before B4/D4. It stores C3 dispatch state and blocks rather than dispatching again if a prior dispatch has no run id.

For `publication: none`, package-index publication, Zenodo wait, and the DOI phase are skipped.

## Regression coverage

- `tests/test_release_run.py::test_release_run_stops_at_b4_then_executes_matching_gate_to_c2`
- `tests/test_release_run.py::test_release_run_wrong_signature_blocks_without_execute_call`
- `tests/test_release_run.py::test_release_run_blocks_on_orchestrator_status_even_with_zero_returncode`
- `tests/test_release_run.py::test_release_run_blocks_when_paths_change_between_b3_and_b4`
- `tests/test_release_run.py::test_release_run_resume_state_starts_at_b4`
- `tests/test_release_run.py::test_release_run_recorded_c3_dispatch_without_run_id_blocks_without_redispatch`
- `tests/test_release_run.py::test_release_run_publication_none_skips_package_index_zenodo_and_doi_phase`

## Remote effect classification

The command has remote release effects only when an approved gate executes an underlying command that already has that effect:

- B4/D4 delegate to `work finish --execute`.
- C2 delegates to signed `release-publish --execute`.
- C3 delegates to the configured package-index workflow.

The default run stops before each gate with `AWAITING_APPROVAL`.

