# Command references: execution or recommendation

Pinned source: `095dfe46028b379acc41102375fe6f49f6bd583d`; manifest `03ed2061b3db`.

Analysis: **BOUNDED_STATIC_INCOMPLETE**, converged in 9 rounds.

Counts describe source reference sites, not executed calls or runtime coverage.

| Site classification | Count |
|---|---:|
| execution | 54 |
| recommendation | 18 |
| unknown | 306 |

## Known-case controls

| Control | Result |
|---|---|
| adopt_bootstrap_is_guidance | PASS |
| adopt_does_not_execute_bootstrap | PASS |
| sync_main_acknowledges_rules | PASS |

## Command-level source flows

These are statically resolved helper flows; empty columns do not prove absence.

| Command | Possible execution | Recommendation |
|---|---|---|
| `agentic-kit chat refresher` | no witness | agentic-kit command-for |
| `agentic-kit context render` | no witness | agentic-kit command-for, agentic-kit context render |
| `agentic-kit rule-registry check` | no witness | agentic-kit rule-registry bootstrap |
| `agentic-kit transfer admin-refresh-pr` | agentic-kit boot write, agentic-kit handoff post-merge-refresh-status, agentic-kit handoff prompt, agentic-kit transfer prepare-successor-handoff | no witness |
| `agentic-kit transfer evidence-inspect-latest` | agentic-kit evidence inspect | no witness |
| `agentic-kit transfer evidence-pr-complete` | agentic-kit transfer branch-create, agentic-kit transfer branch-switch, agentic-kit transfer evidence-inspect-latest, agentic-kit transfer post-merge-check, agentic-kit transfer pr-create-complete, agentic-kit transfer push-current, agentic-kit transfer sync-main | no witness |
| `agentic-kit transfer post-merge-check` | agentic-kit handoff post-merge-refresh-status | no witness |
| `agentic-kit transfer post-merge-complete` | agentic-kit boot write, agentic-kit handoff post-merge-refresh-status, agentic-kit handoff prompt, agentic-kit pr wait-ci, agentic-kit transfer chat-switch-complete, agentic-kit transfer normalize-session, agentic-kit transfer prepare-successor-handoff | no witness |
| `agentic-kit transfer post-merge-settle` | agentic-kit boot write, agentic-kit handoff post-merge-refresh-status, agentic-kit handoff prompt, agentic-kit pr wait-ci, agentic-kit transfer chat-switch-complete, agentic-kit transfer normalize-session, agentic-kit transfer prepare-successor-handoff | no witness |
| `agentic-kit transfer pr-closeout-complete` | agentic-kit boot write, agentic-kit handoff post-merge-refresh-status, agentic-kit handoff prompt, agentic-kit pr wait-ci, agentic-kit transfer chat-switch-complete, agentic-kit transfer normalize-session, agentic-kit transfer prepare-successor-handoff, agentic-kit transfer restore-known-volatile | no witness |
| `agentic-kit transfer remote-next` | agentic-kit rules acknowledge | no witness |
| `agentic-kit transfer remote-work-start` | agentic-kit rules acknowledge, agentic-kit transfer branch-create, agentic-kit transfer branch-switch, agentic-kit transfer normalize-session, agentic-kit transfer pull-current, agentic-kit transfer push-current, agentic-kit transfer repo-status | no witness |
| `agentic-kit transfer standard-error-scan` | agentic-kit audit-doc-currency, agentic-kit audit-ns-legacy-references, agentic-kit audit-planning-docs-consolidation, agentic-kit audit-program-redundancy, agentic-kit docs-audit, agentic-kit release-notes-generate, agentic-kit release-prep, agentic-kit release-status, agentic-kit standard-gates-audit-suite, agentic-kit transfer command-reference-check, agentic-kit transfer patch-cycle-status, agentic-kit transfer post-merge-check, agentic-kit transfer repo-status, agentic-kit transfer require-fresh-llm-context | no witness |
| `agentic-kit transfer sync-main` | agentic-kit rules acknowledge, agentic-kit transfer branch-switch, agentic-kit transfer normalize-session, agentic-kit transfer restore-known-volatile | no witness |
| `agentic-kit workflow cleanup` | no witness | agentic-kit transfer branch-delete |
| `agentic-kit workflow state` | no witness | agentic-kit check-docs, agentic-kit doctor |
| `agentic-kit workflow status` | no witness | agentic-kit check-docs, agentic-kit doctor |
| `agentic-kit workspace adopt` | no witness | agentic-kit rule-registry bootstrap |
| `agentic-kit workspace init` | no witness | agentic-kit rule-registry bootstrap |

## Boundaries

- Possible source flow is not a runtime trace, an executed action or an authorization grant.
- Only literal argv prefixes, simple local aliases and resolved helper returns/parameters are followed.
- Only subprocess argv terminals establish execution; shell/executable overrides, opaque kwargs, command strings and Python module launches remain unknown.
- Unknown calls and container mutation invalidate argv prefixes rather than being guessed.
- Dynamic dispatch, methods on instances, global values, relative imports and code inside subprocesses are not expanded.
- Branches over-approximate possible flow; arbitrary path feasibility and exceptions are not proven.
- Only analyzed function bodies contribute references; globals and unreferenced computed commands are not an inventory.
- No universal call graph, lock coverage, kernel claim or G0 graphic is established by these results.

Historical K0/K0c reports are unchanged. Review this evidence before deciding G0; no drawing is authorized here.
