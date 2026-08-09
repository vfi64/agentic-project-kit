# S4b.2 Site Claim-Evidence Projection Contract

Date: 2026-08-09

Base before S4b.2: `0d1070b35d3658065fa2c59b4efd47b84decedbc`
(`Refresh handoff state after PR2030 (#2031)`).

## Scope

S4b.2 adds computed claim evidence to the generated website. It does not deploy
GitHub Pages and does not add the final presentation layer.

## Contract

- `site/content/claims.yaml` is curated claim content, not a verified-state
  store.
- Claims may contain `id`, `text`, `required`, optional `planned`, and evidence
  bindings.
- Stored derived `status` or `verified` fields are forbidden.
- The build computes `verified`, `unverified`, and `planned` statuses.
- Required claims block the build when not verified.
- Optional claims render as `unverified` without blocking unrelated publication.

## Evidence Types

Implemented evidence types:

- `pyproject-entrypoint`
- `pyproject-value`
- `command-manifest`
- `pytest-node`
- `command-probe`
- `generated-artifact`

`pytest-node` evidence executes the named test node. `generated-artifact`
evidence checks manifest command coverage against the in-memory generated
catalog; file existence alone is not accepted as technical evidence.

## Initial Claims

The initial claim file contains ten claims:

- CLI entry point.
- GUI entry point.
- Python requirement.
- Package version.
- Command manifest synchronization.
- Artifact GC dry-run behavior.
- Workspace adopt read-only behavior.
- Workspace init preview/execute behavior.
- Successor handoff package generation.
- Generated website command catalog coverage.

Required deployment-integrity claims are the CLI entry point, Python
requirement, package version, command manifest synchronization and generated
command catalog coverage.
