# Docker/PyPI First-Contact Validation for agentic-project-kit 1.0.1

Status: historical evidence  
Date recorded: 2026-08-20  
Tested artifact: `agentic-project-kit==1.0.1` from the public PyPI index  
Evidence type: Historical PyPI Validation

## Purpose

This report preserves the anonymized first-contact validation of the first
public PyPI release. It records what was typed and observed in an isolated
Docker container. It is historical evidence for the published `1.0.1` package,
not a claim about later source changes.

The report is authoritative for the observed test steps and outputs. Root-cause
analysis and fixes remain governed by the current repository state.

## Isolation Boundary

The test used a disposable Docker container started with `--rm`.

The container did not mount the local development checkout, did not use a local
`.venv`, did not clone the GitHub repository, did not read local repository
files, did not mutate the local repository, and did not mutate the GitHub
remote.

## Host and Docker Baseline

Observed Docker CLI:

```text
Docker version 29.7.2
```

`docker info` showed Docker Desktop running a Linux engine on `aarch64`.

Baseline command:

```bash
docker run --rm hello-world
```

Observed result:

```text
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

Result: PASS

## Fresh Python Container

Container command:

```bash
docker run --rm -it python:3.13-slim bash
```

Inside the container:

```bash
python --version
pip list
which agentic-kit
```

Observed:

```text
Python 3.13.15

Package Version
------- -------
pip     26.2.1
```

`which agentic-kit` returned no path before installation.

Result: PASS

## PyPI Installation

Command:

```bash
pip install agentic-project-kit
```

Observed excerpt:

```text
Downloading agentic_project_kit-1.0.1-py3-none-any.whl
Successfully installed agentic-project-kit-1.0.1
```

The pip warning about running as root was treated as expected for a short-lived
container.

Result: PASS

## Version and Package Metadata

Commands:

```bash
agentic-kit --version
python -m pip show agentic-project-kit
```

Observed:

```text
agentic-kit 1.0.1
```

Package metadata excerpt:

```text
Name: agentic-project-kit
Version: 1.0.1
Summary: Govern AI-assisted repository work with explicit contracts, gates, evidence, and handoffs.
License-Expression: MIT
Location: /usr/local/lib/python3.13/site-packages
Requires: pydantic, pyyaml, rich, typer
```

Result: PASS

## Empty Test Directory

Commands:

```bash
mkdir /test
cd /test
ls -la
```

The directory contained only `.` and `..`. It had no Kit workspace, no generated
project, and no Git repository.

## CLI Help Outside a Workspace

Command:

```bash
agentic-kit --help
```

The command rendered help successfully, including `init`, `check`, `doctor`,
and `workspace`. No `LegacyProfileDeprecationWarning` appeared.

Result: PASS

## Finding F1: Empty-directory check crash

Command:

```bash
agentic-kit check
```

Observed sequence:

```text
LegacyProfileDeprecationWarning:
agentic-kit implicit legacy profile is deprecated for manifest-less workspaces
and will be removed in 2.0.0
```

Then an internal traceback reached:

```text
check_command
-> check_all(root)
-> check_todo(project_root)
-> load_yaml(project_root / "sentinel.yaml")
```

The command ended with:

```text
FileNotFoundError: Missing config file: /test/sentinel.yaml
```

Result: FAIL

Historical interpretation: a completely empty non-workspace was not handled as
a public CLI state. It fell through into legacy repository-state checks.

## Init Help

Command:

```bash
agentic-kit init --help
```

Observed:

```text
Usage: agentic-kit init [OPTIONS] [name]

Create a governed project skeleton with selected profiles and policy packs.
```

The default project type was `python-cli`, GitHub repository creation defaulted
to `--no-github`, and generated CI defaulted to the `pypi` Kit source.

Result: PASS

## Finding F2: Missing Git init crash

Command in the minimal container:

```bash
cd /test
agentic-kit init demo-project
```

A neutral description was entered. The command reached:

```text
subprocess.run(["git", "init"], cwd=target, check=False)
```

The container did not include Git, and the command ended with:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'git'
```

Result: FAIL

Historical interpretation: missing Git is an environmental prerequisite issue,
but `1.0.1` exposed it as an internal Python traceback.

## Git Installed in the Container

Commands:

```bash
apt-get update
apt-get install -y git
git --version
```

Observed:

```text
git version 2.47.3
```

Result: PASS

## Finding F3: Git identity failure masked by success exit

After deleting the partial in-container target:

```bash
cd /test
rm -rf demo-project
agentic-kit init demo-project
```

Observed:

```text
Initialized empty Git repository in /test/demo-project/.git/
Created project: /test/demo-project
Recommended profiles:
generic-git-repo, markdown-docs, python-cli, git-github
Recommended policy packs:
starter, solo-maintainer, agentic-development
```

Then Git reported:

```text
Author identity unknown
fatal: unable to auto-detect email address
```

The Kit still printed the `Next:` instructions. Immediately afterward:

```bash
echo $?
```

Observed:

```text
0
```

Result: PARTIAL / UX FAILURE

Historical interpretation: the generated project files were present, but an
initial Git follow-up failed fatally while the overall command returned success.

## Generated Project Contents

Observed generated paths included:

```text
.agentic/
.git/
.github/
.gitignore
.pre-commit-config.yaml
AGENTS.md
CHANGELOG.md
README.md
docs/
pyproject.toml
scripts/
sentinel.yaml
src/
tests/
```

## Finding F4: Fresh generated project triggers legacy warning

Inside the newly generated project:

```bash
agentic-kit check
```

Observed:

```text
LegacyProfileDeprecationWarning:
agentic-kit implicit legacy profile is deprecated for manifest-less workspaces
and will be removed in 2.0.0
```

Then:

```text
Agentic project check passed
```

Result: PASS with unexpected warning

Next:

```bash
agentic-kit doctor
echo $?
```

Observed doctor excerpts:

```text
[WARN] workspace manifest: .agentic/config.yaml absent
[WARN] workspace schema: .agentic/config.yaml absent
[PASS] documentation gates: passed
[PASS] document lifecycle audit: passed
[PASS] todo gates: passed
[SKIP] standard audit suite: skipped outside the agentic-project-kit development checkout
[PASS] version drift: project state matches version 0.1.0

Overall: PASS
```

The same `LegacyProfileDeprecationWarning` appeared before the report. The exit
code was `0`.

Result: PASS with unexpected generated-project legacy warning and operating-layer
manifest warnings

Historical interpretation: `init` produced a generator-mode project with
`.agentic/project.yaml`, while operating-layer diagnostics looked for
`.agentic/config.yaml`. This matches the generator-vs-operating-layer boundary
documented in `docs/reports/POST_0_5_0_GREENFIELD_B2_20260811.md`, but the
first-contact UX in `1.0.1` made a freshly generated project look implicitly
legacy.

## Result Matrix

| Test | Result |
|---|---|
| Docker Engine reachable | PASS |
| `hello-world` | PASS |
| fresh `python:3.13-slim` | PASS |
| Kit absent before install | PASS |
| `pip install agentic-project-kit` | PASS |
| PyPI version `1.0.1` installed | PASS |
| `agentic-kit --version` | PASS |
| package metadata | PASS |
| `agentic-kit --help` outside workspace | PASS |
| `agentic-kit check` in empty directory | FAIL: internal traceback |
| `agentic-kit init` without Git | FAIL: internal traceback |
| Git system prerequisite installed | PASS |
| `agentic-kit init` with Git but no Git identity | PARTIAL: files created, Git fatal, exit 0 |
| skeleton generated | PASS |
| `agentic-kit check` in generated project | PASS with unexpected legacy warning |
| `agentic-kit doctor` in generated project | PASS with workspace warnings |
| container exit with `--rm` | PASS |

## Current-main Classification

The current source slice rechecked the four findings against repository code
instead of assuming `main == 1.0.1`.

- F1 still existed before this slice: empty-directory `check` reached
  `sentinel.yaml` through repository-state fallback.
- The related non-workspace `doctor` behavior had the same missing public-state
  classification, although it already produced a controlled FAIL instead of the
  exact `check` traceback.
- F2 still existed before this slice in `templates.create_project`: missing
  `git` could raise `FileNotFoundError`.
- F3 had already been partially improved after `1.0.1`: the initial commit
  failure path prints a Kit-level warning and returns success because file
  generation is the success guarantee, while the initial commit is a convenience
  step.
- F4 still existed before this slice: generated projects use
  `.agentic/project.yaml`, but `check`/`doctor` could still emit legacy-profile
  warnings or operating-layer manifest warnings.

## Evidence Boundary

This report is type A evidence: Historical PyPI Validation for the already
published `1.0.1` artifact.

Post-fix tests against a local checkout or locally built wheel must be labeled
type B: Post-fix Build/Checkout Validation.

Only a later release installed again from the public PyPI index may be labeled
type C: Post-release PyPI Validation.
