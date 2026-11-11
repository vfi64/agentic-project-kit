# KIT-GF-104: Generator types in the workspace recovery path

Date: 2026-11-08

Scope: `workspace init --recover-partial` for projects created by `agentic-kit init`.

Status: fix merged on Kit `main` in PR #2755 (`212cddcf`); not released.

## Finding

A project created by `agentic-kit init --type python-cli` (likewise
`python-lib` and `governance-wrapper`) keeps the generator type in
`.agentic/project.yaml`. Its incomplete operating layer has no
`.agentic/config.yaml` yet. Plain `workspace init` correctly stays
`FOREIGN_AGENTIC`, but `--recover-partial` compared the generator type against
the narrower workspace type set and returned BLOCKED, so the documented
recovery route was unusable for every generator type except `generic`.

## Change

Only the recovery path uses an explicit generator-to-workspace mapping
(`GENERATOR_TO_WORKSPACE_PROJECT_TYPES` in `workspace.py`, applied in
`workspace_recovery._recovery_plan`): `python-cli`, `python-lib` and
`governance-wrapper` map to `python`; `generic` stays `generic`. Unknown
generator types are BLOCKED. `ALLOWED_PROJECT_TYPES` and the generator types
are unchanged, and the preserved project contract is not rewritten. The signed
`approval_subject` records both `generator_project_type` and
`workspace_project_type`. A `--type` override that matches the mapped
workspace type is accepted; a conflicting override is BLOCKED without writes.

## Regression evidence

New tests in `tests/test_workspace_recovery.py`:

- `test_generated_type_mapping_recovery` (parametrized over the three
  generator types): real `init` output, plan AWAITING_APPROVAL with both types
  in the approval subject, execution PASS, `project.yaml` byte-identical,
  `check` and `doctor` exit 0, repeated recovery is a no-write PASS.
- `test_generator_type_override_and_unknown_block_without_writes`: matching
  override accepted, conflicting override and unknown generator type BLOCKED,
  workspace snapshot unchanged.

Counterprobe (2026-11-08): the test module from `212cddcf` run against the
source of the PR base `03f0a51e` gives `4 failed, 25 passed`; the plan returns
BLOCKED instead of AWAITING_APPROVAL. Against `212cddcf` it gives `29 passed`.

CI: the first PR head `a157bf1` failed in test shards 0 and 1 because `init`
creates its initial commit only when a Git identity exists and CI runners have
none. Commit `2916e02` sets a fixture identity through `GIT_AUTHOR_*` and
`GIT_COMMITTER_*` in these tests only; no product behavior changed. Final PR
head `ecb93c5`: `test`, `test-shard (0..2)` and `classify` succeeded,
`pytest-parallel-shadow` skipped.

## Boundaries

Kit closure does not establish external consumer `VERIFIED_FIXED`. The finding
now has a catalog retest description, but the installed-runtime harness has no
partial generator project fixture. No release is claimed.
