---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-063: custom CI runtime plan

Date: 2026-10-13
Kit state: CLOSED in candidate; planned fix release 1.0.25. Consumer VERIFIED_FIXED remains independent.

## Finding and repair

Customized CI cannot adopt the managed template without overwriting its own jobs.
The read-only ci runtime-plan command resolves two exact local Git commits and a
NUL-delimited no-renames diff, then delegates to the existing manifest-derived
workspace classifier. Only its ADMIN_REFRESH_LIGHT result becomes mode=light;
every unknown ref, malformed manifest, unsafe/unknown path, wrong branch or
non-PR event becomes full. The route performs no network access or mutation.
Branch/event are explicit arguments or observable GitHub event environment
values; absent metadata stays full. Exit 0 returns one verdict, including safe
full fallback. Missing required CLI arguments exit 2. --json is one JSON document.

## Regression and external retest

tests/test_ci_runtime_plan.py executes the installed wheel in external Git
fixtures with synchronized command references, no Kit tests/registry and a
custom workflow. It tests refresh-only light, product/full, wrong branch/full,
unknown ref/full, non-PR/full and malformed manifest/full. It parses the actual
documented custom workflow fixture: check has no condition/dependency; both
heavy jobs use always() plus the exact non-light condition, including classifier
failure fallback. The workflow bytes remain unchanged by the classifier.

From a disposable consumer PR checkout:

```text
agentic-kit ci runtime-plan --base {base_sha} --head {head_sha} --branch docs/post-pr42-handoff-refresh --event-name pull_request --json
```

Require mode=light only for manifest-derived administrative paths. Add one
product path, alter the branch, or use an unknown ref and require mode=full.
The custom workflow fragment in HUMAN_WORKFLOW_COMMANDS.md preserves owner
toolchain setup and dependencies; it does not overwrite or install workflows.
No live GitHub or Cockpit CI execution is claimed by the local fixture.

Manifest ACK: COMMAND_MANIFEST_ACK 9633a3a680ad, generated via Kit entrypoint, successor-package and docs/site routes.
