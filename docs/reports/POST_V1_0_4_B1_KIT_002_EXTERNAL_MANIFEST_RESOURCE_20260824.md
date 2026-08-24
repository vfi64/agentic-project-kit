# Post-v1.0.4 B1-KIT-002 External Manifest Resource Fix

Status: implemented_retest_pass  
Status date: 2026-08-24  
Kit branch: `codex/fix-external-command-manifest-resource`  
Finding source: `B1-COMM-SCI-20260824-001`  
Target finding: `B1-KIT-002`

## Scope

This slice fixes the B1 finding that installed Kit commands failed in an
external workspace when the target repository did not contain
`docs/reference/agentic-kit-commands.json`.

The target behavior is:

- Kit-internal files such as the command manifest are packaged with the Kit and
  do not need to be supplied by the foreign repository owner.
- External workspaces can run manifest-dependent Kit commands from an installed
  wheel without a repo-local `docs/reference/` tree.
- The Kit development checkout still uses strict repo-local manifest auditing,
  so package fallback cannot hide command-reference drift.
- Target-repository decisions remain project-owned and must be asked,
  blocked, skipped, or warned explicitly.

## Implementation

Implemented changes:

- added packaged command-reference resources under
  `src/agentic_project_kit/reference/`;
- changed `command_manifest.load_manifest()` to load the repo-local manifest
  when present and fall back to the packaged manifest when absent;
- preserved strict self-hosting audit with
  `allow_package_fallback=False` inside `evaluate_command_manifest()`;
- added a source-checkout package-resource drift check to
  `audit-command-manifest`;
- changed command taxonomy loading to use the same manifest loader;
- updated `commands sync-entrypoints` so the packaged source resource is kept
  synchronized in Kit source checkouts without creating Kit source directories
  in external repositories;
- added external-workspace Doctor behavior: `doctor` reports
  `command manifest` as `WARN` when the repo-local source audit is skipped but
  the packaged command manifest is available.

## Tests

Added regression coverage:

- `tests/test_command_manifest.py`
  - package fallback loads a manifest in an external tmp workspace;
  - strict manifest loading still fails without repo-local docs;
  - source package-resource drift is detected by manifest audit.
- `tests/test_command_selector.py`
  - `agentic-kit command-for --root TMP --raw "git push origin main" --json`
    works without `docs/reference/`.
- `tests/test_command_taxonomy.py`
  - taxonomy report works without `docs/reference/`.
- `tests/test_doctor.py`
  - external workspace Doctor emits `command manifest` WARN with packaged
    manifest evidence.
- `tests/test_chat_entrypoint_contract.py`
  - sync-entrypoints does not create the Kit source package path in a
    non-source external root.

Focused evidence:

- `python -m pytest -q tests/test_doctor.py tests/test_command_manifest.py tests/test_command_selector.py tests/test_command_taxonomy.py tests/test_chat_entrypoint_contract.py`
  passed: 70 passed.
- `agentic-kit audit-command-manifest` passed with
  `STATUS=PASS`, `FINDING_COUNT=0`, `BLOCKER_COUNT=0`.

Full local gate evidence:

- `ruff check .` passed.
- `python -m pytest -q` passed: 2872 passed, 466 warnings.
- `agentic-kit check-docs` passed.
- `agentic-kit doctor` passed overall; the existing document lifecycle audit
  remains WARN/report-only.
- `agentic-kit command-taxonomy-check` passed.
- `agentic-kit direction validate` passed.
- `agentic-kit docs-audit` passed overall.

## Packaging Evidence

A local wheel and sdist were built from the fixed branch:

- `/tmp/agentic-kit-b1kit002-dist2/agentic_project_kit-1.0.4-py3-none-any.whl`;
- `/tmp/agentic-kit-b1kit002-dist2/agentic_project_kit-1.0.4.tar.gz`.

Wheel inspection confirmed these packaged resources:

- `agentic_project_kit/reference/__init__.py`;
- `agentic_project_kit/reference/agentic-kit-commands.json`.

Fresh installed-wheel smoke tests passed in
`/tmp/agentic-kit-b1kit002-final-venv`:

- `agentic-kit command-for --root /tmp --raw "git push origin main" --json`
  returned `status: match` and mapped to
  `agentic-kit transfer push-current`;
- `agentic-kit command-for --root /tmp --raw "agentic-kit doctor" --json`
  returned `status: no_match` without raising `FileNotFoundError`;
- `agentic-kit command-taxonomy-check --root /tmp` returned
  `STATUS=PASS` with 254 commands.

## Comm-SCI Retest

Retest target:

- repository: `vfi64/Comm-SCI-Control-private`;
- local path:
  `/Users/hof/Library/CloudStorage/Dropbox/Privat/GitHub/Comm-SCI-Control-private`;
- branch: `codex/b1-modularize-comm-sci-app2`;
- Kit runtime: fresh local wheel install from this branch.

Read-only retest results:

- `agentic-kit command-for --root . --raw "git push origin main" --json`
  returned `status: match`, `matched_prefix: git push`, command
  `agentic-kit transfer push-current`;
- `agentic-kit command-for --root . --raw "agentic-kit doctor" --json`
  returned `status: no_match` without crashing;
- `agentic-kit command-taxonomy-check --root .` returned `STATUS=PASS`;
- `agentic-kit doctor --root .` returned Overall PASS and explicitly reported:
  `command manifest: WARN ... packaged command manifest available (254 commands;
  manifest_sha: 2ab1c7c2a951)`;
- `agentic-kit check-docs --root .` passed.

The Comm-SCI worktree had the same pre-existing dirty state before and after the
retest:

- modified `Logs/*` files;
- untracked generated `.agentic/state/handoff/...` files from the earlier B1
  handoff cycle.

No additional Comm-SCI files were changed by this retest.

## Decision

`B1-KIT-002` is fixed in the Kit branch and validated against both a fresh
installed-wheel simulation and the real Comm-SCI external workspace.

Doctor external behavior is resolved as follows: external workspaces receive a
`WARN` line for `command manifest` when the repo-local source audit is not
available, while still confirming that the packaged manifest is present and
usable. This avoids a false implication that source-checkout manifest audit ran
inside the target repository.

The next B1 work should resume with additional real Comm-SCI cycles after this
Kit fix is merged and released in the next package version.
