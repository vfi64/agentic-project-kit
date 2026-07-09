Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Repo-backed Work Orders

Status: active
Decision status: accepted

## Purpose

Repo-backed work orders move long implementation instructions out of chat copy-and-paste blocks and into versioned repository artifacts.

The MVP is intentionally small:

- `.agentic/work_orders/<id>.yaml` stores one work order.
- `agentic-kit work-order list` lists available work orders.
- `agentic-kit work-order show <id>` displays the selected work order.
- `agentic-kit work-order check` validates the deterministic work-order contract.
- `agentic-kit work-order run <id>` is dry-run by default.
- `agentic-kit work-order run <id> --execute` runs the stored command only after branch and contract checks.

## Safety Boundary

Work orders must declare an id, title, safety class, expected branch, command, and log path. A bare `exit` token is rejected so generated work orders do not close the user's terminal at the end of a block. Heredoc-style command fragments and inline Python command fragments are rejected.

A work order is not allowed to report success by printing its own PASS marker. The runner owns PASS/FAIL result markers. A work order may only pass after its command returns success and the required contract checks have passed.

## Constitutional Contract

Every executable work order must preserve the project constitution. This is a deterministic MUST, not a recommendation.

The work-order command must include the standard constitutional gates:

- pytest
- ruff check
- check-docs
- doctor

The work order must also declare postconditions that mention:

- pytest
- ruff
- check-docs
- doctor
- log exists
- no false PASS

The expected branch must be a non-main slice branch. The log path must be under `docs/reports/terminal/` and must be listed in `expected_outputs`.

## Next Step

Add checked work-order templates for common read-only gates first. Mutating Git, PR, release, DOI, and finalize flows should use parameterized action specs plus deterministic validators before execution.
