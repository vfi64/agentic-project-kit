# Current Handoff

Status-date: 2026-05-10
Project: agentic-project-kit
Branch: docs/roadmap-after-grok-review
Base branch: main
Current version: 0.2.6

## Current Goal

Record the post-v0.2.5 planning implications from external review without changing code or release metadata.

## Current Repository State

The project has released version 0.2.5. GitHub release automation worked and attached the expected release assets.

Important released work:

- v0.2.0 added GitHub release workflow and release artifacts.
- v0.2.1 fixed generated CI so it installs agentic-project-kit from the package index instead of a private GitHub repository.
- v0.2.2 added --kit-source for generated CI with pypi, testpypi, and none.
- v0.2.3 added release-state validation for local tags, remote tags, and GitHub releases.
- v0.2.4 added Zenodo-backed citation and archival metadata.
- v0.2.5 released the post-v0.2.4 repository-health and visibility work, including project contracts, profiles, policy packs, policy-pack checks, policy-pack doctor checks, documentation coverage drift checks, machine-readable task gates, and the semantic quality boundary.

v0.2.5 release evidence:

- PR #33 improved release visibility and README positioning for v0.2.5.
- PR #34 raised package and citation metadata to 0.2.5 and finalized the changelog heading.
- Tag v0.2.5 was pushed.
- GitHub Release v0.2.5 was created successfully by the Release workflow.
- Release assets were attached: `agentic_project_kit-0.2.5-py3-none-any.whl` and `agentic_project_kit-0.2.5.tar.gz`.
- `agentic-kit release-check --version 0.2.5` now fails as expected because the local tag, remote tag, and GitHub release already exist. That command is a pre-release gate, not a post-release success check.

Zenodo state:

- Zenodo GitHub integration is enabled for vfi64/agentic-project-kit.
- Zenodo archived v0.2.4.
- All-versions DOI: 10.5281/zenodo.20101359.
- v0.2.4 version DOI: 10.5281/zenodo.20101360.
- v0.2.5 version DOI: 10.5281/zenodo.20111119.
- CITATION.cff contains the all-versions DOI.
- .zenodo.json is present.
- README.md contains a Zenodo DOI badge and citation guidance.
- The v0.2.5 version-specific DOI has been verified by `agentic-kit post-release-check --version 0.2.5`: 10.5281/zenodo.20111119.

Post-v0.2.5 external review signal:

- External review characterizes v0.2.5 as a useful late-early MVP with unusually strong dogfooding and machine-checkable repository state.
- Treat that as a planning signal, not as proof of production readiness.
- Preserve the conservative positioning: strong early governance tooling, not a de-facto standard, not production-ready, and not proof of semantic perfection.
- Keep agentic-project-kit generic. Do not rename generic roadmap items after private projects or private legacy-refactoring work.

Post-v0.2.5 roadmap:

1. Add a post-release Zenodo verification command.
   - Candidate command names: `agentic-kit post-release-check --version X.Y.Z` or `agentic-kit zenodo-check --version X.Y.Z`.
   - The command must check GitHub release state and Zenodo archive state after publication.
   - It must only recommend or prepare README.md or CITATION.cff DOI follow-up when a verified Zenodo record for the requested release version exists.
   - If no version-specific DOI exists yet, it must report WAITING or WARN and leave DOI metadata unchanged.
   - This must remain separate from `release-check`, because `release-check` is a pre-release gate.
2. Add advisory review commands after the post-release check exists.
   - Candidate commands: `agentic-kit review-docs` and `agentic-kit review-architecture`.
   - These should be advisory only and must not become merge authority.
   - They may flag clarity, audience fit, missing rationale, overclaims, architecture drift, or review questions.
3. Add generic output-contract-oriented scaffolding after the advisory review layer is stable.
   - Prefer generic names such as `structured-output`, `governed-output`, `response-contracts`, `repairable-output`, and `audit-evidence`.
   - Avoid private-project-specific names in the open kit.
   - Start with fixtures, documentation, and minimal gates before adding any large enforcement pipeline.
4. Consider a later v0.3.0 milestone for minimal response-contract gates.
   - This should be based on generic structured-output needs, not on a single private wrapper implementation.

Current branch work:

- docs/STATUS.md records the post-v0.2.5 external-review planning signal and roadmap.
- This handoff points future agents to the same roadmap.
- README.md and CITATION.cff may now mention the verified v0.2.5 version DOI: 10.5281/zenodo.20111119.
- The branch explicitly avoids code changes, tags, release artifacts, publication artifacts, merges, direct main writes, and repository setting changes.

## Positioning Notes

Useful external-review signals to preserve:

- The strongest value proposition is reproducible AI-assisted repository work through explicit context, machine-checkable gates, bounded evidence, handoff discipline, release-state validation, and dogfooding.
- Avoid overclaims such as production ready, de-facto standard, semantic perfection, or LLM-proven quality.
- Treat mechanized trust as a useful concept, but express it through concrete checked project state rather than marketing claims.
- Do not let examples or wording blur agentic-project-kit with Comm-SCI-Control-private or any private legacy refactoring project.

## Remote Work Authorization

For this repository, assistants and coding agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.

Maintainer approval is still required before merging pull requests, writing directly to main, creating release tags, creating release or publication artifacts, raising release versions, changing repository access settings, or choosing a new architecture direction when multiple plausible options exist.

## Source of Truth

Read in this order:

1. .agentic/project.yaml
2. sentinel.yaml
3. docs/architecture/ARCHITECTURE_CONTRACT.md
4. docs/DOCUMENTATION_COVERAGE.yaml
5. AGENTS.md
6. README.md
7. docs/STATUS.md
8. docs/TEST_GATES.md
9. docs/handoff/CURRENT_HANDOFF.md
10. src/agentic_project_kit/
11. tests/

## Required Local Gate

Run:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit doctor
    gh release view v0.2.5

Expected note:

    agentic-kit release-check --version 0.2.5

is expected to fail after publication because it verifies that the target tag and GitHub release are still unused.

## Latest Known Evidence

Latest validated release evidence:

- python -m pytest -q -> 52 passed
- ruff check . -> passed
- agentic-kit check-docs -> passed
- agentic-kit doctor -> Overall PASS; project state matches version 0.2.5
- agentic-kit release-check --version 0.2.5 -> PASS before tag creation
- python -m build -> successfully built the 0.2.5 wheel and sdist
- twine check dist/* -> passed for the 0.2.5 wheel and sdist
- Release workflow for v0.2.5 -> success
- gh release view v0.2.5 -> release exists with wheel and sdist assets

Evidence still required after the roadmap status updates on this branch:

- python -m pytest -q
- ruff check .
- agentic-kit check-docs
- agentic-kit doctor
- gh release view v0.2.5

## Current Open Work

- Pull docs/roadmap-after-grok-review locally.
- Run the required local gate.
- If the gates pass, open a PR for the roadmap-only update.
- After merge, the next implementation branch should be feature/post-release-zenodo-check.
- The v0.2.5 version-specific DOI is known and verified: 10.5281/zenodo.20111119.

## Next Safe Step

Run the required local gate on docs/update-v025-zenodo-doi. Expected result: tests, ruff, check-docs, doctor, and post-release-check pass.

Current documentation usability work:

- Add `docs/examples/minimal-python-cli.md` as a small end-to-end generated-project demo.
- Keep the example documentation-only; do not add generated fixture trees yet.
- README.md should point users to the example workflow.

Current v0.2.6 release-preparation work:

- v0.2.6 has been released from main after PRs #39, #40, #41, and #42.

- v0.2.6 version DOI: 10.5281/zenodo.20119102.
- The v0.2.6 version-specific DOI has been verified by `agentic-kit post-release-check --version 0.2.6`: 10.5281/zenodo.20119102.
- Next safe step: run the full local release gate and inspect the diff before opening the release PR.

Current collaboration workflow update:

- Document the chat-assisted terminal workflow: visual separator first, no raw decorative separator commands, and `./tools/screen_control_gate.sh` for local evidence capture.
- This is intended for LLM collaboration without Codex CLI, Claude CLI, or another local coding-agent runtime.

Current profile explain work:

- PR #46 added `agentic-kit profile-explain`.
- The command prints available project profiles and policy packs with descriptions.
- Next safe feature step: design a specialized governance-wrapper/profile contract only after documenting the current command.

Current governance-wrapper profile work:

- PR #48 added `governance-wrapper` and `output-contracts`.
- The merged implementation includes CLI defaults, `profile-explain` visibility, and tests for contract/default/init behavior.
- Smoke result: generated `--type governance-wrapper` project passes `agentic-kit doctor`.
- Next safe step: document and then implement generated output-contract skeleton files, without touching Comm-SCI-Control directly.

## No-heredoc screen-control workflow rule

Current collaboration rule: for chat-assisted terminal work, avoid heredocs in copy-paste command blocks when possible. Use a visible `printf` separator as the first command, prefer `./tools/screen_control_gate.sh` for evidence capture, and recover from `heredoc>` or `quote>` hangs with `Ctrl-C` followed by `git status --short`.


Governance-wrapper generated-project guidance:

- PR #51 added generated output-contract skeleton docs for governance-wrapper projects.
- PR #52 fixed `agentic-kit init --type governance-wrapper` next-step guidance so non-Python governance projects are directed to `agentic-kit check-docs`, `agentic-kit check`, and `agentic-kit doctor`.
- PR #54 tightened generated validation/repair guidance so repair wording is singular, bounded, and auditable.
- PR #55 added a small deterministic runtime-validator skeleton in `src/agentic_project_kit/runtime_validator.py` with tests in `tests/test_runtime_validator.py`.
- PR #57 wired the runtime-validator skeleton into a separate `agentic-kit validate-sections` CLI command without changing `doctor` or `check` behavior.
- PR #59 added optional `validate-sections` guidance to generated governance-wrapper `docs/VALIDATION_AND_REPAIR.md` files.
- Next safe step: decide whether to add a higher-level contract validator command beyond literal section checks, or keep the current runtime validator deliberately small.
