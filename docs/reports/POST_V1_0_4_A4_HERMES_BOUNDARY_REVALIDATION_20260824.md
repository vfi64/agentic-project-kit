# Post-v1.0.4 A4 Hermes Boundary Revalidation

Status: done  
Date: 2026-08-24  
Branch: codex/a4-hermes-boundary-revalidation  
Disposition: already_satisfied

## Scope

A4 revalidates that `agentic-project-kit` core behavior does not depend on
Claude CLI, Codex CLI, Hermes, or another concrete agent runtime. The check is
report-only unless the fresh repository state shows an acceptance or
implementation gap.

## Fresh Evidence

- `docs/planning/PROJECT_DIRECTION.yaml` still records
  `planner-kit-executor-hermes-integration` as `done`.
- `pyproject.toml` runtime dependencies are limited to `typer`, `rich`,
  `pyyaml`, and `pydantic`; there is no Hermes runtime dependency.
- The active virtual environment has no `hermes`, `hermes-cli`, or
  `hermes_cli` distribution, and `importlib.util.find_spec()` returns `None`
  for `hermes` and `hermes_cli`.
- `docs/architecture/PLANNER_KIT_EXECUTOR_CONTRACT.md` defines Hermes only as
  the first named executor/browser adapter and keeps step resolution under the
  generated command manifest or cockpit/action registry.
- `src/agentic_project_kit/planner_executor.py` stores `hermes` as an adapter
  string only. It imports no Hermes package or CLI module.
- `tests/test_planner_executor.py` rejects non-`agentic-kit` command steps,
  verifies cockpit/manifest authority resolution, keeps `executor run`
  dry-run-by-default, and gates bounded actions with both intent and CLI allow
  signals.
- `docs/ONBOARDING.md` routes first-chat users through Kit commands
  (`init`, `workspace adopt/init`, `check`, `doctor`, `command-for`) and does
  not describe Hermes as a standard or required path.
- `agentic-kit doctor` returns `Overall: PASS`. Its only warning is the
  existing document lifecycle report-only class; it does not mention Hermes.

## Smoke Results

The fresh smoke intent used `executor_adapter: hermes` and a single
`agentic-kit check-docs` command step.

- `agentic-kit executor plan tmp/a4-hermes-boundary-intent.yaml --json`:
  `result_status=PASS`, `authority=command_manifest`, `safety=READ_ONLY`,
  `dirty_state=clean`.
- `agentic-kit executor run tmp/a4-hermes-boundary-intent.yaml --json`:
  `result_status=PENDING`, `returncode=0`, `executed=false`, message
  `Dry-run only. Re-run with --execute to execute allowed steps.`
- `agentic-kit onboarding measure --json`: `status=PASS`,
  `finding_count=0`.
- `python -m pytest -q tests/test_planner_executor.py
  tests/test_onboarding_measurement.py`: `11 passed`.

The smoke files were temporary `tmp/` evidence and were removed after the
check.

## Drift-Way Classification

| Drift way | Result |
|---|---|
| Hermes becomes a runtime dependency | Not present in `pyproject.toml`; not importable from the active venv. |
| A core command requires Hermes | No runtime import or CLI call exists; executor steps resolve through Kit authorities. |
| `doctor` warns or fails without Hermes | `doctor` is `Overall: PASS` without a Hermes package installed. |
| Onboarding makes Hermes standard or required | Not present in `docs/ONBOARDING.md`; first routes use Kit commands only. |
| GUI or agent safety assumes Hermes | Planner-executor contract requires manifest/cockpit authority and explicit capability boundaries. |
| Core adoption surface depends on one executor | The executor surface accepts adapter labels but executes only Kit-owned manifest/cockpit steps. |

## Decision

Disposition is `already_satisfied`.

No acceptance gap or implementation gap was found. Do not reopen the historical
`planner-kit-executor-hermes-integration` Direction item or duplicate its
completed evidence. The active post-v1.0.4 work program can mark A4 as done
with this report as the current revalidation evidence.
