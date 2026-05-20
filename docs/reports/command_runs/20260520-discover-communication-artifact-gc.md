# Communication Artifact GC Discovery

- run_id: 20260520-discover-communication-artifact-gc
- purpose: discover existing GC policy, registry, commands, tests, and artifact directories before hardening
- result: PASS

## Existing GC anchors
- docs/workflow/COMMUNICATION_ARTIFACT_GC.md
- .agentic/communication_artifacts.yaml

## Required next patch scope
- implement or harden deterministic GC classification from the allowlist registry
- add TTL handling per artifact class
- add dry-run and report behavior
- forbid deletion outside allowlisted zones
- forbid symlink following
- protect repo-backed evidence and latest pointers
- add regression tests for delete/no-delete cases

## Terminal log
- docs/reports/terminal/20260520-discover-communication-artifact-gc.log
