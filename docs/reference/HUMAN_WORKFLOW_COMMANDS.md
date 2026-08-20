# Human Workflow Meta Commands

These commands provide a small human-facing layer over the lower-level agentic-kit wrappers. They do not replace the lower-level commands. They bundle the safest common sequences for command-line use and future GUI orchestration.

The meta commands are intentionally conservative:
- work finish is dry-run by default.
- work finish opens a review PR with generated handoff closeout markers by default.
- merging is an explicit opt-in for maintainer-authorized closeout flows.
- release prepare is dry-run by default.
- release version values are supplied by the caller.
- previous release tags are derived from the latest local v* git tag unless explicitly supplied.
- low-level transfer commands remain available for diagnosis and recovery.

## agentic-kit work start

Start a patch, docs, or release-adjacent slice from a clean synchronized base.

Typical use:

    agentic-kit work start --branch codex/my-slice --kind patch --json

It runs sync-main, rules acknowledge, post-merge-check, repo-status, and then creates or switches to the requested branch.

## agentic-kit work check

Run common checks during a slice.

Typical use:

    agentic-kit work check --profile minimal --json
    agentic-kit work check --profile code --json
    agentic-kit work check --profile docs --json
    agentic-kit work check --profile release --json

## agentic-kit work finish

Finish a slice. It plans by default. On execution it commits selected work,
refreshes and commits the generated successor handoff package, pushes the
branch, opens a review PR, waits for CI, and verifies the PR body carries the
pending post-merge handoff marker.

Typical use:

    agentic-kit work finish --branch codex/my-slice --title "My slice" --message "My slice" --path src/file.py --dry-run --json

Use --execute only after reviewing the plan and selected paths.
Use --merge only for an explicitly authorized merge-and-post-merge closeout.

## agentic-kit work recover

Run safe recovery and status commands after interrupted work.

Typical use:

    agentic-kit work recover --json

## agentic-kit release ready

Run release readiness through standard-error scan and release-status checks.

Typical use:

    agentic-kit release ready --version <version> --from-tag <from-tag> --date <date> --json

If --from-tag is omitted, the command derives it from the latest local v* git tag.

## agentic-kit release prepare

Generate release-notes summary evidence and run release-prep. It is dry-run by default.

Typical use:

    agentic-kit release prepare --version <version> --from-tag <from-tag> --date <date> --dry-run --json

Use --write only when readiness checks are clean. A successful write also refreshes command entrypoints and writes
`docs/reports/release/release-prepare-<version>.json` as release-metadata authority evidence for PR and CI gates.

## Preference and fallback rule

The authoritative preference and fallback policy is defined in these repository rule sources:

- `.agentic/transfer_safety_rules.yaml`
- `.agentic/transfer/one_command_transfer_protocol.yaml`

This document explains the human-facing commands. It must not duplicate the full policy payload. Local-to-LLM transfer headers, successor handoff contracts, and generated projections should render the current policy dynamically from those rule files.
