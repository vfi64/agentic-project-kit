---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-RULE-REGISTRY-BOOTSTRAP: external applicability and signed bootstrap

Date: 2026-10-13
Kit state: CLOSED in the candidate implementation; intended fix release 1.0.25.
External VERIFIED_FIXED remains the consumer's decision after retesting.

## Finding and repair

An initialized external workspace has no Kit-internal mechanism inventory,
migrations or repository tests. Previously check hard-failed and report raised
FileNotFoundError. Check and report now return NOT_APPLICABLE with the exact
bootstrap route when the external inventory is absent. Malformed or unproved
inventories return BLOCKED as structured JSON.

The bootstrap derives a separate Kit-managed projection from three explicit
shipped mechanisms: workspace contract loading, rule acknowledgement validation
and command-manifest authority. Each entry records an installed module/function
and the declared workspace surface, with content hashes. Missing evidence is
excluded with a reason. Project capsule semantics and local test coverage are
never inferred. The existing self-hosting registry and reviewed register route
remain separate. An existing manual inventory is preserved.

The write requires a signature over the workspace, previous target bytes and
derived evidence. A workspace lock and atomic replacement protect the write;
stale signatures and modified inventories block. Init, adopt and kit update
name the bootstrap as their next action. No network access is involved.

## Regression and external retest

`tests/test_external_rule_registry.py` builds and installs the candidate wheel
in fresh and already initialized external fixtures, with a synchronized command
reference, no Kit tests and no Kit documentation registry. The initialized
fixture includes customized pytest/Playwright CI, which is preserved.

Run from the initialized external repository, using the installed 1.0.25 CLI:

```text
agentic-kit commands sync-entrypoints --execute --json
agentic-kit rule-registry check --json
agentic-kit rule-registry report --json
agentic-kit rule-registry bootstrap --json
agentic-kit rule-registry bootstrap --execute --expected-signature <approval_signature> --json
agentic-kit rule-registry check --json
agentic-kit rule-registry report --json
agentic-kit rule-registry bootstrap --json
```

Before bootstrap, check/report must return result_status=NOT_APPLICABLE and a
next_action pointing at bootstrap. The first plan returns PLANNED; signed write
returns PASS/written=true; check/report then return PASS. Replanning is PASS
with changed_paths=[] and a signed repeat returns written=false. Adding an
unproved mechanism, modifying evidence, malformed YAML and a stale signature
must return BLOCKED without overwriting evidence. Missing surfaces must be
named in excluded and must not become invented active mechanisms.

Manifest ACK: `COMMAND_MANIFEST_ACK 8694ff3e27ef`, generated through
commands sync-entrypoints. Native GUI or public release
acceptance is not claimed by these inventory checks.

The existing Kit readiness-ACK refresh also aligns the DPA readiness record with
this manifest. It changes only the ACK field, preserving Maintainer decisions.
