# KIT-GF-112: post-merge-complete after a failed final cleanup

Date: 2026-11-14

Scope: `transfer post-merge-complete` (`cli_commands/transfer_post_merge_complete.py`).

Status: fixed in this change; not released.

## Finding

After the post-merge lifecycle, `post-merge-complete` restores known volatile
transfer paths. When that final cleanup left the tree dirty, the command exited
2 but its JSON still said `result_status: PASS` (only the chat reply and the
missing completion receipt hinted at the problem). A consumer that reads
`result_status` saw success; an existing test pinned the PASS.

## Change

A failed final cleanup after a passing lifecycle turns the result into
`FinalCleanupBlockedResult`: `result_status` BLOCKED, `returncode` 2,
`blocker` `known_volatile_final_cleanup_failed`, and `lifecycle_result_status`
keeps the lifecycle's own status. The result carries the human route (G3) with
the dirty paths and the read-only follow-up `agentic-kit transfer
post-merge-check`; the text summary shows `STATE: BLOCKED`. A lifecycle that
already failed keeps its own status. Exit codes are unchanged.

## Regression evidence

`test_post_merge_complete_cli_blocks_when_final_volatile_cleanup_fails`
(`tests/test_transfer_post_merge_complete_command.py`) now requires BLOCKED,
the lifecycle status, no completion receipt, a valid human route and the
BLOCKED text summary. Against the previous code it fails with
`'PASS' == 'BLOCKED'`.

## Boundaries

The transfer report written before the final cleanup still records the
lifecycle result. A blocked LLM context-carrier refresh keeps a PASS result
without a completion receipt; that path is unchanged here. The route merges a
pull request, so the local retest harness does not run it. No release or
consumer `VERIFIED_FIXED` is claimed.
