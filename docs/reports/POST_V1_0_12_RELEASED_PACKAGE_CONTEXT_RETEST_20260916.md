# Post-v1.0.12 Released-Package Context Retest

Status: implementation blocker confirmed; repair prepared for v1.0.13  
Date: 2026-09-16  
Package under test: `agentic-project-kit==1.0.12` from PyPI  
Machine-readable companion:
`docs/reports/POST_V1_0_12_RELEASED_PACKAGE_CONTEXT_RETEST_20260916.json`

## Scope

This was a real first-contact test of the published v1.0.12 package in a
throwaway `python:3.13-slim` Docker container. Docker Desktop was available
with engine version `29.7.2`. No repository or host directory was mounted.

The test covered installation, generated-project initialization, `check`,
`doctor`, context-carrier refresh, and the fresh-context gate.

## Results

| Step | Result |
|---|---|
| PyPI installation of `1.0.12` | PASS |
| `agentic-kit --version` | PASS |
| `agentic-kit init` | PASS |
| `agentic-kit check` | PASS |
| `agentic-kit doctor` | PASS |
| Initial fresh-context gate before carriers exist | BLOCKED as expected |
| `transfer refresh-llm-context-carriers` | PASS |
| Fresh-context gate after refresh | BLOCKED unexpectedly |

The unexpected blocker was `source_hashes_incomplete`. The generated project
contains `.agentic/project.yaml`, but it intentionally does not contain the
Kit development checkout's canonical internal source files. v1.0.12 treated
that generated project as self-hosting for this gate, so the installed-package
first cycle could not complete after the prescribed refresh step.

## Repair boundary

The repair introduces an explicit `generated_project` workspace mode and a
shared `is_external_operating_workspace` predicate. This keeps the existing
manifest-based external workspace semantics intact while making Kit-internal
source hashes optional for generated projects. The gate still requires fresh,
hash-consistent carriers and still blocks mismatched or malformed evidence.

The same slice hardens live release publication: an existing remote tag is
accepted only when its resolved target matches the current `HEAD`; otherwise
the release plan fails closed.

## Greenfield boundary

This report does not claim v1.0.12 closes `KIT-GF-017`. It records the
released-package blocker that v1.0.13 must repair and revalidate. `KIT-GF-009`
and `KIT-GF-011` retain their separate external first-cycle/released-package
evidence requirements.
