# First-Contact Post-fix Checkout Validation

Status: PASS_WITH_DOCKER_ENGINE_UNAVAILABLE  
Date: 2026-08-20  
Evidence type: Post-fix Build/Checkout Validation  
Package version in source: `1.0.1`

## Scope

This report records validation of the current source checkout after the
first-contact fixes. It is not a PyPI validation. The historical PyPI evidence
for the already-published `1.0.1` package remains
`docs/reports/V1_0_1_DOCKER_PYPI_FIRST_CONTACT_20260820.md`.

## Fix Classification

| Finding | Current source status |
|---|---|
| F1 empty-directory `check` traceback | Fixed: controlled FAIL, exit 1, shared non-workspace message |
| Related empty-directory `doctor` semantics | Fixed: controlled FAIL, exit 1, same non-workspace contract |
| F2 missing Git during `init` | Fixed: preflight before project mutation, controlled exit 2 |
| F3 missing Git identity | Already improved before this slice; retained as explicit initial-commit warning with exit 0 |
| F4 generated project legacy warning | Fixed: generated projects do not emit the legacy warning; operating-layer manifest checks are SKIP |

## Local Gate Evidence

- Full test suite: `2840 passed, 446 warnings`
- Ruff: `All checks passed!`
- `agentic-kit check-docs`: PASS
- `agentic-kit direction validate --root .`: PASS, `FINDING_COUNT=0`
- `agentic-kit doctor`: PASS overall with 73 report-only document lifecycle findings
- Command manifest audit: PASS, `finding_count=0`
- Site fallback build: PASS, 14 files written, 13/13 claims verified, 0 planned claims

## CLI Smoke Evidence

Empty non-workspace:

- `agentic-kit check --root /private/tmp/apk-empty-smoke.sZkSvC --json`
  returned exit 1 with context `mode=non_workspace`.
- `agentic-kit doctor --root /private/tmp/apk-empty-smoke.sZkSvC`
  returned exit 1 with `[FAIL] workspace`.

Missing Git:

- `agentic-kit init ...` with a `PATH` that excluded `git` returned exit 2.
- The target directory remained absent: `TARGET_ABSENT=PASS`.

Fresh generated project:

- `agentic-kit init ... --type generic --kit-source none` with a configured Git
  identity returned exit 0.
- Immediate `agentic-kit check --root .../demo-project` returned PASS.
- Immediate `agentic-kit doctor --root .../demo-project` returned PASS.
- `doctor` reported `.agentic/config.yaml` checks as SKIP because the generated
  project contract uses `.agentic/project.yaml`.

Missing Git identity:

- A forced no-identity Git configuration produced the Kit-level warning
  `Initial Git commit was not created`.
- The command returned exit 0 because file generation is the success guarantee
  and the initial commit is a convenience step.

## Docker Boundary

Docker CLI is installed:

```text
Docker version 29.7.2, build a7dcaa6
```

The Docker engine was not reachable in this environment:

```text
failed to connect to the docker API at unix:///Users/hof/.docker/run/docker.sock
```

Attempting to start Docker Desktop with `open -a Docker` failed:

```text
Unable to find application named 'Docker'
```

Therefore no post-fix Docker container validation was executed in this slice.
Do not describe this report as Docker PASS or PyPI PASS. A later environment
with a running Docker engine should repeat the documented Quickstart container
path against a local checkout or locally built wheel and label it Post-fix
Build/Checkout Validation. Only a later published package installed from
`pypi.org` may be labeled Post-release PyPI Validation.
