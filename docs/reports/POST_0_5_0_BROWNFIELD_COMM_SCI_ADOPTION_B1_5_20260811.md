Status: evidence
Status-date: 2026-08-11
Scope: Phase B1.5 bounded Brownfield adoption probe

# Brownfield Adoption Probe: Comm-SCI-Control-private

## Classification

`PASS_WITH_LIMITATIONS`

The Kit successfully initialized a bounded operating-layer workspace in a real
external repository on a local adoption branch, preserved the existing
repository authority files, passed the target repository's own local gates, and
proved a rollback path after a Kit cleanup defect was fixed.

This is not a claim that `vfi64/Comm-SCI-Control-private` is fully Kit-managed.
No remote target PR was opened or merged because the full Kit handoff and doctor
paths still assume self-hosting or generated-project sources that the external
repository does not contain.

## Exact Inputs

- Kit repository baseline before this slice:
  `03a2d8afbd91e6f536ebdb728d5470f75c5cc3a8`.
- Kit branch for the evidence slice:
  `codex/phase-b1-b3-c1-validation`.
- Target repository: `vfi64/Comm-SCI-Control-private`.
- Target baseline:
  `e65d6c8a8c02204420703829a171f9423a5a49bf`.
- Target local adoption branch:
  `codex/b1-agentic-kit-adoption-20260811`.
- Target local adoption commit:
  `7f29b30bab2cbb37c4e2dd0119bb639c94dc500a`.
- Maintainer adjudication: the current chat authorized bounded external
  adoption and rollback work for Phases B and C.

## Target Repository Boundary

The target repository's existing `AGENTS.md` and README remained the authority
for its behavior. The probe treated these as manual preservation surfaces:

- canonical JSON ruleset remains source of truth;
- active entrypoint remains `Comm-SCI-Control-App2.py`;
- target test command remains `PYTHONPATH=src pytest -q`;
- target quality gate remains `python scripts/quality_gate.py --mode all`;
- no existing governance, specification, CI, or application file was rewritten.

## Adoption Execution

The executed workspace init wrote the standard operating-layer baseline:

- `.agentic/config.yaml`;
- `.agentic/DOC_LIFECYCLE.md`;
- `.agentic/INITIAL_LLM_PROMPT.md`;
- `.agentic/ci/agentic-gate.yaml`;
- `.agentic/ci/pre-commit-snippet.yaml`;
- `.agentic/dpa/workspace_init_projection.json`;
- `.agentic/registries/documentation.yaml`;
- `.agentic/registries/rules.yaml`;
- `.agentic/rules/README.md`;
- `.agentic/state/README.md`;
- `.agentic/state/handoff/README.md`;
- `.agentic/state/status.md`;
- `docs/archive/README.md`;
- one `.gitignore` line: `.agentic/tmp/`.

The target commit changed 14 files with 146 insertions. The init preview and
execute paths reported no CI or pre-commit injection targets.

## Target Gates

The adopted target branch passed the repository's own local validation:

- `bash scripts/setup_venv.sh --python python3.13 --venv .venc313`: PASS,
  including `pip check`.
- `PYTHONPATH=src .venc313/bin/python -m pytest -q`: 1423 passed.
- `.venc313/bin/python scripts/quality_gate.py --mode all`: PASS.
- `agentic-kit workspace upgrade --root <target> --json`: PASS, dry-run,
  already at schema v1.

One target test run changed `Config/Comm-SCI-Config.json` as a runtime side
effect. That change was restored because it was not part of the adoption
surface. The target adoption branch was clean after committing the Kit-generated
baseline.

## Kit Gates Against Target

The classic Kit-wide checks do not yet fit this external operating-layer
workspace:

- `agentic-kit check --root <target>` failed because the command still expects
  generated/self-hosting project files such as `sentinel.yaml`.
- `agentic-kit doctor --root <target>` failed because the external repo does
  not contain self-hosting governance sources such as `docs/STATUS.md`,
  `docs/TEST_GATES.md`, `docs/handoff/CURRENT_HANDOFF.md`,
  `docs/architecture/ARCHITECTURE_CONTRACT.md`, and
  `docs/DOCUMENTATION_COVERAGE.yaml`.

These failures are useful evidence: `workspace init` can establish the
operating layer without overwriting the foreign project, but the health and
handoff commands still need an external-workspace mode before the Kit can claim
full continuation readiness.

## Handoff Continuation Probe

`agentic-kit transfer chat-switch-complete --output-dir
.agentic/state/handoff/packages/latest --no-update-canonical-prompts --json`
was run against the adopted target branch.

Result: `FAIL`.

The validation report listed missing self-hosting handoff sources, including:

- `.agentic/compiled_agent_context.yaml`;
- `.agentic/handoff_state.yaml`;
- `.agentic/operational_handoff_state.yaml`;
- `.agentic/rule_mechanism_inventory.yaml`;
- `.agentic/rule_migrations.yaml`;
- `.agentic/rule_preservation.yaml`;
- `SECURITY.md`;
- `docs/DOCUMENTATION_COVERAGE.yaml`;
- `docs/TEST_GATES.md`;
- `docs/planning/PROJECT_DIRECTION.yaml`;
- `docs/reference/AGENTIC_KIT_COMMANDS.md`;
- `docs/reference/agentic-kit-commands.json`.

The failed generated handoff projection was not committed in the target
repository. `agentic-kit handoff check` also failed because the adopted external
workspace does not contain `.agentic/handoff_state.yaml`.

## Rollback Probe

A fresh local clone of the adoption branch exposed a real Kit defect:

- `workspace remove --execute` removed tracked generated `.agentic` files;
- the lock created `.agentic/tmp`;
- the command then left the empty `.agentic/tmp` directory behind;
- a second remove was blocked as `foreign_agentic_without_workspace_manifest`.

The Kit fix in this slice makes `workspace remove` prune directories from the
plan rebuilt inside the mutation lock. That includes directories introduced by
the lock itself.

Post-fix rollback evidence in a fresh copy:

- first `workspace remove --execute --json`: PASS, `written=true`;
- the 12 generated `.agentic` files were removed;
- the `.agentic` directory was pruned;
- second `workspace remove --json`: NOOP, `written=false`;
- no `.agentic/` directory remained.

The safe default still preserves `docs/archive/README.md` and the `.gitignore`
line, matching the documented bounded cleanup behavior.

## Decision

The existing Comm-SCI repository takeover has succeeded as a local bounded
adoption experiment. It has not succeeded as a complete remote adoption or
successor-continuation workflow.

The next implementation work should add an external-workspace health and
handoff mode that validates `.agentic/config.yaml` workspaces without requiring
the full self-hosting Kit source set.
