# Post-0.5.0 Phase B2 Greenfield Probe

Status: PASS_WITH_LIMITATIONS
Date: 2026-08-11
Kit branch: `codex/phase-b-greenfield-probe`
Base ref: `origin/main` at `700c68670f3fc1e46b0405abdff541a4f65b5473`

## Purpose

Phase B2 tested whether the current Agentic Project Kit can create and operate
on disposable greenfield repositories without using a valuable production
repository. The probe intentionally separated the documented generator mode from
the operating-layer workspace mode, because the architecture keeps those modes
distinct.

## Target Repositories

Two ignored temporary repositories under `tmp/` were used:

- Generator target: `apk-greenfield-probe`
  - fixed generator initial ref: `daa39d5`
  - local feature ref after a small real change: `9e9fbbc`
- Operating-layer target: `workspace-target`
  - initial manifest-less ref: `201ee99`

No remote repository was created. No GitHub repository, PR, merge, release, or
production resource was mutated.

## Generator Path

Command path tested:

- `agentic-kit init apk-greenfield-probe --type python-cli`
- local feature branch `probe/real-change`
- small real code change: add `describe_probe()` and a regression test
- local gates from the generated repository
- successor-handoff generation attempt with `agentic-kit transfer chat-switch-complete --render-prompt`

Initial result before repair:

- Generated project was created and committed successfully.
- `pytest -q`, `ruff check .`, `agentic-kit check`, and `agentic-kit doctor`
  passed.
- Running tests created untracked `__pycache__` files because generated projects
  did not include a `.gitignore`.

Kit repair performed in this slice:

- Added a generated `.gitignore` for Python/tooling byproducts.
- Added generator test coverage for `.gitignore` and `__pycache__/`.
- Updated README and documentation coverage so the generated file remains
  visible.

Post-repair generator rerun:

- Initial generated commit included `.gitignore`.
- The same small code/test change passed `pytest -q`, `ruff check .`,
  `agentic-kit check`, and `agentic-kit doctor`.
- `git status --short --branch` after tests showed only the two intentional
  source/test modifications before commit.
- Local feature commit `9e9fbbc` recorded the change.

Generator limitations:

- Generated projects use `.agentic/project.yaml`, not `.agentic/config.yaml`.
  The operating-layer workspace commands therefore classify the generated
  `.agentic/` directory as foreign. This matches the current two-mode
  architecture, but is a practical onboarding friction point.
- `agentic-kit handoff check` expects `.agentic/handoff_state.yaml`, which
  generated projects do not create.
- `agentic-kit transfer chat-switch-complete --render-prompt` can write a
  successor package in the generated repository, but validation is `FAIL`
  because the generated project lacks the full self-hosting Kit handoff source
  set such as `docs/planning/PROJECT_DIRECTION.yaml`,
  `docs/reference/agentic-kit-commands.json`, and several `.agentic/*` rule
  sources. This is not a full successor-continuation PASS for greenfield
  generated projects.

## Operating-Layer Workspace Path

Command path tested against a separate manifest-less Python repository:

- `workspace adopt --json`
- `workspace dpa-intake --validation-ref 201ee99 --json`
- `dpa repo-adoption-assessment --validation-ref 201ee99 --json`
- `workspace init --json`
- `workspace init --execute --json`
- `workspace upgrade --json`
- `workspace remove --json`
- `workspace remove --execute --json`
- second `workspace remove --json`

Results:

- `workspace adopt` returned `PASS` with `ready_for_workspace_init`.
- DPA repo-adoption assessment returned
  `READY_FOR_DPA_REPO_ADOPTION_ADJUDICATION`, `surface_count=2`,
  `blocker_count=0`, `warning_count=0`, and
  `external_repo_conformance_claimed=false`.
- DPA intake returned `READY_FOR_DPA_INTAKE_ADJUDICATION` with two maintainer
  decision groups: `README.md` and `pyproject.toml`.
- `workspace init` dry-run and execute returned `PASS`.
- The executed init wrote the expected `.agentic/config.yaml`,
  `.agentic/state/status.md`, `.agentic/state/handoff/README.md`,
  `.agentic/ci/*`, `.agentic/dpa/workspace_init_projection.json`,
  `.agentic/INITIAL_LLM_PROMPT.md`, and `docs/archive/README.md`, and appended
  `.agentic/tmp/` to `.gitignore`.
- After init, `pytest -q` and `ruff check .` passed.
- `workspace upgrade` returned `PASS`, already at schema v1.
- `workspace remove` dry-run and execute returned `PASS`; a second remove was
  `NOOP`.

Operating-layer limitations:

- `agentic-kit doctor` failed after `workspace init` on the minimal repository
  because the repo did not contain the generator-style project governance files
  such as `sentinel.yaml`, `docs/STATUS.md`, `docs/TEST_GATES.md`,
  `docs/handoff/CURRENT_HANDOFF.md`,
  `docs/architecture/ARCHITECTURE_CONTRACT.md`, and
  `docs/DOCUMENTATION_COVERAGE.yaml`.
- `workspace remove` removes exact Kit-generated `.agentic/` files, but it
  intentionally preserves project docs/source. As a result, the remove left
  `docs/archive/README.md` and the `.gitignore` line `.agentic/tmp/`.
  This is a bounded cleanup, not an exact byte-for-byte repository rollback.

## Classification

`PASS_WITH_LIMITATIONS`

The Kit can create a greenfield Python CLI project, run its initial local
quality gates, accept a small real feature change, and manage an operating-layer
workspace in a separate manifest-less repository with init, upgrade, and bounded
remove behavior.

The result is limited because generator-mode greenfield projects are not yet
first-class operating-layer workspaces, full successor-continuation validation
does not pass for generated projects, and `workspace init` alone does not make a
minimal repository satisfy the classic generated-project doctor contract.

## Follow-up Candidates

- Decide whether `agentic-kit init` should optionally emit an operating-layer
  `.agentic/config.yaml`, or whether docs should explicitly route users from
  generator mode to operating-layer mode as a second step.
- Decide whether generated projects should include the handoff-state files
  expected by `agentic-kit handoff check`, or whether the handoff command should
  detect generator-mode repositories and explain the mismatch.
- Decide whether `workspace remove` should offer an explicit stronger cleanup
  mode for `.gitignore` and `docs/archive/README.md`, while preserving the
  current safe default.
- Treat remote PR/closeout for generated projects as not tested in B2 because no
  disposable GitHub remote was created.
