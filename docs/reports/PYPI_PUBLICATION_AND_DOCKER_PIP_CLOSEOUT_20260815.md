# PyPI Publication and Docker Pip Closeout

Date: 2026-08-15  
Status: active closeout evidence for public PyPI installation and Docker pip smoke

## Purpose

Close the remaining public installation gap after the `v1.0.1` release. Earlier
reports intentionally kept direct PyPI installation unclaimed until both the
real PyPI project and a fresh install smoke existed. This report records that
promotion.

TestPyPI and PyPI remain separate services with separate accounts:

- TestPyPI account: `vfi1964`
- PyPI account: `vfi64`
- GitHub owner: `vfi64`

TestPyPI success is validation evidence only. Public installation evidence must
come from `pypi.org`.

## Publication Evidence

- TestPyPI Trusted Publisher: PASS
  - repository: `vfi64/agentic-project-kit`
  - workflow: `release.yml`
  - environment: `testpypi`
- TestPyPI publish run: PASS
  - URL: `https://github.com/vfi64/agentic-project-kit/actions/runs/31880238170`
  - package: `agentic-project-kit`
  - version: `1.0.1`
- PyPI publish run: PASS
  - URL: `https://github.com/vfi64/agentic-project-kit/actions/runs/31880379243`
  - head SHA: `07df47108a4fcf6ba68a2a7b36ef9e27c0cfafa3`
  - result: `success`
  - completed: `2026-08-15T10:49:01Z`
- PyPI package API: PASS
  - package: `agentic-project-kit`
  - version: `1.0.1`
  - project page: `https://pypi.org/project/agentic-project-kit/1.0.1/`

## Install Evidence

Fresh PyPI venv install: PASS

```text
agentic-kit 1.0.1
Name: agentic-project-kit
Version: 1.0.1
Requires: pydantic, pyyaml, rich, typer
```

Docker PyPI install smoke: PASS

Environment:

- base image: `python:3.12-slim`
- local work directory: `/tmp/apk-docker-pypi-install-final.tO20jU`
- install command: `python -m pip install agentic-project-kit==1.0.1`

Result:

```text
agentic-kit 1.0.1
Name: agentic-project-kit
Version: 1.0.1
Location: /work/venv/lib/python3.12/site-packages
Requires: pydantic, pyyaml, rich, typer
```

## User-Facing Documentation Decision

- README and generated website quickstart should now use
  `python -m pip install agentic-project-kit` as the primary public install path.
- GitHub source installation remains a fallback for intentionally testing the
  current repository source projection.
- Managed-repository update instructions should use
  `python -m pip install --upgrade agentic-project-kit` before `doctor`,
  `workspace upgrade`, `check`, and `doctor`.
- No official Docker registry image is claimed. Docker public-install smoke uses
  a standard Python base image and pip from `pypi.org`; local source-image Docker
  usage remains documented separately.

## Boundaries

- Zenodo DOI closeout for `1.0.1` remains separate release lifecycle work.
- PyPI and TestPyPI account names must remain distinct in future automation and
  documentation.
- Publishing an official Docker image remains unclaimed.
