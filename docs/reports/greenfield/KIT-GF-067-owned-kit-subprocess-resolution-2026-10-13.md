---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-067: owned Kit resolution in release and transfer diagnostics

Date: 2026-10-13
Kit state: CLOSED in candidate; planned fix release 1.0.25.
Consumer VERIFIED_FIXED remains independent.

## Finding and repair

Standard-error-scan, transfer next actions and related closeout routes invoked
./.venv/bin/agentic-kit literally. Missing local environments raised executable
errors despite an intact installed Kit elsewhere. All active source invocations
now share cli_executable resolution: GF-021 workspace-local/declared interpreter
candidates, then running Kit and compatible PATH fallback. Unrunnable scripts
are rejected. POSIX and Windows running-entrypoint suffixes are covered.
The scan runs child commands in its selected project root. Planner/executor,
GUI and closeout adapters reuse the same core instead of duplicate discovery.
Generated handoff/task/context instructions use the generic Kit command; native
GUI terminal plans resolve that command for the actual selected workspace.

DPA readonly probe commands remain explicit probe declarations, but execution
uses the shared local-owned-only resolver. Its fixed probe contract excludes
declared outside installations and running/global fallback. No DPA approval, assessment decision,
probe permission or publication policy is broadened.

## Regression and expected external retest

tests/test_external_kit_resolution.py creates real virtual environments inside
and outside .venv, installs the candidate wheel, synchronizes references and
requires kit status PASS. Standard-error-scan and release ready both return PASS,
and logged child calls prove selected executable/root propagation. Context and
publication observations are explicitly controlled; other local gates execute
the installed wheel. No network or live release acceptance is claimed.
There are no Kit tests or documentation registry in either external fixture.
tests/test_cli_executable_resolution.py checks owned precedence, unrunnable
negative controls, owned-only refusal, suffixes, native terminal resolution and
absence of literal ./.venv/bin/agentic-kit source instructions/actions.
Existing workflow, GUI, DPA, executor and handoff regressions remain required.

From a disposable initialized release workspace with valid native metadata,
tracking main, prior release tag and current approved context:

```text
agentic-kit kit status --json
agentic-kit transfer standard-error-scan --before-release --version {version} --json
agentic-kit release ready --version {version} --json
```

Run with the Kit in a declared outside interpreter and then in .venv. Require
PASS with no FileNotFoundError or literal-path dependency. A real unrelated
context/release gate failure remains blocking; this repair does not turn it
into PASS. Local Kit availability must take precedence over the declared one;
unrunnable paths must not be executed. Native Windows GUI acceptance is not
claimed by suffix unit tests.

## Scope and modularity

Core selection is isolated in cli_executable; CLI/GUI adapters are thin. The
large legacy transfer modules remain a monolith risk. Review-only extraction
exception: moving their full orchestration would exceed this executable-path
repair; the next safe extraction is standard-error-scan orchestration into a
focused importable module with the existing regression boundary preserved.
Manifest ACK: COMMAND_MANIFEST_ACK 9633a3a680ad; declarations are unchanged.
