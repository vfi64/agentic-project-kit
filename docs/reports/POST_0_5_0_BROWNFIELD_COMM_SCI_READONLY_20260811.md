Status: analysis
Status-date: 2026-08-11
Scope: Phase B1 Brownfield read-only probe
Branch: codex/phase-b-generalizability-probe

# Brownfield Read-Only Probe: Comm-SCI-Control-private

## Classification

`FAIL_SAFE`

The read-only assessment succeeded and the Kit refused to proceed to adoption
without maintainer adjudication. That is the correct safe outcome because the
foreign repository has its own high-authority governance and specification
surfaces. No mutation was performed in `vfi64/Comm-SCI-Control-private`.

## Exact Inputs

- Kit repository head: `700c68670f3fc1e46b0405abdff541a4f65b5473`.
- Kit command manifest SHA: `3d20e7338c12`.
- Target repository: `vfi64/Comm-SCI-Control-private`.
- Target default branch: `main`.
- Target exact ref: `e65d6c8a8c02204420703829a171f9423a5a49bf`.
- Target worktree after probe: clean on `main...origin/main`.
- Target open PR state: PR #2 (`feature/ui-access-levels` -> `main`) open, not
  draft, with completed successful `pytest (3.11)` check.
- Latest target `main` CI: `tests` workflow success for
  `e65d6c8a8c02204420703829a171f9423a5a49bf`.

## Foreign Repository Contracts

`AGENTS.md` declares the active canonical JSON ruleset as the primary source of
truth for behavior, command tokens, output contracts, QC logic, SCI logic, and
control-layer rules. It also requires deterministic behavior, auditability,
separation between specification/rendering/runtime/tests, and tests for every
meaningful behavior change.

The current README names:

- active desktop entrypoint: `Comm-SCI-Control-App2.py`;
- canonical ruleset manifest: `JSON/ACTIVE_RULESET.json`;
- selected ruleset: `JSON/Comm-SCI-v21.1.3.json`;
- local test command: `PYTHONPATH=src pytest -q`;
- quality gate: `python scripts/quality_gate.py --mode all`.

These contracts make silent adoption or governance rewrites inappropriate.

## Read-Only Commands

| Command | Surface | Safety | Result |
|---|---|---|---|
| `git fetch --all --prune` | git read/update remote refs | read-only remote ref refresh | PASS |
| `gh pr list --repo vfi64/Comm-SCI-Control-private --state open --json ...` | GitHub diagnostic | READ_ONLY | PASS |
| `gh run list --repo vfi64/Comm-SCI-Control-private --branch main --limit 5 --json ...` | GitHub diagnostic | READ_ONLY | PASS |
| `agentic-kit workspace adopt --root ... --json` | orchestrator | READ_ONLY | PASS |
| `agentic-kit workspace dpa-intake --root ... --validation-ref e65d6c8... --json` | orchestrator | BOUNDED, non-execute preview | `READY_FOR_DPA_INTAKE_ADJUDICATION` |
| `agentic-kit workspace init --root ... --json` | orchestrator | BOUNDED, dry-run default | PASS, `written=false` |
| `agentic-kit workspace remove --root ... --json` | orchestrator | BOUNDED, dry-run default | NOOP, `written=false` |

## What The Kit Detected

Initial `workspace adopt` correctly detected:

- project type: `python`;
- project profile: `python-default`;
- project name: `comm-sci-control-app`;
- existing CI workflow: `.github/workflows/tests.yml`;
- no existing `.agentic/` workspace;
- readiness for workspace init;
- documentation candidates under `docs/` and `docs/proposals/`;
- DPA management status:
  `DPA_CAPABLE_WITH_FRESH_PER_REPO_ASSESSMENT`;
- adoption status:
  `READY_FOR_DPA_REPO_ADOPTION_ADJUDICATION`;
- no external repo conformance claim;
- no automatic migration claim;
- no production mutation.

## Kit Defect Found And Fixed

The first read-only assessment missed several high-authority foreign-repo
surfaces that are explicit in the repository contract:

- `JSON/ACTIVE_RULESET.json`;
- `JSON/Comm-SCI-v21.1.3.json`;
- other tracked ruleset JSON files in `JSON/`;
- `Format-Memory.md`;
- `ARCHITECTURE.md`;
- `MODULARIZATION.md`.

This was a general inventory defect, not a Comm-SCI special case: DPA adoption
candidate discovery only covered selected top-level files, `docs/`, `.agentic/`,
and `.github/workflows/`.

This branch fixes the Kit by adding generic inventory coverage for:

- top-level candidate authority files;
- common specification directories: `JSON/`, `json/`, `spec/`, `specs/`;
- `specification_authority` classification for specification surfaces.

Regression evidence:

- `python -m pytest -q tests/test_workspace_adopt.py tests/test_workspace_dpa_intake.py`:
  16 passed.
- `ruff check src/agentic_project_kit/dpa_repo_adoption_assessment.py tests/test_workspace_adopt.py`:
  PASS.

After the fix, the rerun reported:

- `workspace adopt`: PASS;
- `workspace dpa-intake`: `READY_FOR_DPA_INTAKE_ADJUDICATION`;
- surface count: 71;
- classification counts:
  - `agent_instruction`: 1;
  - `architecture_authority`: 2;
  - `ci_workflow`: 1;
  - `manual_document`: 21;
  - `onboarding_document`: 2;
  - `project_config`: 1;
  - `release_state`: 2;
  - `specification_authority`: 41.

Key verified surfaces:

- `ARCHITECTURE.md`: `architecture_authority`;
- `MODULARIZATION.md`: `architecture_authority`;
- `Format-Memory.md`: `specification_authority`;
- `JSON/ACTIVE_RULESET.json`: `specification_authority`;
- `JSON/Comm-SCI-v21.1.3.json`: `specification_authority`;
- `README.md` and `README.de.md`: `onboarding_document`.

## Adoption Preview

`workspace init --json` dry-run would create the standard `.agentic/`
operating-layer workspace, including:

- `.agentic/config.yaml`;
- `.agentic/DOC_LIFECYCLE.md`;
- `.agentic/INITIAL_LLM_PROMPT.md`;
- `.agentic/registries/documentation.yaml`;
- `.agentic/registries/rules.yaml`;
- `.agentic/state/status.md`;
- `.agentic/state/handoff/...`;
- `.agentic/transfer/inbox/`;
- `.agentic/transfer/outbox/`;
- `.agentic/ci/agentic-gate.yaml`;
- `.agentic/ci/pre-commit-snippet.yaml`;
- `docs/archive/README.md`;
- one `.gitignore` addition: `.agentic/tmp/`.

The preview listed no workflow or pre-commit injection targets because neither
`--inject-ci` nor `--inject-pre-commit` was requested.

## Reversibility Preview

Before adoption, `workspace remove --json` returned NOOP:

- no workspace manifest;
- no `.agentic/` directory;
- no files to remove;
- safety claims preserved:
  - dry-run default;
  - removes only exact Kit-generated workspace files;
  - unknown or modified paths block execute;
  - does not remove project docs or source.

The real rollback test cannot be executed until an adoption mutation is
authorized.

## Measured Fit

Positive findings:

- The Kit recognized the Python project and CI surface correctly.
- It did not claim conformance for an external repo.
- It did not write during read-only or preview commands.
- It refused to cross the DPA/adoption boundary without maintainer adjudication.
- After the inventory fix, it detected the repository's actual specification
  authority family.

Limitations and gaps:

- No adoption, handoff, successor-continuation, upgrade, or rollback execution
  was performed because the current DPA contract requires maintainer-adjudicated
  scope first.
- The Kit can inventory specification files generically, but it still cannot
  infer the semantic relationship between `JSON/ACTIVE_RULESET.json` and the
  active selected ruleset without reading repository-specific contract text.

## Decision

Do not mutate `vfi64/Comm-SCI-Control-private` in this slice.

The next safe Brownfield step is one bundled maintainer adjudication: authorize
or decline a bounded workspace adoption experiment for the exact target ref and
the previewed file set. If declined, record a no-migration adjudication and use
the read-only result as valid `FAIL_SAFE` Brownfield evidence.
