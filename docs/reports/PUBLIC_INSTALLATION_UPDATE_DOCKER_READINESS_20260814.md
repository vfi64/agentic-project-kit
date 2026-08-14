# Public Installation, Update, and Docker Readiness

Date: 2026-08-14
Status: active closeout evidence for the post-1.0 public installation slice

## Trigger

External review found that the generated public website and README claimed:

```bash
pip install agentic-project-kit
```

The package name exists in `pyproject.toml`, but the public PyPI project is not
published yet. The release workflow built distributions and attached them to the
GitHub release, but it did not publish to TestPyPI or PyPI.

## Decisions

- Direct PyPI installation is no longer presented as the current supported path.
- The current public install path is GitHub source installation from `main`,
  which matches the generated public documentation.
- The direct PyPI path remains visible as planned work until publication
  evidence exists.
- Release automation now contains gated TestPyPI/PyPI Trusted Publishing jobs
  and does not require long-lived PyPI token secrets.
- Docker usage is supported through a local source-built image. No official
  registry image is claimed.
- `doctor` now reports an actionable warning when a manifest workspace is older
  than the Kit-supported manifest schema.
- The self-hosting manifest was upgraded with
  `agentic-kit workspace upgrade --root . --execute`; the v1 backup is retained
  as `.agentic/config.yaml.bak.v1`.

## User-Facing Paths

Current source install:

```bash
python -m pip install "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit --version
```

Managed-repository update:

```bash
python -m pip install --upgrade "agentic-project-kit @ git+https://github.com/vfi64/agentic-project-kit.git@main"
agentic-kit doctor --root PATH
agentic-kit workspace upgrade --root PATH
agentic-kit workspace upgrade --root PATH --execute
agentic-kit check --root PATH
agentic-kit doctor --root PATH
```

Local Docker image:

```bash
git clone https://github.com/vfi64/agentic-project-kit.git
cd agentic-project-kit
docker build -t agentic-project-kit:local .
docker run --rm -v "/path/to/repo:/work" agentic-project-kit:local doctor --root /work
```

GitHub operations inside Docker require project credentials to be mounted or
configured explicitly for `gh` and SSH. Secrets must not be baked into the image.

## Remaining External Setup

PyPI and TestPyPI publication still require account-side Trusted Publisher
configuration for:

- repository owner: `vfi64`
- repository: `agentic-project-kit`
- workflow: `release.yml`
- environments: `testpypi` and `pypi`
- project name: `agentic-project-kit`

After account-side setup, the workflow can be dispatched with `publish_target`
set to `testpypi`, `pypi`, or `both`. Tag-triggered PyPI publishing remains gated
by the repository variable `PYPI_TRUSTED_PUBLISHING_ENABLED=true`.

## Verification

- Fresh Python 3.13 venv source install from GitHub `main`: PASS.
- `agentic-kit --version` from the fresh source-install venv: PASS,
  `agentic-kit 1.0.0`.
- Isolated package build to `/private/tmp/apk-dist-public-install-readiness`:
  PASS, produced `agentic_project_kit-1.0.0.tar.gz` and
  `agentic_project_kit-1.0.0-py3-none-any.whl`.
- `twine check` against those built artifacts with Twine 7.0.0: PASS.
- Docker image build: not run locally because `docker` is not installed in this
  environment. Static Dockerfile contract tests cover the intended local image
  shape.
- Full test suite: PASS, 2825 passed.
- `ruff check .`: PASS.
- `agentic-kit standard-gates-audit-suite`: PASS.
- `agentic-kit doctor`: PASS overall; workspace schema is current.

## Acceptance

- Public docs do not claim direct PyPI installation as current.
- Site claim evidence verifies the current source-install documentation.
- The planned PyPI path is visible but not claimed as available.
- Release workflow includes `twine check` and Trusted Publishing jobs.
- Docker has a local source image path and keeps official image publication
  unclaimed.
- Workspace schema drift is visible in `doctor`.
- The Kit repository itself no longer reports a workspace-schema currency warning
  after the v1 to v2 upgrade.
