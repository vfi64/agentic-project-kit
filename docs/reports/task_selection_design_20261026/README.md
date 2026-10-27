<!-- Historical proposal before owner adoption; runtime authority is the generated manifest task_routes export. -->
# D1 — Proposed task matrix

**Proposed and inactive. Owner review required.**
No runtime reads this fixture; no MATCH grants execution or selects an argv.

Reviewed base: `94ee01063ea6e92bd6552b2e22fb1d57a8300e56`; current manifest `afb7c5e544e0`.

| Intent | Existing command | Phase | Known-state conditions | Inputs | Manifest safety |
|---|---|---|---|---|---|
| check_work | `agentic-kit check` | diagnostic | workspace_mode=managed | none | READ_ONLY |
| diagnose_repository | `agentic-kit doctor` | diagnostic | workspace_mode=managed | none | READ_ONLY |
| assess_adoption | `agentic-kit workspace adopt` | diagnostic | workspace_mode=unmanaged | none | READ_ONLY |
| initialize_workspace | `agentic-kit workspace init` | planning | workspace_mode=unmanaged | none | BOUNDED |
| start_work | `agentic-kit work start` | guarded | workspace_mode=managed, worktree_clean=True | branch | BOUNDED |
| finish_work | `agentic-kit work finish` | planning | branch_role=work, workspace_mode=managed | branch, title, message, paths | BOUNDED |
| complete_open_pr | `agentic-kit transfer pr-complete` | guarded | pr_state=open, workspace_mode=managed | pr_number, expected_head_sha | BOUNDED |
| settle_merged_pr | `agentic-kit transfer pr-closeout-complete` | guarded | pr_state=merged, workspace_mode=managed | after_pr | BOUNDED |
| prepare_handoff | `agentic-kit transfer chat-switch-complete` | guarded | workspace_mode=managed | none | BOUNDED |
| update_kit | `agentic-kit kit update` | planning | branch_role=work, workspace_mode=managed, worktree_clean=True | version | BOUNDED |
| release_version | `agentic-kit release run` | guarded | branch_role=main, release_state=none, workspace_mode=managed, worktree_clean=True | version | BOUNDED |

## Per-route review notes

- **check_work**: Gate outcome is not proof that requirements are correct.
- **diagnose_repository**: Inspect health; do not infer a repair or execute one.
- **assess_adoption**: Assessment may recommend initialization; recommendation is not execution.
- **initialize_workspace**: Inspect the installed command plan; do not add --execute from a selection result.
- **start_work**: Fetch and branch effects require the existing operation authorization.
- **finish_work**: Whole-slice plan; an already open PR is a separate explicit intent, never inferred from closeout tags.
- **complete_open_pr**: Pending CI is handled by the selected workflow; selection does not authorize its merge.
- **settle_merged_pr**: Handoff refresh may itself merge an administrative PR; include that effect in operation consent.
- **prepare_handoff**: Writes generated repository projections despite having no remote effect.
- **update_kit**: Planning can download wheels and write temporary reports; signature-gated install remains separate.
- **release_version**: Fresh release only; existing runs need a separate explicit resume/recovery intent. Without --execute the orchestrator still performs local A/B preparation; publication consent stays separate and version/tag/head-bound.

Structural validation is not semantic acceptance. Release run remains guarded despite declared preview availability; it writes preparation state before its publication gates. Pending CI is handled inside pr-complete, not by selecting a different route.

The recommended future authority is one task_routes export in the existing manifest, with authenticated identity coverage. Existing raw/tag selection remains compatible. See the proposed ADR and contract; this fixture must not become a second runtime registry.
