Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Parameterized Actions

Status: active
Decision status: accepted

## Purpose

Parameterized actions define auditable action objects before the project adds more mutating Git, PR, release, DOI, and finalize automation.

The MVP is intentionally metadata-only. It exposes action metadata through
`agentic-kit actions list`, `agentic-kit actions show <id>`, `./ns action-list`,
and `./ns action-show <id>`.

## Safety Boundary

- Action specs are metadata, not executors.
- Dry-run is the default posture.
- Mutating variants require later explicit execute flags, machine-readable preconditions, postconditions, and repo-backed evidence.
- GUI/Cockpit controls should consume these action specs instead of assembling raw shell snippets.
- Any action spec that surfaces a `docs/handoff/CURRENT_HANDOFF.md` mutation
  must identify the WRT-CH-004 action-surface classification, the selected DPA
  lifecycle writer it dispatches through, and the lifecycle command route.
- Action specs must not become an alternative writer for generated or
  command-updated Handoff artifacts. The source command/generator remains the
  owner of those outputs.

## Initial Specs

- `pr-check-merge`
- `release-verify`
- `release-prepare`
- `doi-record`
- `finalize-release`

## DPA Current-Handoff Routing

`release-prepare`, `doi-record`, and `finalize-release` are the only built-in
action specs that may surface a `docs/handoff/CURRENT_HANDOFF.md` mutation.
They are classified as WRT-CH-004 action-surface mutation authority and must
route the actual target-byte change through an already selected lifecycle
writer:

- `release-prepare` routes through WRT-CH-002 via
  `agentic-kit release prepare --write`;
- `doi-record` routes through WRT-CH-003 via
  `agentic-kit post-release-doi-closeout --write`;
- `finalize-release` routes through WRT-CH-001 via the governed transfer
  handoff-refresh flow.

`agentic-kit actions show <id>` renders this routing metadata, and
`agentic-kit governance check` fails if a current-handoff action surface omits
it.

## Next Step

The next slice may add dry-run validators for individual specs. Actual remote mutation remains out of scope until those validators are deterministic and covered by tests.
