# Post-PR809 kit-generated handoff drift evidence

Status: stale-generator-output-evidence
Use-as-successor-prompt: no
Canonical successor override: docs/reports/terminal/post-pr809-successor-handoff-override.yaml

## Why this file exists

This file records that `agentic-kit handoff prompt` was run during the post-PR809 handoff-file slice, but its generated output was stale because the current status and handoff state still contained older anchors.

The original generated prompt included stale references such as `c07f8ec`, `cf75340`, PR #766, PR #791, and v0.4.2 release-preparation state. Those references are not the current post-PR809 safe state and must not be used as successor-chat instructions.

## Current authoritative handoff file for this slice

Use the YAML override instead:

- `docs/reports/terminal/post-pr809-successor-handoff-override.yaml`

## Required successor behavior

A successor chat must read `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`, inspect `docs/reports/terminal/pr809-merge-finalize-summary-recovery.log`, and then follow the override YAML. It must not treat stale generated prompt content as authoritative.

## Evidence interpretation

This file is intentionally short and additive. It preserves the fact that the generator was run while preventing stale generated prose from becoming an apparent source of truth.
