# Docker Local Smoke

Status: active evidence  
Date: 2026-08-14  
Scope: local source-built Docker image for `agentic-project-kit` after Docker
became available on the maintainer Mac

## Purpose

Close the Docker-host follow-up from
`docs/reports/V1_0_1_RELEASE_PUBLICATION_PREP_20260814.md`. That report could
only inspect the Dockerfile statically because the local Docker CLI was not
available. This report records the first local Docker build and runtime smoke.

No official Docker registry image is claimed. The supported Docker path remains
a local source-built image.

## Environment

- Docker CLI: `Docker version 29.7.2, build a7dcaa6`
- Docker server: `29.7.2`
- Base image: `python:3.12-slim`
- Built image: `agentic-project-kit:local`
- Kit version inside image: `agentic-kit 1.0.1`
- Image install mode: `python -m pip install ".[dev]"` so local self-hosting
  gate checks have `pytest` and `ruff` available.

## Commands

```bash
docker pull python:3.12-slim
docker build -t agentic-project-kit:local .
docker run --rm agentic-project-kit:local --version
docker run --rm agentic-project-kit:local doctor --help
docker run --rm -v /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit:/work:ro agentic-project-kit:local doctor --root /work
docker run --rm -v /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit:/work:ro agentic-project-kit:local transfer command-reference-check --json
docker run --rm -v /private/tmp/apk-docker-smoke:/work agentic-project-kit:local init docker-greenfield --type generic --description "Docker greenfield smoke" --license MIT --kit-source none
docker run --rm -v /private/tmp/apk-docker-smoke:/work agentic-project-kit:local doctor --root /work/docker-greenfield
docker run --rm -e GIT_AUTHOR_NAME=Agentic -e GIT_AUTHOR_EMAIL=agentic@example.invalid -e GIT_COMMITTER_NAME=Agentic -e GIT_COMMITTER_EMAIL=agentic@example.invalid -v /private/tmp/apk-docker-smoke-v3:/work agentic-project-kit:local init with-identity --type generic --description "Docker identity smoke" --license MIT --kit-source none
```

## Results

- Docker daemon access: PASS after running Docker commands outside the local
  sandbox.
- Initial base image fetch: RETRY, first metadata lookup timed out, direct
  `docker pull python:3.12-slim` later succeeded.
- Docker build: PASS with dev gate dependencies.
- Container CLI version: PASS, `agentic-kit 1.0.1`.
- Container CLI command discovery: PASS, `doctor --help` and top-level `--help`
  are available.
- Mounted self-hosting repo doctor: PASS overall after the executable fallback
  and dev-dependency image changes.
- Mounted read-only command-reference check: PASS; pytest reports a harmless
  cache-write warning because `/work` is read-only.
- Greenfield project generation inside Docker: PASS for file creation and
  generated doctor.
- Greenfield project generation with Git identity: PASS, created initial commit
  `Initialize agentic project`.

## Findings

### Host virtualenv executables do not port into the container

When the self-hosting repo is mounted read-only into the container, the
host-side `.venv/bin/agentic-kit` path exists but its shebang points to the host
Python installation. That executable is not runnable inside the container.

Fix: the standard-gates audit launcher now falls back from an unusable local
`.venv/bin/agentic-kit` shebang to the `agentic-kit` executable installed in the
container image.

Follow-up fix: `transfer command-reference-check` and
`transfer command-reference-refresh` now use a shared Python executable helper
that falls back from an unusable local `.venv/bin/python` to the active
container interpreter.

Image fix: the local Docker image now installs the Kit with `".[dev]"` so the
self-hosting command-reference check can run `pytest` inside the container.

### Docker init needs an explicit Git identity for the initial commit

`agentic-kit init` creates project files in Docker, but the convenience initial
commit cannot be created unless Git has an author/committer identity.

Fix: `agentic-kit init` now reports a Kit-level warning when `git add` or
`git commit` fails during the initial convenience commit. The generated files
remain available, and the warning names the follow-up command.

Documentation: README and the generated Quickstart now include Docker
environment variables for `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`,
`GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL`.

## Verification

- Targeted tests: `97 passed`.
- Full test suite: `2829 passed, 634 warnings`.
- Local standard-gates audit suite: PASS.
- Local doctor: PASS overall.
- Docker build: PASS with `".[dev]"`.
- Docker `--version`: PASS.
- Docker mounted self-hosting doctor: PASS overall after the fallback and
  dev-dependency fixes.
- Docker mounted command-reference check: PASS, `2 passed`.
- Docker greenfield init: PASS for generated files; initial commit warning path
  now covered by tests.
- Docker greenfield init with identity: PASS, initial commit exists.

## Remaining boundaries

- No official registry image is claimed.
- GitHub operations inside Docker still require explicit `gh` and SSH
  credentials.
- TestPyPI publication is still blocked by account-side Trusted Publisher
  configuration for the `testpypi` environment.
- Direct PyPI installation remains unclaimed until `pypi.org` package evidence
  exists.
