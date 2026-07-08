# Pre-GUI Hardening Tasks
Status: active
Decision status: accepted
Review policy: update when pre-GUI hardening priorities, command contracts, or canonical planning targets change.

This planning file collects the post-v0.4.11 hardening tasks that should be completed before GUI expansion.

Authoritative target for pre-GUI hardening planning: `docs/planning/PRE_GUI_HARDENING_TASKS.md`.

Do not add new pre-GUI planning content to superseded planning documents such as `docs/archive/WORKFLOW_REDUCTION_FOCUS.md`.

<!-- PRE_GUI_HARDENING_V0411_START -->
## Pre-GUI hardening roadmap after v0.4.11

Updated: 2026-06-26

### Context

v0.4.11 completed the release/handoff stabilization work and introduced the Cockpit/Human-Workflow foundation for GUI usage. Before GUI implementation starts, the remaining reliability work must be made explicit in the planning backlog. The goal is to prevent the known failure classes from returning: STATUS.md drift, unclear final release verification, opaque long-running wrappers, missing remote head before PR creation, and handoff/admin-refresh loop risks.

### Priority order

1. **Add `audit-status-current-state`.**
   - Verify that `STATUS.md` current verified main matches `origin/main`.
   - Verify that the documented version, DOI and current verified state match `release-status --include-remote --json`.
   - Integrate this audit into `standard-gates-audit-suite`.
   - This is the highest-priority drift guard before GUI work.

2. **Add `release verify-final`.**
   - Implement as an aggregation wrapper, not a new release subsystem.
   - Combine `release-status --include-remote --json`, `release-publish --dry-run --json`, `post-merge-check`, `repo-status`, `require-fresh-llm-context`, and `audit-status-current-state`.
   - Output one machine-readable final release verdict for human users, LLM handoff, and future GUI.

3. **Add wrapper live-status reporting.**
   - Long-running wrappers must write a current status file, for example `tmp/current-wrapper-status.json`.
   - Minimum fields: wrapper name, phase, primary PR, admin-refresh PR, elapsed seconds, `safe_to_interrupt`, and next poll time.
   - This is required before GUI buttons can safely represent running PR/release/handoff workflows.

4. **Harden `pr-create-complete` with `ensure-remote-head`.**
   - Before PR creation, verify that the remote head branch exists.
   - Verify that the remote branch points to the local `HEAD`.
   - If missing or stale, push through the existing safe wrapper path or block with a precise diagnostic.
   - This removes the repeated “remote head does not exist / no commits” failure mode.

5. **Promote admin refresh to an explicit state machine.**
   - Model the lifecycle states: `product_pr_merged`, `admin_refresh_required`, `admin_refresh_branch_created`, `admin_refresh_pr_created`, `admin_refresh_ci_waiting`, `admin_refresh_merged`, `main_resynced`, `post_merge_verified`, `fresh_context_verified`.
   - Add a machine-readable status command, for example `transfer admin-refresh-status --json`.
   - This should be implemented outside the already large `transfer.py` where practical.

6. **Add `transfer refresh-handoff-final`.**
   - Implement only after the admin-refresh state model exists.
   - The command must force `main`, require a clean worktree, generate the final handoff, publish the outbox/report carrier, detect and discard non-committable self-referential projections, verify fresh context, and leave no dirty `main`.

7. **Add `release publish-readiness`.**
   - Keep the existing capability-gated publish behavior.
   - Add a GUI/human-facing readiness report that explains whether dry-run passes, whether `.agentic/release/ENABLE_LIVE_PUBLISH` is required, whether it is present, and what the next safe action is.
   - This should reduce accidental live-publish attempts and make the guarded execute path easier to operate.

8. **Extend the Cockpit action inventory.**
   - Add GUI-relevant actions for `release.prepare`, `release.publish_readiness`, `release.publish_execute_guarded`, `release.verify_final`, `handoff.refresh_final`, `admin_refresh.status`, and `work.start/check/finish/recover`.
   - Each action should declare safety, clean-worktree requirements, write behavior, network requirements, expected duration, and next actions on pass/block.

9. **Connect GUI gatekeeper status to the new final checks.**
   - `cockpit gatekeeper-status` should include the new status-current-state, release-final, wrapper-live-status, and admin-refresh readiness signals.
   - GUI should consume one stable machine-readable readiness surface instead of re-implementing CLI logic.

10. **Start GUI prototype only after the above gates are stable.**
    - GUI buttons should call Cockpit actions or bounded wrappers only.
    - GUI must not directly recreate shell/git/release logic.
    - The first GUI milestone should be read-only status plus explicitly bounded actions, not full free-form control.

### Already implemented or partially implemented

- `release-publish` already behaves idempotently when the release lifecycle is `current_verified`; preserve this with regression tests.
- `release-status --include-remote --json` already covers much of the final release state; `release verify-final` should reuse it.
- The publish capability gate already exists; `publish-readiness` should make it observable rather than replacing it.
- The Cockpit concept already exists; the remaining work is to complete its action inventory and metadata for GUI use.

### Implementation constraint

Do not create a parallel CLI. These tasks must harden or wrap existing `agentic-kit` commands and expose clearer machine-readable state for humans, LLM handoff and the future GUI.
<!-- PRE_GUI_HARDENING_V0411_END -->

<!-- PRE_GUI_TARGET_GUARD_START -->
## Planning Target Guard

Purpose: prevent future LLMs, scripts, or wrapper flows from adding new planning content to superseded planning files merely because such files still exist.

### Required hardening slices before GUI expansion

1. Add a planning target resolver.

   Proposed interface:

       agentic-kit planning resolve-target --kind pre_gui_hardening --json

   Expected machine-readable behavior:

       {
         "result_status": "PASS",
         "target": "docs/planning/PRE_GUI_HARDENING_TASKS.md",
         "forbidden_targets": [
           "docs/archive/WORKFLOW_REDUCTION_FOCUS.md"
         ],
         "reason": "WORKFLOW_REDUCTION_FOCUS.md is superseded"
       }

   Scripts must use this resolver instead of guessing from existing files.

2. Block writes to superseded planning documents.

   `audit-doc-currency` or a dedicated planning-target gate must return `BLOCK` when a file marked `status: superseded` in `docs/DOCUMENTATION_REGISTRY.yaml` receives new planning content.

   Allowed exceptions:
   - removing obsolete content,
   - adding or updating a superseded notice,
   - moving content into the active canonical target,
   - other explicitly labelled cleanup-only changes.

3. Extend protected-diff handling for `docs/archive/WORKFLOW_REDUCTION_FOCUS.md`.

   Required behavior:
   - adding new sections: `BLOCK`,
   - deleting obsolete sections: allowed,
   - updating superseded/link notices: allowed,
   - moving content to the active canonical file: allowed.

4. Keep the canonical target explicit.

   Current canonical pre-GUI hardening target:

       docs/planning/PRE_GUI_HARDENING_TASKS.md

   If the project later becomes strictly YAML-first, the resolver may redirect to:

       docs/planning/PROJECT_DIRECTION.yaml

   but it must never silently fall back to `docs/archive/WORKFLOW_REDUCTION_FOCUS.md`.

5. Update script templates.

   Replace fallback logic such as “first existing planning file wins” with resolver-driven logic.

   Example target resolution:

       TARGET="$(./.venv/bin/agentic-kit planning resolve-target --kind pre_gui_hardening --json | jq -r .target)"

   If the resolver cannot determine a non-superseded target, the script must `BLOCK` instead of guessing.

### Implementation constraint

Do not create a parallel CLI. Add this as a small planning/gatekeeper capability inside the existing `agentic-kit` command family and integrate it into the existing docs/planning gates.
<!-- PRE_GUI_TARGET_GUARD_END -->
