# Human Workflow Meta Commands

These commands provide a small human-facing layer over the lower-level agentic-kit wrappers. They do not replace the lower-level commands. They bundle the safest common sequences for command-line use and future GUI orchestration.

The meta commands are intentionally conservative:
- work finish is dry-run by default.
- work finish executes the full four-part slice closeout by default after `--execute`: work commit, handoff commit, PR/CI/merge, and post-merge handoff refresh PR.
- review-only PR publishing is an explicit opt-out with `--no-merge`.
- release prepare is dry-run by default.
- release run is resumable and stops at signed gates before irreversible release effects.
- release version values are supplied by the caller.
- previous release tags are derived from the latest local v* git tag unless explicitly supplied.
- low-level transfer commands remain available for diagnosis and recovery.

## JSON output contract (KIT-GF-023)

With `--json`, stdout contains exactly one JSON document, including transfer
capability blockers and early runtime/input errors. Consumers can use
`json.loads(stdout)` directly; terminal markers such as `FINAL_SIGNAL` and
`FINAL_NEXT` are confined to text mode or represented inside JSON string fields.
Pre-result errors include `result_status`, `returncode`, `error` and `next_action`.
The existing exit codes and remote actions are unchanged. Malformed CLI syntax
continues to use the CLI framework's stderr diagnostics.

## External documentation audit

Use `agentic-kit docs-audit --json` for a read-only audit of an external manifest
workspace's declared documents, version anchors, registry and optional handoff
contracts. `hygiene.doc_lifecycle: warn` keeps lifecycle warnings non-blocking;
missing declared files and integrity drift still block. Explicit
`agentic-kit doc-lifecycle-audit --strict --json` enforces lifecycle blockers.
See `docs/governance/DOCUMENTATION_SYSTEM_AUDIT_CONTRACT.md` for applicability.

## agentic-kit work start

Start a patch, docs, or release-adjacent slice from a clean synchronized base.

Typical use:

    agentic-kit work start --branch codex/my-slice --kind patch --json

For the default `main` start ref, it runs sync-main, rules acknowledge,
post-merge-check, repo-status, and then creates or switches to the requested
branch.

For a non-main `--from-ref`, such as a release tag or remote-tracking
integration branch, it fetches refs, acknowledges rules, skips the post-merge
check as a pre-PR gate, runs repo-status, and then creates or switches to the
requested branch. The lower-level branch-create wrapper accepts any start point
that resolves to a commit, including tags and `origin/...` refs.

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
branch, opens the PR, waits for CI, merges, and runs the post-merge handoff
refresh closeout. The merge path requires the composite command's JSON
completion proof, including the PR number, `PASS` status, and verified
post-merge handoff completion; a zero process exit alone is insufficient.

Typical use:

    agentic-kit work finish --branch codex/my-slice --title "My slice" --message "My slice" --path src/file.py --dry-run --json

Use --execute only after reviewing the plan and selected paths.
Supply `--body` or `--body-file` for the PR description, and
`--release-note-category Fixed` (or another supported release category) to classify
the PR deterministically. The category is placed in the first body line as
`release-note-category: Fixed`, within the release-notes classifier's first 40 lines.
Both merge and review-only modes carry this metadata. The dry-run JSON includes
`pr_body`; unreadable files, unsupported or conflicting categories, and simultaneous
body options return `BLOCKED` before any subprocess or write.
Use --no-merge only when the intended result is an open review PR with pending
post-merge handoff markers.

## agentic-kit work recover

Run safe recovery and status commands after interrupted work.
Recovery preserves `.agentic/rule_ack/current.json` byte for byte, including
legacy tracked acknowledgements. It remains local runtime input, excluded from
commits. A dirty product file is preserved and may keep normalization `BLOCKED`;
a valid prior acknowledgement still permits a subsequent selected-path commit.
If acknowledgement is missing or stale, the commit stays blocked and names
`agentic-kit rules acknowledge` first in `next_action`; `--json` returns only JSON.

Typical use:

    agentic-kit work recover --json

## agentic-kit work rescue

Rescue local work from `main` before realigning `main` to the local `origin/main`. The command is dry-run by default and has no remote effect. On execution it creates a local `rescue/...` branch, commits dirty work there when needed, verifies that the rescue branch contains the original `HEAD`, and only then resets `main` to the local base ref.

Typical use:

    agentic-kit work rescue --json
    agentic-kit work rescue --execute --expected-signature <dry-run-signature> --json

Use this when `main` has uncommitted changes or local commits that block normal startup recovery.

## agentic-kit release ready

Run release readiness through standard-error scan and release-status checks.

Typical use:

    agentic-kit release ready --version <version> --from-tag <from-tag> --date <date> --json

If --from-tag is omitted, the command derives it from the latest local v* git tag.

Repeat `--summary-line "<text>"` to add an explicit changelog summary line to the
generated release-notes lines; it reaches the release-prep dry-run of the scan
(KIT-GF-045).

## agentic-kit release prepare

Generate release-notes summary evidence and run release-prep. It is dry-run by default.

Typical use:

    agentic-kit release prepare --version <version> --from-tag <from-tag> --date <date> --dry-run --json

Repeat `--summary-line "<text>"` with the same lines as in `release ready` when the
generated lines alone do not cover the changelog quality categories; the evidence
report records them as `explicit_summary_lines` (KIT-GF-045).

Use --write only when readiness checks are clean. A successful write also refreshes command entrypoints and writes
`docs/reports/release/release-prepare-<version>.json` as release-metadata authority evidence for PR and CI gates.

In the Kit repository and external workspaces, creating a release section consumes exactly the matching
Unreleased bullets carried into that release, keeping the Unreleased heading.
Unmatched entries and historical sections are preserved. The dry run lists
CHANGELOG.md without modifying it; refreshing an existing release does not consume
later entries, even when their text is identical (KIT-GF-060, KIT-GF-064).

Release summaries must be single-line entries. In external workspaces, an existing
target release section with indented continuations, paragraphs or blank separators
between lists blocks preparation before writing. The error names CHANGELOG.md,
the version, line numbers and bounded excerpts, and requires one list of one-line
bullets. Release-publish surfaces the same diagnosis and preparation JSON errors
instead of only naming a changed file (KIT-GF-052). Historical release sections
and Unreleased entries are outside this target-section validation.

## agentic-kit ci status

Use `agentic-kit ci status --commit <sha> --branch <branch> --json` when a workflow needs the GitHub Actions verdict for a commit or branch without a pull request, such as main after a merge. The command is read-only and returns structured `PASS`, `PENDING`, or `BLOCKED` JSON instead of requiring raw `gh run list` parsing.

## agentic-kit release run

Run the end-to-end release lifecycle through existing orchestrators. It composes
`transfer sync-main`, `release ready`, `release prepare`, `work start`,
`work finish`, `release-publish`, the configured package-index workflow,
`post-release-check`, `post-release-doi-closeout`, and final `release-status`.

Typical use:

    agentic-kit release run --version <version> --json
    agentic-kit release run --version <version> --execute --expected-signature <signature> --json

The command records state and subprocess logs under the workspace temp root, for
example `.agentic/tmp/release-run-<version>.json` and `.agentic/tmp/release-run-<version>.log`.
Reruns resume at the first unfinished step.

The declared publication policy selects the steps (KIT-GF-065): `none` ends at
C2; `github` adds C4; `github+pypi` also adds C3; `github+pypi+zenodo` also adds
D1–D5. Only those steps can be offered or covered by upfront consent. A C3
workflow file must exist before its gate can be approved. Github-only C4 does
one post-release check without a Zenodo wait.

Set `release.branch_prefix: release/` to use `release/<version>` and
`release/<version>-doi`. The unset default remains `codex/release-<version>`.
Prefixes must be safe relative branch prefixes ending in `/` or `-`.
Resuming after a publication-policy or branch-prefix change blocks before actions;
existing upfront consent also binds the applicable step sequence.

The command stops with `AWAITING_APPROVAL` at these gates:

- B4: execute `work finish` for the release metadata branch.
- C2: execute signed `release-publish`.
- C3: dispatch and watch the configured package-index workflow.
- D4: execute `work finish` for the DOI closeout branch.
- D2R: recover a failed D4 on a replacement DOI branch, with a fresh signed approval.

Each gate prints an `approval_signature` over the exact branch, paths, tag,
target commit, or workflow it will affect. A rerun with `--execute
--expected-signature <signature>` executes only that gate, then continues until
the next gate or blocker. A stale signature blocks without running the gated
remote effect. If the workspace publication policy is `none`, package-index
publication, Zenodo wait, and DOI closeout are skipped.

After a failed D4, return to clean main through `transfer sync-main`, then run
`agentic-kit release run --version <version> --json`. This offers D2R, binding the
source PR and head, replacement branch, current commit, regenerated paths and
DOI facts. Approve using the exact `next_action` printed by this dry run.
D2R starts `codex/release-<version>-doi-recovery` from current main, regenerates
closeout, acknowledges rules immediately before `transfer commit`, pushes, and
uses `transfer pr-create-complete --post-merge-complete` to merge the replacement
and handoff. `transfer pr-close-superseded` closes the original PR only after the
replacement has merged into the same base and its original head still matches.
The original branch is preserved. A failed recovery resumes its completed actions
after a fresh approval; it does not repeat regeneration or a completed commit.
Dirty starts, source-head drift and unrelated pre-existing recovery branches block.
If work start synchronizes a newer main, D2R stops before writing and requires
a fresh approval over the new target commit and regenerated paths.

### Declared release consent

Set `release.approval: per_gate` or `release.approval: upfront` in
`.agentic/config.yaml`. With either explicit policy, execution requires
`--approved-by <owner>` and `--consent-source <work-order-or-click-reference>`.
These fields record caller-supplied attribution; they do not authenticate identity.
The default remains per-gate approval. Legacy callers without a declared policy
remain compatible, with missing attribution explicitly recorded as unspecified.

With `upfront`, the first B4 preview includes the consented release plan: version,
tag, preparation and DOI branches, publication policy, summary lines and workflow
inputs, plus B4's paths and source commit. Execute its signature once with the
attribution fields. Matching C2, C3 and D4 gates then proceed under that recorded
consent, including on resume. The only allowed commit transition is the successful
Kit B4 merge and handoff; its resulting HEAD is recorded as the publication target.
A changed version, tag, policy, workflow, summary or target commit blocks.
FAIL/BLOCKED stops the run; D2R recovery always needs a separate signed approval.
Gate subjects, approver, consent source and commit transition are retained in
the state, JSON result and append-only release log (KIT-GF-061).

C3 dispatches the workflow against the release tag and records dispatch intent
before the remote call. It takes a pre-dispatch run inventory, then searches up
to six times, two seconds apart, for the unique matching workflow_dispatch run,
head SHA and creation time. The inventory excludes older runs within GitHub's
one-second timestamp precision. Legacy dispatch states use the strict timestamp.
Missing or ambiguous identity blocks; a rerun searches the saved dispatch and
never dispatches it again. Every query is logged. Incomplete legacy identity
requires inspection, with no automatic redispatch (KIT-GF-055 follow-up).

`agentic-kit transfer pr-close-superseded <pr> --replacement-pr <merged-pr>
--expected-head-sha <sha> --json` is a dry run by default. Its `--execute` route
changes only the verified source PR's open state and emits one JSON document with
`--json`; its manifest declares `pull_request` and `network_read` remote effects.

## Preference and fallback rule

The authoritative preference and fallback policy is defined in these repository rule sources:

- `.agentic/transfer_safety_rules.yaml`
- `.agentic/transfer/one_command_transfer_protocol.yaml`

This document explains the human-facing commands. It must not duplicate the full policy payload. Local-to-LLM transfer headers, successor handoff contracts, and generated projections should render the current policy dynamically from those rule files.
