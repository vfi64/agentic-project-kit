# Agentic Kit Command Reference

Generated from `docs/reference/agentic-kit-commands.json`.

## `agentic-kit transfer pr-complete`

Wait for PR CI, merge safely, sync main, acknowledge rules, and run post-merge completion.

| Parameter | Required | Meaning |
|---|---:|---|
| `pr_number` | yes | Pull request number to complete. |
| `--expected-head-sha` | no | Expected PR head SHA; use a full SHA or current alias where supported. |
| `--merge-method` | no | GitHub merge method, usually squash. |

## `agentic-kit transfer pr-wait-ci`

Wait until PR checks are ready.

| Parameter | Required | Meaning |
|---|---:|---|
| `pr_number` | yes | Pull request number. |
| `--expected-head-sha` | no | Expected PR head SHA. |

## `agentic-kit transfer pr-merge-safe`

Merge a green PR through the guarded merge path.

| Parameter | Required | Meaning |
|---|---:|---|
| `pr_number` | yes | Pull request number. |
| `--expected-head-sha` | no | Expected PR head SHA. |
| `--merge-method` | no | GitHub merge method. |

## `agentic-kit transfer post-merge-complete`

Complete the post-merge lifecycle after a PR merge.

| Parameter | Required | Meaning |
|---|---:|---|
| `--after-pr` | yes | The PR number whose merge triggered the lifecycle. |
