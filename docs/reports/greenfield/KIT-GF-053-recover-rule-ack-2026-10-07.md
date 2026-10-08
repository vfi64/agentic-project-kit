# KIT-GF-053 — Preserve rule acknowledgement during recovery

Source ledger: `vfi64/agp-Cockpit`, `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read at `origin/main` commit `382d00da48c617b516b758f57f1821611cc8db99`. The source workspace remains unchanged. Implementation and validation: 2026-10-08.

## Finding and repair

The volatile-output repair deleted `.agentic/rule_ack/current.json`, removing the authorization input needed by the next commit. The shared repair helper now excludes the acknowledgement directory and its children before either restoring tracked files or removing untracked files. This preserves current bytes, including legacy tracked state, while retaining the existing dirty-status and commit-exclusion policies.

When commit is blocked by its rules-confirmed capability, the next action names `agentic-kit rules acknowledge` first. JSON commit failures emit one JSON document with the acknowledgement decision and blocking reasons. Preservation does not confirm a stale or invalid acknowledgement: the normal snapshot validator still blocks it.

## Regression and external retest

`tests/test_recover_rule_ack.py::test_recover_then_transfer_commit_without_reacknowledging` uses a real temporary external Git workspace, acknowledges once, changes a product file, invokes the recovery composition through actual local Kit CLI routes, and successfully commits through `transfer commit` without another acknowledgement. Remote CI lookup is replaced by a no-op in this fixture. Dirty-worktree normalization may remain BLOCKED and product work stays intact.

Additional tests prove byte-preservation for untracked and legacy tracked acknowledgements and that a missing acknowledgement gives a pure-JSON, acknowledge-first diagnostic without a commit.

Cockpit should repeat the ledger regression with the released Kit on a dirty work branch and verify the selected product change commits after recovery. Only Cockpit sets VERIFIED_FIXED. The native Kit work branch was not recovered or discarded during this slice.
