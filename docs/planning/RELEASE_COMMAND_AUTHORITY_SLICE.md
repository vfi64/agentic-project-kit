# Release Command Authority Slice

Status-date: 2026-06-18
Status: active
Decision status: accepted first implementation slice
Scope: planning source for the first post-v0.4.9 release-governance implementation slice
Review policy: Review before release metadata, release publish, DOI closeout, or GUI work continues.
Project: agentic-project-kit

## Purpose

This document fixes the first implementation slice after the v0.4.9 analysis in a form that a successor LLM can execute without chat memory.

The first slice is:

`release-command-authority-and-publish-core-triage`

This slice comes before DOI closeout atomicity, broad ns/shell documentation cleanup, planning consolidation, absolute-path cleanup, and GUI work.

## Source Of Truth

Do not work from chat memory. Start from current `main`, local Git state, repo files, tests, command help, and bounded command evidence.

Known evidence anchor from the v0.4.9 audit:

- Baseline log: `tmp/codex-v049-analysis-baseline-20260618-120431.log`
- Baseline result: PASS
- Verified package version: `0.4.9`
- Verified tag: `v0.4.9`
- Verified tag target: `cd775a1f2e06f7f7f4fd4ba13ebcf139a2ef30a7`
- Verified `main` audit HEAD: `d33dd595f031445dd73c1f0f75a1ce174a4dfe42`
- Verified version DOI: `10.5281/zenodo.20738074`
- Verified concept DOI: `10.5281/zenodo.20101359`
- Baseline gates in that audit: `repo-status`, `post-merge-check`, `docs-audit`, `post-release-check --version 0.4.9`, command reference check, Ruff, `check-docs`, `doctor`, and full pytest passed.

These facts are anchors only. A successor must re-check current `main` before editing.

## Why This Slice Is First

Release metadata is a coupled project contract, not a free text patch. The next release process must have one supported, documented, tested `agentic-kit` release metadata route before any gate blocks manual release metadata edits.

The v0.4.9 analysis found two higher-risk release-command issues:

1. There is no clearly supported public `agentic-kit release-prep` or `agentic-kit release metadata-prep` route for release metadata preparation, even though package-core logic exists.
2. `src/agentic_project_kit/release_publish_core.py` still contains active `./ns` assumptions, including real subprocess calls. Since `./ns` has been removed, direct use of that module is expected to fail.

Therefore the first implementation slice must establish or explicitly decide the release command authority and make the old publish core fail-safe or portable before adding stricter gates.

## Current Findings To Re-Verify

Re-verify these findings from current `main` at slice start:

- `src/agentic_project_kit/release_prepare.py` contains deterministic release metadata write logic.
- `src/agentic_project_kit/release_metadata_prep.py` is a package script around that core.
- The legacy ns-named release metadata prep tool wrapper is removed; `src/agentic_project_kit/release_metadata_prep.py` is the package route around the deterministic core.
- `src/agentic_project_kit/release_prep_core.py` still advertises `./ns release-prep <version>` in usage or error text and still renders an `NS RELEASE PREP CYCLE` header.
- `src/agentic_project_kit/release_publish_core.py` still advertises `./ns release-publish`, still renders an `NS RELEASE PUBLISH CYCLE` header, and still calls `./ns release-gate` and `./ns release-verify`.
- `src/agentic_project_kit/cli_commands/release.py` registers release planning, preflight, check, post-release check, and DOI closeout commands, but does not register one clear metadata-prep command.
- Tests currently cover parts of these old release cores, including mocks that can hide the removed `./ns` runtime dependency.

If any finding is already false on current `main`, update the implementation plan from repo evidence before editing.

## Non-Goals

Do not:

- prepare a new release;
- bump project version;
- create or push tags;
- publish a GitHub Release;
- write Zenodo DOI metadata;
- run DOI closeout with `--write`;
- start GUI implementation;
- restore `./ns`;
- introduce another shell adapter;
- add a gate that blocks manual metadata edits before the supported metadata route exists;
- broadly rewrite protected status, handoff, planning, governance, YAML, or generated files.

## Slice Objective

At the end of this slice:

1. There is exactly one documented and tested supported release metadata preparation route on the `agentic-kit` command surface, or an explicit repo-backed decision that the existing route is intentionally unsupported until a named follow-up.
2. Active release-prep and release-publish Python cores no longer advertise or execute removed `./ns` commands unless the file is explicitly marked as historical or unsupported and fails closed before side effects.
3. Tests prevent reintroducing active `./ns` calls or `NS RELEASE ...` route names in supported release runtime paths.
4. Command reference and current docs are updated only as needed for the supported route.
5. No release, tag, DOI closeout, or publication side effects occur.

## Start Block

Run a bounded local verification before editing. Keep large output in logs.

```bash
OUT="tmp/release-command-authority-start-$(date +%Y%m%d-%H%M%S).log"
mkdir -p tmp
{
  set -euo pipefail
  git fetch origin --tags
  git switch main
  git pull --ff-only origin main
  ./.venv/bin/agentic-kit transfer restore-known-volatile --json || true
  echo "=== repo state ==="
  git status -sb
  git rev-parse HEAD
  git rev-parse origin/main
  git tag -l 'v0.4.9'
  git rev-parse v0.4.9
  echo "=== baseline gates ==="
  ./.venv/bin/agentic-kit transfer repo-status
  ./.venv/bin/agentic-kit transfer post-merge-check
  ./.venv/bin/agentic-kit docs-audit
  ./.venv/bin/agentic-kit post-release-check --version 0.4.9
  ./.venv/bin/agentic-kit transfer command-reference-check
  echo "=== release command surface ==="
  ./.venv/bin/agentic-kit --help
  ./.venv/bin/agentic-kit release-plan --help
  ./.venv/bin/agentic-kit release-preflight --help
  ./.venv/bin/agentic-kit release-check --help
  ./.venv/bin/agentic-kit post-release-check --help
  ./.venv/bin/agentic-kit post-release-doi-closeout --help
  echo "=== release route references ==="
  rg -n "release-prep|release-publish|release-gate|release-verify|./ns|NS RELEASE" src tools tests docs README.md CHANGELOG.md || true
  echo "RESULT=RELEASE_COMMAND_AUTHORITY_START_DONE"
} > "$OUT" 2>&1
RC=$?
echo "LOG=$OUT"
echo "RC=$RC"
```

Stop before editing if:

- `main` cannot fast-forward;
- worktree is dirty after volatile restore;
- any baseline gate fails;
- command reference is stale;
- `docs/handoff/CURRENT_HANDOFF.md` or `docs/STATUS.md` contains a new blocker that changes this priority.

## Work Order

### Step 1: Inventory The Release Command Authority

Inspect these files first:

- `src/agentic_project_kit/cli_commands/release.py`
- `src/agentic_project_kit/release_prepare.py`
- `src/agentic_project_kit/release_metadata_prep.py`
- Removed legacy tool wrapper path for release metadata prep
- `src/agentic_project_kit/release_prep_core.py`
- `src/agentic_project_kit/release_publish_core.py`
- `tests/test_release_prepare_command.py`
- `tests/test_release_metadata_prep_portability.py`
- `tests/test_release_prep_core.py`
- `tests/test_release_publish_core.py`
- `tests/test_v036_release_route_help_safety.py`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/reference/agentic-kit-commands.json`
- `README.md`
- `docs/TEST_GATES.md`
- `docs/planning/PROJECT_DIRECTION.yaml` (`portability-and-ns-closeout` preserved classification)
- this file

Record, in the PR body or slice notes, which route is authoritative and which routes are compatibility-only, unsupported, historical, or obsolete.

### Step 2: Choose One Public Metadata Route

Choose exactly one supported `agentic-kit` command name for release metadata preparation.

Preferred direction, unless current CLI structure proves otherwise:

- `agentic-kit release-prep --version X --summary-line "..."`

Acceptable alternative:

- `agentic-kit release-metadata-prep --version X`

Do not add both. Do not put release metadata prep under `transfer`.

The route must:

- call Python core logic, not shell;
- use the existing deterministic metadata-prep core where possible;
- support a dry-run or report/evidence mode if the existing core supports it;
- clearly state write behavior and changed paths;
- refuse ambiguous or malformed versions;
- not tag, publish, push, or create releases;
- be visible in command help and command reference.

If the correct route name is ambiguous, stop and open a planning/architecture question instead of implementing two routes.

### Step 3: Make Release Prep Core Portable Or Explicitly Non-Canonical

Handle `src/agentic_project_kit/release_prep_core.py`.

Preferred outcome:

- usage/help/error strings reference the supported `agentic-kit` route;
- rendered headers no longer say `NS RELEASE PREP CYCLE`;
- no subprocess command references removed `./ns`;
- tests cover help, invalid argument behavior, and failure-before-mutation behavior.

Fallback outcome if the module is obsolete:

- mark it as unsupported/deprecated in code and tests;
- make it fail closed before any side effect;
- document the supported route elsewhere;
- add tests proving direct use does not perform release metadata writes or shell calls.

Do not leave a file that looks active and still tells users to run `./ns release-prep`.

### Step 4: Make Release Publish Core Safe

Handle `src/agentic_project_kit/release_publish_core.py` before adding stricter release-metadata gates.

Preferred outcome:

- replace `./ns release-gate` and `./ns release-verify` subprocess calls with supported `agentic-kit` commands or Python core functions;
- usage/help/error strings reference supported `agentic-kit` routes;
- rendered headers no longer say `NS RELEASE PUBLISH CYCLE`;
- tests prove the command sequence never contains `./ns`.

Acceptable first-slice outcome if full publish portability is too large:

- fail closed with a clear unsupported-route message before any branch, tag, push, or release side effect;
- remove or update help text so it no longer presents `./ns release-publish` as current guidance;
- add a follow-up slice for full publish orchestration.

This module must not remain in a state where direct Python invocation can attempt `./ns`.

### Step 5: Add Regression Tests

Add or update focused tests. Expected test coverage:

- exactly one public metadata-prep route is documented and registered;
- command help for the chosen route is available;
- route implementation calls Python/package core, not `tools/ns_*` or `./ns`;
- active release runtime source files do not contain removed `./ns release-*` command calls;
- active release runtime source files do not render `NS RELEASE ...` headers;
- release-publish direct path is either portable or fail-closed before side effects;
- historical mentions remain allowed only in clearly historical docs or tests.

Useful candidate files:

- `tests/test_release_prepare_command.py`
- `tests/test_release_metadata_prep_portability.py`
- `tests/test_release_prep_core.py`
- `tests/test_release_publish_core.py`
- `tests/test_v036_release_route_help_safety.py`
- a new focused test such as `tests/test_release_command_authority.py` if that keeps assertions clearer.

Avoid broad string tests over all docs unless the test classifies historical, current, and generated contexts.

### Step 6: Update Documentation Only Where Needed

If a public command is added or renamed:

- run `./.venv/bin/agentic-kit transfer command-reference-refresh`;
- commit the exact command reference changes:
  - `docs/reference/AGENTIC_KIT_COMMANDS.md`
  - `docs/reference/agentic-kit-commands.json`
- update only current release workflow docs that instruct users or agents which command to run;
- do not rewrite historical changelog entries unless they are presented as current instructions.

Likely current-doc candidates:

- `README.md`
- `docs/TEST_GATES.md`
- `docs/planning/PROJECT_DIRECTION.yaml` (`portability-and-ns-closeout` preserved classification)
- `docs/planning/WORKFLOW_REDUCTION_FOCUS.md`
- this file, only if implementation discovers a different authoritative route.

Use minimal additive patches for protected docs.

## Required Gates

Run at least these before commit:

```bash
./.venv/bin/python -m ruff check src/agentic_project_kit tests
./.venv/bin/python -m pytest -q tests/test_release_prepare_command.py tests/test_release_metadata_prep_portability.py tests/test_release_prep_core.py tests/test_release_publish_core.py tests/test_v036_release_route_help_safety.py
./.venv/bin/python -m pytest -q tests/test_agentic_kit_command_reference_is_current.py
./.venv/bin/agentic-kit transfer command-reference-check
./.venv/bin/agentic-kit check-docs
./.venv/bin/agentic-kit docs-audit
./.venv/bin/agentic-kit doctor
./.venv/bin/agentic-kit transfer protected-diff-plan --label release-command-authority-and-publish-core-triage
```

Run full pytest before PR creation unless the final diff is strictly documentation-only.

If `command-reference-check` fails after adding a CLI route, run:

```bash
./.venv/bin/agentic-kit transfer command-reference-refresh
./.venv/bin/python -m pytest -q tests/test_agentic_kit_command_reference_is_current.py
```

## Acceptance Criteria

The slice is complete only when all are true:

- Current `main` was verified at start.
- The PR states the chosen authoritative release metadata-prep route.
- There is no active supported release metadata-prep path that depends on `tools/ns_*` or `./ns`.
- There is no active supported release publish path that attempts `./ns`.
- Direct release-publish core use is portable or fail-closed before side effects.
- Help/error text no longer instructs users to run removed `./ns release-*` routes.
- Regression tests cover the route decision and the no-`./ns` release-core guarantee.
- Command reference is current if CLI changed.
- Protected diff plan is PASS.
- No release, tag, DOI closeout, or publish side effect happened.

## Stop Conditions

Stop and report instead of continuing if:

- the only viable metadata route would require restoring `./ns`;
- a second plausible public route is needed and there is no maintainer decision;
- release-publish portability requires real tag or publish side effects to test;
- protected-diff-plan reports BLOCK or FAIL;
- command-reference refresh wants broad unrelated changes;
- current-state docs reveal a newer release or active blocker not covered by this plan;
- full publish orchestration is larger than a safe first slice.

## Follow-Up Slices

After this slice is merged, continue in this order:

1. `release-metadata-authority-gate`: block release-anchor file changes unless an authoritative release-prepare evidence report exists.
2. `doi-closeout-atomicity`: make DOI closeout complete and commit-safe for all expected release files, including `docs/releases/VERIFIED_RELEASES.md`.
3. `current-state-doc-currency`: fix and gate README/STATUS/CURRENT_HANDOFF/successor-package drift and chronological ordering.
4. `audit-ns-shell-legacy-references`: classify remaining `./ns`, `ns-menu`, shell, `*.sh`, and historical command references.
5. `audit-absolute-paths-portability`: classify and remove runtime/private absolute local path dependencies.
6. `prepare-gui-gatekeeper-roadmap`: resume GUI only after release, docs, handoff, and planning gates are deterministic.

## Final Report Shape For Successor LLM

End the implementation slice with:

- branch name;
- start HEAD and final HEAD;
- authoritative release metadata-prep route;
- status of `release_prep_core.py`;
- status of `release_publish_core.py`;
- changed files;
- tests/gates run with PASS/FAIL;
- protected-diff-plan result;
- command-reference result;
- explicit note that no release/tag/DOI/publish side effects occurred;
- exact next slice.
## Pre-GUI closeout note: release publish remains fail-closed

The `agentic-kit release-prep --version <version> --summary-line <line>` route is the supported metadata preparation path.  The legacy direct publish core remains intentionally fail-closed after the ns migration until a separate release-publish orchestration follow-up rebuilds tag/publish behavior through supported `agentic-kit` wrappers.

This is a non-GUI follow-up.  It must not be solved by GUI code and must not reintroduce raw shell, raw GitHub CLI, or legacy `ns` routing into GUI actions.  GUI work may start after `agentic-kit gui-readiness-gate --version 0.4.9` is green, but real release publishing remains outside the GUI readiness scope until that follow-up is implemented and tested.

## v0.4.10 release-preparation authority

Status: ACTIVE AUTHORITY.

v0.4.10 is a safety, audit, and workflow-consolidation release. It is not the
GUI implementation release.

Release preparation for v0.4.10 must require the following green signals before
version bump or publication work starts:

- `standard-gates-audit-suite`
- `command-taxonomy-check`
- `patch-scope-preflight --label <slice-label>`
- `gui-readiness-gate`
- `release-publish --dry-run`
- `release-metadata-authority-gate`
- `post-release-check`
- `docs-audit`
- `audit-planning-docs-consolidation`

`release-publish --execute` remains capability-gated. Live publication must not
be treated as a normal GUI or routine automation action.
