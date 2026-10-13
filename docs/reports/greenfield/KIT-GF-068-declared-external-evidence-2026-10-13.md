---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-068: declared external evidence contexts for the legacy-reference audit

Date: 2026-10-13
Kit state: CLOSED in candidate; planned fix release 1.0.25.
Consumer VERIFIED_FIXED remains an independent retest decision.
Manifest ACK: COMMAND_MANIFEST_ACK 9633a3a680ad; CLI declarations unchanged.

## Finding and repair

An external findings ledger quoting ./ns references was classified needs_review
and blocked release readiness unless its text happened to contain a historical
marker. External manifest workspaces can now declare audit.ns_legacy.evidence_paths
in .agentic/config.yaml. The audit classifies matching paths as declared_evidence
using case-sensitive fnmatchcase over the whole root-relative POSIX path, without
examining wording or adding content heuristics. Existing classifications remain
unchanged elsewhere; without a declaration the behavior matches 1.0.24. The Kit
development checkout ignores these extra contexts and retains its own lists.

The focused ns_legacy_audit_config module validates nested keys and path types,
rejecting absolute, parent-relative, backslash and malformed paths. Workspace
loading retains an immutable sorted/deduplicated tuple. Invalid declarations
block the CLI with exit 2 and a JSON configuration diagnostic, without traceback.
No audit file is changed by this read-only command.

## Declaration and limits

Use a narrow exact evidence path, for example:

```yaml
audit:
  ns_legacy:
    evidence_paths:
      - docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json
```

Globs use fnmatchcase semantics: *, ? and character sets are supported; * may
match a slash. Matching is case-sensitive and applies to the whole relative path.
The owner declares a path's evidence role; a broad pattern also trusts any active
instructions inside that matched file. This is an explicit scope declaration,
not proof that arbitrary file content is harmless. Prefer exact ledger paths;
keep executable scripts outside the declaration. No automatic detection or
Cockpit wording workaround is used.

## Regression and expected external retest

Tests: tests/test_ns_legacy_external_evidence.py plus the existing legacy audit
and workspace foundation tests. An installed-wheel external fixture contains
synchronized command references and no Kit tests or documentation registry.
Its ledger quotes both ./ns references and imperative-looking text: undeclared
it blocks, declared it passes deterministically. An active script in the same
fixture still blocks. Malformed declaration also blocks. A released 1.0.24 wheel
and candidate wheel audit exactly the same undeclared workspace: their complete
JSON outputs and exit codes match. A simulated Kit checkout confirms that an
external declaration cannot override the Kit's existing contexts.

In a disposable clone, preserve the real findings ledger, declare only its
exact path, then run:

```text
agentic-kit audit-ns-legacy-references --root . --json
```

Require status PASS, blocker_count 0 and declared_evidence for the matching
ledger references. Add an active legacy invocation to a separate test script:
require status BLOCK and a blocker for that script. Remove that control and the
declaration: the unmodified ledger must retain the old BLOCK classification.
This retest does not claim an entire live release or consumer VERIFIED_FIXED.
