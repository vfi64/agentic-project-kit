# K0c — Protection mechanisms and their static reach

Product source `99e5038b2d7b88488561fb14b19b96dcbc71da09`; manifest `84540b010909`.

Working vocabulary: orchestrators; primitives and diagnostics; protection mechanisms. Kernel still means L0. No Microkernel claim or architecture-contract change.

| Mechanism | Static command roots | Non-READ_ONLY roots | Direct test references |
|---|---:|---:|---:|
| agentic_project_kit.rule_ack:validate_rule_acknowledgement | 19 | 17 | 6 |
| agentic_project_kit.workspace_lock:workspace_mutation_lock | 17 | 17 | 0 |
| agentic_project_kit.safe_push:safe_push | 16 | 16 | 6 |
| agentic_project_kit.evidence_guard:check_change_scope | 1 | 1 | 3 |
| agentic_project_kit.evidence_guard:check_terminal_log | 1 | 1 | 6 |
| agentic_project_kit.workspace_lock:acquire_workspace_lock | 29 | 29 | 4 |

## Interpretation

Of 186 non-READ_ONLY entries, 29 statically reach either named lock entry point. 157 have no such in-process witness in this graph. Neither denominator nor complement is a count of mutators or confirmed defects.

The semantic alias reaches the same underlying lock via its implementation; 0 alias-only roots and 12 roots using the underlying entry without the alias are recorded. Looking only for workspace_mutation_lock misses legitimate acquire_workspace_lock calls.

The unchanged mutation_lock_audit reports PASS: 0 blocking and 666 review-visible findings. Its classification summary and original findings remain in the JSON. The LC3 blocking scope is enforced core runtime mutators, while other categories are explicitly advisory; text-marker acceptance is not proof of runtime execution.

The lock source uses holder PID and process-local reentrancy depth. It does not grant subprocesses inherited lock ownership. Existing ensure_remote_head regression explicitly prevents an outer lock around a child push. Do not use generic child-inheritance as an explanation without a concrete path.

The JSON includes every reached command with a shortest potential function witness. The five named mechanisms are a review focus, not an exhaustive safety core. No claim that every mutation necessarily passes a common kernel can be made from these data.

## Regression mapping

Direct imported calls in named tests are linked in each mechanism record; test-node names and lines allow review of assertions and fixtures. The underlying-lock row includes family-level tests for the semantic alias. Contract tests in tests/test_mutation_lock_enforcement_contract.py and classifier tests in tests/test_mutation_lock_audit.py and tests/test_mutation_lock_finding_taxonomy.py cover a different, source-marker boundary. Ordinary regression execution is recorded separately in validation.json.

## Consumer check

Owner-local Cockpit source at `7f4cfe21d2db494a869dd8e5257a34de7087c49b`: 454 tracked runtime/config/test files scanned; dedicated taxonomy-token occurrences: `{"command-taxonomy-check": 0, "command_taxonomy": 0, "composition_level": 0, "recommendation_weight": 0}`. Generic manifest references occur in 11 files. This is a bounded literal source search, not proof that generic dispatch or external callers never use taxonomy; private source content and local paths are omitted.

## Remaining boundary

K0 literal argv and potential_command_closure still mix runner-bound calls, data construction, dry-run options and recommendations. K0c deliberately does not convert those fields into execution edges. G0 remains blocked on this distinction and an explicit terminology decision. W0a evidence-integrity repair is independent.

- Static in-process may-reachability, not mandatory execution, coverage or a count of unprotected mutators.
- Does not cross subprocess boundaries or distinguish recommendations from executable argv. No execution diagram can be inferred.
- BOUNDED is not a mutator classification. tmp/report writes, aliases and primitive delegation need separate adjudication.
- Existing LC3 audit uses textual markers and blocks only its declared core runtime-mutator bodies; PASS is not universal lock proof.
- Lock reentrancy is same-process (PID/depth). Cross-process inheritance is not supplied by workspace_lock.py.
- Direct imported test calls omit helpers/module-attribute calls and do not prove every branch tested.

Reproduce with scripts/protection_mechanism_audit.py using the pinned product source and an owner-local --consumer-root; historical map_callbacks.py and analyze.py are reused unchanged. No Kit callbacks, simulations, paid agents or remote consumer actions are run.
