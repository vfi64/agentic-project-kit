---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-086 — CI pin downgrade guard

## Observed
On 2026-10-22 a consumer workspace had CI pinned to Kit 1.1.5 while its local installed Kit remained at 1.1.4. Release preparation synchronized the older manifest and entrypoints, causing a downgrade in release artifacts.

## Defect and intended fix
A read-only numeric guard must compare the installed Kit version against exact workspace CI pins. Write-mode synchronization and release preparation must stop before modifications on downgrade. Preview synchronization stays nonblocking; kit update keeps its upgrade order.

## Evidence and verification
On 2026-10-25 the local feature gate reported 4068 passed and 26 failed. This does not constitute successful verification. Focused regressions, a greenfield machine retest and green PR CI are still required.

## Release target
Planned 1.1.6, category Fixed. No consumer-identifying material is included.

## KIT-GF-086 local gate follow-up (2026-10-25)

- `agentic-kit greenfield retest --id KIT-GF-086 --json`: PASS (step 125).
- `agentic-kit dev local-feature-gate`: FAIL (step 142): 26 failed, 4078 passed, 545 warnings; Ruff PASS. No named KIT-GF-086 tests failed.
- Gate remains blocking; no commit, push, PR, or release accepted as verified.
- Test-file comparison against HEAD: 13 unchanged, 0 altered among 13 failing test files. This does not establish the same tests fail on clean main.

### Local gate status (2026-10-25, step 146)
- `agentic-kit dev local-feature-gate`: **FAIL**; 4079 passed, 26 failed, 545 warnings.
- Ruff, project check and doctor: PASS. No named KIT-GF-086 regression failed.
- The 26 failed tests span existing test files unchanged from HEAD; this does **not** establish a passing baseline or waive the failures.
- Commit, push, PR, and DONE remain pending while the Kit gate is red.


## Codex takeover and review (2026-10-25)

PR #2633 is continued in an independent Git clone with an isolated Python 3.13
virtual environment, installed from this branch (version 1.1.5, candidate source
for planned 1.1.6). The consumer workspace and the stopped operator checkout were
not changed. No release was run.

The canonical Pages generator repaired three stale site projection files. The
initial isolated full suite then passed **4105 tests**, rc 0 (160.80 seconds).
All 26 tests listed in the original PR body also passed on clean `origin/main`
`27c1ac90b808969ba3b0207d003d28e911047162`, rc 0. This establishes the comparison;
it does not retrospectively claim a proven cause for the other environment's
failures. The stale projection is a demonstrated branch defect, now repaired.

Review corrections share one exact-pin expression between the guard and the CI
pin planner (text/bytes compiled from that expression). File read/decode failures
are explicit BLOCKED results, never skipped pins; their diagnostics expose only
workspace-relative paths and exception types. The helper has typed top-level
functions. A blocked release guard now returns before tag lookup, workspace or
summary preparation. Actual orchestration tests replace source-string tests:
release run stops at A3 through the real prepare guard, and kit update's callback
checks the installed runtime and both new pins before entrypoint writes.

### Classification of the original 26 tests

Every row below passed both the isolated repaired candidate and `origin/main`.
The fallback row was previously demonstrated failing on the original branch in
CI; it is classified as a repaired branch defect. No remaining failure was
attributable to this branch in the isolated comparison.

| Test | main | Candidate | Classification |
| --- | --- | --- | --- |
| `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_blocks_current_absolute_user_path` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_blocks_absolute_tmp_path` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_allows_test_fixture` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_absolute_path_portability_audit.py::test_render_absolute_path_audit_reports_counts` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_classifies_audit_patterns_as_implementation` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_blocks_source_path_even_with_historical_word` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_command_composition_audit.py::test_current_static_report_is_deterministic_and_complete` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_command_flow_analysis.py::test_current_source_reproduces_without_historical_commits` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_dpa_repo_adoption_assessment.py::test_dpa_repo_adoption_assessment_blocks_missing_exact_ref` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_dpa_repo_adoption_assessment.py::test_dpa_repo_adoption_assessment_cli_blocks_missing_ref_when_required` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_evidence_finalize_log.py::test_finalize_log_rejects_invalid_pass_remote_evidence` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_evidence_finalize_log.py::test_cli_finalize_log_invalid_pass_has_no_traceback` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_evidence_finalize_log.py::test_finalize_log_rejects_hidden_fail_before_final_pass` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_gui_cockpit.py::test_open_project_validates_git_and_updates_state` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_gui_state_signature.py::test_signature_fails_closed_without_a_repository` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_ns_legacy_external_evidence.py::test_installed_external_declared_ledger_and_active_script` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_ns_legacy_external_evidence.py::test_undeclared_external_output_matches_released_contract[released-1.0.24]` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_ns_legacy_external_evidence.py::test_kit_checkout_keeps_existing_context_lists` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_ns_legacy_reference_audit.py::test_audit_blocks_current_doc_instruction` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_ns_legacy_reference_audit.py::test_render_lists_blockers` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_ns_legacy_reference_audit.py::test_cli_command_raises_on_block` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_protection_mechanism_audit.py::test_explicit_invalid_consumer_fails` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_protection_mechanism_audit.py::test_kit_analysis_is_independent_of_optional_consumer` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_site_fallback_staleness.py::test_docs_pages_fallback_projection_is_fresh` | PASS | PASS | Branch defect: stale projection, fixed |
| `tests/test_transfer_startup_hardening_commands.py::test_static_meta_preference_projection_gate_blocks_yaml_json_projections` | PASS | PASS | Passes on both; original failure not reproduced |
| `tests/test_workspace_dpa_intake.py::test_workspace_dpa_intake_require_ready_blocks_missing_exact_ref` | PASS | PASS | Passes on both; original failure not reproduced |


### Final validation

The reviewed helper/CLI/orchestration/kit-update set passes **86 tests**, rc 0.
The release-content audit file passes **20 tests**, rc 0. Ruff passes, rc 0.
`agentic-kit greenfield retest --id KIT-GF-086 --json` reports PASS (1 PASS,
0 FAIL). `agentic-kit greenfield export --json` reports PASS with no changed
paths, confirming both generated finding-status copies and the retest index
already match their canonical catalog; none was hand-edited.

A control run against an independently installed **released** 1.1.5 was not run:
no verified released 1.1.5 environment is available in this working environment.
The candidate identifies as 1.1.5 because 1.1.6 is only a planned release; it is
not used to claim that the historical released package passes this regression.
The final full suite on correction commit `6d3fb0ab` passes **4114 tests**,
rc 0, 148.08 seconds (545 existing warnings). All 26 named tests pass there too.
The previous failed-gate statements above are retained historical observations,
superseded by this isolated comparison and reviewed-candidate validation.

| Check | Command | Result |
| --- | --- | --- |
| Focused helper, CLI, release and update tests | `python -m pytest -q tests/test_kit_ci_pin_guard.py tests/test_kit_ci_pin_guard_cli.py tests/test_kit_ci_pin_guard_release.py tests/test_kit_ci_pin_guard_orchestration.py tests/test_kit_update.py` | 86 passed, rc 0 |
| Release-content audits | `python -m pytest -q tests/test_release_content_audits_on_checkout.py` | 20 passed, rc 0 |
| Full candidate suite | `python -m pytest -q -n 4 --dist worksteal` | 4114 passed, rc 0 |
| Baseline comparison | The 26 exact node IDs in the table, on origin/main | 26 passed, rc 0 |
| Machine contract | `agentic-kit greenfield retest --id KIT-GF-086 --json` | PASS, rc 0 |
| Catalog projections | `agentic-kit greenfield export --json` | PASS, changed_paths empty |
| Canonical site projection | `python site/scripts/build.py --docs-pages-fallback --json` | PASS, no blockers |
| Lint | `ruff check --no-cache .` | PASS, rc 0 |
| Documentation | `agentic-kit check-docs` | PASS, rc 0 |
| Repository health | `agentic-kit doctor` | PASS, rc 0; existing lifecycle advisories |

Only validation prose and generated successor projections follow the tested code
commit. The final PR head is additionally checked by remote CI before merging.
The initial PR body's stop/validation notes describe the earlier operator run;
the owner's 2026-10-25 takeover decision authorizes completion. They were not
rewritten through a raw GitHub mutation: the installed manifest has no PR-edit
route. This report contains the current comparison and validation evidence.
The Kit finding remains CLOSED for planned 1.1.6; independent consumer verification
and a release are not implied by these candidate tests.
