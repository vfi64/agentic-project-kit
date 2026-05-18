# Repo-backed Work Orders

Status: active
Decision status: accepted

## Purpose

Repo-backed work orders move long implementation instructions out of chat copy-and-paste blocks and into versioned repository artifacts.

The MVP is intentionally small:

- `.agentic/work_orders/<id>.yaml` stores one work order.
- `agentic-kit work-order list` lists available work orders.
- `agentic-kit work-order show <id>` displays the selected work order.
- `agentic-kit work-order run <id>` is dry-run by default.
- `agentic-kit work-order run <id> --execute` runs the stored command.

## Safety Boundary

Work orders must declare an id, title, safety class, command, and log path. A bare `exit` token is rejected so generated work orders do not close the user's terminal at the end of a block.

This MVP does not replace action validators. Mutating work orders still need explicit review, logs, and deterministic postconditions before they become routine automation.

## Next Step

Add checked work-order templates for common read-only gates first. Mutating Git, PR, release, DOI, and finalize flows should use parameterized action specs plus deterministic validators before execution.
