# Post-0.5.0 v1.0 Schema and Neutral External Validation

Date: 2026-08-13
Branch: `codex/v1-schema-readiness`
Base main: `3539e52c`
Status: PASS with remote-CI limitation

## Scope

This report closes the next post-A/B/C readiness slice:

- update the canonical planning state after PR #2078;
- clarify `check`/`doctor` External-Mode semantics;
- implement a real workspace manifest schema bump;
- validate a neutral external repository beyond Comm-SCI;
- exercise a controlled remote adoption PR;
- harden `workspace remove` based on the neutral probe.

## Schema Readiness

Implemented:

- `SUPPORTED_MANIFEST_SCHEMA_VERSION = 2`;
- v1 manifests remain loadable for compatibility;
- v2 manifests require an explicit `hygiene` mapping;
- `workspace init` and `workspace adopt` now emit v2 manifests with hygiene
  defaults;
- `workspace upgrade` has a real v1 to v2 migration that materializes
  `hygiene.doc_lifecycle` and `hygiene.review_budgets`;
- too-old and too-new loader boundaries are covered by tests.

Evidence:

- `tests/test_workspace_foundation.py`
- `tests/test_workspace_upgrade.py`
- `tests/test_workspace_init.py`
- CLI smoke: v1 manifest upgraded to v2, `check-docs` PASS, `doctor` Overall PASS.

The schema work is no longer a simulated v0->v1 fixture. It is a real v1->v2
manifest transformation with dry-run diff, backup, execute, and final
load-validation behavior.

## External-Mode Semantics

Clarified:

- `check` and `check-docs` are error-list gates with zero/non-zero exits;
- `doctor` is the command that renders `PASS`, `FAIL`, `WARN`, and `SKIP`;
- `SKIP` is used for not-applicable Kit checks in external manifest workspaces;
- Kit-specific version drift remains project-owned release governance.

This resolves the ambiguity found during external review: `checks.py` loads the
manifest workspace and uses external state-gate documents, but it does not render
doctor-style statuses.

## Neutral External Repository

Rejected candidate:

- `vfi64/wrapper` was inspected but rejected as neutral evidence because the repo
  still carries Comm-SCI lineage and content.

Selected candidate:

- Source: `pypa/sampleproject`
- Controlled fork: `vfi64/sampleproject`
- Local clone path: temporary `/tmp/agentic-kit-neutral-sampleproject.*`
- Probe branch: `codex/agentic-kit-adoption-probe-20260813`

Local lifecycle evidence:

- `workspace dpa-intake`: PASS, read-only;
- `workspace adopt`: PASS, read-only;
- `workspace init` dry-run: PASS;
- `workspace init --execute`: PASS;
- `workspace upgrade`: PASS, already at schema v2 after init;
- `check-docs --root`: PASS;
- `check --root`: PASS;
- `doctor --root`: Overall PASS with external-workspace SKIPs;
- `transfer chat-switch-complete --render-prompt`: PASS;
- `workspace remove`: initially BLOCKED after handoff package generation;
- `workspace remove` after hardening: PASS;
- second `workspace init --execute`: PASS;
- target-owned native tests in a separate temporary venv: `1 passed`.

Observed defect and fix:

`workspace remove` did not classify external successor handoff package files as
Kit-generated runtime files. After `transfer chat-switch-complete`, removal
blocked on generated prompt/package files. The fix adds signaturized recognition
for known successor package and chat-switch prompt files while preserving blockers
for unknown or invalid `.agentic/` content.

## Remote PR Probe

Remote PR:

- URL: `https://github.com/vfi64/sampleproject/pull/1`
- Head branch: `codex/agentic-kit-adoption-probe-20260813`
- Head SHA: `1a6d0815fb062702f86a625fb0f8d39f9497b774`
- Merge state: CLEAN
- State after evidence capture: closed
- Remote branch: deleted after close

Result:

- Branch push: PASS
- PR creation: PASS
- PR metadata read: PASS
- GitHub checks: no checks reported on the branch
- PR closeout: PASS

The remote mechanics are exercised in a controlled fork without opening noise on
upstream `pypa/sampleproject`. Because the target fork has no CI, this evidence
does not claim remote target-CI validation. It records the limitation explicitly.

## 1.0 Readiness Impact

The four existing `v1-0-milestone` acceptance criteria now have direct evidence:

1. Self-hosting litmus passed in prior A/B/C closeout.
2. `workspace adopt/init` is stable on at least one real external project
   (Comm-SCI) and now additionally on neutral `sampleproject`.
3. Too-old and too-new `kit_schema_version` failure paths are tested.
4. A tested `workspace upgrade` transformation exists with the first real schema
   bump.

This is readiness evidence, not a release action. Version bump, tag, release
publication, DOI publication, and GUI work remain maintainer-owned follow-ups.

## Gates

Gates run for this slice:

- `pytest -q tests/test_workspace_upgrade.py tests/test_workspace_foundation.py tests/test_workspace_init.py tests/test_workspace_adopt.py tests/test_checks.py tests/test_doctor.py`: 106 passed.
- `pytest -q tests/test_workspace_remove.py tests/test_successor_handoff_package.py::test_external_workspace_successor_handoff_package_uses_operating_layer_paths`: 8 passed.
- `pytest -q tests/test_site_generator.py tests/test_release_metadata_authority_gate.py`: 19 passed.
- `pytest -q tests/test_th1_negative_path_hardening.py::test_th1_workspace_upgrade_unknown_field_type_is_structured_failure tests/test_workspace_upgrade.py`: 8 passed.
- `pytest -q`: 2810 passed, 630 warnings.
- `ruff check .`: PASS.
- `agentic-kit direction validate --root .`: PASS.
- `agentic-kit check-docs`: PASS.
- `agentic-kit docs-registry`: PASS.
- `agentic-kit doctor`: Overall PASS.
- site docs-pages fallback build: PASS.
- `agentic-kit transfer protected-diff-plan --label v1-schema-readiness`: PASS.
- `git diff --check`: PASS.

PR lifecycle gates remain required for the repository PR closeout.
