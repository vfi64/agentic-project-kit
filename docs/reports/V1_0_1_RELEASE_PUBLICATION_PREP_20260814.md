# v1.0.1 Release Publication Prep

Status: in-progress  
Date: 2026-08-14  
Branch: release/prepare-v1.0.1  
Base main: 6630f1f0 (`Refresh handoff state after PR2096 (#2097)`)

## Purpose

Prepare v1.0.1 as the public package publication baseline after the post-1.0
installation, Trusted Publishing, update-path, and local Docker readiness work.
This is a release-prep record only; tag creation, TestPyPI publication, PyPI
publication, PyPI install-claim promotion, and DOI closeout remain separate
guarded steps.

## Version decision

Use v1.0.1 instead of publishing v1.0.0 from the current main state.

Reason: v1.0.0 is already tagged and DOI-verified. Main contains additional
substantive and administrative commits after v1.0.0, including the public
installation readiness work. A patch release keeps the package version aligned
with the source state that will be published.

## Publication targets

The publication accounts and services are intentionally distinct:

| Target | Service | Account | Current state |
|---|---|---|---|
| GitHub | github.com | vfi64 | source repository and release workflow authority |
| TestPyPI | test.pypi.org | vfi1964 | project exists; last observed release 0.2.2 |
| PyPI | pypi.org | vfi64 | project not active yet; pending Trusted Publisher configured |

TestPyPI evidence must not be treated as PyPI availability evidence. The direct
install claim is promoted only after `pypi.org` serves the package and a fresh
environment can run `python -m pip install agentic-project-kit==1.0.1`.

## Remote configuration observed

GitHub environments were readable through the GitHub connector on 2026-08-14:

- `testpypi` exists and has no required reviewer rule.
- `pypi` exists and requires reviewer `vfi64`.

The repository variable `PYPI_TRUSTED_PUBLISHING_ENABLED` was not readable by
the connector (`403 Resource not accessible by integration`). Because the
`pypi` environment requires review, an automatic tag-triggered PyPI job, if the
variable is enabled, still requires human approval before publishing.

## Intended release order

1. Merge the v1.0.1 release-prep PR after local and CI gates pass.
2. Push tag `v1.0.1`; let the Release workflow build artifacts and create the
   GitHub Release.
3. Run Release workflow on ref `v1.0.1` with `publish_target=testpypi`.
4. Smoke-test TestPyPI install.
5. Run Release workflow on ref `v1.0.1` with `publish_target=pypi`, approving
   the `pypi` environment when GitHub asks.
6. Smoke-test real PyPI install.
7. Promote the PyPI install claim, switch public docs to direct PyPI as the
   primary path, and run DOI/post-release closeout as a separate PR.

## Docker boundary

The repository contains a local-source `Dockerfile` for:

```bash
docker build -t agentic-project-kit:local .
docker run --rm agentic-project-kit:local --version
```

No official Docker registry image is claimed. Docker is useful but not a blocker
for the first PyPI publication. This local environment does not currently expose
the `docker` CLI, so the Docker build remains a Docker-host follow-up unless CI
or a maintainer machine runs it.

## Pre-publication claim state

- GitHub source install: documented and claim-backed.
- TestPyPI publication: planned validation step.
- Direct PyPI install: planned, not claimed.
- Docker registry image: not claimed.
