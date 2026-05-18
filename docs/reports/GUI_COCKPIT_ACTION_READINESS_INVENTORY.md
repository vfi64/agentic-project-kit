# GUI Cockpit Action Readiness Inventory

Status: v0.3.24 implementation inventory.

## Implemented result

The initial GUI/Cockpit readiness slice introduces a read-only action metadata layer and a cockpit readiness report.

Implemented files:

- `src/agentic_project_kit/action_registry.py`
- `src/agentic_project_kit/cockpit_readiness.py`
- `tools/cockpit_readiness.py`
- `tests/test_action_registry.py`
- `tests/test_cockpit_readiness.py`
- `./ns cockpit-readiness`

## Safety boundary

- The cockpit readiness path is read-only.
- It renders static metadata only.
- It does not execute workflow actions.
- It does not merge, delete, push, tag, publish, or call GitHub.

## Minimal outcome

- Known actions have explicit safety class metadata.
- Read-only actions are asserted to have `mutation_scope="none"`.
- Local-mutating actions are not marked read-only.
- `./ns cockpit-readiness` provides a deterministic Markdown report for a future local cockpit.

## Deferred intentionally

- No GUI actions.
- No mutating action layer.
- No release, tag, merge, delete, or remote mutation.
